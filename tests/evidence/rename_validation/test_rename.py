#!/usr/bin/env python3
"""
Comprehensive Post-Rename Validation Test
Tests all aspects of the project after renaming from transcribems to transcribe_mcp
"""

import sys
import os
from pathlib import Path
import json
import subprocess
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

class RenameValidationTest:
    """Comprehensive validation tests for the rename operation."""

    def __init__(self):
        self.evidence_dir = Path(__file__).parent
        self.test_results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   {details}")

    def test_imports(self):
        """Test that all imports work correctly."""
        print("\n" + "="*70)
        print("TEST 1: Import Validation")
        print("="*70)

        try:
            # Test core imports
            from src.core.config import settings
            self.log_result("Import: src.core.config", True, "Settings loaded successfully")

            from src.core.logging import setup_logging
            self.log_result("Import: src.core.logging", True, "Logging module loaded")

            from src.services.transcription_service import TranscriptionService
            self.log_result("Import: TranscriptionService", True, "Service class loaded")

            from src.mcp_server.server import main as mcp_main
            self.log_result("Import: MCP server", True, "MCP server module loaded")

            # Test MCP FastMCP server
            from src.mcp_server.fastmcp_server import mcp
            self.log_result("Import: FastMCP server", True, "FastMCP server loaded")

            return True
        except Exception as e:
            self.log_result("Import validation", False, str(e))
            return False

    def test_mcp_server_initialization(self):
        """Test MCP server can be initialized."""
        print("\n" + "="*70)
        print("TEST 2: MCP Server Initialization")
        print("="*70)

        try:
            from src.mcp_server.fastmcp_server import mcp

            # Check that MCP tools are registered
            tools_count = len(mcp.list_tools())
            self.log_result(
                "MCP tools registration",
                tools_count >= 6,
                f"Found {tools_count} tools registered"
            )

            # Save tool list
            tools_file = self.evidence_dir / f"mcp_tools_{self.timestamp}.json"
            tools = mcp.list_tools()
            with open(tools_file, 'w') as f:
                json.dump(tools, f, indent=2)

            self.log_result(
                "MCP tools list saved",
                True,
                f"Saved to {tools_file.name}"
            )

            return True
        except Exception as e:
            self.log_result("MCP server initialization", False, str(e))
            return False

    def test_project_structure(self):
        """Test that project structure is correct."""
        print("\n" + "="*70)
        print("TEST 3: Project Structure")
        print("="*70)

        required_paths = [
            "src/core/config.py",
            "src/mcp_server/server.py",
            "src/mcp_server/fastmcp_server.py",
            "src/services/transcription_service.py",
            "tests/integration",
            "docs/guides",
            "scripts/utils",
            "transcribe_mcp_env",
            "pyproject.toml"
        ]

        all_exist = True
        for path_str in required_paths:
            path = project_root / path_str
            exists = path.exists()
            all_exist = all_exist and exists
            self.log_result(f"Path exists: {path_str}", exists)

        return all_exist

    def test_configuration(self):
        """Test that configuration is correctly renamed."""
        print("\n" + "="*70)
        print("TEST 4: Configuration Validation")
        print("="*70)

        try:
            from src.core.config import settings

            # Check important settings
            checks = [
                ("Settings object exists", settings is not None),
                ("HF token configured", hasattr(settings, 'huggingface_token')),
                ("Model name configured", hasattr(settings, 'default_model')),
            ]

            all_passed = True
            for check_name, check_result in checks:
                self.log_result(check_name, check_result)
                all_passed = all_passed and check_result

            return all_passed
        except Exception as e:
            self.log_result("Configuration validation", False, str(e))
            return False

    def test_no_old_references(self):
        """Test that no old 'transcribems' references remain in key files."""
        print("\n" + "="*70)
        print("TEST 5: Old Reference Check")
        print("="*70)

        # Check key Python files
        key_files = [
            "src/mcp_server/server.py",
            "src/mcp_server/fastmcp_server.py",
            "src/core/config.py",
        ]

        all_clean = True
        for file_path in key_files:
            full_path = project_root / file_path
            if full_path.exists():
                content = full_path.read_text()
                has_old_ref = 'transcribems' in content.lower() and 'transcribems_env' not in content
                clean = not has_old_ref
                all_clean = all_clean and clean
                self.log_result(
                    f"No old refs in {file_path}",
                    clean,
                    "File is clean" if clean else "Contains old references"
                )

        return all_clean

    def save_results(self):
        """Save test results to JSON file."""
        results_file = self.evidence_dir / f"validation_results_{self.timestamp}.json"

        summary = {
            "timestamp": self.timestamp,
            "total_tests": len(self.test_results),
            "passed": sum(1 for r in self.test_results if r["passed"]),
            "failed": sum(1 for r in self.test_results if not r["passed"]),
            "tests": self.test_results
        }

        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print("\n" + "="*70)
        print("TEST RESULTS SUMMARY")
        print("="*70)
        print(f"Total tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Results saved to: {results_file}")

        return summary['failed'] == 0

def main():
    """Run all validation tests."""
    print("="*70)
    print("TranscribeMCP Rename Validation Tests")
    print("="*70)
    print(f"Project root: {project_root}")
    print()

    validator = RenameValidationTest()

    # Run all tests
    tests = [
        validator.test_imports,
        validator.test_mcp_server_initialization,
        validator.test_project_structure,
        validator.test_configuration,
        validator.test_no_old_references,
    ]

    all_passed = True
    for test in tests:
        try:
            passed = test()
            all_passed = all_passed and passed
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            all_passed = False

    # Save results
    success = validator.save_results()

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
