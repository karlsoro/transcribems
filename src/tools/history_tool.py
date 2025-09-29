"""History MCP tool.

This tool provides access to transcription history with filtering,
search capabilities, and statistics.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..services.history_service import HistoryService
from ..services.storage_service import StorageService
from ..error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)

# Initialize services
storage_service = StorageService()
history_service = HistoryService(storage_service)
error_handler = MCPErrorHandler()

async def list_transcription_history_tool(request: dict) -> dict:
    """MCP tool for listing transcription history.

    Args:
        request: MCP request containing:
            - limit: Maximum entries to return (default 10)
            - status_filter: Filter by status (completed, failed, processing, etc.)
            - date_from: Start date filter (ISO format)
            - date_to: End date filter (ISO format)
            - search_query: Search in filenames (optional)
            - get_statistics: Include usage statistics (default False)
            - statistics_days: Days for statistics (default 30)

    Returns:
        dict: History data with optional statistics
    """
    try:
        # Extract parameters
        limit = request.get('limit', 10)
        status_filter = request.get('status_filter')
        search_query = request.get('search_query')
        get_statistics = request.get('get_statistics', False)
        statistics_days = request.get('statistics_days', 30)

        # Parse date filters
        date_from = None
        date_to = None
        if request.get('date_from'):
            try:
                date_from = datetime.fromisoformat(request['date_from'].replace('Z', '+00:00'))
            except ValueError:
                return error_handler.invalid_parameters("Invalid date_from format. Use ISO format.")

        if request.get('date_to'):
            try:
                date_to = datetime.fromisoformat(request['date_to'].replace('Z', '+00:00'))
            except ValueError:
                return error_handler.invalid_parameters("Invalid date_to format. Use ISO format.")

        # Handle search query
        if search_query:
            search_results = await history_service.search_history(search_query, limit)
            response = {
                "success": True,
                "history": search_results
            }
        else:
            # Get filtered history
            history = await history_service.get_history(
                limit=limit,
                status_filter=status_filter,
                date_from=date_from,
                date_to=date_to
            )
            response = {
                "success": True,
                "history": history
            }

        # Add statistics if requested
        if get_statistics:
            stats = await history_service.get_statistics(statistics_days)
            response["statistics"] = stats

        return response

    except Exception as e:
        logger.error(f"History tool error: {e}")
        return error_handler.internal_error(f"History retrieval failed: {str(e)}")

list_transcription_history_tool.__name__ = 'list_transcription_history_tool'