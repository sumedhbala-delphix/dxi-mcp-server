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
def search_snapshots(limit: Optional[int] = None, cursor: Optional[str] = None, sort: Optional[str] = None, filter_expression: Optional[str] = None) -> Dict[str, Any]:
    """
    Search snapshots.
    :param limit: Maximum number of objects to return per query. The value must be between 1 and 1000. Default is 100.
    :param limit: Maximum number of objects to return per query. The value must be between 1 and 1000. Default is 100.(optional)
    :param cursor: Cursor to fetch the next or previous page of results. The value of this property must be extracted from the 'prev_cursor' or 'next_cursor' property of a PaginatedResponseMetadata which is contained in the response of list and search API endpoints.
    :param cursor: Cursor to fetch the next or previous page of results. The value of this property must be extracted from the 'prev_cursor' or 'next_cursor' property of a PaginatedResponseMetadata which is contained in the response of list and search API endpoints.(optional)
    :param sort: The field to sort results by. A property name with a prepended '-' signifies descending order.
    :param sort: The field to sort results by. A property name with a prepended '-' signifies descending order.(optional)
    :param filter_expression: Filter expression string (optional)
    Filter expression can include the following fields:
     - id: The Snapshot ID.
     - engine_id: The id of the engine the snapshot belongs to.
     - namespace: Alternate namespace for this object, for replicated and restored snapshots.
     - name: The snapshot's name.
     - namespace_id: The namespace id of this snapshot.
     - namespace_name: The namespace name of this snapshot.
     - is_replica: Is this a replicated object.
     - consistency: Indicates what type of recovery strategies must be invoked when provisioning from this snapshot.
     - missing_non_logged_data: Indicates if a virtual database provisioned from this snapshot will be missing nologging changes.
     - dataset_id: The ID of the Snapshot's dSource or VDB.
     - creation_time: The time when the snapshot was created.
     - start_timestamp: The timestamp within the parent TimeFlow at which this snapshot was initiated. \
No recovery earlier than this point needs to be applied in order to provision a database from \
this snapshot. If start_timestamp equals timestamp, then no recovery needs to be \
applied in order to provision a database.

     - start_location: The database specific indentifier within the parent TimeFlow at which this snapshot was initiated. \
No recovery earlier than this point needs to be applied in order to provision a database from \
this snapshot. If start_location equals location, then no recovery needs to be \
applied in order to provision a database.

     - timestamp: The logical time of the data contained in this Snapshot.
     - location: Database specific identifier for the data contained in this Snapshot, such as the Log Sequence Number (LSN) for MSsql databases, System Change Number (SCN) for Oracle databases.
     - retention: Retention policy, in days. A value of -1 indicates the snapshot should be kept forever. Deprecated in favor of expiration and retain_forever.
     - expiration: The expiration date of this snapshot. If this is unset and retain_forever is false, and the snapshot is not included in a Bookmark, the snapshot is subject to the retention policy of its dataset.
     - retain_forever: Indicates that the snapshot is protected from retention, i.e it will be kept forever. If false, see expiration.
     - effective_expiration: The effective expiration is that max of the snapshot expiration and the expiration of any Bookmark which includes this snapshot.
     - effective_retain_forever: True if retain_forever is set or a Bookmark retains this snapshot forever.
     - timeflow_id: The TimeFlow this snapshot was taken on.
     - timezone: Time zone of the source database at the time the snapshot was taken.
     - version: Version of database source repository at the time the snapshot was taken.
     - temporary: Indicates that this snapshot is in a transient state and should not be user visible.
     - appdata_toolkit: The toolkit associated with this snapshot.
     - appdata_metadata: The JSON payload conforming to the DraftV4 schema based on the type of application data being manipulated.
     - ase_db_encryption_key: Database encryption key present for this snapshot.
     - mssql_internal_version: Internal version of the source database at the time the snapshot was taken.
     - mssql_backup_set_uuid: UUID of the source database backup that was restored for this snapshot.
     - mssql_backup_software_type: Backup software used to restore the source database backup for this snapshot
     - mssql_backup_location_type: Backup software used to restore the source database backup for this snapshot
     - mssql_empty_snapshot: True if the staging push dSource snapshot is empty.
     - mssql_incremental_export_source_snapshot: True if this snapshot belongs to Incremental VDB and can be used for Incremental V2P.
     - oracle_from_physical_standby_vdb: True if this snapshot was taken of a standby database.
     - oracle_redo_log_size_in_bytes: Online redo log size in bytes when this snapshot was taken.
     - tags: No description

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
    return make_api_request('POST', '/snapshots/search', params=params, json_body=search_body)

@log_tool_execution
def get_snapshot_by_id() -> Dict[str, Any]:
    """
    Get a Snapshot by ID.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('GET', '/snapshots/{snapshotId}', params=params)

@log_tool_execution
def delete_snapshot_by_id() -> Dict[str, Any]:
    """
    Delete a Snapshot.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/snapshots/{snapshotId}/delete', params=params)

@log_tool_execution
def unset_snapshot_retention() -> Dict[str, Any]:
    """
    Unset a Snapshot's expiration, removing expiration and retain_forever values for the snapshot.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/snapshots/{snapshotId}/unset_expiration', params=params)


def register_tools(app, dct_client):
    global client
    client = dct_client
    logger.info(f'Registering tools for snapshots_endpoints...')
    try:
        logger.info(f'  Registering tool function: search_snapshots')
        app.add_tool(search_snapshots, name="search_snapshots")
        logger.info(f'  Registering tool function: get_snapshot_by_id')
        app.add_tool(get_snapshot_by_id, name="get_snapshot_by_id")
        logger.info(f'  Registering tool function: delete_snapshot_by_id')
        app.add_tool(delete_snapshot_by_id, name="delete_snapshot_by_id")
        logger.info(f'  Registering tool function: unset_snapshot_retention')
        app.add_tool(unset_snapshot_retention, name="unset_snapshot_retention")
    except Exception as e:
        logger.error(f'Error registering tools for snapshots_endpoints: {e}')
    logger.info(f'Tools registration finished for snapshots_endpoints.')
