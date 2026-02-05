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
def search_sources(limit: Optional[int] = None, cursor: Optional[str] = None, sort: Optional[str] = None, filter_expression: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for Sources.
    :param limit: Maximum number of objects to return per query. The value must be between 1 and 1000. Default is 100.
    :param limit: Maximum number of objects to return per query. The value must be between 1 and 1000. Default is 100.(optional)
    :param cursor: Cursor to fetch the next or previous page of results. The value of this property must be extracted from the 'prev_cursor' or 'next_cursor' property of a PaginatedResponseMetadata which is contained in the response of list and search API endpoints.
    :param cursor: Cursor to fetch the next or previous page of results. The value of this property must be extracted from the 'prev_cursor' or 'next_cursor' property of a PaginatedResponseMetadata which is contained in the response of list and search API endpoints.(optional)
    :param sort: The field to sort results by. A property name with a prepended '-' signifies descending order.
    :param sort: The field to sort results by. A property name with a prepended '-' signifies descending order.(optional)
    :param filter_expression: Filter expression string (optional)
    Filter expression can include the following fields:
     - id: The Source object entity ID.
     - database_type: The type of this source database.
     - name: The name of this source database.
     - namespace_id: The namespace id of this source database.
     - namespace_name: The namespace name of this source database.
     - is_replica: Is this a replicated object.
     - database_version: The version of this source database.
     - environment_id: A reference to the Environment that hosts this source database.
     - environment_name: name of environment that hosts this source database.
     - data_uuid: A universal ID that uniquely identifies this source database.
     - ip_address: The IP address of the source's host.
     - fqdn: The FQDN of the source's host.
     - size: The total size of this source database, in bytes.
     - jdbc_connection_string: The JDBC connection URL for this source database.
     - plugin_version: The version of the plugin associated with this source database.
     - toolkit_id: The ID of the toolkit associated with this source database(AppData only).
     - is_dsource: No description
     - repository: The repository id for this source
     - recovery_model: Recovery model of the source database (MSSql Only).
     - mssql_source_type: The type of this mssql source database (MSSql Only).
     - appdata_source_type: The type of this appdata source database (Appdata Only).
     - is_pdb: If this source is of PDB type (Oracle Only).
     - tags: No description
     - instance_name: The instance name of this single instance database source.
     - instance_number: The instance number of this single instance database source.
     - instances: No description
     - oracle_services: No description
     - user: The username of the database user.
     - environment_user_ref: The environment user reference.
     - non_sys_user: The username of a database user that does not have administrative privileges.
     - discovered: Whether this source was discovered.
     - linking_enabled: Whether this source should be used for linking.
     - cdb_type: The cdb type for this source. (Oracle only)
     - data_connection_id: The ID of the associated DataConnection.
     - database_name: The name of this source database.
     - database_unique_name: The unique name of the database.

    How to use filter_expresssion: 
    A request body containing a filter expression. This enables searching
    for items matching arbitrarily complex conditions. The list of
    attributes which can be used in filter expressions is available
    in the x-filterable vendor extension.
    
    # Filter Expression Overview
    **Note: All keywords are case-insensitive**
    
    ## Comparison Operators
    | Operator | Description | Example |
    | --- | --- | --- |
    | CONTAINS | Substring or membership testing for string and list attributes respectively. | field3 CONTAINS 'foobar', field4 CONTAINS TRUE  |
    | IN | Tests if field is a member of a list literal. List can contain a maximum of 100 values | field2 IN ['Goku', 'Vegeta'] |
    | GE | Tests if a field is greater than or equal to a literal value | field1 GE 1.2e-2 |
    | GT | Tests if a field is greater than a literal value | field1 GT 1.2e-2 |
    | LE | Tests if a field is less than or equal to a literal value | field1 LE 9000 |
    | LT | Tests if a field is less than a literal value | field1 LT 9.02 |
    | NE | Tests if a field is not equal to a literal value | field1 NE 42 |
    | EQ | Tests if a field is equal to a literal value | field1 EQ 42 |
    
    ## Search Operator
    The SEARCH operator filters for items which have any filterable
    attribute that contains the input string as a substring, comparison
    is done case-insensitively. This is not restricted to attributes with
    string values. Specifically `SEARCH '12'` would match an item with an
    attribute with an integer value of `123`.
    
    ## Logical Operators
    Ordered by precedence.
    | Operator | Description | Example |
    | --- | --- | --- |
    | NOT | Logical NOT (Right associative) | NOT field1 LE 9000 |
    | AND | Logical AND (Left Associative) | field1 GT 9000 AND field2 EQ 'Goku' |
    | OR | Logical OR (Left Associative) | field1 GT 9000 OR field2 EQ 'Goku' |
    
    ## Grouping
    Parenthesis `()` can be used to override operator precedence.
    
    For example:
    NOT (field1 LT 1234 AND field2 CONTAINS 'foo')
    
    ## Literal Values
    | Literal      | Description | Examples |
    | --- | --- | --- |
    | Nil | Represents the absence of a value | nil, Nil, nIl, NIL |
    | Boolean | true/false boolean | true, false, True, False, TRUE, FALSE |
    | Number | Signed integer and floating point numbers. Also supports scientific notation. | 0, 1, -1, 1.2, 0.35, 1.2e-2, -1.2e+2 |
    | String | Single or double quoted | "foo", "bar", "foo bar", 'foo', 'bar', 'foo bar' |
    | Datetime | Formatted according to [RFC3339](https://datatracker.ietf.org/doc/html/rfc3339) | 2018-04-27T18:39:26.397237+00:00 |
    | List | Comma-separated literals wrapped in square brackets | [0], [0, 1], ['foo', "bar"] |
    
    ## Limitations
    - A maximum of 8 unique identifiers may be used inside a filter expression.
    
    """
    # Build parameters excluding None values
    params = build_params(limit=limit, cursor=cursor, sort=sort)
    search_body = {'filter_expression': filter_expression}
    return make_api_request('POST', '/sources/search', params=params, json_body=search_body)

@log_tool_execution
def create_oracle_source() -> Dict[str, Any]:
    """
    Create an Oracle Source.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/sources/oracle', params=params)

@log_tool_execution
def create_postgres_source() -> Dict[str, Any]:
    """
    Create a PostgreSQL source.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/sources/postgres', params=params)

@log_tool_execution
def create_ase_source() -> Dict[str, Any]:
    """
    Create an ASE source.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/sources/ase', params=params)

@log_tool_execution
def create_app_data_source() -> Dict[str, Any]:
    """
    Create an AppData source.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/sources/appdata', params=params)

@log_tool_execution
def get_source_by_id() -> Dict[str, Any]:
    """
    Get a source by ID.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('GET', '/sources/{sourceId}', params=params)


def register_tools(app, dct_client):
    global client
    client = dct_client
    logger.info(f'Registering tools for sources_endpoints...')
    try:
        logger.info(f'  Registering tool function: search_sources')
        app.add_tool(search_sources, name="search_sources")
        logger.info(f'  Registering tool function: create_oracle_source')
        app.add_tool(create_oracle_source, name="create_oracle_source")
        logger.info(f'  Registering tool function: create_postgres_source')
        app.add_tool(create_postgres_source, name="create_postgres_source")
        logger.info(f'  Registering tool function: create_ase_source')
        app.add_tool(create_ase_source, name="create_ase_source")
        logger.info(f'  Registering tool function: create_app_data_source')
        app.add_tool(create_app_data_source, name="create_app_data_source")
        logger.info(f'  Registering tool function: get_source_by_id')
        app.add_tool(get_source_by_id, name="get_source_by_id")
    except Exception as e:
        logger.error(f'Error registering tools for sources_endpoints: {e}')
    logger.info(f'Tools registration finished for sources_endpoints.')
