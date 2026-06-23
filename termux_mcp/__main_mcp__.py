"""
Entry point for running Termux-MCP with MCP protocol bridge.

Usage:
    python -m termux_mcp --mcp          # Run MCP server only (port 3000)
    python -m termux_mcp                # Run original REST server only
    python -m termux_mcp --mcp --mcp-port 3000
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Termux MCP Server")
    parser.add_argument("--mcp", action="store_true", default=False,
                        help="Run MCP protocol server (default port 3000)")
    parser.add_argument("--mcp-port", type=int, default=3000,
                        help="MCP server port (default: 3000)")
    parser.add_argument("--mcp-host", type=str, default="0.0.0.0",
                        help="MCP server bind address (default: 0.0.0.0)")
    args = parser.parse_args()

    if args.mcp:
        from .mcp_bridge import run_mcp_server

        print("", flush=True)
        print("=" * 52, flush=True)
        print("       Termux MCP Server v0.7.3", flush=True)
        print("=" * 52, flush=True)
        print(f"  MCP:     http://{args.mcp_host}:{args.mcp_port}/mcp", flush=True)
        print(f"  Health:  http://{args.mcp_host}:{args.mcp_port}/health", flush=True)
        print("=" * 52, flush=True)
        print("  Press Ctrl+C to stop", flush=True)
        print("", flush=True)

        try:
            run_mcp_server(args.mcp_host, args.mcp_port)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            sys.exit(0)
    else:
        from . import server
        server.run()


if __name__ == "__main__":
    main()
