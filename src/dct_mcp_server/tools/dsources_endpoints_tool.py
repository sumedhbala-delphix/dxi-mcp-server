from enum import Enum
from typing import Literal

class Dsources_EndpointsOperation(Enum):
    """Available operations for dsources_endpoints."""
    ATTACH_MSSQL = "attach_mssql"
    ATTACH_MSSQL_STAGING = "attach_mssql_staging"
    ATTACH_ORACLE = "attach_oracle"
    DELETE = "delete"
    DETACH_MSSQL = "detach_mssql"
    DETACH_ORACLE = "detach_oracle"
    DISABLE = "disable"
    ENABLE = "enable"
    LINK_APPDATA = "link_appdata"
    LINK_ASE = "link_ase"
    LINK_MSSQL = "link_mssql"
    LINK_MSSQL_STAGING = "link_mssql_staging"
    LINK_ORACLE = "link_oracle"
    LINK_ORACLE_STAGING = "link_oracle_staging"
    SEARCH = "search"
    SNAPSHOT = "snapshot"
    UPDATE_APPDATA = "update_appdata"
    UPDATE_ASE = "update_ase"
    UPDATE_MSSQL = "update_mssql"
    UPDATE_ORACLE = "update_oracle"
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
async def manage_dsources_endpoints(
    operation_type: Literal["attach_mssql", "attach_mssql_staging", "attach_oracle", "delete", "detach_mssql", "detach_oracle", "disable", "enable", "link_appdata", "link_ase", "link_mssql", "link_mssql_staging", "link_oracle", "link_oracle_staging", "search", "snapshot", "update_appdata", "update_ase", "update_mssql", "update_oracle"],
    body: Optional[Dict[str, Any]] = None,
    vdbId: Optional[str] = None,
    snapshotId: Optional[str] = None,
    sourceId: Optional[str] = None,
    dsourceId: Optional[str] = None,
    environmentId: Optional[str] = None,
    jobId: Optional[str] = None
) -> Dict[str, Any]:
    """Manage dsources_endpoints operations.

    Supported operations:
    - attach_mssql: Attaches a MSSql source to a previously detached dsource.
    - attach_mssql_staging: Attaches a MSSql staging push database to a previously detached dsource.
    - attach_oracle: Attach an Oracle dSource to an Oracle database.
    - delete: Delete the specified dSource.
    - detach_mssql: Detaches a linked source from a MSSql database.
    - detach_oracle: Detaches an Oracle source from an Oracle database.
    - disable: Disable a dSource.
    - enable: Enable a dSource.
    - link_appdata: Link an AppData database as dSource.
    - link_ase: Link an ASE database as dSource.
    - link_mssql: Link a MSSql database as dSource.
    - link_mssql_staging: Link a MSSql staging push database as dSource.
    - link_oracle: Link Oracle database as dSource.
    - link_oracle_staging: Link an Oracle staging push database as dSource.
    - search: Search for dSources.
    - snapshot: Snapshot a dSource.
    - update_appdata
    - update_ase
    - update_mssql
    - update_oracle
    """
    operation_map = {
        "attach_mssql": ("/dsources/mssql/{dsourceId}/attachSource", "POST"),
        "attach_mssql_staging": ("/dsources/mssql/staging-push/{dsourceId}/attachSource", "POST"),
        "attach_oracle": ("/dsources/oracle/{dsourceId}/attachSource", "POST"),
        "delete": ("/dsources/delete", "POST"),
        "detach_mssql": ("/dsources/mssql/{dsourceId}/detachSource", "POST"),
        "detach_oracle": ("/dsources/oracle/{dsourceId}/detachSource", "POST"),
        "disable": ("/dsources/{dsourceId}/disable", "POST"),
        "enable": ("/dsources/{dsourceId}/enable", "POST"),
        "link_appdata": ("/dsources/appdata", "POST"),
        "link_ase": ("/dsources/ase", "POST"),
        "link_mssql": ("/dsources/mssql", "POST"),
        "link_mssql_staging": ("/dsources/mssql/staging-push", "POST"),
        "link_oracle": ("/dsources/oracle", "POST"),
        "link_oracle_staging": ("/dsources/oracle/staging-push", "POST"),
        "search": ("/dsources/search", "POST"),
        "snapshot": ("/dsources/{dsourceId}/snapshots", "POST"),
        "update_appdata": ("/dsources/appdata/{dsourceId}", "GET"),
        "update_ase": ("/dsources/ase/{dsourceId}", "GET"),
        "update_mssql": ("/dsources/mssql/{dsourceId}", "GET"),
        "update_oracle": ("/dsources/oracle/{dsourceId}", "GET"),
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
    logger.info(f"Registering consolidated tool: manage_dsources_endpoints")
    try:
        app.add_tool(manage_dsources_endpoints, name="manage_dsources_endpoints")
    except Exception as e:
        logger.error(f"Error registering manage_dsources_endpoints: {e}")
    logger.info(f"Tool registration finished for dsources_endpoints.")
