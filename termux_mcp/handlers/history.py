"""History tools: list, save, and clear command execution history."""

import json
import os
import time

from ..registry import register_tool
from ..utils import error_msg, json_result

HISTORY_FILE = os.path.join(
    os.environ.get("HOME", "/data/data/com.termux/files/home"),
    ".termux_history.json",
)
MAX_ENTRIES = 2000


def _load() -> list:
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(entries: list) -> None:
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]
    with open(HISTORY_FILE, "w") as f:
        json.dump(entries, f)


@register_tool(
    name="history_list",
    description="List command execution history.",
    schema={"type": "object", "properties": {}},
    category="history",
)
def handle_history_list(data: dict) -> str:
    entries = _load()
    return json_result({"entries": entries, "count": len(entries)})


@register_tool(
    name="history_save",
    description="Save a command execution record to history.",
    schema={
        "type": "object",
        "properties": {
            "raw_input": {"type": "string", "description": "Command that was run"},
            "output": {"type": "string", "description": "Command output"},
            "success": {"type": "boolean", "description": "Whether the command succeeded"},
        },
    },
    category="history",
)
def handle_history_save(data: dict) -> str:
    raw_input = (data.get("rawInput") or data.get("raw_input") or "").strip()
    output = (data.get("output") or "").strip()
    if not raw_input and not output:
        return error_msg("Missing rawInput or output")

    entries = _load()
    ran_cmd = (data.get("ranCommand") or "").strip()
    entry = {
        "rawInput": raw_input,
        "output": output[:5000] if len(output) > 5000 else output,
        "ranCommand": ran_cmd if ran_cmd else None,
        "success": data.get("success", True),
        "traces": data.get("traces") or data.get("agentTraces") or [],
        "timestamp": time.time(),
    }
    entries.append(entry)
    _save(entries)
    return json_result({"saved": True, "total": len(entries)})


@register_tool(
    name="history_clear",
    description="Clear all command execution history.",
    schema={"type": "object", "properties": {}},
    category="history",
)
def handle_history_clear(data: dict) -> str:
    try:
        os.remove(HISTORY_FILE)
        return json_result({"cleared": True})
    except FileNotFoundError:
        return json_result({"cleared": True})
    except Exception as e:
        return error_msg(str(e))
import json
import os
import time
from typing import TYPE_CHECKING

