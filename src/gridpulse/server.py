"""Dependency-free HTTP API and dashboard server."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import urlparse

from .alarms import derive_alarms
from .health import HealthEngine
from .incidents import IncidentController, IncidentType
from .metrics import render_metrics
from .models import utc_now
from .progression import ProgressionEngine
from .quality import QualityEngine
from .simulator import FleetSimulator


class Application:
    def __init__(self) -> None:
        self.simulator = FleetSimulator()
        self.incidents = IncidentController()
        self.quality = QualityEngine()
        self.progression = ProgressionEngine()
        self.health = HealthEngine()

    def _snapshot(self):
        now = utc_now()
        assets = self.simulator.snapshot(now)
        self.incidents.apply(assets)
        progression = {}
        health = {}
        for asset in assets:
            self.quality.evaluate(asset, now)
            progression[asset.asset_id] = self.progression.evaluate(asset, now)
            health[asset.asset_id] = self.health.evaluate(
                asset,
                progression[asset.asset_id],
                now,
            )
        return now, assets, progression, health, derive_alarms(assets)

    def telemetry(self) -> dict:
        now, assets, progression, health, alarms = self._snapshot()
        payload_assets = []
        for asset in assets:
            payload = asset.to_dict()
            payload["progression"] = progression[asset.asset_id]
            payload["health"] = health[asset.asset_id].to_dict()
            payload_assets.append(payload)
        return {
            "generated_at": now.isoformat(),
            "quality_summary": self.quality.summary(assets),
            "progression_summary": self._progression_summary(progression),
            "health_summary": self._health_summary(health),
            "alarms": [alarm.to_dict() for alarm in alarms],
            "assets": payload_assets,
        }

    def metrics(self) -> str:
        now, assets, progression, health, alarms = self._snapshot()
        return render_metrics(
            assets,
            progression,
            health,
            alarm_count=len(alarms),
            incident_count=len(self.incidents.list()),
            now=now,
        )

    @staticmethod
    def _progression_summary(progression: dict[str, dict[str, object]]) -> dict[str, int]:
        counts = {"progressing": 0, "unchanged": 0, "frozen": 0}
        for item in progression.values():
            counts[str(item["status"])] += 1
        return counts

    @staticmethod
    def _health_summary(health: dict[str, object]) -> dict[str, int]:
        counts = {"healthy": 0, "degraded": 0, "stale": 0, "failed": 0}
        for result in health.values():
            counts[result.status.value] += 1
        return counts


APP = Application()


class GridPulseHandler(BaseHTTPRequestHandler):
    server_version = "GridPulse/0.1"

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/v1/health":
            self._json({"status": "ok", "service": "gridpulse-lab"})
        elif path == "/api/v1/telemetry":
            self._json(APP.telemetry())
        elif path == "/metrics":
            self._text(APP.metrics(), "text/plain; version=0.0.4; charset=utf-8")
        elif path == "/api/v1/incidents":
            self._json({"incidents": [
                {"asset_id": item.asset_id, "kind": item.kind.value}
                for item in APP.incidents.list()
            ]})
        elif path in ("/", "/index.html"):
            self._static("index.html", "text/html; charset=utf-8")
        elif path == "/app.js":
            self._static("app.js", "text/javascript; charset=utf-8")
        elif path == "/styles.css":
            self._static("styles.css", "text/css; charset=utf-8")
        else:
            self._json({"error": "not_found", "path": path}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/v1/incidents":
            self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            asset_id = str(payload["asset_id"])
            kind = IncidentType(payload["kind"])
            incident = APP.incidents.activate(asset_id, kind)
            self._json(
                {"asset_id": incident.asset_id, "kind": incident.kind.value},
                HTTPStatus.CREATED,
            )
        except (KeyError, ValueError, json.JSONDecodeError) as error:
            self._json({"error": "invalid_request", "detail": str(error)}, HTTPStatus.BAD_REQUEST)

    def do_DELETE(self) -> None:  # noqa: N802
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) == 4 and parts[:3] == ["api", "v1", "incidents"]:
            APP.incidents.clear(parts[3])
            self._json({}, HTTPStatus.NO_CONTENT)
        else:
            self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def _static(self, name: str, content_type: str) -> None:
        body = files("gridpulse.web").joinpath(name).read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _text(self, payload: str, content_type: str) -> None:
        body = payload.encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = b"" if status is HTTPStatus.NO_CONTENT else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[gridpulse] {self.address_string()} {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the GridPulse Lab server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8080, type=int)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), GridPulseHandler)
    print(f"GridPulse Lab running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
