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
def search_vdbs(limit: Optional[int] = None, cursor: Optional[str] = None, sort: Optional[str] = None, filter_expression: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for VDBs.
    :param limit: Maximum number of objects to return per query. The value must be between 1 and 1000. Default is 100.
    :param limit: Maximum number of objects to return per query. The value must be between 1 and 1000. Default is 100.(optional)
    :param cursor: Cursor to fetch the next or previous page of results. The value of this property must be extracted from the 'prev_cursor' or 'next_cursor' property of a PaginatedResponseMetadata which is contained in the response of list and search API endpoints.
    :param cursor: Cursor to fetch the next or previous page of results. The value of this property must be extracted from the 'prev_cursor' or 'next_cursor' property of a PaginatedResponseMetadata which is contained in the response of list and search API endpoints.(optional)
    :param sort: The field to sort results by. A property name with a prepended '-' signifies descending order.
    :param sort: The field to sort results by. A property name with a prepended '-' signifies descending order.(optional)
    :param filter_expression: Filter expression string (optional)
    Filter expression can include the following fields:
     - id: The VDB object entity ID.
     - database_type: The database type of this VDB.
     - name: The logical name of this VDB.
     - description: The container description of this VDB.
     - database_name: The name of the database on the target environment or in the database management system.
     - namespace_id: The namespace id of this VDB.
     - namespace_name: The namespace name of this VDB.
     - is_replica: Is this a replicated object.
     - is_locked: Is this VDB locked.
     - locked_by: The ID of the account that locked this VDB.
     - locked_by_name: The name of the account that locked this VDB.
     - database_version: The database version of this VDB.
     - jdbc_connection_string: The JDBC connection URL for this VDB.
     - size: The total size of this VDB, in bytes.
     - storage_size: The actual space used by this VDB, in bytes.
     - unvirtualized_space: The disk space, in bytes, that it would take to store the VDB without Delphix.
     - engine_id: A reference to the Engine that this VDB belongs to.
     - status: The runtime status of the VDB. 'Unknown' if all attempts to connect to the dataset failed.
     - masked: The VDB is masked or not.
     - content_type: The content type of the vdb.
     - parent_timeflow_timestamp: The timestamp for parent timeflow.
     - parent_timeflow_timezone: The timezone for parent timeflow.
     - environment_id: A reference to the Environment that hosts this VDB.
     - ip_address: The IP address of the VDB's host.
     - fqdn: The FQDN of the VDB's host.
     - parent_id: A reference to the parent dataset of this VDB.
     - parent_dsource_id: A reference to the parent dSource of this VDB.
     - root_parent_id: A reference to the root parent dataset of this VDB which could be a VDB or a dSource.
     - group_name: The name of the group containing this VDB.
     - engine_name: Name of the Engine where this VDB is hosted
     - cdb_id: A reference to the CDB or VCDB associated with this VDB.
     - tags: No description
     - creation_date: The date this VDB was created.
     - hooks: No description
     - appdata_source_params: The JSON payload conforming to the DraftV4 schema based on the type of application data being manipulated.
     - template_id: A reference to the Database Template.
     - template_name: Name of the Database Template.
     - config_params: Database configuration parameter overrides.
     - environment_user_ref: The environment user reference.
     - additional_mount_points: Specifies additional locations on which to mount a subdirectory of an AppData container. Can only be updated while the VDB is disabled.
     - appdata_config_params: The parameters specified by the source config schema in the toolkit
     - mount_point: Mount point for the VDB (Oracle, ASE, AppData).
     - current_timeflow_id: A reference to the currently active timeflow for this VDB.
     - previous_timeflow_id: A reference to the previous timeflow for this VDB.
     - last_refreshed_date: The date this VDB was last refreshed.
     - vdb_restart: Indicates whether the Engine should automatically restart this vdb when target host reboot is detected.
     - is_appdata: Indicates whether this VDB has an AppData database.
     - exported_data_directory: ZFS exported data directory path.
     - vcdb_exported_data_directory: ZFS exported data directory path of the virtual CDB container (vCDB).
     - toolkit_id: The ID of the toolkit associated with this VDB.
     - plugin_version: The version of the plugin associated with this VDB.
     - primary_object_id: The ID of the parent object from which replication was done.
     - primary_engine_id: The ID of the parent engine from which replication was done.
     - primary_engine_name: The name of the parent engine from which replication was done.
     - replicas: The list of replicas replicated from this object.
     - invoke_datapatch: Indicates whether datapatch should be invoked.
     - enabled: True if VDB is enabled false if VDB is disabled.
     - node_listeners: The list of node listeners for this VDB.
     - instance_name: The instance name name of this single instance VDB.
     - instance_number: The instance number of this single instance VDB.
     - instances: No description
     - oracle_services: No description
     - repository_id: The repository id of this VDB.
     - containerization_state: No description
     - parent_tde_keystore_path: Path to a copy of the parent's Oracle transparent data encryption keystore on the target host. Required to provision from snapshots containing encrypted database files.
     - target_vcdb_tde_keystore_path: Path to the keystore of the target vCDB.
     - tde_key_identifier: ID of the key created by Delphix, as recorded in v$encryption_keys.key_id.
     - parent_pdb_tde_keystore_path: Path to a copy of the parent PDB's Oracle transparent data encryption keystore on the target host.
Required to provision from snapshots of PDB containing encrypted database files with isolated mode keystore.

     - target_pdb_tde_keystore_path: Path of the virtual PDB's Oracle transparent data encryption keystore on the target host.
     - recovery_model: Recovery model of the vdb database.
     - cdc_on_provision: Whether to enable CDC on provision for MSSql.
     - data_connection_id: The ID of the associated DataConnection.
     - mssql_ag_backup_location: Shared backup location to be used for VDB provision on AG Cluster.
     - mssql_ag_backup_based: Indicates whether to do fast operations for VDB on AG which will use a healthy secondary replica to recreate the AG or backup based operations which will use the primary replica to recreate the AG using backup and restore process.
     - mssql_ag_replicas: Indicates the mssql replica sources constitutes in MSSQL AG virtual source.
     - database_unique_name: The unique name of the database.
     - db_username: The user name of the database.
     - new_db_id: Indicates whether Delphix will generate a new DBID during VDB provision or refresh.
     - redo_log_groups: Number of Online Redo Log Groups.
     - redo_log_size_in_mb: Online Redo Log size in MB.
     - custom_env_vars: No description
     - active_instances: No description
     - nfs_version: The NFS version that was last used to mount this source."
     - nfs_version_reason: No description
     - nfs_encryption_enabled: Flag indicating whether the data transfer is encrypted or not.
     - cache_priority: When set to a value other than NORMAL (valid only for object storage engines) the engine will aggressively cache required data to ensure improved performance.
     - mssql_incremental_export_backup_frequency_minutes: Frequency in minutes for incremental export backups for VDBs.

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
    return make_api_request('POST', '/vdbs/search', params=params, json_body=search_body)

@log_tool_execution
def provision_vdb_by_timestamp() -> Dict[str, Any]:
    """
    Provision a new VDB by timestamp.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/provision_by_timestamp', params=params)

@log_tool_execution
def provision_vdb_by_snapshot() -> Dict[str, Any]:
    """
    Provision a new VDB by snapshot.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/provision_by_snapshot', params=params)

@log_tool_execution
def provision_vdb_by_location() -> Dict[str, Any]:
    """
    Provision a new VDB by location.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/provision_by_location', params=params)

@log_tool_execution
def provision_vdb_from_bookmark() -> Dict[str, Any]:
    """
    Provision a new VDB from a bookmark with a single VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/provision_from_bookmark', params=params)

@log_tool_execution
def empty_vdb() -> Dict[str, Any]:
    """
    Provision an empty VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/empty_vdb', params=params)

@log_tool_execution
def get_vdb_by_id() -> Dict[str, Any]:
    """
    Get a VDB by ID.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('GET', '/vdbs/{vdbId}', params=params)

@log_tool_execution
def delete_vdb() -> Dict[str, Any]:
    """
    Delete a VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/delete', params=params)

@log_tool_execution
def snapshot_vdb() -> Dict[str, Any]:
    """
    Snapshot a VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/snapshots', params=params)

@log_tool_execution
def start_vdb() -> Dict[str, Any]:
    """
    Start a VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/start', params=params)

@log_tool_execution
def stop_vdb() -> Dict[str, Any]:
    """
    Stop a VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/stop', params=params)

@log_tool_execution
def enable_vdb() -> Dict[str, Any]:
    """
    Enable a VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/enable', params=params)

@log_tool_execution
def disable_vdb() -> Dict[str, Any]:
    """
    Disable a VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/disable', params=params)

@log_tool_execution
def refresh_vdb_by_timestamp() -> Dict[str, Any]:
    """
    Refresh a VDB by timestamp.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/refresh_by_timestamp', params=params)

@log_tool_execution
def refresh_vdb_by_snapshot() -> Dict[str, Any]:
    """
    Refresh a VDB by snapshot.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/refresh_by_snapshot', params=params)

@log_tool_execution
def refresh_vdb_by_location() -> Dict[str, Any]:
    """
    Refresh a VDB by location.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/refresh_by_location', params=params)

@log_tool_execution
def refresh_vdb_from_bookmark() -> Dict[str, Any]:
    """
    Refresh a VDB from bookmark with a single VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/refresh_from_bookmark', params=params)

@log_tool_execution
def rollback_vdb_by_timestamp() -> Dict[str, Any]:
    """
    Rollback a VDB by timestamp.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/rollback_by_timestamp', params=params)

@log_tool_execution
def rollback_vdb_by_snapshot() -> Dict[str, Any]:
    """
    Rollback a VDB by snapshot.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/rollback_by_snapshot', params=params)

@log_tool_execution
def rollback_vdb_from_bookmark() -> Dict[str, Any]:
    """
    Rollback a VDB from a bookmark with only the same VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/rollback_from_bookmark', params=params)

@log_tool_execution
def upgrade_vdb() -> Dict[str, Any]:
    """
    Upgrade VDB
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/upgrade', params=params)

@log_tool_execution
def lock_vdb() -> Dict[str, Any]:
    """
    Lock a VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/lock', params=params)

@log_tool_execution
def unlock_vdb() -> Dict[str, Any]:
    """
    Unlock a VDB.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/vdbs/{vdbId}/unlock', params=params)


def register_tools(app, dct_client):
    global client
    client = dct_client
    logger.info(f'Registering tools for vdbs_endpoints...')
    try:
        logger.info(f'  Registering tool function: search_vdbs')
        app.add_tool(search_vdbs, name="search_vdbs")
        logger.info(f'  Registering tool function: provision_vdb_by_timestamp')
        app.add_tool(provision_vdb_by_timestamp, name="provision_vdb_by_timestamp")
        logger.info(f'  Registering tool function: provision_vdb_by_snapshot')
        app.add_tool(provision_vdb_by_snapshot, name="provision_vdb_by_snapshot")
        logger.info(f'  Registering tool function: provision_vdb_by_location')
        app.add_tool(provision_vdb_by_location, name="provision_vdb_by_location")
        logger.info(f'  Registering tool function: provision_vdb_from_bookmark')
        app.add_tool(provision_vdb_from_bookmark, name="provision_vdb_from_bookmark")
        logger.info(f'  Registering tool function: empty_vdb')
        app.add_tool(empty_vdb, name="empty_vdb")
        logger.info(f'  Registering tool function: get_vdb_by_id')
        app.add_tool(get_vdb_by_id, name="get_vdb_by_id")
        logger.info(f'  Registering tool function: delete_vdb')
        app.add_tool(delete_vdb, name="delete_vdb")
        logger.info(f'  Registering tool function: snapshot_vdb')
        app.add_tool(snapshot_vdb, name="snapshot_vdb")
        logger.info(f'  Registering tool function: start_vdb')
        app.add_tool(start_vdb, name="start_vdb")
        logger.info(f'  Registering tool function: stop_vdb')
        app.add_tool(stop_vdb, name="stop_vdb")
        logger.info(f'  Registering tool function: enable_vdb')
        app.add_tool(enable_vdb, name="enable_vdb")
        logger.info(f'  Registering tool function: disable_vdb')
        app.add_tool(disable_vdb, name="disable_vdb")
        logger.info(f'  Registering tool function: refresh_vdb_by_timestamp')
        app.add_tool(refresh_vdb_by_timestamp, name="refresh_vdb_by_timestamp")
        logger.info(f'  Registering tool function: refresh_vdb_by_snapshot')
        app.add_tool(refresh_vdb_by_snapshot, name="refresh_vdb_by_snapshot")
        logger.info(f'  Registering tool function: refresh_vdb_by_location')
        app.add_tool(refresh_vdb_by_location, name="refresh_vdb_by_location")
        logger.info(f'  Registering tool function: refresh_vdb_from_bookmark')
        app.add_tool(refresh_vdb_from_bookmark, name="refresh_vdb_from_bookmark")
        logger.info(f'  Registering tool function: rollback_vdb_by_timestamp')
        app.add_tool(rollback_vdb_by_timestamp, name="rollback_vdb_by_timestamp")
        logger.info(f'  Registering tool function: rollback_vdb_by_snapshot')
        app.add_tool(rollback_vdb_by_snapshot, name="rollback_vdb_by_snapshot")
        logger.info(f'  Registering tool function: rollback_vdb_from_bookmark')
        app.add_tool(rollback_vdb_from_bookmark, name="rollback_vdb_from_bookmark")
        logger.info(f'  Registering tool function: upgrade_vdb')
        app.add_tool(upgrade_vdb, name="upgrade_vdb")
        logger.info(f'  Registering tool function: lock_vdb')
        app.add_tool(lock_vdb, name="lock_vdb")
        logger.info(f'  Registering tool function: unlock_vdb')
        app.add_tool(unlock_vdb, name="unlock_vdb")
    except Exception as e:
        logger.error(f'Error registering tools for vdbs_endpoints: {e}')
    logger.info(f'Tools registration finished for vdbs_endpoints.')
