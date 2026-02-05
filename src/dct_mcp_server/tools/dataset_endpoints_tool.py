from enum import Enum

class Dataset_EndpointsOperation(Enum):
    """Available operations for dataset_endpoints."""
    SEARCH_BOOKMARKS = "search_bookmarks"
    SEARCH_DATA_CONNECTIONS = "search_data_connections"
    SEARCH_DSOURCES = "search_dsources"
    SEARCH_SNAPSHOTS = "search_snapshots"
    SEARCH_SOURCES = "search_sources"
    SEARCH_TIMEFLOWS = "search_timeflows"
    SEARCH_VDB_GROUPS = "search_vdb_groups"
    SEARCH_VDBS = "search_vdbs"
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

def make_api_request(method: str, endpoint: str, params: dict = None, json_body: dict = None):
    """Utility function to make API requests with consistent parameter handling."""
    @async_to_sync
    async def _make_request():
        return await client.make_request(method, endpoint, params=params or {}, json=json_body)
    return _make_request()

def build_params(**kwargs):
    """Build parameters dictionary excluding None values."""
    return {k: v for k, v in kwargs.items() if v is not None}

@log_tool_execution
async def manage_dataset_endpoints(operation_type: Dataset_EndpointsOperation) -> Dict[str, Any]:
    """Manage dataset_endpoints operations.

    Supported operations:
    - search_bookmarks: Search for bookmarks.
    - search_data_connections: Search for data connections.
    - search_dsources: Search for dSources.
    - search_snapshots: Search snapshots.
    - search_sources: Search for Sources.
    - search_timeflows: Search timeflows.
    - search_vdb_groups: Search for VDB Groups.
    - search_vdbs: Search for VDBs.
    """
    operation_map = {
        "search_bookmarks": ("/bookmarks/search", "POST"),
        "search_data_connections": ("/data-connections/search", "POST"),
        "search_dsources": ("/dsources/search", "POST"),
        "search_snapshots": ("/snapshots/search", "POST"),
        "search_sources": ("/sources/search", "POST"),
        "search_timeflows": ("/timeflows/search", "POST"),
        "search_vdb_groups": ("/vdb-groups/search", "POST"),
        "search_vdbs": ("/vdbs/search", "POST"),
    }

    endpoint, method = operation_map.get(operation_type.value)
    if not endpoint:
        raise ValueError(f"Unknown operation: {operation_type.value}")
    return make_api_request(method, endpoint, params={})

def register_tools(app, dct_client):
    global client
    client = dct_client
    logger.info(f"Registering consolidated tool: manage_dataset_endpoints")
    try:
        app.add_tool(manage_dataset_endpoints, name="manage_dataset_endpoints")
    except Exception as e:
        logger.error(f"Error registering manage_dataset_endpoints: {e}")
    logger.info(f"Tool registration finished for dataset_endpoints.")
