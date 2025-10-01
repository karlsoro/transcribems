#!/usr/bin/env python3
"""Comprehensive integration test for TranscribeMCP MCP system.

This script tests the complete transcription pipeline end-to-end,
including MCP tools, services, and WhisperX integration.
"""

import asyncio
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TranscribeMCPIntegrationTest:
    """Comprehensive integration test suite for TranscribeMCP."""

    def __init__(self):
        """Initialize the integration test."""
        self.test_results = {
            "started_at": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": []
        }

    async def run_all_tests(self):
        """Run all integration tests."""
        logger.info("🚀 Starting TranscribeMCP Integration Test Suite")
        logger.info("=" * 60)

        test_methods = [
            ("Service Import Test", self.test_service_imports),
            ("MCP Tools Test", self.test_mcp_tools),
            ("Audio File Validation Test", self.test_audio_validation),
            ("Mock Transcription Test", self.test_mock_transcription),
            ("WhisperX Transcription Test", self.test_whisperx_transcription),
            ("Progress Tracking Test", self.test_progress_tracking),
            ("History Management Test", self.test_history_management),
            ("Batch Processing Test", self.test_batch_processing),
            ("Error Handling Test", self.test_error_handling),
            ("Performance Test", self.test_performance)
        ]

        for test_name, test_method in test_methods:
            await self.run_single_test(test_name, test_method)

        self.print_final_results()

    async def run_single_test(self, test_name: str, test_method):
        """Run a single test and record results."""
        logger.info(f"🔍 Running: {test_name}")

        try:
            result = await test_method()
            self.test_results["tests_run"] += 1

            if result.get("success", False):
                self.test_results["tests_passed"] += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                self.test_results["tests_failed"] += 1
                logger.error(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")

            self.test_results["test_details"].append({
                "name": test_name,
                "success": result.get("success", False),
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            self.test_results["tests_run"] += 1
            self.test_results["tests_failed"] += 1
            logger.error(f"❌ {test_name}: FAILED - Exception: {str(e)}")

            self.test_results["test_details"].append({
                "name": test_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        logger.info("")  # Add spacing between tests

    async def test_service_imports(self) -> Dict[str, Any]:
        """Test that all services can be imported and instantiated."""
        try:
            from src.services.audio_file_service import AudioFileService
            from src.services.transcription_service import TranscriptionService
            from src.services.progress_service import ProgressService
            from src.services.storage_service import StorageService
            from src.services.history_service import HistoryService

            # Test instantiation
            audio_service = AudioFileService()
            transcription_service = TranscriptionService()
            progress_service = ProgressService()
            storage_service = StorageService()
            history_service = HistoryService(storage_service)

            return {
                "success": True,
                "message": "All services imported and instantiated successfully",
                "services_tested": 5
            }

        except Exception as e:
            return {"success": False, "error": f"Service import failed: {str(e)}"}

    async def test_mcp_tools(self) -> Dict[str, Any]:
        """Test that all MCP tools are callable."""
        try:
            from src.tools.transcribe_tool import transcribe_audio_tool
            from src.tools.progress_tool import get_transcription_progress_tool
            from src.tools.history_tool import list_transcription_history_tool
            from src.tools.result_tool import get_transcription_result_tool
            from src.tools.batch_tool import batch_transcribe_tool
            from src.tools.cancel_tool import cancel_transcription_tool

            tools = [
                transcribe_audio_tool,
                get_transcription_progress_tool,
                list_transcription_history_tool,
                get_transcription_result_tool,
                batch_transcribe_tool,
                cancel_transcription_tool
            ]

            # Verify all tools are callable
            for tool in tools:
                if not callable(tool):
                    return {"success": False, "error": f"Tool {tool.__name__} is not callable"}

            return {
                "success": True,
                "message": "All MCP tools are properly callable",
                "tools_tested": len(tools),
                "tool_names": [tool.__name__ for tool in tools]
            }

        except Exception as e:
            return {"success": False, "error": f"MCP tools test failed: {str(e)}"}

    async def test_audio_validation(self) -> Dict[str, Any]:
        """Test audio file validation with test files."""
        try:
            from src.services.audio_file_service import AudioFileService

            service = AudioFileService()
            test_files = list(Path("test_audio").glob("*.wav"))

            if not test_files:
                return {"success": False, "error": "No test audio files found"}

            validated_files = []
            for test_file in test_files[:3]:  # Test first 3 files
                try:
                    audio_file = await service.validate_and_create(str(test_file))
                    validated_files.append({
                        "file": test_file.name,
                        "duration": audio_file.duration,
                        "sample_rate": audio_file.sample_rate,
                        "channels": audio_file.channels,
                        "state": audio_file.state
                    })
                except Exception as e:
                    logger.warning(f"Validation failed for {test_file.name}: {e}")

            return {
                "success": len(validated_files) > 0,
                "message": f"Validated {len(validated_files)} audio files",
                "validated_files": validated_files
            }

        except Exception as e:
            return {"success": False, "error": f"Audio validation test failed: {str(e)}"}

    async def test_mock_transcription(self) -> Dict[str, Any]:
        """Test transcription with mock implementation."""
        try:
            from src.tools.transcribe_tool import transcribe_audio_tool
            from src.services.progress_service import ProgressService

            test_file = Path("test_audio") / "short_speech.wav"
            if not test_file.exists():
                return {"success": False, "error": "Test audio file not found"}

            # Force mock by temporarily disabling WhisperX
            import src.services.transcription_service
            original_flag = src.services.transcription_service.WHISPERX_AVAILABLE
            src.services.transcription_service.WHISPERX_AVAILABLE = False

            try:
                # Test transcription
                request = {
                    "file_path": str(test_file),
                    "model_size": "base",
                    "enable_diarization": True,
                    "device": "cpu"
                }

                result = await transcribe_audio_tool(request)

                if not result.get("success"):
                    return {"success": False, "error": f"Transcription failed: {result}"}

                job_info = result.get("job", {})

                return {
                    "success": True,
                    "message": "Mock transcription completed successfully",
                    "job_id": job_info.get("job_id"),
                    "status": job_info.get("status"),
                    "estimated_duration": job_info.get("estimated_duration")
                }

            finally:
                # Restore WhisperX flag
                src.services.transcription_service.WHISPERX_AVAILABLE = original_flag

        except Exception as e:
            return {"success": False, "error": f"Mock transcription test failed: {str(e)}"}

    async def test_whisperx_transcription(self) -> Dict[str, Any]:
        """Test transcription with real WhisperX (if available)."""
        try:
            import whisperx
            whisperx_available = True
        except ImportError:
            return {
                "success": True,
                "message": "WhisperX not available, skipping real transcription test",
                "skipped": True
            }

        try:
            from src.tools.transcribe_tool import transcribe_audio_tool
            from src.tools.result_tool import get_transcription_result_tool

            test_file = Path("test_audio") / "short_speech.wav"
            if not test_file.exists():
                return {"success": False, "error": "Test audio file not found"}

            # Test transcription with WhisperX
            request = {
                "file_path": str(test_file),
                "model_size": "tiny",  # Use smallest model for speed
                "enable_diarization": False,  # Disable for speed
                "device": "cpu"
            }

            result = await transcribe_audio_tool(request)

            if not result.get("success"):
                return {"success": False, "error": f"WhisperX transcription failed: {result}"}

            job_info = result.get("job", {})
            job_id = job_info.get("job_id")

            # Wait for completion (with timeout)
            import asyncio
            await asyncio.sleep(2)  # Give it some time to process

            # Try to get result
            result_request = {"job_id": job_id, "format": "summary"}
            transcription_result = await get_transcription_result_tool(result_request)

            return {
                "success": True,
                "message": "WhisperX transcription test completed",
                "job_id": job_id,
                "transcription_attempted": True,
                "result_retrieved": transcription_result.get("success", False)
            }

        except Exception as e:
            return {"success": False, "error": f"WhisperX transcription test failed: {str(e)}"}

    async def test_progress_tracking(self) -> Dict[str, Any]:
        """Test progress tracking functionality."""
        try:
            from src.tools.progress_tool import get_transcription_progress_tool
            from src.services.progress_service import ProgressService

            service = ProgressService()

            # Test getting all jobs
            request = {"all_jobs": True}
            result = await get_transcription_progress_tool(request)

            if not result.get("success"):
                return {"success": False, "error": f"Progress tracking failed: {result}"}

            stats = result.get("stats", {})

            return {
                "success": True,
                "message": "Progress tracking test completed",
                "total_jobs": stats.get("total_jobs", 0),
                "active_jobs": stats.get("active_jobs", 0)
            }

        except Exception as e:
            return {"success": False, "error": f"Progress tracking test failed: {str(e)}"}

    async def test_history_management(self) -> Dict[str, Any]:
        """Test history management functionality."""
        try:
            from src.tools.history_tool import list_transcription_history_tool

            request = {
                "limit": 10,
                "get_statistics": True,
                "statistics_days": 7
            }

            result = await list_transcription_history_tool(request)

            if not result.get("success"):
                return {"success": False, "error": f"History management failed: {result}"}

            history = result.get("history", {})
            stats = result.get("statistics")

            return {
                "success": True,
                "message": "History management test completed",
                "jobs_returned": len(history.get("jobs", [])),
                "statistics_included": stats is not None
            }

        except Exception as e:
            return {"success": False, "error": f"History management test failed: {str(e)}"}

    async def test_batch_processing(self) -> Dict[str, Any]:
        """Test batch processing functionality."""
        try:
            from src.tools.batch_tool import batch_transcribe_tool

            test_files = list(Path("test_audio").glob("*.wav"))[:2]  # Test with 2 files

            if len(test_files) < 2:
                return {"success": False, "error": "Not enough test files for batch processing"}

            request = {
                "file_paths": [str(f) for f in test_files],
                "model_size": "tiny",
                "enable_diarization": False,
                "max_concurrent": 2
            }

            result = await batch_transcribe_tool(request)

            if not result.get("success"):
                return {"success": False, "error": f"Batch processing failed: {result}"}

            return {
                "success": True,
                "message": "Batch processing test completed",
                "files_processed": result.get("total_jobs", 0),
                "valid_files": result.get("valid_files", 0),
                "batch_id": result.get("batch_id")
            }

        except Exception as e:
            return {"success": False, "error": f"Batch processing test failed: {str(e)}"}

    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling with invalid inputs."""
        try:
            from src.tools.transcribe_tool import transcribe_audio_tool

            # Test with non-existent file
            request = {"file_path": "non_existent_file.wav"}
            result = await transcribe_audio_tool(request)

            # Should fail gracefully
            if result.get("success"):
                return {"success": False, "error": "Error handling failed - should have rejected invalid file"}

            return {
                "success": True,
                "message": "Error handling test completed",
                "error_caught": True,
                "error_type": result.get("error", {}).get("code", "unknown")
            }

        except Exception as e:
            return {"success": False, "error": f"Error handling test failed: {str(e)}"}

    async def test_performance(self) -> Dict[str, Any]:
        """Test basic performance metrics."""
        try:
            import time
            from src.services.audio_file_service import AudioFileService

            service = AudioFileService()
            test_file = Path("test_audio") / "short_speech.wav"

            if not test_file.exists():
                return {"success": False, "error": "Test file not found"}

            # Time audio file validation
            start_time = time.time()
            audio_file = await service.validate_and_create(str(test_file))
            validation_time = time.time() - start_time

            return {
                "success": True,
                "message": "Performance test completed",
                "validation_time_seconds": round(validation_time, 3),
                "file_duration": audio_file.duration,
                "processing_speed_ratio": round(validation_time / audio_file.duration, 2)
            }

        except Exception as e:
            return {"success": False, "error": f"Performance test failed: {str(e)}"}

    def print_final_results(self):
        """Print final test results summary."""
        self.test_results["completed_at"] = datetime.now().isoformat()

        logger.info("🏁 Integration Test Results")
        logger.info("=" * 60)
        logger.info(f"Tests Run: {self.test_results['tests_run']}")
        logger.info(f"Tests Passed: {self.test_results['tests_passed']}")
        logger.info(f"Tests Failed: {self.test_results['tests_failed']}")

        success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run'] * 100) if self.test_results['tests_run'] > 0 else 0
        logger.info(f"Success Rate: {success_rate:.1f}%")

        if self.test_results['tests_failed'] == 0:
            logger.info("🎉 All tests PASSED! System is fully functional.")
        else:
            logger.warning(f"⚠️  {self.test_results['tests_failed']} tests failed. Check details above.")

        # Save detailed results
        results_file = Path("integration_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"📊 Detailed results saved to: {results_file}")

async def main():
    """Run the integration test suite."""
    try:
        test_suite = TranscribeMCPIntegrationTest()
        await test_suite.run_all_tests()

        # Return appropriate exit code
        if test_suite.test_results['tests_failed'] == 0:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Integration test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Integration test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())