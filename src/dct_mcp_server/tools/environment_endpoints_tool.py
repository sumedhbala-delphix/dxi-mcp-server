from enum import Enum
from typing import Literal

class Environment_EndpointsOperation(Enum):
    """Available operations for environment_endpoints."""
    CREATE = "create"
    CREATE_HOST = "create_host"
    CREATE_LISTENER = "create_listener"
    CREATE_REPOSITORY = "create_repository"
    CREATE_USER = "create_user"
    DELETE = "delete"
    DELETE_HOST = "delete_host"
    DELETE_LISTENER = "delete_listener"
    DELETE_REPOSITORY = "delete_repository"
    DELETE_USER = "delete_user"
    DISABLE = "disable"
    ENABLE = "enable"
    GET = "get"
    REFRESH = "refresh"
    SEARCH = "search"
    UPDATE = "update"
    UPDATE_HOST = "update_host"
    UPDATE_LISTENER = "update_listener"
    UPDATE_REPOSITORY = "update_repository"
    UPDATE_USER = "update_user"
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
async def manage_environment_endpoints(
    operation_type: Literal["create", "create_host", "create_listener", "create_repository", "create_user", "delete", "delete_host", "delete_listener", "delete_repository", "delete_user", "disable", "enable", "get", "refresh", "search", "update", "update_host", "update_listener", "update_repository", "update_user"],
    body: Optional[Dict[str, Any]] = None,
    vdbId: Optional[str] = None,
    snapshotId: Optional[str] = None,
    sourceId: Optional[str] = None,
    dsourceId: Optional[str] = None,
    environmentId: Optional[str] = None,
    jobId: Optional[str] = None
) -> Dict[str, Any]:
    """Manage environment_endpoints operations.

    Supported operations:
    - create: Create an environment.
    - create_host: Create a new Host.
    - create_listener: Create Oracle listener.
    - create_repository: Create a repository.
    - create_user: Create environment user.
    - delete: Returns an environment by ID.
    - delete_host
    - delete_listener
    - delete_repository
    - delete_user
    - disable: Disable environment.
    - enable: Enable a disabled environment.
    - get: Returns an environment by ID.
    - refresh: Refresh environment.
    - search: Search for environments.
    - update: Returns an environment by ID.
    - update_host
    - update_listener
    - update_repository
    - update_user
    """
    operation_map = {
        "create": ("/environments", "POST"),
        "create_host": ("/environments/{environmentId}/hosts", "POST"),
        "create_listener": ("/environments/{environmentId}/listeners", "POST"),
        "create_repository": ("/environments/{environmentId}/repository", "POST"),
        "create_user": ("/environments/{environmentId}/users", "POST"),
        "delete": ("/environments/{environmentId}", "GET"),
        "delete_host": ("/environments/{environmentId}/hosts/{hostId}", "GET"),
        "delete_listener": ("/environments/{environmentId}/listeners/{listenerId}", "GET"),
        "delete_repository": ("/environments/{environmentId}/repository/{repositoryId}", "GET"),
        "delete_user": ("/environments/{environmentId}/users/{userRef}", "GET"),
        "disable": ("/environments/{environmentId}/disable", "POST"),
        "enable": ("/environments/{environmentId}/enable", "POST"),
        "get": ("/environments/{environmentId}", "GET"),
        "refresh": ("/environments/{environmentId}/refresh", "POST"),
        "search": ("/environments/search", "POST"),
        "update": ("/environments/{environmentId}", "GET"),
        "update_host": ("/environments/{environmentId}/hosts/{hostId}", "GET"),
        "update_listener": ("/environments/{environmentId}/listeners/{listenerId}", "GET"),
        "update_repository": ("/environments/{environmentId}/repository/{repositoryId}", "GET"),
        "update_user": ("/environments/{environmentId}/users/{userRef}", "GET"),
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
    
    return make_api_request(method, endpoint, params={}, json_body=json_body)

def register_tools(app, dct_client):
    global client
    client = dct_client
    logger.info(f"Registering consolidated tool: manage_environment_endpoints")
    try:
        app.add_tool(manage_environment_endpoints, name="manage_environment_endpoints")
    except Exception as e:
        logger.error(f"Error registering manage_environment_endpoints: {e}")
    logger.info(f"Tool registration finished for environment_endpoints.")
