"""CLI launcher for TranscribeMCP server with stdio and HTTP transport options.

This module provides command-line interface for starting the TranscribeMCP server
in different modes: stdio (for Claude Desktop) or HTTP (for other AI applications).
"""

import argparse
import asyncio
import logging
import sys
from typing import Literal

from .server import TranscribeMCPServer

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the server.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr  # Log to stderr to keep stdout clean for stdio mode
    )


async def run_stdio_mode(server: TranscribeMCPServer) -> None:
    """Run server in stdio mode for Claude Desktop integration.

    Args:
        server: Initialized TranscribeMCPServer instance
    """
    logger.info("Starting TranscribeMCP in stdio mode (Claude Desktop compatible)")
    try:
        await server.run_stdio()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


async def run_http_mode(
    server: TranscribeMCPServer,
    host: str = "0.0.0.0",
    port: int = 8000,
    transport: Literal["sse", "streamable_http"] = "sse"
) -> None:
    """Run server in HTTP mode for general AI application integration.

    Args:
        server: Initialized TranscribeMCPServer instance
        host: Host address to bind to
        port: Port number to listen on
        transport: HTTP transport type ('sse' or 'streamable_http')
    """
    logger.info(f"Starting TranscribeMCP in HTTP mode ({transport})")
    logger.info(f"Server listening on http://{host}:{port}")

    try:
        if transport == "sse":
            await server.run_sse(host=host, port=port)
        else:
            await server.run_streamable_http(host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="transcribe-mcp",
        description="TranscribeMCP Server - Audio transcription with WhisperX",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start in stdio mode (for Claude Desktop)
  transcribe-mcp stdio

  # Start in HTTP SSE mode (default)
  transcribe-mcp http

  # Start in HTTP mode with custom host and port
  transcribe-mcp http --host 127.0.0.1 --port 3000

  # Start in HTTP StreamableHTTP mode
  transcribe-mcp http --transport streamable_http

  # Enable debug logging
  transcribe-mcp stdio --log-level DEBUG
        """
    )

    # Add subparsers for different modes
    subparsers = parser.add_subparsers(dest="mode", help="Server mode", required=True)

    # Stdio mode (for Claude Desktop)
    stdio_parser = subparsers.add_parser(
        "stdio",
        help="Run in stdio mode for Claude Desktop integration"
    )
    stdio_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    # HTTP mode (for general AI applications)
    http_parser = subparsers.add_parser(
        "http",
        help="Run in HTTP mode for general AI application integration"
    )
    http_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host address to bind to (default: 0.0.0.0)"
    )
    http_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number to listen on (default: 8000)"
    )
    http_parser.add_argument(
        "--transport",
        choices=["sse", "streamable_http"],
        default="sse",
        help="HTTP transport type (default: sse)"
    )
    http_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    return parser


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Create server instance
    try:
        server = TranscribeMCPServer()
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}", exc_info=True)
        sys.exit(1)

    # Run in the appropriate mode
    try:
        if args.mode == "stdio":
            asyncio.run(run_stdio_mode(server))
        elif args.mode == "http":
            asyncio.run(run_http_mode(
                server,
                host=args.host,
                port=args.port,
                transport=args.transport
            ))
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
