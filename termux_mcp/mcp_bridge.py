"""
MCP Protocol Bridge for Termux-MCP (Standalone Mode)
=====================================================
Runs MCP protocol directly — no separate REST server needed.
Tool calls invoke the existing handlers in-process via a mock
HTTP handler that captures output.

No external dependencies — pure Python standard library.
"""

import io
import json
import logging
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from uuid import uuid4

from .config import AUTH_TOKEN, REQUIRE_AUTH, HOST, PORT
from .mcp_tools import MCP_TOOLS

logger = logging.getLogger(__name__)

MCP_HOST = "0.0.0.0"
MCP_PORT = 3000


# ─── Fake HTTP Handler (captures handler output in-memory) ─────────────

class _CaptureBuffer:
    """Captures bytes written by handlers."""
    def __init__(self):
        self.buf = io.BytesIO()

    def write(self, data):
        self.buf.write(data)

    def getvalue(self):
        return self.buf.getvalue()

    def flush(self):
        pass


class FakeHandler(BaseHTTPRequestHandler):
    """
    A fake HTTP request handler that captures output in memory.
    Used to invoke existing handlers without a real HTTP server.
    """

    protocol_version = "HTTP/1.1"

    def __init__(self, method: str = "POST", path: str = "/",
                 body: dict | None = None, headers: dict | None = None):
        self._method = method
        self._path = path
        self._body = body or {}
        self._extra_headers = headers or {}
        self._response_code = 200
        self._response_headers: list[tuple[str, str]] = []
        self._wfile = _CaptureBuffer()

        # Required attributes that handlers access
        self.requestline = f"{method} {path} HTTP/1.1"
        self.client_address = ("127.0.0.1", 0)
        self.server_version = "FakeServer/1.0"
        self.sys_version = ""

    # ── Attributes expected by handlers ──

    @property
    def wfile(self):
        return self._wfile

    @property
    def rfile(self):
        body_bytes = json.dumps(self._body).encode("utf-8")
        return io.BytesIO(body_bytes)

    @property
    def headers(self):
        """Return a dict-like headers object."""
        h = _FakeHeaders(self._extra_headers)
        body_bytes = json.dumps(self._body).encode("utf-8")
        h["Content-Length"] = str(len(body_bytes))
        h["Content-Type"] = "application/json"
        return h

    @property
    def command(self):
        return self._method

    @property
    def path(self):
        return self._path

    @property
    def request(self):
        """Some handlers access self.request for the socket."""
        return None

    # ── Methods called by handlers to write responses ──

    def send_response(self, code, message=None):
        self._response_code = code

    def send_header(self, key, value):
        self._response_headers.append((key, str(value)))

    def end_headers(self):
        pass

    def flush_headers(self):
        pass

    def log_message(self, fmt, *args):
        pass  # suppress handler logs

    # ── Response access ──

    def get_body(self) -> str:
        raw = self._wfile.getvalue()
        if not raw:
            return ""
        return raw.decode("utf-8", errors="replace")


class _FakeHeaders:
    """Minimal dict-like headers object."""
    def __init__(self, initial: dict | None = None):
        self._h = dict(initial or {})

    def get(self, key, default=""):
        return self._h.get(key, default)

    def __getitem__(self, key):
        return self._h[key]

    def __setitem__(self, key, value):
        self._h[key] = value

    def __contains__(self, key):
        return key in self._h

    def keys(self):
        return self._h.keys()

    def items(self):
        return self._h.items()

    def as_string(self, *args, **kwargs):
        return "\r\n".join(f"{k}: {v}" for k, v in self._h.items())


# ─── Endpoint → Handler Mapping ──────────────────────────────────────────

def _build_handler_map() -> dict:
    """Build mapping from endpoint path to handler function."""
    from .handler import MCPHandler
    from .handlers.terminal import (
        handle_diagnose, handle_pkg_smart, handle_explain, handle_dev_env,
        handle_review, handle_log_analyze, handle_script_gen, handle_deps_tree,
        handle_storage_audit, handle_config_fix, handle_git_smart, handle_regex,
        handle_db_design, handle_backup, handle_restore,
    )
    from .handlers.features import (
        handle_system_info, handle_process_list, handle_process_kill,
        handle_cron_add, handle_cron_list, handle_cron_remove,
        handle_diff, handle_patch, handle_health, handle_cloud_sync,
        handle_git_pr, handle_recipe_list, handle_recipe_run, handle_recipe_save,
        handle_context, handle_context_save,
    )
    from .handlers.history import (
        handle_history_list, handle_history_save, handle_history_clear,
    )
    from .handlers.ai_power import (
        handle_smart_install, handle_permission_fix, handle_profile,
        handle_error_explain, handle_ssh_wizard, handle_service_guard,
        handle_history_insight, handle_optimize, handle_quick_cmd,
        handle_port_manage, handle_migrate, handle_tutorial,
    )

    return {
        # External handlers (from handler modules)
        "/diagnose": handle_diagnose,
        "/pkg-smart": handle_pkg_smart,
        "/explain": handle_explain,
        "/dev-env": handle_dev_env,
        "/review": handle_review,
        "/log-analyze": handle_log_analyze,
        "/script-gen": handle_script_gen,
        "/deps-tree": handle_deps_tree,
        "/storage-audit": handle_storage_audit,
        "/config-fix": handle_config_fix,
        "/git-smart": handle_git_smart,
        "/regex": handle_regex,
        "/db-design": handle_db_design,
        "/backup": handle_backup,
        "/restore": handle_restore,
        "/system-info": handle_system_info,
        "/process-list": handle_process_list,
        "/process-kill": handle_process_kill,
        "/cron-add": handle_cron_add,
        "/cron-list": handle_cron_list,
        "/cron-remove": handle_cron_remove,
        "/diff": handle_diff,
        "/patch": handle_patch,
        "/health": handle_health,
        "/cloud-sync": handle_cloud_sync,
        "/git-pr": handle_git_pr,
        "/recipe-list": handle_recipe_list,
        "/recipe-run": handle_recipe_run,
        "/recipe-save": handle_recipe_save,
        "/context": handle_context,
        "/context-save": handle_context_save,
        "/smart-install": handle_smart_install,
        "/permission-fix": handle_permission_fix,
        "/profile": handle_profile,
        "/error-explain": handle_error_explain,
        "/ssh-wizard": handle_ssh_wizard,
        "/service-guard": handle_service_guard,
        "/history-insight": handle_history_insight,
        "/optimize": handle_optimize,
        "/quick-cmd": handle_quick_cmd,
        "/port-manage": handle_port_manage,
        "/migrate": handle_migrate,
        "/tutorial": handle_tutorial,
        "/history": handle_history_list,
        "/history-clear": handle_history_clear,
    }


# Cache handler map
_HANDLER_MAP: dict | None = None


def _get_handler_map() -> dict:
    global _HANDLER_MAP
    if _HANDLER_MAP is None:
        _HANDLER_MAP = _build_handler_map()
    return _HANDLER_MAP


# ─── Invoke Handler In-Process ───────────────────────────────────────────

def _call_handler(endpoint: str, arguments: dict) -> str:
    """
    Invoke a handler function in-process using a FakeHandler.
    Returns the captured response body as a string.
    """
    handler_map = _get_handler_map()

    # Check if endpoint has a direct handler mapping
    if endpoint in handler_map:
        fake = FakeHandler(method="POST", path=endpoint, body=arguments)
        try:
            handler_map[endpoint](fake, arguments)
            return fake.get_body() or "(handler returned no output)"
        except Exception as e:
            return f"[Handler Error] {e}"

    # For inline handlers in MCPHandler, we need to create an instance
    # and call the private method. We'll create a minimal instance.
    fake = FakeHandler(method="POST", path=endpoint, body=arguments)

    # Map endpoints to MCPHandler private method names
    inline_methods = {
        "/run": "_handle_run",
        "/ls": "_handle_ls",
        "/read": "_handle_read",
        "/write": "_handle_write",
        "/mkdir": "_handle_mkdir",
        "/delete": "_handle_delete",
        "/search": "_handle_search",
        "/cancel": None,  # special case
        "/battery": "_handle_battery",
        "/vibrate": "_handle_vibrate",
        "/torch": "_handle_torch",
        "/wallpaper": "_handle_wallpaper",
        "/brightness": "_handle_brightness",
        "/volume": "_handle_volume",
        "/sensor": "_handle_sensor",
        "/fingerprint": "_handle_fingerprint",
        "/infrared": "_handle_infrared",
        "/wifi-info": "_handle_wifi_info",
        "/wifi-scan": "_handle_wifi_scan",
        "/location": "_handle_location",
        "/public-ip": "_handle_public_ip",
        "/clipboard-get": "_handle_clipboard_get",
        "/clipboard-set": "_handle_clipboard_set",
        "/sms-send": "_handle_sms_send",
        "/sms-inbox": "_handle_sms_inbox",
        "/contacts": "_handle_contacts",
        "/call": "_handle_call",
        "/notify": "_handle_notify",
        "/notify-remove": "_handle_notify_remove",
        "/share": "_handle_share",
        "/open-url": "_handle_open_url",
        "/download": "_handle_download",
        "/list-apps": "_handle_list_apps",
        "/camera-photo": "_handle_camera_photo",
        "/camera-info": "_handle_camera_info",
        "/screenshot": "_handle_screenshot",
        "/screen-record": "_handle_screen_record",
        "/tts-speak": "_handle_tts_speak",
        "/speech-to-text": "_handle_speech_to_text",
        "/microphone-record": "_handle_microphone_record",
        "/media-player": "_handle_media_player",
        "/qrcode": "_handle_qrcode",
        "/scan-barcode": "_handle_scan_barcode",
        "/speedtest": "_handle_speedtest",
        "/image-process": "_handle_image_process",
        "/video-process": "_handle_video_process",
        "/text-extract": "_handle_text_extract",
        "/weather": "_handle_weather",
        "/translate": "_handle_translate",
        "/db-query": "_handle_db_query",
        "/web-server": "_handle_web_server",
        "/git-op": "_handle_git_op",
        "/telephony-deviceinfo": "_handle_telephony_deviceinfo",
        "/telephony-cellinfo": "_handle_telephony_cellinfo",
        "/storage-get": "_handle_storage_get",
    }

    if endpoint == "/cancel":
        from .shell import cancel_active
        ok = cancel_active()
        return json.dumps({"cancelled": ok})

    method_name = inline_methods.get(endpoint)
    if method_name is None:
        return f"[Error] Unknown endpoint: {endpoint}"

    # Create MCPHandler-like object by using FakeHandler as base
    # We need to copy the method from MCPHandler onto our fake
    from .handler import MCPHandler
    method_fn = getattr(MCPHandler, method_name, None)
    if method_fn is None:
        return f"[Error] Handler method {method_name} not found"

    try:
        method_fn(fake, arguments)
        return fake.get_body() or "(no output)"
    except Exception as e:
        return f"[Handler Error] {endpoint}: {e}"


# ─── MCP JSON-RPC Handlers ──────────────────────────────────────────────

def _handle_initialize(params: dict) -> dict:
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": {"name": "termux-mcp", "version": "0.7.3"},
    }


def _handle_tools_list(params: dict) -> dict:
    return {"tools": MCP_TOOLS}


def _handle_tools_call(params: dict) -> dict:
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    # Map MCP tool name to endpoint
    from .mcp_bridge import ENDPOINT_MAP
    if tool_name in ENDPOINT_MAP:
        endpoint, _ = ENDPOINT_MAP[tool_name]
    else:
        endpoint = "/" + tool_name.replace("_", "-")

    logger.info(f"MCP tools/call: {tool_name} → {endpoint}")
    result_text = _call_handler(endpoint, arguments)

    return {
        "content": [{"type": "text", "text": result_text}],
    }


# ─── MCP HTTP Server ────────────────────────────────────────────────────

class MCPBridgeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        logger.debug("[MCP] " + fmt, *args)

    def _send_json(self, code: int, data: dict) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, code: int, rpc_id, error_code: int, message: str) -> None:
        self._send_json(code, {
            "jsonrpc": "2.0", "id": rpc_id,
            "error": {"code": error_code, "message": message},
        })

    def _check_auth(self) -> bool:
        if not REQUIRE_AUTH:
            return True
        auth = (self.headers.get("X-API-Key", "")
                or self.headers.get("Authorization", "").removeprefix("Bearer "))
        if auth == AUTH_TOKEN:
            return True
        self._send_json(401, {
            "jsonrpc": "2.0", "id": None,
            "error": {"code": -32000, "message": "Unauthorized"},
        })
        return False

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, Authorization, X-API-Key, MCP-Session-Id, Accept")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        if path != "/mcp":
            self._send_json(404, {"error": "Use POST /mcp"})
            return
        if not self._check_auth():
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8")
            request = json.loads(raw) if raw else {}
        except Exception as e:
            self._send_error(400, None, -32700, f"Parse error: {e}")
            return

        rpc_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        handlers = {
            "initialize": _handle_initialize,
            "notifications/initialized": lambda p: None,
            "tools/list": _handle_tools_list,
            "tools/call": _handle_tools_call,
        }

        handler_fn = handlers.get(method)
        if handler_fn is None:
            self._send_error(200, rpc_id, -32601, f"Method not found: {method}")
            return

        try:
            result = handler_fn(params)

            if request.get("id") is None and method.startswith("notifications/"):
                self.send_response(202)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            session_id = self.headers.get("MCP-Session-Id", str(uuid4()))
            response = {"jsonrpc": "2.0", "id": rpc_id, "result": result}
            body = json.dumps(response).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("MCP-Session-Id", session_id)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            logger.error(f"MCP handler error: {e}", exc_info=True)
            self._send_error(200, rpc_id, -32603, f"Internal error: {e}")

    def do_GET(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        if path == "/mcp":
            self._send_json(405, {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": "Use POST /mcp"},
                "id": None,
            })
        elif path == "/health":
            self._send_json(200, {
                "status": "ok", "name": "termux-mcp",
                "version": "0.7.3", "protocol": "mcp-standalone",
            })
        else:
            self._send_json(404, {"error": "Not found"})

    def do_DELETE(self) -> None:
        self._send_json(405, {
            "jsonrpc": "2.0",
            "error": {"code": -32000, "message": "Not supported"},
            "id": None,
        })


class ThreadingMCPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def run_mcp_server(host: str = MCP_HOST, port: int = MCP_PORT) -> None:
    server = ThreadingMCPServer((host, port), MCPBridgeHandler)
    logger.info("MCP Bridge listening on http://%s:%d/mcp", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("MCP Bridge shutting down...")
        server.server_close()
