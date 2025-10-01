# Project Rename: transcribe_mcp → transcribe_mcp

**Date**: 2025-10-01
**Status**: IN PROGRESS
**Backup Branch**: `backup-before-rename-20251001-054433`

## Objective

Rename the project from `transcribe_mcp` to `transcribe_mcp` to match naming standards for MCP components.

## Pre-Rename State

### Current Configuration
- **Package Name**: `transcribe_mcp`
- **Virtual Environment**: `transcribe_mcp_env/`
- **MCP Server Name**: `transcribe_mcp`
- **Repository**: `https://github.com/karlsoro/transcribe_mcp`
- **Last Commit**: aa7867a (Merge branch '002-adjust-the-current')

### Backup Created
- **Branch**: `backup-before-rename-20251001-054433`
- **Location**: Local (not pushed to remote)
- **Restoration**: `git checkout backup-before-rename-20251001-054433`

## Rename Scope

### Files to Modify
1. **Configuration Files**
   - `pyproject.toml` - package name, project metadata
   - `setup.cfg` - package name
   - `.gitignore` - virtual environment name
   - `CLAUDE.md` - project references

2. **Python Package**
   - Virtual environment: `transcribe_mcp_env/` → `transcribe_mcp_env/`
   - Import statements across all Python files
   - Module references

3. **Documentation**
   - `README.md`
   - `docs/guides/MCP_CONNECTION_GUIDE.md`
   - `docs/guides/MCP_QUICK_REFERENCE.md`
   - `docs/guides/MCP_SERVER_READY.md`
   - `docs/INTEGRATION_EXAMPLES.md`
   - All other documentation files

4. **Scripts**
   - `scripts/start_mcp_server.sh`
   - `scripts/test_mcp_connection.py`
   - All validation and test scripts

5. **MCP Server**
   - Server name in `src/mcp_server/fastmcp_server.py`
   - Server name in `src/mcp_server/server.py`
   - Tool implementations

## Risk Assessment

### High Risk Areas
- ✅ **Backup Created**: Local backup branch exists
- ⚠️ **Virtual Environment**: Will need recreation
- ⚠️ **Import Statements**: Breaking change if missed
- ⚠️ **MCP Configuration**: Client configs will need updating

### Mitigation
1. Create comprehensive backup (DONE)
2. Search and document all occurrences
3. Make changes systematically
4. Test thoroughly with evidence
5. Document rollback procedure

## Rollback Procedure

If issues occur:

```bash
# 1. Return to backup branch
git checkout backup-before-rename-20251001-054433

# 2. Recreate main from backup
git branch -D main
git checkout -b main

# 3. Force push to remote (CAUTION)
git push origin main --force

# 4. Cleanup
git branch -d backup-before-rename-20251001-054433
```

## Testing Requirements

### Must Pass Before Completion
1. ✅ MCP server starts successfully
2. ✅ MCP connection test passes
3. ✅ Actual transcription completes
4. ✅ All imports resolve correctly
5. ✅ Documentation is consistent
6. ✅ Evidence files generated

### Test Evidence Required
- MCP server startup logs
- Connection test output
- Transcription result files
- Import verification results
- Documentation consistency check

## Progress Tracking

- [x] Backup branch created
- [ ] Current state documented
- [ ] All occurrences found
- [ ] Python package renamed
- [ ] Configuration files updated
- [ ] Import statements updated
- [ ] Virtual environment updated
- [ ] Documentation updated
- [ ] MCP server tested
- [ ] Transcription tested
- [ ] Evidence generated
- [ ] Changes committed
- [ ] Changes pushed to main

## Notes

This is a breaking change that will require:
- Updating any external references
- Recreating virtual environment
- Updating MCP client configurations
- Reinstalling the package

---

**Last Updated**: 2025-10-01
**Status**: Documenting current state
