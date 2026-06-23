"""
Entry point for running Termux-MCP (MCP-only mode).

Usage:
    python -m termux_mcp                          # Start MCP server (default port 3000)
    python -m termux_mcp --port 3000 --host 0.0.0.0
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


def _import_handlers() -> None:
    """Import all handler modules so @register_tool decorators fire."""
    from .handlers import basic, device, tools, ai_power, terminal, features, history  # noqa: F401


def main():
    parser = argparse.ArgumentParser(description="Termux MCP Server")
    parser.add_argument("--port", type=int, default=3000,
                        help="MCP server port (default: 3000)")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="MCP server bind address (default: 0.0.0.0)")
    args = parser.parse_args()

    # Register all tools
    _import_handlers()

    from .registry import TOOL_REGISTRY, list_categories
    logger.info(f"Registered {len(TOOL_REGISTRY)} tools:")
    for cat, names in sorted(list_categories().items()):
        logger.info(f"  [{cat}] {', '.join(names)}")

    # Update server config
    from . import mcp_server
    mcp_server.MCP_HOST = args.host
    mcp_server.MCP_PORT = args.port

    logger.info("")
    logger.info("╔══════════════════════════════════════════════════╗")
    logger.info("║         Termux MCP Server v1.0.0                ║")
    logger.info("╠══════════════════════════════════════════════════╣")
    logger.info(f"║  MCP:  http://{args.host}:{args.port}/mcp")
    logger.info("╚══════════════════════════════════════════════════╝")
    logger.info("")

    try:
        mcp_server.run_mcp_server(args.host, args.port)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
