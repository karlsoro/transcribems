#!/usr/bin/env python3
"""Performance benchmarking suite for TranscribeMCP MCP server.

This benchmark measures system performance across different scenarios
and provides detailed performance analysis for production planning.
"""

import asyncio
import time
import statistics
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TranscribeMCPBenchmark:
    """Comprehensive performance benchmarking for TranscribeMCP."""

    def __init__(self):
        """Initialize benchmark suite."""
        self.results = {
            "benchmark_started": datetime.now().isoformat(),
            "system_info": {},
            "benchmarks": [],
            "summary": {}
        }

    async def run_benchmarks(self):
        """Run all performance benchmarks."""
        logger.info("🚀 Starting TranscribeMCP Performance Benchmark Suite")
        logger.info("=" * 60)

        benchmarks = [
            ("Audio File Validation", self.benchmark_audio_validation),
            ("Memory Usage", self.benchmark_memory_usage),
            ("Concurrent Processing", self.benchmark_concurrent_processing),
            ("Batch Processing Scalability", self.benchmark_batch_scalability),
            ("Service Import Times", self.benchmark_service_imports),
            ("MCP Tool Response Times", self.benchmark_mcp_tools),
            ("Storage Operations", self.benchmark_storage_operations)
        ]

        for benchmark_name, benchmark_func in benchmarks:
            logger.info(f"\n📊 {benchmark_name}")
            logger.info("-" * 40)

            start_time = time.time()
            try:
                result = await benchmark_func()
                duration = time.time() - start_time

                result["benchmark_duration"] = duration
                result["success"] = True

                self.results["benchmarks"].append({
                    "name": benchmark_name,
                    "duration": duration,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })

                logger.info(f"✅ Completed in {duration:.3f}s")

            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"❌ Failed: {e}")

                self.results["benchmarks"].append({
                    "name": benchmark_name,
                    "duration": duration,
                    "error": str(e),
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                })

        await self.generate_performance_report()

    async def benchmark_audio_validation(self) -> Dict[str, Any]:
        """Benchmark audio file validation performance."""
        from src.services.audio_file_service import AudioFileService

        service = AudioFileService()
        test_files = list(Path("test_audio").glob("*.wav"))

        if not test_files:
            return {"error": "No test files available"}

        validation_times = []
        file_sizes = []
        durations = []

        for test_file in test_files:
            # Single file validation benchmark
            times = []
            for _ in range(5):  # 5 iterations per file
                start = time.time()
                try:
                    audio_file = await service.validate_and_create(str(test_file))
                    elapsed = time.time() - start
                    times.append(elapsed)

                    if len(durations) < len(test_files):
                        durations.append(audio_file.duration or 0)
                        file_sizes.append(audio_file.file_size)
                except Exception:
                    continue

            if times:
                validation_times.extend(times)

        if not validation_times:
            return {"error": "No successful validations"}

        avg_validation_time = statistics.mean(validation_times)
        avg_file_size = statistics.mean(file_sizes) if file_sizes else 0
        avg_duration = statistics.mean(durations) if durations else 0

        return {
            "files_tested": len(test_files),
            "total_validations": len(validation_times),
            "average_validation_time": avg_validation_time,
            "min_validation_time": min(validation_times),
            "max_validation_time": max(validation_times),
            "std_dev": statistics.stdev(validation_times) if len(validation_times) > 1 else 0,
            "average_file_size_mb": avg_file_size / (1024 * 1024),
            "average_audio_duration": avg_duration,
            "processing_speed_ratio": avg_validation_time / avg_duration if avg_duration else 0,
            "files_per_second": 1 / avg_validation_time if avg_validation_time else 0
        }

    async def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Benchmark memory usage patterns."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Memory usage during service imports
        memory_before_imports = process.memory_info().rss

        from src.services.audio_file_service import AudioFileService
        from src.services.transcription_service import TranscriptionService
        from src.services.progress_service import ProgressService
        from src.services.storage_service import StorageService
        from src.services.history_service import HistoryService

        memory_after_imports = process.memory_info().rss

        # Memory usage during service instantiation
        services = [
            AudioFileService(),
            TranscriptionService(),
            ProgressService(),
            StorageService(),
            HistoryService(StorageService())
        ]

        memory_after_instantiation = process.memory_info().rss

        # Memory usage during file processing
        if Path("test_audio").exists():
            test_files = list(Path("test_audio").glob("*.wav"))[:3]

            for test_file in test_files:
                try:
                    await services[0].validate_and_create(str(test_file))
                except Exception:
                    continue

        final_memory = process.memory_info().rss

        return {
            "initial_memory_mb": initial_memory / (1024 * 1024),
            "memory_after_imports_mb": memory_after_imports / (1024 * 1024),
            "memory_after_instantiation_mb": memory_after_instantiation / (1024 * 1024),
            "final_memory_mb": final_memory / (1024 * 1024),
            "import_overhead_mb": (memory_after_imports - memory_before_imports) / (1024 * 1024),
            "instantiation_overhead_mb": (memory_after_instantiation - memory_after_imports) / (1024 * 1024),
            "processing_overhead_mb": (final_memory - memory_after_instantiation) / (1024 * 1024),
            "total_memory_increase_mb": (final_memory - initial_memory) / (1024 * 1024)
        }

    async def benchmark_concurrent_processing(self) -> Dict[str, Any]:
        """Benchmark concurrent audio file processing."""
        from src.services.audio_file_service import AudioFileService

        service = AudioFileService()
        test_files = list(Path("test_audio").glob("*.wav"))[:3]

        if not test_files:
            return {"error": "No test files available"}

        # Sequential processing
        start_time = time.time()
        sequential_results = []
        for test_file in test_files:
            try:
                result = await service.validate_and_create(str(test_file))
                sequential_results.append(result)
            except Exception:
                continue
        sequential_time = time.time() - start_time

        # Concurrent processing
        start_time = time.time()
        tasks = []
        for test_file in test_files:
            task = service.validate_and_create(str(test_file))
            tasks.append(task)

        concurrent_results = []
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            concurrent_results = [r for r in results if not isinstance(r, Exception)]
        except Exception:
            pass

        concurrent_time = time.time() - start_time

        speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0
        efficiency = speedup / len(test_files) if test_files else 0

        return {
            "files_processed": len(test_files),
            "sequential_time": sequential_time,
            "concurrent_time": concurrent_time,
            "speedup_factor": speedup,
            "efficiency": efficiency,
            "sequential_success_count": len(sequential_results),
            "concurrent_success_count": len(concurrent_results),
            "time_saved": sequential_time - concurrent_time,
            "performance_improvement": ((sequential_time - concurrent_time) / sequential_time) * 100 if sequential_time > 0 else 0
        }

    async def benchmark_batch_scalability(self) -> Dict[str, Any]:
        """Benchmark batch processing scalability."""
        from src.tools.batch_tool import batch_transcribe_tool

        test_files = list(Path("test_audio").glob("*.wav"))
        if len(test_files) < 2:
            return {"error": "Need at least 2 test files"}

        scalability_results = []

        # Test different batch sizes
        batch_sizes = [1, 2, min(3, len(test_files))]

        for batch_size in batch_sizes:
            files_to_process = test_files[:batch_size]

            start_time = time.time()
            try:
                batch_request = {
                    "file_paths": [str(f) for f in files_to_process],
                    "model_size": "base",
                    "enable_diarization": False,
                    "device": "cpu",
                    "max_concurrent": batch_size
                }

                result = await batch_transcribe_tool(batch_request)
                processing_time = time.time() - start_time

                scalability_results.append({
                    "batch_size": batch_size,
                    "processing_time": processing_time,
                    "success": result.get("success", False),
                    "time_per_file": processing_time / batch_size,
                    "throughput": batch_size / processing_time if processing_time > 0 else 0
                })

            except Exception as e:
                processing_time = time.time() - start_time
                scalability_results.append({
                    "batch_size": batch_size,
                    "processing_time": processing_time,
                    "error": str(e),
                    "success": False
                })

        # Calculate scalability metrics
        successful_results = [r for r in scalability_results if r.get("success")]
        if len(successful_results) >= 2:
            throughputs = [r["throughput"] for r in successful_results]
            scalability_factor = max(throughputs) / min(throughputs) if min(throughputs) > 0 else 0
        else:
            scalability_factor = 0

        return {
            "batch_sizes_tested": batch_sizes,
            "results": scalability_results,
            "successful_tests": len(successful_results),
            "scalability_factor": scalability_factor,
            "max_throughput": max([r.get("throughput", 0) for r in scalability_results]),
            "optimal_batch_size": max(successful_results, key=lambda x: x.get("throughput", 0))["batch_size"] if successful_results else 1
        }

    async def benchmark_service_imports(self) -> Dict[str, Any]:
        """Benchmark service import times."""
        import importlib
        import sys

        services = [
            "src.services.audio_file_service",
            "src.services.transcription_service",
            "src.services.progress_service",
            "src.services.storage_service",
            "src.services.history_service"
        ]

        import_times = {}

        for service_module in services:
            # Remove from cache if present
            if service_module in sys.modules:
                del sys.modules[service_module]

            start_time = time.time()
            try:
                importlib.import_module(service_module)
                import_time = time.time() - start_time
                import_times[service_module] = {
                    "time": import_time,
                    "success": True
                }
            except Exception as e:
                import_time = time.time() - start_time
                import_times[service_module] = {
                    "time": import_time,
                    "success": False,
                    "error": str(e)
                }

        total_import_time = sum(data["time"] for data in import_times.values())
        successful_imports = sum(1 for data in import_times.values() if data.get("success"))

        return {
            "services_tested": len(services),
            "successful_imports": successful_imports,
            "total_import_time": total_import_time,
            "average_import_time": total_import_time / len(services),
            "fastest_import": min(data["time"] for data in import_times.values()),
            "slowest_import": max(data["time"] for data in import_times.values()),
            "import_details": import_times
        }

    async def benchmark_mcp_tools(self) -> Dict[str, Any]:
        """Benchmark MCP tool response times."""
        from src.tools.progress_tool import get_transcription_progress_tool
        from src.tools.history_tool import list_transcription_history_tool

        tools_to_test = [
            ("get_transcription_progress_tool", get_transcription_progress_tool, {"all_jobs": True}),
            ("list_transcription_history_tool", list_transcription_history_tool, {"limit": 5})
        ]

        tool_performance = []

        for tool_name, tool_func, test_params in tools_to_test:
            response_times = []

            for _ in range(10):  # 10 iterations per tool
                start_time = time.time()
                try:
                    result = await tool_func(test_params)
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                except Exception:
                    continue

            if response_times:
                tool_performance.append({
                    "tool": tool_name,
                    "average_response_time": statistics.mean(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times),
                    "std_dev": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                    "requests_per_second": 1 / statistics.mean(response_times),
                    "total_requests": len(response_times)
                })

        return {
            "tools_tested": len(tools_to_test),
            "tool_performance": tool_performance,
            "average_response_time": statistics.mean([t["average_response_time"] for t in tool_performance]) if tool_performance else 0,
            "fastest_tool": min(tool_performance, key=lambda x: x["average_response_time"])["tool"] if tool_performance else None
        }

    async def benchmark_storage_operations(self) -> Dict[str, Any]:
        """Benchmark storage operation performance."""
        from src.services.storage_service import StorageService
        from src.models.transcription_job import TranscriptionJob
        from src.models.audio_file_mcp import AudioFile

        storage = StorageService()

        # Create test data
        test_file = Path("test_audio/short_speech.wav")
        if not test_file.exists():
            return {"error": "No test file available"}

        from src.services.audio_file_service import AudioFileService
        audio_service = AudioFileService()
        audio_file = await audio_service.validate_and_create(str(test_file))

        job = TranscriptionJob(audio_file=audio_file)

        # Benchmark save operations
        save_times = []
        for _ in range(5):
            start_time = time.time()
            try:
                await storage.save_job(job)
                save_time = time.time() - start_time
                save_times.append(save_time)
            except Exception:
                continue

        # Benchmark load operations
        load_times = []
        for _ in range(5):
            start_time = time.time()
            try:
                await storage.load_job(job.job_id)
                load_time = time.time() - start_time
                load_times.append(load_time)
            except Exception:
                continue

        return {
            "save_operations": len(save_times),
            "load_operations": len(load_times),
            "average_save_time": statistics.mean(save_times) if save_times else 0,
            "average_load_time": statistics.mean(load_times) if load_times else 0,
            "storage_throughput_ops_per_sec": 1 / statistics.mean(save_times + load_times) if (save_times + load_times) else 0,
            "total_operations": len(save_times) + len(load_times)
        }

    async def generate_performance_report(self):
        """Generate comprehensive performance report."""
        self.results["benchmark_completed"] = datetime.now().isoformat()

        successful_benchmarks = sum(1 for b in self.results["benchmarks"] if b.get("result", {}).get("success", False))
        total_benchmarks = len(self.results["benchmarks"])

        # Generate summary statistics
        total_time = sum(b["duration"] for b in self.results["benchmarks"])
        avg_time_per_benchmark = total_time / total_benchmarks if total_benchmarks else 0

        self.results["summary"] = {
            "total_benchmarks": total_benchmarks,
            "successful_benchmarks": successful_benchmarks,
            "success_rate": (successful_benchmarks / total_benchmarks) * 100 if total_benchmarks else 0,
            "total_benchmark_time": total_time,
            "average_time_per_benchmark": avg_time_per_benchmark
        }

        logger.info("\n" + "=" * 60)
        logger.info("📊 PERFORMANCE BENCHMARK COMPLETE")
        logger.info("=" * 60)
        logger.info(f"✅ Successful Benchmarks: {successful_benchmarks}/{total_benchmarks}")
        logger.info(f"📈 Success Rate: {self.results['summary']['success_rate']:.1f}%")
        logger.info(f"⏱️  Total Time: {total_time:.3f}s")

        # Save detailed report
        report_file = Path("performance_benchmark_report.json")

        # Convert to JSON-serializable format
        import json
        json_results = json.loads(json.dumps(self.results, default=str))

        with open(report_file, 'w') as f:
            json.dump(json_results, f, indent=2)

        logger.info(f"📋 Detailed report saved to: {report_file}")

        # Performance insights
        logger.info("\n🔍 Key Performance Insights:")

        for benchmark in self.results["benchmarks"]:
            if benchmark.get("result", {}).get("success"):
                name = benchmark["name"]
                result = benchmark["result"]

                if "Audio File Validation" in name:
                    avg_time = result.get("average_validation_time", 0)
                    files_per_sec = result.get("files_per_second", 0)
                    logger.info(f"  • Audio validation: {avg_time:.3f}s avg, {files_per_sec:.1f} files/sec")

                elif "Concurrent Processing" in name:
                    speedup = result.get("speedup_factor", 0)
                    improvement = result.get("performance_improvement", 0)
                    logger.info(f"  • Concurrency: {speedup:.2f}x speedup, {improvement:.1f}% faster")

                elif "MCP Tool" in name:
                    avg_response = result.get("average_response_time", 0)
                    logger.info(f"  • MCP tools: {avg_response:.3f}s avg response time")

async def main():
    """Run the performance benchmark suite."""
    try:
        benchmark = TranscribeMCPBenchmark()
        await benchmark.run_benchmarks()
        return 0

    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)