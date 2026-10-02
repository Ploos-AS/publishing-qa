from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class ArtifactValidationError(ValueError):
    pass


def validate(instance: Any, schema: dict[str, Any], label: str) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        err = errors[0]
        where = ".".join(str(x) for x in err.absolute_path) or "<root>"
        raise ArtifactValidationError(f"{label}: {where}: {err.message}")


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
