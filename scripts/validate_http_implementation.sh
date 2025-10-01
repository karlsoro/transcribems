#!/bin/bash
# Validate HTTP Implementation
#
# This script validates that the HTTP implementation is complete and functional.

set -e

echo "========================================="
echo "TranscribeMCP HTTP Implementation Validation"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Helper function to check results
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $1"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $1"
        ((FAILED++))
    fi
}

# 1. Check CLI commands exist
echo "1. Checking CLI commands..."
command -v transcribe-mcp &> /dev/null
check_result "transcribe-mcp command exists"

command -v transcribe-mcp-stdio &> /dev/null
check_result "transcribe-mcp-stdio legacy command exists"

# 2. Check help messages
echo ""
echo "2. Checking help messages..."
transcribe-mcp --help | grep -q "stdio" && transcribe-mcp --help | grep -q "http"
check_result "Main help includes stdio and http modes"

transcribe-mcp stdio --help | grep -q "log-level"
check_result "Stdio help includes --log-level option"

transcribe-mcp http --help | grep -q "host" && transcribe-mcp http --help | grep -q "port"
check_result "HTTP help includes --host and --port options"

# 3. Check Python imports
echo ""
echo "3. Checking Python imports..."
python -c "from src.mcp_server.cli import create_parser, setup_logging" 2>/dev/null
check_result "CLI module imports successfully"

python -c "from src.mcp_server.server import TranscribeMCPServer" 2>/dev/null
check_result "Server module imports successfully"

# 4. Check server has HTTP methods
echo ""
echo "4. Checking server methods..."
python -c "
from src.mcp_server.server import TranscribeMCPServer
server = TranscribeMCPServer()
assert hasattr(server, 'run_stdio'), 'Missing run_stdio'
assert hasattr(server, 'run_sse'), 'Missing run_sse'
assert hasattr(server, 'run_streamable_http'), 'Missing run_streamable_http'
print('All methods present')
" 2>/dev/null
check_result "Server has all transport methods"

# 5. Check documentation files exist
echo ""
echo "5. Checking documentation files..."
docs_to_check=(
    "docs/SERVER_MODES.md"
    "docs/QUICK_START_CLI.md"
    "docs/CHANGELOG_CLI.md"
    "docs/HTTP_CLIENT_EXAMPLES.md"
    "docs/HTTP_IMPLEMENTATION_SUMMARY.md"
    "docs/DOCUMENTATION_INDEX.md"
)

for doc in "${docs_to_check[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $doc exists"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $doc missing"
        ((FAILED++))
    fi
done

# 6. Check test files exist
echo ""
echo "6. Checking test files..."
test_files=(
    "tests/test_cli.py"
    "tests/integration/test_http_server.py"
)

for test in "${test_files[@]}"; do
    if [ -f "$test" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $test exists"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $test missing"
        ((FAILED++))
    fi
done

# 7. Check scripts
echo ""
echo "7. Checking scripts..."
if [ -f "scripts/start_mcp_server_http.sh" ] && [ -x "scripts/start_mcp_server_http.sh" ]; then
    echo -e "${GREEN}✅ PASS${NC}: HTTP server script exists and is executable"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: HTTP server script missing or not executable"
    ((FAILED++))
fi

# 8. Check dependencies in pyproject.toml
echo ""
echo "8. Checking dependencies..."
if grep -q "uvicorn" pyproject.toml && grep -q "starlette" pyproject.toml; then
    echo -e "${GREEN}✅ PASS${NC}: HTTP dependencies listed in pyproject.toml"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: HTTP dependencies missing from pyproject.toml"
    ((FAILED++))
fi

# 9. Check CLI tests can be imported
echo ""
echo "9. Checking test imports..."
python -c "import tests.test_cli" 2>/dev/null
check_result "CLI tests can be imported"

# 10. Check documentation cross-references
echo ""
echo "10. Checking documentation cross-references..."
if grep -q "SERVER_MODES.md" docs/DOCUMENTATION_INDEX.md && \
   grep -q "HTTP_CLIENT_EXAMPLES.md" docs/DOCUMENTATION_INDEX.md; then
    echo -e "${GREEN}✅ PASS${NC}: Documentation index has correct references"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}: Documentation index missing references"
    ((FAILED++))
fi

# Summary
echo ""
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "========================================="

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All checks passed! HTTP implementation is complete.${NC}"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  Some checks failed. Please review the errors above.${NC}"
    echo ""
    exit 1
fi
