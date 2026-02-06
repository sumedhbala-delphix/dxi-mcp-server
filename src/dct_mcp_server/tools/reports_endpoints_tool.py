from enum import Enum
from typing import Literal

class Reports_EndpointsOperation(Enum):
    """Available operations for reports_endpoints."""
    SEARCH_STORAGE_CAPACITY = "search_storage_capacity"
    SEARCH_STORAGE_SAVINGS = "search_storage_savings"
    SEARCH_VIRTUALIZATION_SUMMARY = "search_virtualization_summary"
from mcp.server.fastmcp import FastMCP
from typing import Dict,Any,Optional
from ..core.decorators import log_tool_execution
import asyncio
import logging
import threading
from functools import wraps

client = None
logger = logging.getLogger(__name__)

def async_to_sync(async_func):
    """Utility decorator to convert async functions to sync with proper event loop handling."""
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a task and run it synchronously
                result = None
                exception = None
                def run_in_thread():
                    nonlocal result, exception
                    try:
                        result = asyncio.run(async_func(*args, **kwargs))
                    except Exception as e:
                        exception = e
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()
                if exception:
                    raise exception
                return result
            else:
                return loop.run_until_complete(async_func(*args, **kwargs))
        except RuntimeError:
            return asyncio.run(async_func(*args, **kwargs))
    return wrapper

async def make_api_request(method: str, endpoint: str, params: dict = None, json_body: dict = None):
    """Utility function to make API requests with consistent parameter handling."""
    return await client.make_request(method, endpoint, params=params or {}, json=json_body)

def build_params(**kwargs):
    """Build parameters dictionary excluding None values."""
    return {k: v for k, v in kwargs.items() if v is not None}

@log_tool_execution
async def manage_reports_endpoints(
    operation_type: Literal["search_storage_capacity", "search_storage_savings", "search_virtualization_summary"],
    body: Optional[Dict[str, Any]] = None,
    vdbId: Optional[str] = None,
    snapshotId: Optional[str] = None,
    sourceId: Optional[str] = None,
    dsourceId: Optional[str] = None,
    environmentId: Optional[str] = None,
    jobId: Optional[str] = None
) -> Dict[str, Any]:
    """Manage reports_endpoints operations.

    Supported operations:
    - search_storage_capacity: Search engine storage capacity data.
    - search_storage_savings: Search the saving storage summary report for virtualization engines.
    - search_virtualization_summary: Search the storage summary report for virtualization engines.
    """
    operation_map = {
        "search_storage_capacity": ("/reporting/storage-capacity-data-report/search", "POST"),
        "search_storage_savings": ("/reporting/storage-savings-report/search", "POST"),
        "search_virtualization_summary": ("/reporting/virtualization-storage-summary-report/search", "POST"),
    }

    # operation_type is already a string (Literal type)
    result = operation_map.get(operation_type)
    if not result:
        raise ValueError(f"Unknown operation: {operation_type}")
    endpoint, method = result
    
    # Substitute path parameters
    path_params = {
        "vdbId": vdbId,
        "snapshotId": snapshotId,
        "sourceId": sourceId,
        "dsourceId": dsourceId,
        "environmentId": environmentId,
        "jobId": jobId,
    }
    for key, value in path_params.items():
        if value is not None:
            endpoint = endpoint.replace(f"{{{key}}}", value)
    
    # Prepare request body - use empty dict for search if not provided
    json_body = body if body is not None else {}
    
    return await make_api_request(method, endpoint, params={}, json_body=json_body)

def register_tools(app, dct_client):
    global client
    client = dct_client
    logger.info(f"Registering consolidated tool: manage_reports_endpoints")
    try:
        app.add_tool(manage_reports_endpoints, name="manage_reports_endpoints")
    except Exception as e:
        logger.error(f"Error registering manage_reports_endpoints: {e}")
    logger.info(f"Tool registration finished for reports_endpoints.")
