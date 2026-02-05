# MCP Server Tool Consolidation Roadmap

## Current Status ✅

**Completed:**
- ✅ 77 tools auto-generated from DCT OpenAPI spec  
- ✅ All CRUD operations for: sources, datasources, vdbs, snapshots, environments, jobs
- ✅ Tools successfully deployed and tested on fork
- ✅ Consolidation strategy documented in instructions.md
- ✅ Consolidator module created (consolidator.py)
- ✅ Consolidation config template created (consolidation_config.yaml)

**Current Generation:**
```
Total Tools: 77
├── Sources: 10 tools (search, create variants, delete)
├── Datasources: 20 tools (search, link variants, attach/detach, management)
├── VDBs: 23 tools (search, provision variants, refresh, rollback, lifecycle, management)
├── Snapshots: 4 tools (search, get, delete, retention management)
├── Environments: 20 tools (search, create, update, delete, resource management)
└── Jobs: 3 tools (search, results, abandonment)
```

## Phase 1: Consolidation Strategy (Current Phase)

**Goal:** Reduce 77 tools to <15 by grouping related operations under parameterized functions.

**Approach:**

1. **Create Operation Enums per Tool**
   - Instead of `search_vdbs()`, `provision_vdb_by_timestamp()`, etc.
   - Have one `manage_vdbs(operation: VdbOperation)` function
   - Operations defined as enum: `VdbOperation.SEARCH`, `VdbOperation.PROVISION_BY_TIMESTAMP`, etc.

2. **Endpoint File Tagging**
   - Modify endpoint definition files to include operation tags
   - Format: `operation_name|/endpoint/path`
   - Example: `search|/vdbs/search`, `provision_timestamp|/vdbs/provision_by_timestamp`

3. **Generator Enhancement**
   - Update `driver.py` to parse operation tags
   - Group endpoints with same operation_name
   - Generate single function with operation routing logic
   - Create enum classes for operation type hints

**Key Changes Needed:**

| File | Change | Status |
|------|--------|--------|
| driver.py | Parse operation tags, consolidate function generation | 🔄 Pending |
| Endpoint files | Add operation tags (operation\|path format) | 🔄 Partially Done |
| consolidator.py | Implement operation routing and enum generation | ✅ Created |
| instructions.md | Add consolidation guide | ✅ Done |

## Phase 2: Target Consolidated Tool Structure

**Target: 12-14 consolidated tools**

```python
# Instead of 77 individual functions, generate these consolidated functions:

# 1. manage_sources(operation, ...)
#    - search, create_oracle, create_postgres, create_ase, create_appdata, delete

# 2. manage_datasources(operation, ...)
#    - search, link_oracle, link_postgres, link_ase, link_appdata
#    - update, delete, attach, detach, enable, disable

# 3. manage_vdbs(operation, ...)
#    - search, provision_by_timestamp, provision_by_snapshot, provision_by_location, provision_from_bookmark
#    - refresh_by_timestamp, refresh_by_snapshot, refresh_by_location, refresh_from_bookmark
#    - rollback_by_timestamp, rollback_by_snapshot, rollback_from_bookmark
#    - upgrade, empty, start, stop, enable, disable, lock, unlock

# 4. manage_snapshots(operation, ...)
#    - search, get_details, delete, set_retention, unset_retention

# 5. manage_environments(operation, ...)
#    - search, create, update, delete, enable, disable

# 6. manage_environment_resources(operation, ...)
#    - manage_repositories, manage_hosts, manage_users, manage_listeners

# 7. manage_jobs(operation, ...)
#    - search, get_result, abandon

# 8. (Additional specialized tools as needed)
```

## Phase 3: Implementation Steps

### Step 1: Update Endpoint Files
Modify `src/dct_mcp_server/toolsgenerator/endpoints/*.txt` to use operation tagging:

```bash
# Current format:
/sources/search
/sources/oracle
/sources/postgres

# New format:
search|/sources/search
create_oracle|/sources/oracle
create_postgres|/sources/postgres
```

### Step 2: Enhance load_api_endpoints() in driver.py
Parse the new format and return operation-grouped structure:

```python
# Current return:
{'sources': ['/sources/search', '/sources/oracle', ...]}

# New return:
{
    'sources': {
        'search': ['/sources/search'],
        'create_oracle': ['/sources/oracle'],
        'create_postgres': ['/sources/postgres'],
        ...
    }
}
```

### Step 3: Implement Consolidated Tool Generation
Update `generate_tools_from_openapi()` to:
- Detect when tool_name maps to a dict of operations
- Generate single function with operation enum parameter
- Create operation routing logic
- Include operation enum class definition

### Step 4: Testing & Validation
- Restart server and verify <15 tools generated
- Test each operation via tool routing
- Validate all 77+ operations still accessible
- Update API documentation

## Benefits of Consolidation

| Aspect | Before (77 tools) | After (<15 tools) |
|--------|-------------------|-------------------|
| Cognitive Load | Very High | Low |
| AI Client Confusion | High | Low |
| Type Safety | Per-function | Enum-based |
| Discoverability | Difficult | Grouped by resource |
| Maintainability | High (many functions) | Low (few consolidated) |
| Flexibility | Fixed parameters | Dynamic routing |

## Implementation Timeline

**Estimated Effort:**
- Phase 1 Strategy: ✅ Complete
- Phase 2 Endpoint Updates: 1-2 hours
- Phase 3 Generator Enhancement: 2-3 hours  
- Phase 4 Testing: 1-2 hours
- **Total: 4-7 hours**

## Related Files

- **Strategy Guide**: [instructions.md](instructions.md#tool-consolidation-strategy)
- **Generator**: [driver.py](src/dct_mcp_server/toolsgenerator/driver.py)
- **Consolidator**: [consolidator.py](src/dct_mcp_server/toolsgenerator/consolidator.py)
- **Config**: [consolidation_config.yaml](src/dct_mcp_server/toolsgenerator/consolidation_config.yaml)
- **Endpoints**: [endpoints/](src/dct_mcp_server/toolsgenerator/endpoints/)

## Current Commits

- `28448c1`: Added consolidator.py and flexible generator
- `0e2ec3d`: Added consolidation strategy documentation
- Push to fork: ✅ https://github.com/sumedhbala-delphix/dxi-mcp-server

## Next Actions

1. **Update endpoint files** with operation|endpoint format
2. **Enhance driver.py** load_api_endpoints() to parse new format
3. **Implement consolidated tool generation** in generate_tools_from_openapi()
4. **Test consolidated generation** by restarting server
5. **Validate** all operations accessible via operation enums
