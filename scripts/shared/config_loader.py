from __future__ import annotations

"""Les maskin- og materialkonfigurasjon fra config/-mappen.

Modulen holder all I/O samlet slik at både stirling_core og
knife_gd66_carver kan validere parametre mot den samme dataflyten.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"


def _load_serialized(path: Path) -> Any:
    if not path.exists():
        return None

    try:
        if path.suffix in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore
            except Exception:
                return None
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_machine_park() -> Dict[str, Dict[str, Any]]:
    """Last maskinparken fra YAML/JSON med fornuftige standarder."""

    default: Dict[str, Dict[str, Any]] = {
        "cnc_mill": {"volume_mm": {"x": 320.0, "y": 220.0, "z": 110.0}},
        "lathe": {
            "swing_diameter_mm": 180.0,
            "between_centers_mm": 300.0,
        },
        "printer": {"volume_mm": {"x": 220.0, "y": 220.0, "z": 250.0}},
    }

    machines: Dict[str, Dict[str, Any]] = default.copy()
    yaml_data = _load_serialized(CONFIG_DIR / "machines.yaml")
    json_data = _load_serialized(CONFIG_DIR / "machines.json")
    data = yaml_data or json_data

    if isinstance(data, Mapping):
        payload = data.get("machines", data)
        if isinstance(payload, Mapping):
            for key, value in payload.items():
                if isinstance(value, Mapping):
                    merged = machines.get(key, {}).copy()
                    merged.update(value)
                    machines[key] = merged
    return machines


def load_material_catalog() -> List[Dict[str, Any]]:
    """Last materialkatalogen fra YAML/JSON og returner en flat liste."""

    default = [
        {"code": "AL6061", "name": "Aluminium 6061"},
        {"code": "GLASS_QUARTZ", "name": "Kvartsglass"},
    ]

    yaml_data = _load_serialized(CONFIG_DIR / "materials.yaml")
    json_data = _load_serialized(CONFIG_DIR / "materials.json")
    data = yaml_data or json_data

    if isinstance(data, Mapping):
        records = data.get("materials")
    else:
        records = data

    if isinstance(records, list):
        filtered: List[Dict[str, Any]] = []
        for entry in records:
            if isinstance(entry, Mapping):
                filtered.append(dict(entry))
        if filtered:
            return filtered
    return default
