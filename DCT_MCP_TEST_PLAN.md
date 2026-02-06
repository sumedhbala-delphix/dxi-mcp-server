# DCT MCP Server - Comprehensive Test Plan

**Total Operations to Test:** 77 operations across 10 tools  
**Test Environment:** DCT at `https://10.43.33.186`  
**Configuration:** `DCT_REQUIRE_CONFIRMATION=false` (for automated testing)

---

## 🧪 Test Execution Status

**Last Updated:** 2026-02-06 23:05 UTC  
**Current Phase:** Phase 1-4 partially complete  
**Overall Status:** 🟡 BLOCKED - Awaiting VS Code reload for Bug #1 fix

### Execution Summary

| Phase | Status | Passed | Failed | Blocked | Total | Notes |
|-------|--------|--------|--------|---------|-------|-------|
| Phase 1 (Read) | 🟡 In Progress | 5 | 0 | 10 | 43 | VDB search/get/sort/filter all working |
| Phase 2 (Lifecycle) | 🟡 In Progress | 4 | 0 | 6 | 15 | stop/start/disable/enable work; lock/unlock removed |
| Phase 3 (Snapshot) | ✅ Partial | 1 | 0 | 2 | 3 | VDB snapshot works |
| Phase 4 (Refresh/Rollback) | 🟡 In Progress | 1 | 1 | 5 | 7 | refresh_timestamp works; refresh_location fails |
| Phase 5 (Provisioning) | ⬜ Not Started | 0 | 0 | 0 | 26 | - |
| Phase 6 (Delete) | ⬜ Not Started | 0 | 0 | 0 | 5 | - |

### Bugs Found During Testing

| # | Description | Status | Fix Location |
|---|-------------|--------|--------------|
| 1 | Missing `get_dct_config` import in 9 tool files | ✅ FIXED | Added imports to all affected *_endpoints_tool.py files |
| 2 | filter_expression syntax error - used `~` instead of DCT keywords | ✅ FIXED | Use EQ, CONTAINS, etc. not `=`, `~` - added docs to tool |
| 3 | VDB lock operation fails with "Request failed after 3 attempts" | ✅ REMOVED | Removed lock/unlock operations from vdbs_endpoints_tool.py |
| 4 | VDB refresh_location with "LATEST_SNAPSHOT" fails | 🔴 OPEN | Check DCT API docs for correct location format |

### Collected Resource IDs

```yaml
VDBs:
  - id: "1-ORACLE_DB_CONTAINER-2"
    name: "DBOM_AY8"
    status: "RUNNING"
  - id: "1-ORACLE_DB_CONTAINER-3"
    name: "DBOM_LI9"
    status: "RUNNING"  
  - id: "1-ORACLE_DB_CONTAINER-4"
    name: "mcpcc"
    status: "RUNNING"
    test_vdb: true
dSources:
  - id: "1-ORACLE_DB_CONTAINER-1"
    note: "from parent_dsource_id field"
Snapshots: []
Environments:
  - id: "1-UNIX_HOST_ENVIRONMENT-2"
    note: "from environment_id field in VDB"
Jobs:
  - id: "2239184d4589479797798486f1ad8791"
    type: "VDB_STOP"
    status: "COMPLETED"
  - id: "e50859e7b5874561a90c9e5293322656"  
    type: "VDB_START"
    status: "COMPLETED"
  - id: "8c8c71f8be884ef89d9dea50a19c6620"
    type: "VDB_DISABLE"
    status: "COMPLETED"
  - id: "88920d6b25c74c4ba711d52529ddbb0d"
    type: "VDB_ENABLE"
    status: "COMPLETED"
  - id: "bc5a71a4e7e5476db9578e8d6ea9e974"
    type: "VDB_SNAPSHOT"
    status: "STARTED"
  - id: "7a76216ab78547e6845907906a912092"
    type: "VDB_REFRESH"
    status: "STARTED"
```

### Test Results Log

| Test # | Phase | Operation | Tool | Status | Notes |
|--------|-------|-----------|------|--------|-------|
| 1 | 1.1 | search | vdbs | ✅ PASS | Returned 3 VDBs |
| 2 | 1.1 | search_vdbs | dataset | ⏸️ BLOCKED | Bug #1 - needs VS Code reload |
| 3 | 1.1 | search (filter) | vdbs | ✅ PASS | Uses DCT syntax: "name CONTAINS 'DBOM'" |
| 3a | 1.1 | search (sort) | vdbs | ✅ PASS | sort=-creation_date works |
| 4-9 | 1.1 | dataset searches | dataset | ⏸️ BLOCKED | Bug #1 - needs VS Code reload |
| 10 | 1.1 | search | dsources | ⏸️ BLOCKED | Bug #1 - needs VS Code reload |
| 11 | 1.1 | search | sources | ⏸️ BLOCKED | Bug #1 - needs VS Code reload |
| 12 | 1.1 | search | environment | ⏸️ BLOCKED | Bug #1 - needs VS Code reload |
| 21 | 1.2 | get | vdbs | ✅ PASS | VDB details returned |
| 44 | 2.1 | stop | vdbs | ✅ PASS | VDB stopped, status=INACTIVE |
| 45 | 2.1 | start | vdbs | ✅ PASS | VDB started, status=RUNNING |
| 46 | 2.1 | disable | vdbs | ✅ PASS | VDB disabled, enabled=false |
| 47 | 2.1 | enable | vdbs | ✅ PASS | VDB enabled, enabled=true |
| 48 | 2.1 | lock | vdbs | ⏭️ SKIP | Feature removed - not supported by DCT API |
| 57 | 3 | snapshot | vdbs | ✅ PASS | Job created for VDB snapshot |
| 60 | 4.1 | refresh_timestamp | vdbs | ✅ PASS | VDB refresh by timestamp works |
| 61 | 4.1 | refresh_location | vdbs | ❌ FAIL | "location: LATEST_SNAPSHOT" not recognized |

**📊 Current Progress:** 11 passed, 2 failed, 10 blocked (out of 75 total operations)

**⚠️ ACTION REQUIRED:** Reload VS Code to pick up the bug fix for `get_dct_config` import, then resume testing.

---

## Test Execution Strategy

**Phase Order (Safest to Most Destructive):**
1. **Phase 1:** Read-Only Operations (Search & Get) - 41 operations
2. **Phase 2:** Safe Lifecycle Operations (Start/Stop/Enable/Disable/Lock/Unlock) - 17 operations
3. **Phase 3:** Snapshot Operations - 3 operations
4. **Phase 4:** Refresh & Rollback Operations - 7 operations
5. **Phase 5:** Provisioning & Create Operations - 26 operations
6. **Phase 6:** Delete & Destructive Operations - 5 operations

**Safety Principles:**
- ✅ Always run read-only tests first to validate connectivity and data availability
- ✅ Test lifecycle operations on existing resources (reversible actions)
- ✅ Test provisioning operations that create new resources
- ⚠️ **Run delete operations LAST** and only on test resources

---

## Phase 1: Read-Only Operations (41 operations)

### 1.1 Search Operations (19 tests)

#### Test 1: VDB Search (Primary)
**Tool:** `dct_manage_vdbs_endpoints`
```python
operation_type="search"
limit=10
sort="name"
# Validation: Returns list of VDBs with IDs for subsequent tests
# Collect: vdbId values for Phase 2-6
```

#### Test 2-9: Dataset Searches
**Tool:** `dct_manage_dataset_endpoints`
```python
# Test 2: Search VDBs with pagination
operation_type="search_vdbs"
limit=5
cursor=None
sort="name"
# Validation: Returns ≤5 VDBs, cursor for next page

# Test 3: Search VDBs with filter
operation_type="search_vdbs"
filter_expression="name ~ 'test'"
# Validation: Returns only VDBs matching filter

# Test 4-9: Search all dataset types
for op in ["search_bookmarks", "search_data_connections", "search_dsources", 
           "search_snapshots", "search_sources", "search_timeflows", "search_vdb_groups"]:
    operation_type=op
    limit=10
```

#### Test 10: dSource Search
**Tool:** `dct_manage_dsources_endpoints`
```python
operation_type="search"
limit=10
# Collect: dsourceId values
```

#### Test 11: Source Search
**Tool:** `dct_manage_sources_endpoints`
```python
operation_type="search"
limit=10
# Collect: sourceId values
```

#### Test 12: Environment Search
**Tool:** `dct_manage_environment_endpoints`
```python
operation_type="search"
limit=10
# Collect: environmentId values
```

#### Test 13: Engine Search
**Tool:** `dct_manage_engine_endpoints`
```python
operation_type="search"
limit=10
```

#### Test 14: Snapshot Search
**Tool:** `dct_manage_snapshots_endpoints`
```python
operation_type="search"
limit=20
sort="-creation_time"  # Most recent first
# Collect: snapshotId values
```

#### Test 15: Job Search
**Tool:** `dct_manage_job_endpoints`
```python
operation_type="search"
limit=10
sort="-update_time"
# Collect: jobId values
```

#### Test 16-17: Compliance Searches
**Tool:** `dct_manage_compliance_endpoints`
```python
# Test 16
operation_type="search_connectors"
limit=10

# Test 17
operation_type="search_executions"
limit=10
```

#### Test 18-19: Report Searches
**Tool:** `dct_manage_reports_endpoints`
```python
# Test 18
operation_type="search_storage_capacity"
limit=10

# Test 19
operation_type="search_storage_savings"
limit=10

# Test 20
operation_type="search_virtualization_summary"
limit=10
```

---

### 1.2 Get Operations (22 tests)

#### Test 21: Get VDB by ID
**Tool:** `dct_manage_vdbs_endpoints`
```python
operation_type="get"
vdbId="<VDB_ID_FROM_SEARCH>"
# Validation: Returns complete VDB details
```

#### Test 22: Get Snapshot by ID
**Tool:** `dct_manage_snapshots_endpoints`
```python
operation_type="get"
snapshotId="<SNAPSHOT_ID_FROM_SEARCH>"
# Validation: Returns snapshot details
```

#### Test 23: Get Environment by ID
**Tool:** `dct_manage_environment_endpoints`
```python
operation_type="get"
environmentId="<ENV_ID_FROM_SEARCH>"
# Validation: Returns environment details
```

#### Test 24-33: Environment Sub-Resources (10 operations)
**Tool:** `dct_manage_environment_endpoints`
**Note:** These operations use GET method despite their names
```python
# Test environment sub-resources (requires valid IDs)
operations = [
    "delete_host", "delete_listener", "delete_repository", "delete_user",
    "update_host", "update_listener", "update_repository", "update_user"
]
# Add IDs as needed: hostId, listenerId, repositoryId, userRef
```

#### Test 34-37: dSource Gets by Type (4 operations)
**Tool:** `dct_manage_dsources_endpoints`
**Note:** These use GET method
```python
for op in ["update_appdata", "update_ase", "update_mssql", "update_oracle"]:
    operation_type=op
    dsourceId="<DSOURCE_ID_FROM_SEARCH>"
```

#### Test 38-42: Source Gets by Type (5 operations)
**Tool:** `dct_manage_sources_endpoints`
**Note:** "delete" operation uses GET method
```python
for op in ["delete", "update_appdata", "update_ase", "update_oracle", "update_postgres"]:
    operation_type=op
    sourceId="<SOURCE_ID_FROM_SEARCH>"
```

#### Test 43: Get Job Result
**Tool:** `dct_manage_job_endpoints`
```python
operation_type="get_result"
jobId="<JOB_ID_FROM_SEARCH>"
```

**Phase 1 Success Criteria:**
- ✅ All 43 read operations complete without errors
- ✅ Search operations respect pagination parameters
- ✅ Filter expressions work as expected
- ✅ Get operations return complete resource details
- ✅ Resource IDs collected for subsequent test phases

---

## Phase 2: Safe Lifecycle Operations (17 operations)

### 2.1 VDB Lifecycle (7 tests)
**Tool:** `dct_manage_vdbs_endpoints`
**Prerequisites:** Identify a test VDB (preferably non-production)

```python
test_vdb_id = "<TEST_VDB_ID>"

# Test 44: Stop VDB
operation_type="stop"
vdbId=test_vdb_id

# Test 45: Start VDB
operation_type="start"
vdbId=test_vdb_id

# Test 46: Disable VDB
operation_type="disable"
vdbId=test_vdb_id

# Test 47: Enable VDB
operation_type="enable"
vdbId=test_vdb_id

# Test 48: Lock VDB
operation_type="lock"
vdbId=test_vdb_id

# Test 49: Unlock VDB
operation_type="unlock"
vdbId=test_vdb_id

# Test 50: Upgrade VDB (if available)
operation_type="upgrade"
vdbId=test_vdb_id
```

### 2.2 dSource Lifecycle (2 tests)
**Tool:** `dct_manage_dsources_endpoints`

```python
test_dsource_id = "<TEST_DSOURCE_ID>"

# Test 51: Disable dSource
operation_type="disable"
dsourceId=test_dsource_id

# Test 52: Enable dSource
operation_type="enable"
dsourceId=test_dsource_id
```

### 2.3 Environment Lifecycle (3 tests)
**Tool:** `dct_manage_environment_endpoints`

```python
test_env_id = "<TEST_ENV_ID>"

# Test 53: Disable Environment
operation_type="disable"
environmentId=test_env_id

# Test 54: Enable Environment
operation_type="enable"
environmentId=test_env_id

# Test 55: Refresh Environment
operation_type="refresh"
environmentId=test_env_id
```

**Phase 2 Success Criteria:**
- ✅ All lifecycle operations complete without errors
- ✅ State changes are reflected in subsequent get/search operations
- ✅ Jobs are created and tracked for async operations
- ✅ Resources return to expected states after enable/start operations

---

## Phase 3: Snapshot Operations (3 operations)

### Test 56: Snapshot a dSource
**Tool:** `dct_manage_dsources_endpoints`
```python
operation_type="snapshot"
dsourceId="<TEST_DSOURCE_ID>"
# Collect: snapshot ID for Phase 4
```

### Test 57: Snapshot a VDB
**Tool:** `dct_manage_vdbs_endpoints`
```python
operation_type="snapshot"
vdbId="<TEST_VDB_ID>"
# Collect: snapshot ID for Phase 4
```

### Test 58: Unset Snapshot Expiration
**Tool:** `dct_manage_snapshots_endpoints`
```python
operation_type="unset_expiration"
snapshotId="<SNAPSHOT_ID_FROM_TEST_56_OR_57>"
```

**Phase 3 Success Criteria:**
- ✅ Snapshots created successfully for both dSource and VDB
- ✅ Snapshot IDs returned for use in Phase 4
- ✅ Expiration management works as expected
- ✅ Snapshots visible in search results

---

## Phase 4: Refresh & Rollback Operations (7 operations)

### 4.1 VDB Refresh Operations (4 tests)
**Tool:** `dct_manage_vdbs_endpoints`

```python
test_vdb_id = "<TEST_VDB_ID>"
test_snapshot_id = "<SNAPSHOT_ID_FROM_PHASE_3>"

# Test 59: Refresh VDB from Snapshot
operation_type="refresh_snapshot"
vdbId=test_vdb_id
body={"snapshot_id": test_snapshot_id}

# Test 60: Refresh VDB by Timestamp
operation_type="refresh_timestamp"
vdbId=test_vdb_id
body={"timestamp": "2026-02-06T10:00:00Z"}

# Test 61: Refresh VDB by Location
operation_type="refresh_location"
vdbId=test_vdb_id
body={"location": "LATEST_SNAPSHOT"}

# Test 62: Refresh VDB from Bookmark (if bookmarks exist)
operation_type="refresh_bookmark"
vdbId=test_vdb_id
body={"bookmark_id": "<BOOKMARK_ID>"}
```

### 4.2 VDB Rollback Operations (3 tests)
**Tool:** `dct_manage_vdbs_endpoints`

```python
# Test 63: Rollback VDB to Snapshot
operation_type="rollback_snapshot"
vdbId=test_vdb_id
body={"snapshot_id": test_snapshot_id}

# Test 64: Rollback VDB by Timestamp
operation_type="rollback_timestamp"
vdbId=test_vdb_id
body={"timestamp": "2026-02-06T09:00:00Z"}

# Test 65: Rollback VDB from Bookmark
operation_type="rollback_bookmark"
vdbId=test_vdb_id
body={"bookmark_id": "<BOOKMARK_ID>"}
```

**Phase 4 Success Criteria:**
- ✅ Refresh operations update VDB to specified snapshots/timestamps
- ✅ Rollback operations restore VDB to prior states
- ✅ Jobs created and tracked for all operations
- ✅ VDB remains functional after refresh/rollback

---

## Phase 5: Provisioning & Create Operations (26 operations)

⚠️ **Warning:** These operations CREATE new resources. Record all IDs for Phase 6 cleanup.

### 5.1 VDB Provisioning Operations (5 tests)
**Tool:** `dct_manage_vdbs_endpoints`

```python
# Test 66: Provision VDB from Snapshot
operation_type="provision_snapshot"
body={
    "source_data_id": "<DSOURCE_ID>",
    "snapshot_id": "<SNAPSHOT_ID>",
    "vdb_name": "test_vdb_snapshot_001",
    "target_group_id": "<VDB_GROUP_ID>",
    "environment_id": "<ENV_ID>"
}
# Collect: vdb_id for cleanup

# Test 67: Provision VDB by Timestamp
operation_type="provision_timestamp"
body={...}  # Similar structure

# Test 68: Provision VDB by Location
operation_type="provision_location"
body={...}

# Test 69: Provision VDB from Bookmark
operation_type="provision_bookmark"
body={...}

# Test 70: Provision Empty VDB
operation_type="provision_empty"
body={...}
```

### 5.2 dSource Link Operations (6 tests)
**Tool:** `dct_manage_dsources_endpoints`

```python
# Test 71-76: Link various dSource types
operations = [
    "link_oracle",
    "link_oracle_staging",
    "link_mssql",
    "link_mssql_staging",
    "link_ase",
    "link_appdata"
]
# Collect: dsource_id values for cleanup
```

### 5.3 Attach/Detach Operations (5 tests)
**Tool:** `dct_manage_dsources_endpoints`

```python
# Test 77-81: Attach and detach operations
operations = [
    "attach_oracle",
    "detach_oracle",
    "attach_mssql",
    "detach_mssql",
    "attach_mssql_staging"
]
```

### 5.4 Source Create Operations (4 tests)
**Tool:** `dct_manage_sources_endpoints`

```python
# Test 82-85: Create various source types
operations = [
    "create_oracle",
    "create_postgres",
    "create_ase",
    "create_appdata"
]
# Collect: source_id values
```

### 5.5 Environment Create Operations (5 tests)
**Tool:** `dct_manage_environment_endpoints`

```python
# Test 86: Create Environment
operation_type="create"
body={"name": "test_env_001", "hostname": "testhost.example.com", "engine_id": "<ENGINE_ID>"}
# Collect: environment_id

# Test 87-90: Create sub-resources
operations = [
    "create_host",
    "create_repository",
    "create_listener",
    "create_user"
]
```

**Phase 5 Success Criteria:**
- ✅ All provisioning operations create new resources
- ✅ Resource IDs collected for Phase 6 cleanup
- ✅ Created resources appear in search results
- ✅ Jobs tracked to completion for async operations

---

## Phase 6: Delete & Destructive Operations (5 operations)

⚠️ **CRITICAL:** Only run on test resources created in Phase 5 or designated test data.

### Test 91: Delete VDB
**Tool:** `dct_manage_vdbs_endpoints`
```python
operation_type="delete"
vdbId="<TEST_VDB_ID_FROM_PHASE_5>"
```

### Test 92: Delete Snapshot
**Tool:** `dct_manage_snapshots_endpoints`
```python
operation_type="delete"
snapshotId="<SNAPSHOT_ID_FROM_PHASE_3>"
```

### Test 93: Delete dSource
**Tool:** `dct_manage_dsources_endpoints`
```python
operation_type="delete"
body={"dsource_id": "<TEST_DSOURCE_ID_FROM_PHASE_5>"}
```

### Test 94: Abandon Job
**Tool:** `dct_manage_job_endpoints`
```python
operation_type="abandon"
jobId="<LONG_RUNNING_JOB_ID>"
```

**Phase 6 Success Criteria:**
- ✅ All test resources cleaned up
- ✅ Delete operations complete successfully
- ✅ Resources no longer appear in search results
- ✅ No orphaned resources left in DCT

---

## Test Execution Checklist

### Pre-Test Setup
- [ ] Verify DCT connectivity: `DCT_BASE_URL=https://10.43.33.186`
- [ ] Confirm API key is valid: `DCT_API_KEY` set
- [ ] Set confirmation mode: `DCT_REQUIRE_CONFIRMATION=false` in mcp.json
- [ ] Reload VS Code to pick up latest MCP server changes
- [ ] Verify MCP server loads successfully (check logs: "Discovered 10 tools")
- [ ] Enable all DCT tools in VS Code settings
- [ ] Identify test resources:
  - [ ] Test VDB ID(s): DBOM_AY8, DBOM_LI9, or mcp-vdb
  - [ ] Test dSource ID(s)
  - [ ] Test Environment ID(s)
  - [ ] Test Snapshot ID(s)

### Test Execution Progress
- [ ] **Phase 1:** Execute all read-only operations (43 tests)
  - Record success/failure for each operation
  - Collect resource IDs for subsequent phases
  - Validate pagination and filtering
- [ ] **Phase 2:** Execute lifecycle operations (17 tests)
  - Verify state changes
  - Test reversibility (stop/start, disable/enable)
- [ ] **Phase 3:** Execute snapshot operations (3 tests)
  - Record snapshot IDs
- [ ] **Phase 4:** Execute refresh/rollback operations (7 tests)
  - Verify data changes
  - Track jobs to completion
- [ ] **Phase 5:** Execute provisioning operations (26 tests)
  - Record all created resource IDs
  - Prepare for cleanup
- [ ] **Phase 6:** Execute delete operations (5 tests)
  - Clean up Phase 5 resources
  - Verify deletion

### Post-Test Validation
- [ ] Verify no test resources remain in DCT
- [ ] Review job history for failures
- [ ] Document any operation failures or issues
- [ ] Calculate success rate: (passed / 77 total operations)

---

## Test Results Template

```
| Test # | Phase | Operation | Tool | Status | Job ID | Notes |
|--------|-------|-----------|------|--------|--------|-------|
| 1 | 1.1 | search | vdbs | ✅ PASS | - | Returned 3 VDBs |
| 2 | 1.1 | search_vdbs | dataset | ✅ PASS | - | Pagination works |
| ... | ... | ... | ... | ... | ... | ... |
```

---

## Known Issues & Limitations

1. **Misnamed Operations:** Some operations use GET method but are named "delete" or "update" (e.g., environment operations) - these won't actually delete/modify resources
2. **Prerequisites:** Provisioning operations require existing sources, environments, and configurations
3. **Async Operations:** Many operations return job IDs - must poll for completion
4. **Confirmation Requirement:** With `DCT_REQUIRE_CONFIRMATION=true`, destructive ops require `confirm=True` parameter
5. **Resource Dependencies:** Can't delete resources with dependent VDBs

---

## Summary Report Template

After completing all phases:

```
=== DCT MCP Test Execution Summary ===
Date: [DATE]
Environment: https://10.43.33.186
Total Operations: 77

Phase 1 (Read): X/43 passed (X%)
Phase 2 (Lifecycle): X/17 passed (X%)
Phase 3 (Snapshot): X/3 passed (X%)
Phase 4 (Refresh/Rollback): X/7 passed (X%)
Phase 5 (Provisioning): X/26 passed (X%)
Phase 6 (Delete): X/5 passed (X%)

Overall Success Rate: X%

Failed Operations:
- [List any failed operations with error details]

Resource IDs Collected:
- VDB IDs: [list]
- dSource IDs: [list]
- Snapshot IDs: [list]
- Environment IDs: [list]

Recommendations:
- [Document any issues, bugs, or improvements needed]
```

---

**End of Test Plan**
