# Tool Generation and OpenAPI Usage Guide

This document describes how tools are automatically generated from the Delphix Control Tower (DCT) OpenAPI specification in this MCP server.

## Purpose

The MCP server dynamically generates tool modules from the DCT OpenAPI specification. This approach ensures that tools remain in sync with the API without manual maintenance for every new endpoint.

## Prerequisites

For tool generation to succeed, ensure:

- **Environment Variables**: `DCT_BASE_URL` and `DCT_API_KEY` are configured (see [README.md](README.md))
- **Optional Configuration**:
  - `DCT_REQUIRE_CONFIRMATION` (default: `true`) - Controls whether destructive operations (POST/PUT/DELETE excluding search/get) require explicit confirmation via the `confirm` parameter
  - Set to `false` to auto-confirm all destructive operations in the MCP settings
- **OpenAPI Accessibility**: The DCT API endpoint `/api/v3/openapi.yaml` must be reachable
- **SSL Verification**: Controlled by `IGNORE_SSL_WARNINGS` config setting (see [config.py](src/dct_mcp_server/config/config.py))

## Endpoint Definition Files

Tool generation is controlled by endpoint definition files located in [`src/dct_mcp_server/toolsgenerator/endpoints/`](src/dct_mcp_server/toolsgenerator/endpoints/).

### Naming Convention

- Filename: `{category}_endpoints.txt`
- Maps to generated tool module: `{category}_endpoints_tool.py` (in `src/dct_mcp_server/tools/`)
- Example: `sources_endpoints.txt` → `sources_endpoints_tool.py`

### Format

Each file contains one OpenAPI path per line. Paths support:
- `/path/search` — Search endpoints (POST with filter support)
- `/path/{id}` — Resource ID-based endpoints (GET, PATCH, DELETE)
- `/path/operation` — Action endpoints (POST)

Example: [job_endpoints.txt](src/dct_mcp_server/toolsgenerator/endpoints/job_endpoints.txt)
```
/jobs/search
/jobs/{jobId}/abandon
```

## Generation Flow

The generation process runs automatically during server startup in [`main.py`](src/dct_mcp_server/main.py):

1. **Load Endpoint Lists**: Read all `*_endpoints.txt` files from `toolsgenerator/endpoints/`
2. **Download OpenAPI Spec**: Fetch `{DCT_BASE_URL}/api/v3/openapi.yaml` and save to temporary `src/api.yaml`
3. **Parse Specification**: Extract endpoint definitions using the path and HTTP method
4. **Generate Tool Functions**:
   - Use OpenAPI `operationId` as the function name
   - Extract parameters from the spec and map types
   - Mark optional parameters with default values (`None`)
   - For search endpoints (with `x-filterable`), auto-generate `filter_expression` parameter with documentation
5. **Write Tool Modules**: Create Python files in `src/dct_mcp_server/tools/` with:
   - Generated function implementations
   - Helper utilities (`make_api_request`, `build_params`, `async_to_sync`)
   - `register_tools(app, dct_client)` function for MCP registration
   - **Tool Naming Convention**: All tools are prefixed with `dct_` (e.g., `dct_manage_vdbs_endpoints`) to prevent conflicts in multi-server MCP environments. The MCP protocol does not automatically namespace tools by server, so this prefix ensures AI agents can distinguish DCT tools from other MCP servers (like Atlassian) when multiple servers are configured.
6. **Clean Up**: Delete temporary `src/api.yaml`
7. **Discover and Register**: MCP server imports all `*_tool.py` modules and registers tools via their `register_tools()` functions

## Search Endpoints and Filter Expressions

Search endpoints (paths like `/entities/search`) support powerful filtering through the `filter_expression` parameter. The generator:

- Detects the `x-filterable` extension in the OpenAPI spec
- Extracts available filter fields from the response schema
- Generates documentation showing:
  - All filterable field names
  - Example filter expression syntax
  - Common operators (e.g., `=`, `!=`, `>`, `<`, `~`, `contains`)

Example from generated tool:
```python
filter_expression: str | None = None
    """
    Filter results using DCT filter expressions. Available fields:
    [list of fields extracted from OpenAPI spec]
    
    Example: "name ~ 'prod' AND status = 'ACTIVE'"
    """
```

## Common Generated Utilities

All generated tool modules include:

- **`make_api_request(method, endpoint, params=None, json_body=None)`**: 
  - Constructs HTTP requests to the DCT API
  - Handles authentication via DCT client
  - Returns parsed JSON response

- **`build_params(**kwargs)`**:
  - Builds parameter dictionaries excluding `None` values
  - Used to construct request payloads

- **`async_to_sync(async_func)`**:
  - Converts async functions to sync for MCP compatibility
  - Handles event loop lifecycle

## Best Practices

### Adding New Endpoints

1. **Identify the OpenAPI path**: Check the DCT OpenAPI spec for the exact path (e.g., `/sources/search`)
2. **Choose the right file**: Add to existing `{category}_endpoints.txt` or create a new one
3. **One path per line**: Keep the format simple and consistent
4. **Restart the server**: Changes to endpoint files take effect on server startup

### Naming Conventions

- Use lowercase filenames with underscores: `sources_endpoints.txt`, not `SourcesEndpoints.txt`
- Group related endpoints (same entity/domain) in the same file
- Use singular entity names when possible: `source_endpoints.txt` rather than `sources_endpoints.txt` (though either works)

### Managing Tool Count

To keep the number of tools minimal:

- **Group by domain**: All VDB operations in one file, all environment operations in another
- **Leverage search**: Use search endpoints with `filter_expression` instead of separate GET-by-ID tools
- **Combine variants**: List all CRUD operations in one file rather than creating separate files per operation type

### Parameter Handling

Generated functions automatically:

- Convert optional OpenAPI parameters to Python optional parameters (`param: type | None = None`)
- Extract parameter descriptions from OpenAPI and include them in docstrings
- Build request bodies using `build_params()` to exclude `None` values

## Regeneration

To regenerate tools after updating endpoint definition files:

1. **Modify endpoint files**: Edit `src/dct_mcp_server/toolsgenerator/endpoints/*.txt`
2. **Restart the MCP server**: Tools are regenerated on startup
3. **Verify logs**: Check server logs for generation status (enable debug logging if needed)

## Troubleshooting

### Tools Not Generated or Registered

1. **Enable Debug Logging**: Set `DEBUG=true` and check logs for generation errors
2. **Verify API Accessibility**: 
   ```bash
   curl -k https://{DCT_BASE_URL}/api/v3/openapi.yaml
   ```
3. **Check Endpoint File Format**: Ensure `*_endpoints.txt` files have valid paths (one per line)
4. **Inspect Generated Files**: Check `src/dct_mcp_server/tools/` for generated `*_tool.py` files

### Parameter or Filter Errors

- **Missing parameters in generated function**: Verify the OpenAPI spec includes the parameter definition
- **Filter expression not documented**: Ensure the endpoint has the `x-filterable` extension in the spec
- **Type mismatches**: Check OpenAPI schema for correct parameter types (string, integer, boolean, etc.)

## Related Files

- **Generator**: [driver.py](src/dct_mcp_server/toolsgenerator/driver.py)
- **Server Startup**: [main.py](src/dct_mcp_server/main.py)
- **Configuration**: [config.py](src/dct_mcp_server/config/config.py)
- **DCT Client**: [client.py](src/dct_mcp_server/dct_client/client.py)
- **OpenAPI Spec**: [swagger.json](swagger.json) (local reference; actual spec from DCT API)

## Tool Consolidation Strategy

To reduce the number of generated tools from ~77 to <15 for better AI client usability, implement consolidation:

### Current Status
- **77 individual tools** generated (one per endpoint operation)
- Each operation is a separate function: `search_vdbs()`, `provision_vdb_by_timestamp()`, etc.

### Consolidated Approach

Create **parameterized tools** with operation enums instead:

```python
# Target: manage_vdbs(operation="search") instead of search_vdbs()
# Single function handles multiple related operations with routing logic
```

### Implementation Steps

1. Group endpoints by resource type (sources, datasources, vdbs, snapshots, etc.)
2. Create operation enums per group (VdbOperation.SEARCH, etc.)
3. Generate single function per group with operation parameter
4. Add operation tags to endpoint files (e.g., `search|/vdbs/search`)
5. Update generator in driver.py to parse and consolidate

### Target: <15 Consolidated Tools

All tools use the `dct_` prefix for multi-server disambiguation:

- dct_manage_sources
- dct_manage_datasources  
- dct_manage_vdbs
- dct_manage_snapshots
- dct_manage_environments
- dct_manage_jobs
- dct_manage_vdb_lifecycle
- (plus 5-8 additional specialized tools)

### Benefits

- **Reduced Complexity**: 77 tools → ~12 tools  
- **Better AI Understanding**: Operation enums clarify intent
- **Type Safety**: Enum prevents invalid operations
- **Backward Compatible**: Both approaches can coexist during transition
