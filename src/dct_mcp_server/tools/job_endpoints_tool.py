from enum import Enum
from typing import Literal

class Job_EndpointsOperation(Enum):
    """Available operations for job_endpoints."""
    ABANDON = "abandon"
    GET_RESULT = "get_result"
    SEARCH = "search"
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
async def manage_job_endpoints(
    operation_type: Job_EndpointsOperation,
    body: Optional[Dict[str, Any]] = None,
    vdbId: Optional[str] = None,
    snapshotId: Optional[str] = None,
    sourceId: Optional[str] = None,
    dsourceId: Optional[str] = None,
    environmentId: Optional[str] = None,
    jobId: Optional[str] = None
) -> Dict[str, Any]:
    """Manage job_endpoints operations.

    Supported operations:
    - abandon: Abandons a job.
    - get_result: Get job result.
    - search: Search for jobs.
    """
    operation_map = {
        "abandon": ("/jobs/{jobId}/abandon", "POST"),
        "get_result": ("/jobs/{jobId}/result", "GET"),
        "search": ("/jobs/search", "POST"),
    }

    # Handle both Enum and string input for operation_type
    op_value = operation_type.value if hasattr(operation_type, "value") else operation_type
    result = operation_map.get(op_value)
    if not result:
        raise ValueError(f"Unknown operation: {op_value}")
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
    
    return make_api_request(method, endpoint, params={}, json_body=json_body)

def register_tools(app, dct_client):
    global client
    client = dct_client
    logger.info(f"Registering consolidated tool: manage_job_endpoints")
    try:
        app.add_tool(manage_job_endpoints, name="manage_job_endpoints")
    except Exception as e:
        logger.error(f"Error registering manage_job_endpoints: {e}")
    logger.info(f"Tool registration finished for job_endpoints.")
