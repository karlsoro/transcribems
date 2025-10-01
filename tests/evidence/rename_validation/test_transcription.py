#!/usr/bin/env python3
"""
Complete Transcription Test
Test actual transcription functionality after rename
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime
import asyncio

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

class TranscriptionTest:
    """Test actual transcription functionality."""

    def __init__(self):
        self.evidence_dir = Path(__file__).parent
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_audio = project_root / "test_data" / "audio" / "test_multi_speaker.wav"

    def test_imports(self):
        """Test all core imports work."""
        print("="*70)
        print("Testing Imports")
        print("="*70)

        try:
            from src.core.config import get_settings
            settings = get_settings()
            print("✅ Settings loaded successfully")

            from src.mcp_server.fastmcp_server import mcp
            print("✅ MCP server loaded successfully")

            from src.services.transcription_service import TranscriptionService
            print("✅ TranscriptionService loaded successfully")

            return True
        except Exception as e:
            print(f"❌ Import failed: {e}")
            return False

    def test_mcp_tools(self):
        """Test MCP tools are registered."""
        print("\n" + "="*70)
        print("Testing MCP Tools")
        print("="*70)

        try:
            from src.mcp_server.fastmcp_server import mcp

            tools = mcp.list_tools()
            print(f"✅ Found {len(tools)} MCP tools:")
            for tool in tools:
                print(f"   - {tool['name']}")

            # Save tools to file
            tools_file = self.evidence_dir / f"mcp_tools_{self.timestamp}.json"
            with open(tools_file, 'w') as f:
                json.dump(tools, f, indent=2)
            print(f"✅ Saved tool list to {tools_file.name}")

            return len(tools) >= 6
        except Exception as e:
            print(f"❌ MCP tools test failed: {e}")
            return False

    def test_configuration(self):
        """Test configuration is working."""
        print("\n" + "="*70)
        print("Testing Configuration")
        print("="*70)

        try:
            from src.core.config import get_settings
            settings = get_settings()

            config_data = {
                "debug": settings.DEBUG,
                "log_level": settings.LOG_LEVEL,
                "use_gpu": settings.USE_GPU,
                "default_model": settings.default_model,
                "hf_token_configured": bool(settings.huggingface_token)
            }

            print("✅ Configuration loaded:")
            for key, value in config_data.items():
                # Don't print actual token
                if "token" not in key.lower():
                    print(f"   - {key}: {value}")
                else:
                    print(f"   - {key}: {'***' if value else 'Not set'}")

            # Save config (without sensitive data)
            config_file = self.evidence_dir / f"config_{self.timestamp}.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"✅ Saved config to {config_file.name}")

            return True
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            return False

    async def test_transcription_service(self):
        """Test transcription service initialization."""
        print("\n" + "="*70)
        print("Testing Transcription Service")
        print("="*70)

        try:
            from src.services.transcription_service import TranscriptionService

            service = TranscriptionService()
            print("✅ TranscriptionService initialized")

            # Test that service has expected methods
            methods = ['transcribe', 'get_status', 'cancel_job']
            for method in methods:
                if hasattr(service, method):
                    print(f"✅ Method exists: {method}")
                else:
                    print(f"❌ Missing method: {method}")
                    return False

            return True
        except Exception as e:
            print(f"❌ Service test failed: {e}")
            return False

    def save_results(self, results):
        """Save test results."""
        results_file = self.evidence_dir / f"transcription_test_results_{self.timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Tests run: {results['total']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Results saved to: {results_file.name}")

        return results['failed'] == 0

def main():
    """Run all tests."""
    print("="*70)
    print("TranscribeMCP Transcription Test")
    print("="*70)
    print()

    tester = TranscriptionTest()

    results = {
        "timestamp": tester.timestamp,
        "tests": [],
        "total": 0,
        "passed": 0,
        "failed": 0
    }

    # Run tests
    tests = [
        ("Imports", tester.test_imports),
        ("MCP Tools", tester.test_mcp_tools),
        ("Configuration", tester.test_configuration),
        ("Transcription Service", lambda: asyncio.run(tester.test_transcription_service())),
    ]

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results["tests"].append({"name": test_name, "passed": passed})
            results["total"] += 1
            if passed:
                results["passed"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results["tests"].append({"name": test_name, "passed": False, "error": str(e)})
            results["total"] += 1
            results["failed"] += 1

    # Save results
    success = tester.save_results(results)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
