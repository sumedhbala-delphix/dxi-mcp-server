from enum import Enum
from typing import Literal

class Vdbs_EndpointsOperation(Enum):
    """Available operations for vdbs_endpoints."""
    DELETE = "delete"
    DISABLE = "disable"
    ENABLE = "enable"
    GET = "get"
    PROVISION_BOOKMARK = "provision_bookmark"
    PROVISION_EMPTY = "provision_empty"
    PROVISION_LOCATION = "provision_location"
    PROVISION_SNAPSHOT = "provision_snapshot"
    PROVISION_TIMESTAMP = "provision_timestamp"
    REFRESH_BOOKMARK = "refresh_bookmark"
    REFRESH_LOCATION = "refresh_location"
    REFRESH_SNAPSHOT = "refresh_snapshot"
    REFRESH_TIMESTAMP = "refresh_timestamp"
    ROLLBACK_BOOKMARK = "rollback_bookmark"
    ROLLBACK_SNAPSHOT = "rollback_snapshot"
    ROLLBACK_TIMESTAMP = "rollback_timestamp"
    SEARCH = "search"
    SNAPSHOT = "snapshot"
    START = "start"
    STOP = "stop"
    UPGRADE = "upgrade"
from mcp.server.fastmcp import FastMCP
from typing import Dict,Any,Optional
from ..core.decorators import log_tool_execution
from ..config.config import get_dct_config
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
async def manage_vdbs_endpoints(
    operation_type: Literal["delete", "disable", "enable", "get", "provision_bookmark", "provision_empty", "provision_location", "provision_snapshot", "provision_timestamp", "refresh_bookmark", "refresh_location", "refresh_snapshot", "refresh_timestamp", "rollback_bookmark", "rollback_snapshot", "rollback_timestamp", "search", "snapshot", "start", "stop", "upgrade"],
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
    """Manage vdbs_endpoints operations.

    Resource: VDBs (virtual databases, provisioning, refresh, snapshot, start/stop).
    Use this tool only for VDBs (virtual databases, provisioning, refresh, snapshot, start/stop) operations.

    Supported operations:
    - delete: Delete a VDB.
    - disable: Disable a VDB.
    - enable: Enable a VDB.
    - get: Get a VDB by ID.
    - provision_bookmark: Provision a new VDB from a bookmark with a single VDB.
    - provision_empty: Provision an empty VDB.
    - provision_location: Provision a new VDB by location.
    - provision_snapshot: Provision a new VDB by snapshot.
    - provision_timestamp: Provision a new VDB by timestamp.
    - refresh_bookmark: Refresh a VDB from bookmark with a single VDB.
    - refresh_location: Refresh a VDB by location.
    - refresh_snapshot: Refresh a VDB by snapshot.
    - refresh_timestamp: Refresh a VDB by timestamp.
    - rollback_bookmark: Rollback a VDB from a bookmark with only the same VDB.
    - rollback_snapshot: Rollback a VDB by snapshot.
    - rollback_timestamp: Rollback a VDB by timestamp.
    - search: Search for VDBs.
    - snapshot: Snapshot a VDB.
    - start: Start a VDB.
    - stop: Stop a VDB.
    - upgrade: Upgrade VDB

    Filter Expression Syntax (for search operations):
    DCT uses keyword operators, NOT symbols. Examples:
    - "name CONTAINS 'prod'" - partial match
    - "database_name EQ 'mydb'" - exact match
    - "status EQ 'RUNNING'" - filter by status
    - "name CONTAINS 'test' AND status EQ 'RUNNING'" - combine with AND/OR
    Available operators: EQ, NE, CONTAINS, NOT_CONTAINS, LT, LE, GT, GE, IN, NOT_IN
    """
    operation_map = {
        "delete": ("/vdbs/{vdbId}/delete", "POST"),
        "disable": ("/vdbs/{vdbId}/disable", "POST"),
        "enable": ("/vdbs/{vdbId}/enable", "POST"),
        "get": ("/vdbs/{vdbId}", "GET"),
        "provision_bookmark": ("/vdbs/provision_from_bookmark", "POST"),
        "provision_empty": ("/vdbs/empty_vdb", "POST"),
        "provision_location": ("/vdbs/provision_by_location", "POST"),
        "provision_snapshot": ("/vdbs/provision_by_snapshot", "POST"),
        "provision_timestamp": ("/vdbs/provision_by_timestamp", "POST"),
        "refresh_bookmark": ("/vdbs/{vdbId}/refresh_from_bookmark", "POST"),
        "refresh_location": ("/vdbs/{vdbId}/refresh_by_location", "POST"),
        "refresh_snapshot": ("/vdbs/{vdbId}/refresh_by_snapshot", "POST"),
        "refresh_timestamp": ("/vdbs/{vdbId}/refresh_by_timestamp", "POST"),
        "rollback_bookmark": ("/vdbs/{vdbId}/rollback_from_bookmark", "POST"),
        "rollback_snapshot": ("/vdbs/{vdbId}/rollback_by_snapshot", "POST"),
        "rollback_timestamp": ("/vdbs/{vdbId}/rollback_by_timestamp", "POST"),
        "search": ("/vdbs/search", "POST"),
        "snapshot": ("/vdbs/{vdbId}/snapshots", "POST"),
        "start": ("/vdbs/{vdbId}/start", "POST"),
        "stop": ("/vdbs/{vdbId}/stop", "POST"),
        "upgrade": ("/vdbs/{vdbId}/upgrade", "POST"),
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
    is_destructive = method in ["POST", "PUT", "DELETE"] and not is_search and operation_type != "get"
    if is_destructive and dct_config["require_confirmation"] and not confirm:
        return {
            "requires_confirmation": True,
            "operation": operation_type,
            "method": method,
            "endpoint": endpoint,
            "parameters": {
                "vdbId": vdbId,
                "snapshotId": snapshotId,
                "sourceId": sourceId,
                "dsourceId": dsourceId,
                "environmentId": environmentId,
                "jobId": jobId,
                "body": body
            },
            "message": f"This operation '{operation_type}' is destructive and requires confirmation. Please review the parameters and call again with confirm=True to proceed."
        }
    
    return await make_api_request(method, endpoint, params=params, json_body=json_body)

def register_tools(app, dct_client):
    global client
    client = dct_client
    logger.info(f"Registering DCT tool: dct_manage_vdbs_endpoints")
    try:
        app.add_tool(manage_vdbs_endpoints, name="dct_manage_vdbs_endpoints")
    except Exception as e:
        logger.error(f"Error registering dct_manage_vdbs_endpoints: {e}")
    logger.info(f"Tool registration finished for vdbs_endpoints.")
