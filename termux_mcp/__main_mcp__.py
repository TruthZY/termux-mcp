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
        # Override config if specified
        if args.api_port:
            from . import config
            config.PORT = args.api_port
        if args.api_host:
            from . import config
            config.HOST = args.api_host

        from .config import HOST, PORT

        # ── Step 1: Start MCP bridge in a background thread ──
        from . import mcp_bridge
        mcp_bridge.MCP_HOST = args.mcp_host
        mcp_bridge.MCP_PORT = args.mcp_port
        mcp_bridge.INTERNAL_HOST = HOST
        mcp_bridge.INTERNAL_PORT = PORT

        mcp_error = [None]  # use list so inner function can write to it

        def run_mcp():
            try:
                mcp_bridge.run_mcp_server(args.mcp_host, args.mcp_port)
            except Exception as e:
                mcp_error[0] = e

        mcp_thread = threading.Thread(target=run_mcp, daemon=True, name="mcp-bridge")
        mcp_thread.start()

        # Give MCP bridge a moment to bind its port
        time.sleep(0.5)

        if mcp_error[0] is not None:
            logger.error(f"MCP Bridge failed to start: {mcp_error[0]}")
            sys.exit(1)

        # ── Step 2: Print banner ──
        print("")
        print("=" * 54)
        print("       Termux MCP Server + Bridge v0.7.3")
        print("=" * 54)
        print(f"  REST API:  http://{HOST}:{PORT}")
        print(f"  MCP:       http://{args.mcp_host}:{args.mcp_port}/mcp")
        print(f"  Health:    http://{args.mcp_host}:{args.mcp_port}/health")
        print("=" * 54)
        print("")
        sys.stdout.flush()

        # ── Step 3: Start original REST server on main thread ──
        from . import server as original_server
        try:
            original_server.run()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            sys.exit(0)
    else:
        # Original mode: just run the REST server
        from . import server
        server.run()


if __name__ == "__main__":
    main()
