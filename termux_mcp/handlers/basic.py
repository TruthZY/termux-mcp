"""Core tools: shell execution, file operations, ping, env."""

import base64
import os

from ..registry import register_tool
from ..security import get_risk_assessment
from ..shell import cancel_active, execute, get_active_pid, get_current_dir, set_current_dir
from ..utils import encode_base64, error_msg, is_safe_path, shell_quote, shell_quote_num

HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")


# ── Shell ────────────────────────────────────────────────────────────────

@register_tool(
    name="shell_exec",
    description="Execute a shell command in Termux and return the output. Dangerous commands require confirmation.",
    schema={
        "type": "object",
        "properties": {
            "cmd": {"type": "string", "description": "Shell command to execute"},
            "confirmed": {"type": "boolean", "description": "Confirm dangerous commands (set true after risk warning)"},
        },
        "required": ["cmd"],
    },
    category="core",
)
def handle_shell_exec(data: dict) -> str:
    cmd = data.get("cmd", "").strip()
    if not cmd:
        return error_msg("Missing 'cmd'")
    risk = get_risk_assessment(cmd)
    if risk["blocked"]:
        return f"BLOCKED [{risk['risk_level']}]: {risk['message']}"
    if risk["requires_confirmation"] and not data.get("confirmed"):
        return (
            f"Confirmation required [{risk['risk_level']}]: {risk['message']}\n"
            "Re-send with confirmed: true to proceed."
        )
    return execute(cmd)


@register_tool(
    name="shell_cancel",
    description="Cancel the currently running shell command (sends SIGTERM).",
    schema={"type": "object", "properties": {}},
    category="core",
)
def handle_shell_cancel(data: dict) -> str:
    ok = cancel_active()
    return "Command cancelled." if ok else "No active command to cancel."


# ── File operations ───────────────────────────────────────────────────────

@register_tool(
    name="file_list",
    description="List files and directories. Returns names, sizes, and permissions.",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path (default: current dir)"},
            "bare": {"type": "boolean", "description": "Show only names without details"},
            "no_dotfiles": {"type": "boolean", "description": "Hide hidden files"},
        },
    },
    category="core",
)
def handle_file_list(data: dict) -> str:
    path = (data.get("path") or ".").strip()
    if not is_safe_path(path):
        return error_msg("Path not allowed")
    flags = "-la"
    if data.get("bare"):
        flags = "-1"
    elif data.get("no_dotfiles"):
        flags = "-l"
    return execute(
        f"ls {flags} {shell_quote(path)} 2>/dev/null || echo Cannot access: {shell_quote(path)}"
    )


@register_tool(
    name="file_read",
    description="Read the contents of a file (first 500 lines).",
    schema={
        "type": "object",
        "properties": {"path": {"type": "string", "description": "File path to read"}},
        "required": ["path"],
    },
    category="core",
)
def handle_file_read(data: dict) -> str:
    path = (data.get("path") or "").strip()
    if not path:
        return error_msg("Missing 'path'")
    if not is_safe_path(path):
        return error_msg("Path not allowed")
    return execute(
        f"head -n 500 {shell_quote(path)} 2>/dev/null || echo Cannot read: {shell_quote(path)}"
    )


@register_tool(
    name="file_write",
    description="Write content to a file (creates or overwrites).",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to write"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    },
    category="core",
)
def handle_file_write(data: dict) -> str:
    path = (data.get("path") or "").strip()
    content = data.get("content") or ""
    if not path:
        return error_msg("Missing 'path'")
    if not is_safe_path(path):
        return error_msg("Path not allowed")
    encoded = encode_base64(content)
    return execute(
        f'mkdir -p "$(dirname {shell_quote(path)})" 2>/dev/null; '
        f"echo {shell_quote(encoded)} | base64 -d > {shell_quote(path)} && "
        f"echo Written: {shell_quote(path)}"
    )


@register_tool(
    name="file_mkdir",
    description="Create a directory (including parent directories).",
    schema={
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Directory path to create"}},
        "required": ["path"],
    },
    category="core",
)
def handle_file_mkdir(data: dict) -> str:
    path = (data.get("path") or "").strip()
    if not path:
        return error_msg("Missing 'path'")
    if not is_safe_path(path):
        return error_msg("Path not allowed")
    return execute(f"mkdir -p {shell_quote(path)} && echo Created: {shell_quote(path)}")


@register_tool(
    name="file_delete",
    description="Delete a file or directory. Requires confirmation for safety.",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to delete"},
            "recursive": {"type": "boolean", "description": "Delete directories recursively"},
            "confirmed": {"type": "boolean", "description": "Must be true to confirm deletion"},
        },
        "required": ["path"],
    },
    category="core",
)
def handle_file_delete(data: dict) -> str:
    path = (data.get("path") or "").strip()
    recursive = data.get("recursive", False)
    if not path:
        return error_msg("Missing 'path'")
    if not data.get("confirmed"):
        return (
            f"Confirmation required: Delete {path} "
            f"({'recursive' if recursive else 'non-recursive'})\n"
            "Re-send with confirmed: true to proceed."
        )
    if not is_safe_path(path):
        return error_msg("Path not allowed")
    flags = "-rf" if recursive else ""
    return execute(
        f"rm {flags} {shell_quote(path)} 2>/dev/null && "
        f"echo Deleted: {shell_quote(path)} || echo Failed to delete: {shell_quote(path)}"
    )


@register_tool(
    name="file_search",
    description="Search for files by name pattern. Returns up to 30 results.",
    schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Base directory to search (default: .)"},
            "pattern": {"type": "string", "description": "Glob pattern (default: *)"},
            "name": {"type": "string", "description": "Alternative name filter"},
        },
    },
    category="core",
)
def handle_file_search(data: dict) -> str:
    path = (data.get("path") or ".").strip()
    pattern = (data.get("pattern") or data.get("query") or data.get("name") or "*").strip()
    if not is_safe_path(path):
        return error_msg("Path not allowed")
    return execute(
        f"find {shell_quote(path)} -name {shell_quote(pattern)} -type f 2>/dev/null | head -n 30"
    )


# ── Info ──────────────────────────────────────────────────────────────────

@register_tool(
    name="ping",
    description="Health check / ping. Returns server status and current working directory.",
    schema={"type": "object", "properties": {}},
    category="core",
)
def handle_ping(data: dict) -> str:
    return f"status: ok\ncwd: {get_current_dir()}"


@register_tool(
    name="env",
    description="Get current environment: working directory, home path, PIDs.",
    schema={"type": "object", "properties": {}},
    category="core",
)
def handle_env(data: dict) -> str:
    import json
    return json.dumps({
        "cwd": get_current_dir(),
        "home": HOME,
        "pid": os.getpid(),
        "active_command_pid": get_active_pid(),
    })

