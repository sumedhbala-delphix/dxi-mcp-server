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
def search_dsources(limit: Optional[int] = None, cursor: Optional[str] = None, sort: Optional[str] = None, filter_expression: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for dSources.
    :param limit: Maximum number of objects to return per query. The value must be between 1 and 1000. Default is 100.
    :param limit: Maximum number of objects to return per query. The value must be between 1 and 1000. Default is 100.(optional)
    :param cursor: Cursor to fetch the next or previous page of results. The value of this property must be extracted from the 'prev_cursor' or 'next_cursor' property of a PaginatedResponseMetadata which is contained in the response of list and search API endpoints.
    :param cursor: Cursor to fetch the next or previous page of results. The value of this property must be extracted from the 'prev_cursor' or 'next_cursor' property of a PaginatedResponseMetadata which is contained in the response of list and search API endpoints.(optional)
    :param sort: The field to sort results by. A property name with a prepended '-' signifies descending order.
    :param sort: The field to sort results by. A property name with a prepended '-' signifies descending order.(optional)
    :param filter_expression: Filter expression string (optional)
    Filter expression can include the following fields:
     - id: The dSource object entity ID.
     - database_type: The database type of this dSource.
     - name: The container name of this dSource.
     - description: The container description of this dSource.
     - namespace_id: The namespace id of this dSource.
     - namespace_name: The namespace name of this dSource.
     - is_replica: Is this a replicated object.
     - database_version: The database version of this dSource.
     - content_type: The content type of the dSource.
     - data_uuid: A universal ID that uniquely identifies the dSource database.
     - storage_size: The actual space used by this dSource, in bytes.
     - plugin_version: The version of the plugin associated with this source database.
     - creation_date: The date this dSource was created.
     - group_name: The name of the group containing this dSource.
     - enabled: A value indicating whether this dSource is enabled.
     - is_detached: A value indicating whether this dSource is detached.
     - engine_id: A reference to the Engine that this dSource belongs to.
     - source_id: A reference to the Source associated with this dSource.
     - staging_source_id: A reference to the Staging Source associated with this dSource.
     - status: The runtime status of the dSource. 'Unknown' if all attempts to connect to the source failed.
     - engine_name: Name of the Engine where this DSource is hosted
     - cdb_id: A reference to the CDB associated with this dSource.
     - current_timeflow_id: A reference to the currently active timeflow for this dSource.
     - previous_timeflow_id: A reference to the previous timeflow for this dSource.
     - is_appdata: Indicates whether this dSource has an AppData database.
     - toolkit_id: The ID of the toolkit associated with this dSource(AppData only).
     - unvirtualized_space: This is the sum of unvirtualized space from the dependants VDBs of the dSource.
     - dependant_vdbs: The number of VDBs that are dependant on this dSource. This includes all VDB descendants that have this dSource as an ancestor.
     - appdata_source_params: The JSON payload conforming to the DraftV4 schema based on the type of application data being manipulated.
     - appdata_config_params: The parameters specified by the source config schema in the toolkit
     - tags: No description
     - primary_object_id: The ID of the parent object from which replication was done.
     - primary_engine_id: The ID of the parent engine from which replication was done.
     - primary_engine_name: The name of the parent engine from which replication was done.
     - replicas: The list of replicas replicated from this object.
     - hooks: No description
     - sync_policy_id: The id of the snapshot policy associated with this dSource.
     - retention_policy_id: The id of the retention policy associated with this dSource.
     - replica_retention_policy_id: The id of the replica retention policy associated with this dSource.
     - quota_policy_id: The id of the quota policy associated with this dSource.
     - logsync_enabled: True if LogSync is enabled for this dSource.
     - logsync_mode: No description
     - logsync_interval: Interval between LogSync requests, in seconds.
     - exported_data_directory: ZFS exported data directory path.
     - template_id: A reference to the Non Virtual Database Template.
     - allow_auto_staging_restart_on_host_reboot: Indicates whether Delphix should automatically restart this staging database when staging host reboot is detected.
     - physical_standby: Indicates whether this staging database is configured as a physical standby.
     - validate_by_opening_db_in_read_only_mode: Indicates whether this staging database snapshot is validated by opening it in read-only mode.
     - mssql_sync_strategy_managed_type: No description
     - validated_sync_mode: Specifies the backup types ValidatedSync will use to synchronize the dSource with the source database.
     - shared_backup_locations: Shared source database backup locations.
     - backup_policy: Specify which node of an availability group to run the copy-only full backup on
     - compression_enabled: Specify whether the backups taken should be compressed or uncompressed.
     - staging_database_name: The name of the staging database
     - db_state: User provided db state that is used to create staging push db
     - encryption_key: The encryption key to use when restoring encrypted backups.
     - external_netbackup_config_master_name: The master server name of this NetBackup configuration.
     - external_netbackup_config_source_client_name: The source's client server name of this NetBackup configuration.
     - external_netbackup_config_params: NetBackup configuration parameter overrides.
     - external_netbackup_config_templates: Optional config template selection for NetBackup configurations.
     - external_commserve_host_name: The commserve host name of this Commvault configuration.
     - external_commvault_config_source_client_name: The source client name of this Commvault configuration.
     - external_commvault_config_staging_client_name: The staging client name of this Commvault configuration.
     - external_commvault_config_params: Commvault configuration parameter overrides.
     - external_commvault_config_templates: Optional config template selection for Commvault configurations.
     - mssql_user_type: Database user type for Database authentication.
     - domain_user_credential_type: credential types.
     - mssql_database_username: The database user name for database user type.
     - mssql_user_environment_reference: The name or reference of the environment user for environment user type.
     - mssql_user_domain_username: Domain User name for password credentials.
     - mssql_user_domain_vault_username: Delphix display name for the vault user.
     - mssql_user_domain_vault: The name or reference of the vault.
     - mssql_user_domain_hashicorp_vault_engine: Vault engine name where the credential is stored.
     - mssql_user_domain_hashicorp_vault_secret_path: Path in the vault engine where the credential is stored.
     - mssql_user_domain_hashicorp_vault_username_key: Hashicorp vault key for the username in the key-value store.
     - mssql_user_domain_hashicorp_vault_secret_key: Hashicorp vault key for the password in the key-value store.
     - mssql_user_domain_azure_vault_name: Azure key vault name.
     - mssql_user_domain_azure_vault_username_key: Azure vault key in the key-value store.
     - mssql_user_domain_azure_vault_secret_key: Azure vault key in the key-value store.
     - mssql_user_domain_cyberark_vault_query_string: Query to find a credential in the CyberArk vault.
     - diagnose_no_logging_faults: If true, NOLOGGING operations on this container are treated as faults and cannot be resolved manually. Otherwise, these operations are ignored.
     - pre_provisioning_enabled: If true, pre-provisioning will be performed after every sync.
     - backup_level_enabled: Boolean value indicates whether LEVEL-based incremental backups can be used on the source db.
     - rman_channels: Number of parallel channels to use.
     - files_per_set: Number of data files to include in each RMAN backup set.
     - check_logical: True if extended block checking should be used for this linked database.
     - encrypted_linking_enabled: True if SnapSync data from the source should be retrieved through an encrypted connection. Enabling this feature can decrease the performance of SnapSync from the source but has no impact on the performance of VDBs created from the retrieved data.
     - compressed_linking_enabled: True if SnapSync data from the source should be compressed over the network. Enabling this feature will reduce network bandwidth consumption and may significantly improve throughput, especially over slow network.
     - bandwidth_limit: Bandwidth limit (MB/s) for SnapSync and LogSync network traffic. A value of 0 means no limit.
     - number_of_connections: Total number of transport connections to use during SnapSync.
     - data_connection_id: The ID of the associated DataConnection.

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
    return make_api_request('POST', '/dsources/search', params=params, json_body=search_body)

@log_tool_execution
def link_oracle_database() -> Dict[str, Any]:
    """
    Link Oracle database as dSource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/oracle', params=params)

@log_tool_execution
def link_ase_database() -> Dict[str, Any]:
    """
    Link an ASE database as dSource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/ase', params=params)

@log_tool_execution
def link_mssql_database() -> Dict[str, Any]:
    """
    Link a MSSql database as dSource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/mssql', params=params)

@log_tool_execution
def link_appdata_database() -> Dict[str, Any]:
    """
    Link an AppData database as dSource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/appdata', params=params)

@log_tool_execution
def link_oracle_staging_push_database() -> Dict[str, Any]:
    """
    Link an Oracle staging push database as dSource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/oracle/staging-push', params=params)

@log_tool_execution
def link_mssql_staging_push_database() -> Dict[str, Any]:
    """
    Link a MSSql staging push database as dSource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/mssql/staging-push', params=params)

@log_tool_execution
def delete_dsource() -> Dict[str, Any]:
    """
    Delete the specified dSource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/delete', params=params)

@log_tool_execution
def attach_oracle_dsource() -> Dict[str, Any]:
    """
    Attach an Oracle dSource to an Oracle database.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/oracle/{dsourceId}/attachSource', params=params)

@log_tool_execution
def attach_mssql_database() -> Dict[str, Any]:
    """
    Attaches a MSSql source to a previously detached dsource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/mssql/{dsourceId}/attachSource', params=params)

@log_tool_execution
def attach_mssql_staging_push_database() -> Dict[str, Any]:
    """
    Attaches a MSSql staging push database to a previously detached dsource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/mssql/staging-push/{dsourceId}/attachSource', params=params)

@log_tool_execution
def detach_oracle_dsource() -> Dict[str, Any]:
    """
    Detaches an Oracle source from an Oracle database.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/oracle/{dsourceId}/detachSource', params=params)

@log_tool_execution
def detach_mssql_database() -> Dict[str, Any]:
    """
    Detaches a linked source from a MSSql database.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/mssql/{dsourceId}/detachSource', params=params)

@log_tool_execution
def enable_dsource() -> Dict[str, Any]:
    """
    Enable a dSource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/{dsourceId}/enable', params=params)

@log_tool_execution
def disable_dsource() -> Dict[str, Any]:
    """
    Disable a dSource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/{dsourceId}/disable', params=params)

@log_tool_execution
def snapshot_dsource() -> Dict[str, Any]:
    """
    Snapshot a dSource.
    """
    # Build parameters excluding None values
    params = {}
    return make_api_request('POST', '/dsources/{dsourceId}/snapshots', params=params)


def register_tools(app, dct_client):
    global client
    client = dct_client
    logger.info(f'Registering tools for dsources_endpoints...')
    try:
        logger.info(f'  Registering tool function: search_dsources')
        app.add_tool(search_dsources, name="search_dsources")
        logger.info(f'  Registering tool function: link_oracle_database')
        app.add_tool(link_oracle_database, name="link_oracle_database")
        logger.info(f'  Registering tool function: link_ase_database')
        app.add_tool(link_ase_database, name="link_ase_database")
        logger.info(f'  Registering tool function: link_mssql_database')
        app.add_tool(link_mssql_database, name="link_mssql_database")
        logger.info(f'  Registering tool function: link_appdata_database')
        app.add_tool(link_appdata_database, name="link_appdata_database")
        logger.info(f'  Registering tool function: link_oracle_staging_push_database')
        app.add_tool(link_oracle_staging_push_database, name="link_oracle_staging_push_database")
        logger.info(f'  Registering tool function: link_mssql_staging_push_database')
        app.add_tool(link_mssql_staging_push_database, name="link_mssql_staging_push_database")
        logger.info(f'  Registering tool function: delete_dsource')
        app.add_tool(delete_dsource, name="delete_dsource")
        logger.info(f'  Registering tool function: attach_oracle_dsource')
        app.add_tool(attach_oracle_dsource, name="attach_oracle_dsource")
        logger.info(f'  Registering tool function: attach_mssql_database')
        app.add_tool(attach_mssql_database, name="attach_mssql_database")
        logger.info(f'  Registering tool function: attach_mssql_staging_push_database')
        app.add_tool(attach_mssql_staging_push_database, name="attach_mssql_staging_push_database")
        logger.info(f'  Registering tool function: detach_oracle_dsource')
        app.add_tool(detach_oracle_dsource, name="detach_oracle_dsource")
        logger.info(f'  Registering tool function: detach_mssql_database')
        app.add_tool(detach_mssql_database, name="detach_mssql_database")
        logger.info(f'  Registering tool function: enable_dsource')
        app.add_tool(enable_dsource, name="enable_dsource")
        logger.info(f'  Registering tool function: disable_dsource')
        app.add_tool(disable_dsource, name="disable_dsource")
        logger.info(f'  Registering tool function: snapshot_dsource')
        app.add_tool(snapshot_dsource, name="snapshot_dsource")
    except Exception as e:
        logger.error(f'Error registering tools for dsources_endpoints: {e}')
    logger.info(f'Tools registration finished for dsources_endpoints.')
