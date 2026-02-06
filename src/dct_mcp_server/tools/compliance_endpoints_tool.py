from enum import Enum
from typing import Literal

class Compliance_EndpointsOperation(Enum):
    """Available operations for compliance_endpoints."""
    SEARCH_CONNECTORS = "search_connectors"
    SEARCH_EXECUTIONS = "search_executions"
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
async def manage_compliance_endpoints(
    operation_type: Literal["search_connectors", "search_executions"],
    body: Optional[Dict[str, Any]] = None,
    vdbId: Optional[str] = None,
    snapshotId: Optional[str] = None,
    sourceId: Optional[str] = None,
    dsourceId: Optional[str] = None,
    environmentId: Optional[str] = None,
    jobId: Optional[str] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
    sort: Optional[str] = None,
    filter_expression: Optional[str] = None,
    confirm: bool = False
) -> Dict[str, Any]:
    """Manage compliance_endpoints operations.

    Resource: compliance (masking connectors/executions).
    Use this tool only for compliance (masking connectors/executions) operations.

    Supported operations:
    - search_connectors: Search for masking Connectors.
    - search_executions: Search masking executions.
    """
    operation_map = {
        "search_connectors": ("/connectors/search", "POST"),
        "search_executions": ("/executions/search", "POST"),
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
    
    is_search = operation_type.startswith("search")
    params = build_params(limit=limit, cursor=cursor, sort=sort) if is_search else {}
    
    # Prepare request body - include filter_expression for search operations
    json_body = body if body is not None else {}
    if is_search and filter_expression is not None:
        json_body = {**json_body, "filter_expression": filter_expression}
    
    # Check if confirmation is required for destructive operations
    dct_config = get_dct_config()
    is_destructive = method in ["POST", "PUT", "DELETE"] and not is_search and operation_type != "get" and operation_type != "get_result"
    if is_destructive and dct_config["require_confirmation"] and not confirm:
        return {
            "requires_confirmation": True,
            "operation": operation_type,
            "method": method,
            "endpoint": endpoint,
            "parameters": {k: v for k, v in {"vdbId": vdbId, "snapshotId": snapshotId, "sourceId": sourceId, "dsourceId": dsourceId, "environmentId": environmentId, "jobId": jobId, "body": body}.items() if v is not None},
            "message": f"This operation '{operation_type}' is destructive and requires confirmation. Please review the parameters and call again with confirm=True to proceed."
        }
    
    return await make_api_request(method, endpoint, params=params, json_body=json_body)

def register_tools(app, dct_client):
    global client
    client = dct_client
    logger.info(f"Registering DCT tool: dct_manage_compliance_endpoints")
    try:
        app.add_tool(manage_compliance_endpoints, name="dct_manage_compliance_endpoints")
    except Exception as e:
        logger.error(f"Error registering dct_manage_compliance_endpoints: {e}")
    logger.info(f"Tool registration finished for compliance_endpoints.")
