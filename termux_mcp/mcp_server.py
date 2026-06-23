"""
MCP Server for Termux-MCP (Direct Mode)
=========================================
A standalone MCP (Streamable HTTP) server that calls registered tool
handlers directly — no REST bridge, no internal HTTP forwarding.

Protocol: JSON-RPC 2.0 over HTTP POST /mcp
No external dependencies — uses only Python standard library.
"""

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from uuid import uuid4

from .config import AUTH_TOKEN, REQUIRE_AUTH

logger = logging.getLogger(__name__)

# ─── Server Defaults ────────────────────────────────────────────────────

MCP_HOST = "0.0.0.0"
MCP_PORT = 3000


# ─── JSON-RPC Helpers ───────────────────────────────────────────────────

def _handle_initialize(params: dict) -> dict:
    """Handle MCP initialize handshake."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {"listChanged": False},
        },
        "serverInfo": {
            "name": "termux-mcp",
            "version": "1.0.0",
        },
    }


def _handle_tools_list(params: dict) -> dict:
    """Return all registered tools from the registry."""
    from .registry import get_mcp_tools
    return {"tools": get_mcp_tools()}


def _handle_tools_call(params: dict) -> dict:
    """Dispatch a tools/call to the registry."""
    from .registry import call_tool

    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    logger.info(f"MCP tools/call: {tool_name}")
    result_text = call_tool(tool_name, arguments)

    return {
        "content": [
            {
                "type": "text",
                "text": result_text if result_text else "(no output)",
            }
        ],
    }


# ─── MCP HTTP Request Handler ────────────────────────────────────────────

class MCPHandler(BaseHTTPRequestHandler):
    """Handles MCP protocol requests on /mcp endpoint."""

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
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": error_code, "message": message},
        })

    def _check_auth(self) -> bool:
        if not REQUIRE_AUTH:
            return True
        auth = (
            self.headers.get("X-API-Key", "")
            or self.headers.get("Authorization", "").removeprefix("Bearer ")
        )
        if auth == AUTH_TOKEN:
            return True
        self._send_json(401, {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32000, "message": "Unauthorized: Invalid API Key"},
        })
        return False

    # ── HTTP Methods ─────────────────────────────────────────────────────

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
            "notifications/initialized": lambda p: None,
            "tools/list":              _handle_tools_list,
            "tools/call":              _handle_tools_call,
        }

        handler_fn = handlers.get(method)

        if handler_fn is None:
            self._send_error(200, rpc_id, -32601, f"Method not found: {method}")
            return

        try:
            result = handler_fn(params)

            # Notifications (no id) — just acknowledge
            if request.get("id") is None and method.startswith("notifications/"):
                self.send_response(202)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            # Build JSON-RPC response
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
        """Handle GET /mcp (SSE) — return 405 for stateless mode."""
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
                "version": "1.0.0",
                "protocol": "mcp-direct",
            })
        else:
            self._send_json(404, {"error": "Not found"})

    def do_DELETE(self) -> None:
        self._send_json(405, {
            "jsonrpc": "2.0",
            "error": {"code": -32000, "message": "Session management not supported in stateless mode"},
            "id": None,
        })


# ─── Threaded Server ─────────────────────────────────────────────────────

class ThreadingMCPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def run_mcp_server(host: str = MCP_HOST, port: int = MCP_PORT) -> None:
    """Start the MCP server."""
    server = ThreadingMCPServer((host, port), MCPHandler)
    logger.info(f"MCP server listening on http://{host}:{port}/mcp")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("MCP server shutting down...")
        server.server_close()
