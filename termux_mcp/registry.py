"""
Tool Registry for Termux-MCP
==============================
Central registry for all tools. Each handler uses @register_tool to declare
its metadata (name, description, schema, category, requires).

Two output formats are auto-generated from the single source of truth:
  - MCP tools/list   (get_mcp_tools)
  - OpenAI function calling (get_openai_tools)
"""

import subprocess
from typing import Callable, Optional


TOOL_REGISTRY: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------

def register_tool(
    name: str,
    description: str,
    schema: dict,
    category: str = "",
    requires: Optional[list[dict]] = None,
) -> Callable:
    """
    Decorator that registers a handler function as an MCP tool.

    Parameters
    ----------
    name        : Unique tool identifier (used as MCP tool name).
    description : Human-readable description shown to the LLM.
    schema      : JSON Schema dict for the tool's input parameters.
    category    : Optional group label (e.g. "shell", "device", "ai_power").
    requires    : Optional list of external dependencies, each a dict with
                  keys "pkg" (binary name checked via `which`) and "install"
                  (the shell command to install it).
                  Example: [{"pkg": "tesseract", "install": "pkg install tesseract"}]
    """
    def decorator(func: Callable) -> Callable:
        TOOL_REGISTRY[name] = {
            "name": name,
            "description": description,
            "schema": schema,
            "category": category,
            "requires": requires or [],
            "handler": func,
        }
        return func
    return decorator


# ---------------------------------------------------------------------------
# Format generators
# ---------------------------------------------------------------------------

def get_mcp_tools() -> list[dict]:
    """
    Return all registered tools in MCP format.

    Dependency information from `requires` is automatically appended to the
    description so the LLM knows what needs to be installed before calling.
    """
    result = []
    for tool in TOOL_REGISTRY.values():
        desc = tool["description"]
        if tool["requires"]:
            req_lines = ", ".join(
                f"{r['pkg']} ({r['install']})" for r in tool["requires"]
            )
            desc += f"\n\nRequires: {req_lines}"
        result.append({
            "name": tool["name"],
            "description": desc,
            "inputSchema": tool["schema"],
        })
    return result


def get_openai_tools() -> list[dict]:
    """Return all registered tools in OpenAI function-calling format."""
    result = []
    for tool in TOOL_REGISTRY.values():
        desc = tool["description"]
        if tool["requires"]:
            req_lines = ", ".join(
                f"{r['pkg']} ({r['install']})" for r in tool["requires"]
            )
            desc += f"\n\nRequires: {req_lines}"
        result.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": desc,
                "parameters": tool["schema"],
            },
        })
    return result


# ---------------------------------------------------------------------------
# Dependency check helpers
# ---------------------------------------------------------------------------

def _is_installed(pkg: str) -> bool:
    """Check if a binary is available in PATH (via `which`)."""
    try:
        return subprocess.run(
            ["which", pkg],
            capture_output=True,
            timeout=5,
        ).returncode == 0
    except Exception:
        return False


def _check_requires(name: str) -> Optional[str]:
    """
    Check all required packages for a tool.
    Returns None if all are present, or an error message string listing
    what needs to be installed.
    """
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        return None
    missing = [r for r in tool["requires"] if not _is_installed(r["pkg"])]
    if not missing:
        return None
    lines = [f"Tool '{name}' requires packages that are not installed:"]
    for m in missing:
        lines.append(f"  - {m['pkg']}: {m['install']}")
    lines.append("Please install the missing packages first, then retry.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def call_tool(name: str, arguments: dict) -> str:
    """
    Look up a registered tool by name, run its dependency check, then invoke
    the handler.  Returns the result as a plain string (used directly as the
    MCP `content[].text` value).
    """
    tool = TOOL_REGISTRY.get(name)
    if tool is None:
        return f"Error: Unknown tool '{name}'. Use tools/list to see available tools."

    # Pre-flight dependency check
    dep_error = _check_requires(name)
    if dep_error:
        return dep_error

    try:
        return tool["handler"](arguments)
    except Exception as e:
        return f"Error executing '{name}': {e}"


def list_categories() -> dict[str, list[str]]:
    """Return tools grouped by category (useful for documentation)."""
    cats: dict[str, list[str]] = {}
    for tool in TOOL_REGISTRY.values():
        cat = tool["category"] or "uncategorized"
        cats.setdefault(cat, []).append(tool["name"])
    return cats
