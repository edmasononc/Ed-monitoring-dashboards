import json
from difflib import unified_diff
from pathlib import Path
from typing import Any


def build_json_diff(current_data: Any, updated_data: Any, *, file_name: str) -> str:
    current_lines = json.dumps(current_data, indent=4, sort_keys=True).splitlines()
    updated_lines = json.dumps(updated_data, indent=4, sort_keys=True).splitlines()
    diff_lines = list(
        unified_diff(
            current_lines,
            updated_lines,
            fromfile=f"{file_name} (current)",
            tofile=f"{file_name} (new)",
            lineterm="",
        )
    )
    return "\n".join(diff_lines)


def read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)
