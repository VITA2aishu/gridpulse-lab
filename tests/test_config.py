import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from gridpulse import server
from gridpulse.config import AssetConfigError, load_fleet
from gridpulse.server import Application
from gridpulse.simulator import AssetConfig, FleetSimulator

EXAMPLE_FLEET = (
    Path(__file__).resolve().parent.parent
    / "examples" / "assets" / "workshop-fleet.json"
)


def asset(**overrides):
    fields = {
        "asset_id": "harbor-1",
        "name": "Harbor Point Battery",
        "region": "East",
        "capacity_mw": 60,
        "energy_mwh": 240,
        "initial_soc": 55,
    }
    fields.update(overrides)
    return fields


class LoadFleetTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def write(self, payload, name="fleet.json"):
        path = self.dir / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def write_text(self, text, name="fleet.json"):
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_loads_multi_asset_fleet(self):
        path = self.write({"assets": [
            asset(),
            asset(asset_id="mesa-1", name="Mesa Ridge Storage", region="West",
                  capacity_mw=120.5, energy_mwh=480, initial_soc=40),
        ]})
        fleet = load_fleet(path)
        self.assertIsInstance(fleet, tuple)
        self.assertEqual(2, len(fleet))
        self.assertEqual(
            AssetConfig("harbor-1", "Harbor Point Battery", "East", 60.0, 240.0, 55.0),
            fleet[0],
        )
        self.assertEqual("mesa-1", fleet[1].asset_id)
        self.assertEqual(120.5, fleet[1].capacity_mw)
        self.assertIsInstance(fleet[1].capacity_mw, float)

    def test_initial_soc_defaults_to_50(self):
        payload = asset()
        del payload["initial_soc"]
        fleet = load_fleet(self.write({"assets": [payload]}))
        self.assertEqual(50.0, fleet[0].initial_soc)

    def test_loaded_fleet_drives_simulator(self):
        path = self.write({"assets": [asset(), asset(asset_id="mesa-1")]})
        simulator = FleetSimulator(seed=3, fleet=load_fleet(path))
        snapshot = simulator.snapshot()
        self.assertEqual({"harbor-1", "mesa-1"}, {a.asset_id for a in snapshot})
        self.assertEqual("Harbor Point Battery", snapshot[0].name)
        self.assertEqual(240.0, snapshot[0].energy_mwh)

    def test_default_fleet_is_preserved_without_config(self):
        app = Application()
        ids = {a.asset_id for a in app.simulator.snapshot()}
        self.assertEqual({"aurora-1", "bluebonnet-1", "canyon-1"}, ids)

    def test_shipped_example_file_is_valid(self):
        fleet = load_fleet(EXAMPLE_FLEET)
        self.assertEqual(
            {"harbor-1", "mesa-1", "willow-1"},
            {a.asset_id for a in fleet},
        )
        # The example intentionally omits initial_soc for one asset.
        self.assertEqual(50.0, fleet[2].initial_soc)

    def test_missing_file_is_reported(self):
        with self.assertRaises(AssetConfigError) as ctx:
            load_fleet(self.dir / "missing.json")
        self.assertIn("cannot read asset configuration", str(ctx.exception))
        self.assertIn("missing.json", str(ctx.exception))

    def test_malformed_json_is_reported(self):
        path = self.write_text('{"assets": [')
        with self.assertRaises(AssetConfigError) as ctx:
            load_fleet(path)
        self.assertIn("not valid JSON", str(ctx.exception))

    def test_non_finite_json_constant_is_rejected(self):
        path = self.write_text('{"assets": [{"asset_id": "a-1", "name": "A", '
                               '"region": "R", "capacity_mw": NaN, '
                               '"energy_mwh": 100}]}')
        with self.assertRaises(AssetConfigError) as ctx:
            load_fleet(path)
        self.assertIn("unsupported JSON value 'NaN'", str(ctx.exception))

    def test_top_level_must_be_an_object(self):
        path = self.write([asset()])
        with self.assertRaises(AssetConfigError) as ctx:
            load_fleet(path)
        self.assertIn('JSON object with an "assets" array', str(ctx.exception))

    def test_unknown_top_level_field_is_rejected(self):
        path = self.write({"assets": [asset()], "seed": 7})
        with self.assertRaises(AssetConfigError) as ctx:
            load_fleet(path)
        self.assertIn("unsupported top-level field(s) ['seed']", str(ctx.exception))

    def test_assets_array_is_required(self):
        path = self.write({"fleet": []})
        with self.assertRaises(AssetConfigError) as ctx:
            load_fleet(path)
        self.assertIn("unsupported top-level field", str(ctx.exception))

    def test_assets_must_be_a_non_empty_array(self):
        for payload in ({"assets": []}, {"assets": {"a": 1}}):
            path = self.write(payload)
            with self.assertRaises(AssetConfigError) as ctx:
                load_fleet(path)
            self.assertIn("non-empty array", str(ctx.exception))

    def test_fleet_size_is_bounded(self):
        entries = [asset(asset_id=f"unit-{i}") for i in range(51)]
        path = self.write({"assets": entries})
        with self.assertRaises(AssetConfigError) as ctx:
            load_fleet(path)
        self.assertIn("at most 50", str(ctx.exception))

    def test_asset_entry_must_be_an_object(self):
        path = self.write({"assets": ["harbor-1"]})
        with self.assertRaises(AssetConfigError) as ctx:
            load_fleet(path)
        self.assertIn('assets[0]: expected an object, got string', str(ctx.exception))

    def test_unknown_asset_field_is_rejected(self):
        path = self.write({"assets": [asset(owner="example-lab")]})
        with self.assertRaises(AssetConfigError) as ctx:
            load_fleet(path)
        self.assertIn("unsupported field(s) ['owner']", str(ctx.exception))
        self.assertIn("allowed fields", str(ctx.exception))

    def test_missing_required_field_is_reported(self):
        payload = asset()
        del payload["capacity_mw"]
        path = self.write({"assets": [payload]})
        with self.assertRaises(AssetConfigError) as ctx:
            load_fleet(path)
        self.assertIn("missing required field 'capacity_mw'", str(ctx.exception))

    def test_asset_id_must_be_a_lowercase_slug(self):
        for bad in ("", "Aurora-1", "aurora 1", "aurora_1", "-aurora-1",
                    "aurora--1", 42, "a" * 65):
            path = self.write({"assets": [asset(asset_id=bad)]})
            with self.assertRaises(AssetConfigError, msg=f"asset_id={bad!r}"):
                load_fleet(path)

    def test_duplicate_asset_id_is_rejected(self):
        path = self.write({"assets": [asset(), asset()]})
        with self.assertRaises(AssetConfigError) as ctx:
            load_fleet(path)
        self.assertIn("duplicate asset id 'harbor-1'", str(ctx.exception))

    def test_name_and_region_must_be_non_empty_strings(self):
        for field in ("name", "region"):
            for bad in ("", "   ", 12, None):
                path = self.write({"assets": [asset(**{field: bad})]})
                with self.assertRaises(AssetConfigError, msg=f"{field}={bad!r}"):
                    load_fleet(path)

    def test_power_and_energy_must_be_positive_numbers(self):
        for field in ("capacity_mw", "energy_mwh"):
            for bad in ("60", True, 0, -5, None, [60]):
                path = self.write({"assets": [asset(**{field: bad})]})
                with self.assertRaises(AssetConfigError, msg=f"{field}={bad!r}"):
                    load_fleet(path)

    def test_initial_soc_must_be_within_0_to_100(self):
        for bad in (-1, 101, "high", True, None):
            path = self.write({"assets": [asset(initial_soc=bad)]})
            with self.assertRaises(AssetConfigError, msg=f"initial_soc={bad!r}"):
                load_fleet(path)


class ServerAssetsFlagTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.original_app = server.APP
        self.addCleanup(setattr, server, "APP", self.original_app)

    def run_main(self, argv):
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(server, "ThreadingHTTPServer") as httpd, \
                mock.patch.object(sys, "stderr", io.StringIO()):
            server.main()
        return httpd

    def test_assets_flag_loads_configured_fleet(self):
        path = self.dir / "fleet.json"
        path.write_text(json.dumps({"assets": [asset(), asset(asset_id="mesa-1")]}))
        httpd = self.run_main(["gridpulse", "--assets", str(path)])
        ids = {a.asset_id for a in server.APP.simulator.snapshot()}
        self.assertEqual({"harbor-1", "mesa-1"}, ids)
        httpd.assert_called_once()
        httpd.return_value.serve_forever.assert_called_once()

    def test_invalid_assets_file_exits_with_error(self):
        path = self.dir / "fleet.json"
        path.write_text('{"assets": [')
        with self.assertRaises(SystemExit) as ctx:
            self.run_main(["gridpulse", "--assets", str(path)])
        self.assertEqual(2, ctx.exception.code)
        self.assertIs(self.original_app, server.APP)

    def test_missing_flag_keeps_default_fleet(self):
        self.run_main(["gridpulse"])
        self.assertIs(self.original_app, server.APP)


if __name__ == "__main__":
    unittest.main()
