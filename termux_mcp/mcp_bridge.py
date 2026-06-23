"""
MCP Protocol Bridge for Termux-MCP
====================================
Adds Model Context Protocol (Streamable HTTP) support on top of the
existing REST API server. MiClaw (or any MCP client) connects to
/mcp and gets standard JSON-RPC 2.0 responses.

Architecture:
  - Original HTTP server runs on 127.0.0.1:8080 (unchanged)
  - MCP server runs on 0.0.0.0:3000, exposes /mcp endpoint
  - tools/call → internal HTTP request to original server → return result

No external dependencies — uses only Python standard library.
"""

import json
import logging
import threading
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from uuid import uuid4

from .config import AUTH_TOKEN, REQUIRE_AUTH
from .mcp_tools import MCP_TOOLS

logger = logging.getLogger(__name__)

# ─── MCP Server Configuration ───────────────────────────────────────────
MCP_HOST = "0.0.0.0"
MCP_PORT = 3000

# Where the original termux-mcp server runs
INTERNAL_HOST = "127.0.0.1"
INTERNAL_PORT = 8080


# ─── Internal HTTP Bridge ───────────────────────────────────────────────

def _call_internal(endpoint: str, payload: dict, method: str = "POST") -> str:
    """Make an HTTP request to the original server and return the response body."""
    url = f"http://{INTERNAL_HOST}:{INTERNAL_PORT}{endpoint}"

    if method == "GET":
        req = urllib.request.Request(url, method="GET")
    else:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")

    # Forward auth token if required
    if REQUIRE_AUTH and AUTH_TOKEN:
        req.add_header("Authorization", f"Bearer {AUTH_TOKEN}")

    try:
        with urllib.request.urlopen(req, timeout=130) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return f"[HTTP {e.code}] {body}"
    except Exception as e:
        return f"[Error] {e}"


# ─── Endpoint Mapping ────────────────────────────────────────────────────

# Maps MCP tool names to (endpoint, http_method)
# Tools not listed here will use the default pattern: /tool-name (POST)
ENDPOINT_MAP: dict[str, tuple[str, str]] = {
    # Shell & File
    "shell_exec":       ("/run", "POST"),
    "shell_cancel":     ("/cancel", "POST"),
    "file_list":        ("/ls", "POST"),
    "file_read":        ("/read", "POST"),
    "file_write":       ("/write", "POST"),
    "file_mkdir":       ("/mkdir", "POST"),
    "file_delete":      ("/delete", "POST"),
    "file_search":      ("/search", "POST"),
    # Device
    "battery_status":   ("/battery", "POST"),
    "vibrate":          ("/vibrate", "POST"),
    "torch":            ("/torch", "POST"),
    "wallpaper":        ("/wallpaper", "POST"),
    "brightness":       ("/brightness", "POST"),
    "volume":           ("/volume", "POST"),
    "sensor_read":      ("/sensor", "POST"),
    "fingerprint":      ("/fingerprint", "POST"),
    "infrared":         ("/infrared", "POST"),
    # Network
    "wifi_info":        ("/wifi-info", "POST"),
    "wifi_scan":        ("/wifi-scan", "POST"),
    "location":         ("/location", "POST"),
    "public_ip":        ("/public-ip", "POST"),
    # Communication
    "clipboard_get":    ("/clipboard-get", "POST"),
    "clipboard_set":    ("/clipboard-set", "POST"),
    "sms_send":         ("/sms-send", "POST"),
    "sms_inbox":        ("/sms-inbox", "POST"),
    "contacts":         ("/contacts", "POST"),
    "phone_call":       ("/call", "POST"),
    "notify":           ("/notify", "POST"),
    "notify_remove":    ("/notify-remove", "POST"),
    "share":            ("/share", "POST"),
    "open_url":         ("/open-url", "POST"),
    # Media
    "camera_photo":     ("/camera-photo", "POST"),
    "camera_info":      ("/camera-info", "POST"),
    "screenshot":       ("/screenshot", "POST"),
    "screen_record":    ("/screen-record", "POST"),
    "tts_speak":        ("/tts-speak", "POST"),
    "speech_to_text":   ("/speech-to-text", "POST"),
    "microphone_record":("/microphone-record", "POST"),
    "media_player":     ("/media-player", "POST"),
    "qrcode":           ("/qrcode", "POST"),
    "scan_barcode":     ("/scan-barcode", "POST"),
    # System
    "system_info":      ("/system-info", "POST"),
    "process_list":     ("/process-list", "POST"),
    "process_kill":     ("/process-kill", "POST"),
    "health":           ("/health", "POST"),
    "env":              ("/env", "GET"),
    "ping":             ("/ping", "GET"),
    # Tools & Dev
    "download":         ("/download", "POST"),
    "list_apps":        ("/list-apps", "POST"),
    "speedtest":        ("/speedtest", "POST"),
    "image_process":    ("/image-process", "POST"),
    "video_process":    ("/video-process", "POST"),
    "text_extract":     ("/text-extract", "POST"),
    "weather":          ("/weather", "POST"),
    "translate":        ("/translate", "POST"),
    "db_query":         ("/db-query", "POST"),
    "web_server":       ("/web-server", "POST"),
    "git_op":           ("/git-op", "POST"),
    # Terminal Power-Tools
    "diagnose":         ("/diagnose", "POST"),
    "pkg_smart":        ("/pkg-smart", "POST"),
    "explain":          ("/explain", "POST"),
    "dev_env":          ("/dev-env", "POST"),
    "review":           ("/review", "POST"),
    "log_analyze":      ("/log-analyze", "POST"),
    "script_gen":       ("/script-gen", "POST"),
    "deps_tree":        ("/deps-tree", "POST"),
    "storage_audit":    ("/storage-audit", "POST"),
    "config_fix":       ("/config-fix", "POST"),
    "git_smart":        ("/git-smart", "POST"),
    "regex_test":       ("/regex", "POST"),
    "db_design":        ("/db-design", "POST"),
    "backup":           ("/backup", "POST"),
    "restore":          ("/restore", "POST"),
    # AI Power Features
    "smart_install":    ("/smart-install", "POST"),
    "permission_fix":   ("/permission-fix", "POST"),
    "profile":          ("/profile", "POST"),
    "error_explain":    ("/error-explain", "POST"),
    "ssh_wizard":       ("/ssh-wizard", "POST"),
    "service_guard":    ("/service-guard", "POST"),
    "history_insight":  ("/history-insight", "POST"),
    "optimize":         ("/optimize", "POST"),
    "quick_cmd":        ("/quick-cmd", "POST"),
    "port_manage":      ("/port-manage", "POST"),
    "migrate":          ("/migrate", "POST"),
    "tutorial":         ("/tutorial", "POST"),
    # Features
    "cron_add":         ("/cron-add", "POST"),
    "cron_list":        ("/cron-list", "POST"),
    "cron_remove":      ("/cron-remove", "POST"),
    "diff_files":       ("/diff", "POST"),
    "patch_file":       ("/patch", "POST"),
    "cloud_sync":       ("/cloud-sync", "POST"),
    "git_pr":           ("/git-pr", "POST"),
    "recipe_list":      ("/recipe-list", "POST"),
    "recipe_run":       ("/recipe-run", "POST"),
    "recipe_save":      ("/recipe-save", "POST"),
    "context":          ("/context", "POST"),
    "context_save":     ("/context-save", "POST"),
    # History
    "history_list":     ("/history", "GET"),
    "history_save":     ("/history", "POST"),
    "history_clear":    ("/history-clear", "POST"),
    # Telephony
    "telephony_device": ("/telephony-deviceinfo", "POST"),
    "telephony_cell":   ("/telephony-cellinfo", "POST"),
    "storage_get":      ("/storage-get", "POST"),
}


# ─── MCP JSON-RPC Handler ───────────────────────────────────────────────

def _handle_initialize(params: dict) -> dict:
    """Handle MCP initialize request."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {"listChanged": False},
        },
        "serverInfo": {
            "name": "termux-mcp",
            "version": "0.7.3",
        },
    }


def _handle_tools_list(params: dict) -> dict:
    """Return all tool definitions in MCP format."""
    return {"tools": MCP_TOOLS}


def _handle_tools_call(params: dict) -> dict:
    """Forward tool call to the original server and return result."""
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    # Look up endpoint
    if tool_name in ENDPOINT_MAP:
        endpoint, method = ENDPOINT_MAP[tool_name]
    else:
        # Default: convert tool_name to kebab-case endpoint
        endpoint = "/" + tool_name.replace("_", "-")
        method = "POST"

    # Call the original server
    logger.info(f"MCP tools/call: {tool_name} → {method} {endpoint}")
    result_text = _call_internal(endpoint, arguments, method)

    return {
        "content": [
            {
                "type": "text",
                "text": result_text if result_text else "(no output)",
            }
        ],
    }


# ─── MCP HTTP Request Handler ────────────────────────────────────────────

class MCPBridgeHandler(BaseHTTPRequestHandler):
    """Handles MCP protocol requests on /mcp endpoint."""

    protocol_version = "HTTP/1.1"
    sessions: dict[str, dict] = {}

    def log_message(self, fmt, *args):
        logger.debug("[MCP-Bridge] " + fmt, *args)

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
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": error_code, "message": message},
        })

    def _check_auth(self) -> bool:
        if not REQUIRE_AUTH:
            return True
        auth = self.headers.get("X-API-Key", "") or \
               self.headers.get("Authorization", "").removeprefix("Bearer ")
        if auth == AUTH_TOKEN:
            return True
        self._send_json(401, {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32000, "message": "Unauthorized: Invalid API Key"},
        })
        return False

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key, MCP-Session-Id, Accept")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/mcp":
            self._send_json(404, {"error": "Not found. Use POST /mcp"})
            return

        if not self._check_auth():
            return

        # Read JSON-RPC body
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

        logger.info(f"MCP request: method={method}, id={rpc_id}")

        # Route to handlers
        handlers = {
            "initialize":              _handle_initialize,
            "notifications/initialized": lambda p: None,  # notification, no response needed
            "tools/list":               _handle_tools_list,
            "tools/call":               _handle_tools_call,
        }

        handler_fn = handlers.get(method)

        if handler_fn is None:
            self._send_error(200, rpc_id, -32601, f"Method not found: {method}")
            return

        try:
            result = handler_fn(params)

            # Notifications (no id) don't get a response
            if request.get("id") is None and method.startswith("notifications/"):
                self.send_response(202)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            # Set session ID on initialize response
            session_id = self.headers.get("MCP-Session-Id", str(uuid4()))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("MCP-Session-Id", session_id)
            self.send_header("Access-Control-Allow-Origin", "*")

            response = {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": result,
            }
            body = json.dumps(response).encode("utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            logger.error(f"MCP handler error: {e}", exc_info=True)
            self._send_error(200, rpc_id, -32603, f"Internal error: {e}")

    def do_GET(self) -> None:
        """Handle GET /mcp (SSE stream) — return 405 for stateless mode."""
        if self.path.rstrip("/") == "/mcp":
            self._send_json(405, {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": "GET /mcp not supported in stateless mode"},
                "id": None,
            })
        elif self.path == "/health":
            self._send_json(200, {
                "status": "ok",
                "name": "termux-mcp",
                "version": "0.7.3",
                "protocol": "mcp-bridge",
            })
        else:
            self._send_json(404, {"error": "Not found"})

    def do_DELETE(self) -> None:
        self._send_json(405, {
            "jsonrpc": "2.0",
            "error": {"code": -32000, "message": "Session management not supported in stateless mode"},
            "id": None,
        })


class ThreadingMCPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def run_mcp_server(host: str = MCP_HOST, port: int = MCP_PORT) -> None:
    """Start the MCP bridge server."""
    server = ThreadingMCPServer((host, port), MCPBridgeHandler)
    logger.info(f"MCP Bridge listening on http://{host}:{port}/mcp")
    logger.info(f"Internal server: http://{INTERNAL_HOST}:{INTERNAL_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("MCP Bridge shutting down...")
        server.server_close()
