#!/usr/bin/env python3

"""
Driver code for the MCP server tool generation from Delphix DCT OpenAPI specification.

This script downloads the OpenAPI YAML specification from the DCT server,
parses it, and generates tool files for each API category defined in the
toolsgenerator/endpoints directory. Each tool file contains functions
corresponding to the API endpoints specified in the OpenAPI spec.

Generated tool files are saved in the dct_mcp_server/tools directory.
Each generated function includes:
- Function signature with parameters and types.
- Docstrings with parameter descriptions.
- Implementation using utility functions for making API requests.
"""


from textwrap import indent

import yaml
import os
import requests
import urllib3
import logging
from dct_mcp_server.config.config import get_dct_config

# Get the absolute path of the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

TOOL_DIR = os.path.join(project_root, "src/dct_mcp_server/toolsgenerator/endpoints")
TOOLS_DIR = os.path.join(project_root, "src/dct_mcp_server/tools/")
APIS_TO_SUPPORT = {}
indent = 4

logger = logging.getLogger(__name__)

def load_api_endpoints():
    """Loads API endpoints from files in TOOL_DIR into APIS_TO_SUPPORT dict.
    
    Supports two formats:
    1. Simple: /path/to/endpoint (generates one function per endpoint)
    2. Consolidated: operation_name|/path/to/endpoint (groups operations into single function)
    """
    global APIS_TO_SUPPORT
    APIS_TO_SUPPORT = {}  # Reset the dictionary before loading
    os.makedirs(TOOL_DIR, exist_ok=True)
    for file in os.listdir(TOOL_DIR):
        # Store the files as values of the dict with key as filename without _endpoints.txt
        if file.endswith("_endpoints.txt"):
            file_name = file.split(".")[0]
            APIS_TO_SUPPORT[file_name] = {}  # Change to dict to support grouping
            with open(os.path.join(TOOL_DIR, file), "r") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith("#"):
                        # Check if this is consolidated format (operation|endpoint)
                        if "|" in stripped_line:
                            operation_name, endpoint = stripped_line.split("|", 1)
                            if operation_name not in APIS_TO_SUPPORT[file_name]:
                                APIS_TO_SUPPORT[file_name][operation_name] = []
                            APIS_TO_SUPPORT[file_name][operation_name].append(endpoint)
                        else:
                            # Legacy format - treat endpoint as operation name
                            if stripped_line not in APIS_TO_SUPPORT[file_name]:
                                APIS_TO_SUPPORT[file_name][stripped_line] = []
                            APIS_TO_SUPPORT[file_name][stripped_line].append(stripped_line)


def download_open_api_yaml(api_url: str, save_path: str):
    """Downloads the OpenAPI YAML from the given URL."""
    try:
        logger.info(f"Downloading OpenAPI spec from {api_url}...")
        
        # Get SSL verification setting from config
        dct_config = get_dct_config()
        verify_ssl = dct_config.get("verify_ssl", False)

        # Use the configured SSL verification
        response = requests.get(api_url, timeout=30, verify=verify_ssl)
        response.raise_for_status()  # Raise an exception for bad status codes
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        logger.info(f"Successfully saved OpenAPI spec to {save_path}")
    except requests.exceptions.RequestException as e:
        logger.info(f"Error downloading OpenAPI spec: {e}")
        raise

translated_dict_for_types = {
    "integer": "int",
    "string": "str",
    "boolean": "bool",
    "float": "float",
}

prefix = """from mcp.server.fastmcp import FastMCP
from typing import Dict,Any,Optional
from ..core.decorators import log_tool_execution
import asyncio
import logging
import threading
from functools import wraps

client = None
logger = logging.getLogger(__name__)

def async_to_sync(async_func):
    \"\"\"Utility decorator to convert async functions to sync with proper event loop handling.\"\"\"
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
    \"\"\"Utility function to make API requests with consistent parameter handling.\"\"\"
    return await client.make_request(method, endpoint, params=params or {}, json=json_body)

def build_params(**kwargs):
    \"\"\"Build parameters dictionary excluding None values.\"\"\"
    return {k: v for k, v in kwargs.items() if v is not None}

"""

def create_register_tool_function(tool_name, apis):
    func_str = "\n"
    func_str += "def register_tools(app, dct_client):\n"
    func_str += " "*indent + "global client\n"
    func_str += " "*indent + "client = dct_client\n"
    func_str += " "*indent + f"logger.info(f'Registering tools for {tool_name}...')\n"
    func_str += " "*indent + "try:\n"
    for function in apis:
        func_str += " "*indent*2 + f"logger.info(f'  Registering tool function: {function}')\n"
        func_str += " "*indent*2 + f"app.add_tool({function}, name=\"{function}\")\n"
    func_str += " "*indent + "except Exception as e:\n"
    func_str += " "*indent*2 + f"logger.error(f'Error registering tools for {tool_name}: {{e}}')\n"
    func_str += " "*indent + f"logger.info(f'Tools registration finished for {tool_name}.')\n"
    return func_str

def read_open_api_yaml(api_file):
    yaml_body = ""
    with open(api_file, "r") as f:
        yaml_body = yaml.safe_load(f)
    return yaml_body


def resolve_ref(ref: str, root: dict):
    """
    Resolve a JSON pointer $ref like '#/components/schemas/DSource'
    inside a loaded OpenAPI YAML dict.
    """
    if not ref.startswith('#/'):
        raise ValueError(f"Unsupported ref format: {ref}")

    # Remove starting '#/' and split by "/"
    path = ref.lstrip('#/').split('/')

    node = root
    for part in path:
        node = node[part]
    return node

def generate_tools_from_openapi():
    """Generates consolidated tool files from OpenAPI spec.
    
    Creates one function per tool that handles multiple operations via an operation_type enum.
    Supports consolidated format: operation_name|/path/to/endpoint
    
    """
    load_api_endpoints()

    # Try to download the latest OpenAPI spec
    client_address = f"{os.getenv('DCT_BASE_URL')}/dct/static/api-external.yaml"
    API_FILE = os.path.join(project_root, "src", "api.yaml")
    
    try:
        download_open_api_yaml(client_address, API_FILE)
        logger.info(f"DCT_BASE_URL found: {client_address}")
    except Exception as e:
        logger.error(f"No OpenAPI spec available - cannot generate tools: {e}")
        raise

    api_spec = read_open_api_yaml(API_FILE)
    logger.info(f"APIS to support loaded: {len(APIS_TO_SUPPORT)} tool categories")
    
    os.makedirs(TOOLS_DIR, exist_ok=True)

    for tool_name, operations_dict in APIS_TO_SUPPORT.items():
        TOOL_FILE = os.path.join(TOOLS_DIR, f"{tool_name}_tool.py")
        
        # Build operation mapping: operation_name -> list of endpoints
        if not isinstance(operations_dict, dict):
            logger.warning(f"Skipping {tool_name}: not in consolidated format")
            continue
        
        # Generate enum class for operations
        tool_class = "_".join([word.capitalize() for word in tool_name.split("_")])
        enum_class_name = f"{tool_class}Operation"
        
        # Build list of operation names for Literal type
        op_names = sorted(operations_dict.keys())
        op_literals = ", ".join([f'"{op}"' for op in op_names])
        
        enum_code = f"from enum import Enum\nfrom typing import Literal\n\nclass {enum_class_name}(Enum):\n"
        enum_code += f'    """Available operations for {tool_name}."""\n'
        
        for op_name in op_names:
            enum_value = op_name.upper()
            enum_code += f'    {enum_value} = "{op_name}"\n'
        
        # Build tool file content
        tool_file_content = prefix
        tool_file_content = tool_file_content.replace("from enum import Enum", "")
        tool_file_content = tool_file_content.replace("from typing import Literal", "")
        tool_file_content = enum_code + tool_file_content
        
        # Generate consolidated function signature with Literal type for MCP compatibility
        # FastMCP can't serialize custom Enum classes, so we use Literal with string values
        func_name = f"dct_manage_{tool_name}"
        function_head = f"@log_tool_execution\nasync def {func_name}(\n"
        function_head += f"    operation_type: Literal[{op_literals}],\n"
        function_head += f"    body: Optional[Dict[str, Any]] = None,\n"
        function_head += f"    vdbId: Optional[str] = None,\n"
        function_head += f"    snapshotId: Optional[str] = None,\n"
        function_head += f"    sourceId: Optional[str] = None,\n"
        function_head += f"    dsourceId: Optional[str] = None,\n"
        function_head += f"    environmentId: Optional[str] = None,\n"
        function_head += f"    jobId: Optional[str] = None,\n"
        function_head += f"    limit: Optional[int] = None,\n"
        function_head += f"    cursor: Optional[str] = None,\n"
        function_head += f"    sort: Optional[str] = None,\n"
        function_head += f"    filter_expression: Optional[str] = None,\n"
        function_head += f"    confirm: bool = False\n"
        function_head += f") -> Dict[str, Any]:\n"
        
        # Build docstring with all supported operations
        resource_hints = {
            "engine_endpoints": "engines (DCT engines/servers, inventory, status)",
            "vdbs_endpoints": "VDBs (virtual databases, provisioning, refresh, snapshot, start/stop)",
            "snapshots_endpoints": "snapshots (list, create, delete)",
            "sources_endpoints": "sources (dSources and source databases)",
            "dsources_endpoints": "dSources (source databases)",
            "environment_endpoints": "environments (hosts/targets)",
            "dataset_endpoints": "datasets",
            "job_endpoints": "jobs (async tasks and results)",
            "reports_endpoints": "reports",
            "compliance_endpoints": "compliance (masking connectors/executions)",
        }
        resource_hint = resource_hints.get(
            tool_name,
            tool_name.replace("_endpoints", "").replace("_", " ")
        )
        docstring = f'    """Manage {tool_name} operations.\n\n'
        docstring += f'    Resource: {resource_hint}.\n'
        docstring += f'    Use this tool only for {resource_hint} operations.\n\n'
        docstring += '    Supported operations:\n'
        for op_name in sorted(operations_dict.keys()):
            # Get first endpoint for this operation to look up its description
            endpoints = operations_dict[op_name]
            if endpoints:
                api = endpoints[0]
                path_item = api_spec.get("paths", {}).get(api, {})
                operation = path_item.get("post", path_item.get("get"))
                if operation:
                    summary = operation.get("summary", op_name)
                    docstring += f'    - {op_name}: {summary}\n'
                else:
                    docstring += f'    - {op_name}\n'
        docstring += '    """\n'
        
        # Build operation routing logic
        routing_logic = '    operation_map = {\n'
        for op_name, endpoints in sorted(operations_dict.items()):
            if not endpoints:
                continue
            
            # For consolidated tools with single endpoint per operation
            api = endpoints[0]
            path_item = api_spec.get("paths", {}).get(api, {})
            http_method = "POST" if "post" in path_item else "GET"
            
            routing_logic += f'        "{op_name}": ("{api}", "{http_method}"),\n'
        
        routing_logic += '    }\n\n'
        routing_logic += '    # operation_type is already a string (Literal type)\n'
        routing_logic += '    result = operation_map.get(operation_type)\n'
        routing_logic += '    if not result:\n'
        routing_logic += f'        raise ValueError(f"Unknown operation: {{operation_type}}")\n'
        routing_logic += '    endpoint, method = result\n'
        routing_logic += '    \n'
        routing_logic += '    # Substitute path parameters\n'
        routing_logic += '    path_params = {\n'
        routing_logic += '        "vdbId": vdbId,\n'
        routing_logic += '        "snapshotId": snapshotId,\n'
        routing_logic += '        "sourceId": sourceId,\n'
        routing_logic += '        "dsourceId": dsourceId,\n'
        routing_logic += '        "environmentId": environmentId,\n'
        routing_logic += '        "jobId": jobId,\n'
        routing_logic += '    }\n'
        routing_logic += '    for key, value in path_params.items():\n'
        routing_logic += '        if value is not None:\n'
        routing_logic += '            endpoint = endpoint.replace(f"{{{key}}}", value)\n'
        routing_logic += '    \n'
        routing_logic += '    is_search = operation_type.startswith("search")\n'
        routing_logic += '    params = build_params(limit=limit, cursor=cursor, sort=sort) if is_search else {}\n'
        routing_logic += '    \n'
        routing_logic += '    # Prepare request body - include filter_expression for search operations\n'
        routing_logic += '    json_body = body if body is not None else {}\n'
        routing_logic += '    if is_search and filter_expression is not None:\n'
        routing_logic += '        json_body = {**json_body, "filter_expression": filter_expression}\n'
        routing_logic += '    \n'
        routing_logic += '    # Check if confirmation is required for destructive operations\n'
        routing_logic += '    is_destructive = method in ["POST", "PUT", "DELETE"] and not is_search and operation_type != "get" and operation_type != "get_result"\n'
        routing_logic += '    if is_destructive and not confirm:\n'
        routing_logic += '        return {\n'
        routing_logic += '            "requires_confirmation": True,\n'
        routing_logic += '            "operation": operation_type,\n'
        routing_logic += '            "method": method,\n'
        routing_logic += '            "endpoint": endpoint,\n'
        routing_logic += '            "parameters": {k: v for k, v in {"vdbId": vdbId, "snapshotId": snapshotId, "sourceId": sourceId, "dsourceId": dsourceId, "environmentId": environmentId, "jobId": jobId, "body": body}.items() if v is not None},\n'
        routing_logic += '            "message": f"This operation \'{operation_type}\' is destructive and requires confirmation. Please review the parameters and call again with confirm=True to proceed."\n'
        routing_logic += '        }\n'
        routing_logic += '    \n'
        routing_logic += '    return await make_api_request(method, endpoint, params=params, json_body=json_body)\n'
        
        tool_file_content += function_head + docstring + routing_logic
        
        # Register the consolidated function
        tool_file_content += f"\ndef register_tools(app, dct_client):\n"
        tool_file_content += f'    global client\n'
        tool_file_content += f'    client = dct_client\n'
        tool_file_content += f'    logger.info(f"Registering DCT tool: {func_name}")\n'
        tool_file_content += f'    try:\n'
        tool_file_content += f'        app.add_tool({func_name}, name="{func_name}")\n'
        tool_file_content += f'    except Exception as e:\n'
        tool_file_content += f'        logger.error(f"Error registering {func_name}: {{e}}")\n'
        tool_file_content += f'    logger.info(f"Tool registration finished for {tool_name}.")'  
        
        with open(TOOL_FILE, "w") as f:
            f.write(tool_file_content)
        
        logger.info(f"Generated consolidated tool: {func_name} with {len(operations_dict)} operations")

    # Delete the api.yaml file after generating all tools
    if os.path.exists(API_FILE):
        os.remove(API_FILE)
    
    logger.info(f"Tool generation complete: {len(APIS_TO_SUPPORT)} consolidated tools created")

if __name__ == "__main__":
    generate_tools_from_openapi()
