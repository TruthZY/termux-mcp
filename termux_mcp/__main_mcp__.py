"""
Entry point for running Termux-MCP with MCP protocol bridge.

Usage:
    python -m termux_mcp --mcp          # Run with MCP bridge (default port 3000)
    python -m termux_mcp                # Run original REST server only
    python -m termux_mcp --mcp --mcp-port 3000 --api-port 8080
"""

import argparse
import logging
import sys
import threading
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Termux MCP Server")
    parser.add_argument("--mcp", action="store_true", default=False,
                        help="Enable MCP protocol bridge on /mcp endpoint")
    parser.add_argument("--mcp-port", type=int, default=3000,
                        help="MCP bridge port (default: 3000)")
    parser.add_argument("--mcp-host", type=str, default="0.0.0.0",
                        help="MCP bridge bind address (default: 0.0.0.0)")
    parser.add_argument("--api-port", type=int, default=None,
                        help="Override internal API server port")
    parser.add_argument("--api-host", type=str, default=None,
                        help="Override internal API server host")
    args = parser.parse_args()

    if args.mcp:
        _run_with_mcp(args)
    else:
        from . import server
        server.run()


def _run_with_mcp(args):
    """Run both REST API server and MCP bridge simultaneously."""
    from .config import HOST, PORT, AUTH_TOKEN, REQUIRE_AUTH
    from .handler import MCPHandler
    from .network import kill_port
    from .shell import get_current_dir
    from .mcp_bridge import MCPBridgeHandler, ThreadingMCPServer

    # Override config if specified
    if args.api_port:
        from . import config
        config.PORT = args.api_port
        import importlib
        importlib.reload(config)
        from .config import PORT
    if args.api_host:
        from . import config
        config.HOST = args.api_host
        import importlib
        importlib.reload(config)
        from .config import HOST

    # ── Auth checks ──
    if REQUIRE_AUTH:
        if len(AUTH_TOKEN) < 16:
            logger.error("TERMUX_MCP_AUTH_TOKEN too short (< 16 chars).")
            sys.exit(1)
        logger.info("Auth token configured (length=%d)", len(AUTH_TOKEN))

    if HOST not in ("127.0.0.1", "localhost") and not REQUIRE_AUTH:
        logger.error("HOST=%s is non-loopback but no auth token set.", HOST)
        sys.exit(1)

    # ── Free ports ──
    logger.info("Freeing port %d (REST)...", PORT)
    kill_port(PORT)
    logger.info("Freeing port %d (MCP)...", args.mcp_port)
    kill_port(args.mcp_port)

    # ── Create both servers ──
    from http.server import HTTPServer
    from socketserver import ThreadingMixIn

    class RestServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    rest_server = RestServer((HOST, PORT), MCPHandler)
    mcp_server = ThreadingMCPServer((args.mcp_host, args.mcp_port), MCPBridgeHandler)

    # Update bridge internal target
    from . import mcp_bridge
    mcp_bridge.INTERNAL_HOST = HOST
    mcp_bridge.INTERNAL_PORT = PORT

    # ── Start both in daemon threads ──
    errors = []

    def run_rest():
        try:
            rest_server.serve_forever()
        except Exception as e:
            errors.append(f"REST server error: {e}")

    def run_mcp():
        try:
            mcp_server.serve_forever()
        except Exception as e:
            errors.append(f"MCP bridge error: {e}")

    t_rest = threading.Thread(target=run_rest, daemon=True, name="rest-server")
    t_mcp = threading.Thread(target=run_mcp, daemon=True, name="mcp-bridge")

    t_rest.start()
    t_mcp.start()

    # Give both a moment to bind
    time.sleep(0.3)

    if errors:
        for err in errors:
            logger.error(err)
        sys.exit(1)

    # ── Banner ──
    print("", flush=True)
    print("=" * 56, flush=True)
    print("       Termux MCP Server + Bridge v0.7.3", flush=True)
    print("=" * 56, flush=True)
    print(f"  REST API:  http://{HOST}:{PORT}", flush=True)
    print(f"  MCP:       http://{args.mcp_host}:{args.mcp_port}/mcp", flush=True)
    print(f"  Health:    http://{args.mcp_host}:{args.mcp_port}/health", flush=True)
    print(f"  Work dir:  {get_current_dir()}", flush=True)
    print("=" * 56, flush=True)
    print("  Press Ctrl+C to stop", flush=True)
    print("", flush=True)

    logger.info("REST API running on http://%s:%d", HOST, PORT)
    logger.info("MCP Bridge running on http://%s:%d/mcp", args.mcp_host, args.mcp_port)

    # ── Block main thread ──
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        rest_server.shutdown()
        mcp_server.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()
