from enum import Enum

class Engine_EndpointsOperation(Enum):
    """Available operations for engine_endpoints."""
    /MANAGEMENT/ENGINES/SEARCH = "/management/engines/search"
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
async def manage_engine_endpoints(operation_type: Engine_EndpointsOperation) -> Dict[str, Any]:
    """Manage engine_endpoints operations.

    Supported operations:
    - /management/engines/search: Search for engines.
    """
    operation_map = {
        "/management/engines/search": ("/management/engines/search", "POST"),
    }

    endpoint, method = operation_map.get(operation_type.value)
    if not endpoint:
        raise ValueError(f"Unknown operation: {operation_type.value}")
    return make_api_request(method, endpoint, params={})

def register_tools(app, dct_client):
    global client
    client = dct_client
    logger.info(f"Registering consolidated tool: manage_engine_endpoints")
    try:
        app.add_tool(manage_engine_endpoints, name="manage_engine_endpoints")
    except Exception as e:
        logger.error(f"Error registering manage_engine_endpoints: {e}")
    logger.info(f"Tool registration finished for engine_endpoints.")
