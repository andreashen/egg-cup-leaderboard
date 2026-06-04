"""Raw payload snapshot helpers."""

from pathlib import Path
import json
from typing import Any, Dict


def write_raw_snapshot(output_dir: Path, name: str, payload: Dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "{name}.json".format(name=name)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target
