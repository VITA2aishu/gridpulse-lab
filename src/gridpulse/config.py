"""Load and validate a fictional fleet from a local JSON configuration file.

The configuration format is intentionally small so workshops, demos and tests
can model different fictional fleets without changing simulator source code.
Valid entries are converted into ``AssetConfig`` so the rest of the lab keeps
using the existing asset model. See ``docs/configuration.md`` for the schema.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from .simulator import AssetConfig

ASSET_ID_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
ASSET_ID_MAX_LENGTH = 64
MAX_ASSETS = 50
DEFAULT_INITIAL_SOC = 50.0

REQUIRED_FIELDS = ("asset_id", "name", "region", "capacity_mw", "energy_mwh")
OPTIONAL_FIELDS = ("initial_soc",)
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


class AssetConfigError(ValueError):
    """Raised when a fictional fleet configuration file is invalid."""


def load_fleet(path: str | Path) -> tuple[AssetConfig, ...]:
    """Read a JSON fleet configuration and return validated asset entries.

    The file must contain a JSON object with a non-empty ``"assets"`` array.
    Every malformed or unsupported input raises ``AssetConfigError`` with a
    message that points at the offending field.
    """
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        detail = error.strerror or str(error)
        raise AssetConfigError(
            f"cannot read asset configuration '{path}': {detail}"
        ) from error

    try:
        document = json.loads(text, parse_constant=_reject_constant)
    except json.JSONDecodeError as error:
        raise AssetConfigError(f"'{path}' is not valid JSON: {error}") from error

    if not isinstance(document, dict):
        raise AssetConfigError(
            f"'{path}' must contain a JSON object with an \"assets\" array, "
            f"got {_describe(document)}"
        )
    unknown = sorted(set(document) - {"assets"})
    if unknown:
        raise AssetConfigError(
            f"'{path}' has unsupported top-level field(s) {unknown}; "
            'only "assets" is allowed'
        )
    if "assets" not in document:
        raise AssetConfigError(f"'{path}' must define an \"assets\" array")

    entries = document["assets"]
    if not isinstance(entries, list) or not entries:
        raise AssetConfigError(f"'{path}' \"assets\" must be a non-empty array")
    if len(entries) > MAX_ASSETS:
        raise AssetConfigError(
            f"'{path}' declares {len(entries)} assets; at most {MAX_ASSETS} "
            "are supported to keep dashboards and metrics low-cardinality"
        )

    assets: list[AssetConfig] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        asset = _load_asset(entry, index)
        if asset.asset_id in seen:
            raise AssetConfigError(
                f"assets[{index}].asset_id: duplicate asset id '{asset.asset_id}'"
            )
        seen.add(asset.asset_id)
        assets.append(asset)
    return tuple(assets)


def _reject_constant(value: str) -> None:
    raise AssetConfigError(
        f"unsupported JSON value '{value}'; use finite numbers only"
    )


def _load_asset(entry: Any, index: int) -> AssetConfig:
    prefix = f"assets[{index}]"
    if not isinstance(entry, dict):
        raise AssetConfigError(
            f"{prefix}: expected an object, got {_describe(entry)}"
        )
    unknown = sorted(set(entry) - set(ALL_FIELDS))
    if unknown:
        raise AssetConfigError(
            f"{prefix}: unsupported field(s) {unknown}; "
            f"allowed fields are {sorted(ALL_FIELDS)}"
        )
    for field in REQUIRED_FIELDS:
        if field not in entry:
            raise AssetConfigError(f"{prefix}: missing required field '{field}'")

    return AssetConfig(
        asset_id=_asset_id(entry["asset_id"], index),
        name=_text(entry["name"], index, "name"),
        region=_text(entry["region"], index, "region"),
        capacity_mw=_positive_number(entry["capacity_mw"], index, "capacity_mw"),
        energy_mwh=_positive_number(entry["energy_mwh"], index, "energy_mwh"),
        initial_soc=_initial_soc(entry, index),
    )


def _asset_id(value: Any, index: int) -> str:
    prefix = f"assets[{index}].asset_id"
    if not isinstance(value, str) or not value:
        raise AssetConfigError(
            f"{prefix}: expected a non-empty string, got {_describe(value)}"
        )
    if len(value) > ASSET_ID_MAX_LENGTH or not ASSET_ID_PATTERN.fullmatch(value):
        raise AssetConfigError(
            f"{prefix}: '{value}' is not a valid asset id; use a lowercase slug "
            "of letters, digits and single dashes such as 'aurora-1' "
            f"(at most {ASSET_ID_MAX_LENGTH} characters)"
        )
    return value


def _text(value: Any, index: int, field: str) -> str:
    prefix = f"assets[{index}].{field}"
    if not isinstance(value, str) or not value.strip():
        raise AssetConfigError(
            f"{prefix}: expected a non-empty string, got {_describe(value)}"
        )
    return value.strip()


def _positive_number(value: Any, index: int, field: str) -> float:
    prefix = f"assets[{index}].{field}"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssetConfigError(
            f"{prefix}: expected a number, got {_describe(value)}"
        )
    if not math.isfinite(value):
        raise AssetConfigError(f"{prefix}: expected a finite number, got {value}")
    if value <= 0:
        raise AssetConfigError(
            f"{prefix}: expected a value greater than 0, got {value}"
        )
    return float(value)


def _initial_soc(entry: dict, index: int) -> float:
    if "initial_soc" not in entry:
        return DEFAULT_INITIAL_SOC
    value = entry["initial_soc"]
    prefix = f"assets[{index}].initial_soc"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssetConfigError(
            f"{prefix}: expected a number between 0 and 100, got {_describe(value)}"
        )
    if not math.isfinite(value) or not 0 <= value <= 100:
        raise AssetConfigError(
            f"{prefix}: expected a value between 0 and 100, got {value}"
        )
    return float(value)


def _describe(value: Any) -> str:
    """Describe a parsed JSON value using JSON vocabulary."""
    if value is None:
        kind = "null"
    elif isinstance(value, bool):
        kind = "boolean"
    elif isinstance(value, str):
        kind = "string"
    elif isinstance(value, (int, float)):
        kind = "number"
    elif isinstance(value, list):
        kind = "array"
    elif isinstance(value, dict):
        kind = "object"
    else:
        return type(value).__name__
    return f"{kind} {json.dumps(value)}"
