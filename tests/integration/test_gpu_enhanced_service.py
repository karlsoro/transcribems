"""
Comprehensive test for GPU-enhanced SimpleWhisperXCLI service.
Tests both GPU and CPU modes with performance benchmarking.
"""
import asyncio
import sys
import time
import os
from pathlib import Path

sys.path.append('/home/karlsoro/Projects/TranscribeMS/src')
from services.simple_whisperx_cli import SimpleWhisperXCLI


async def test_gpu_enhanced_service():
    """Test the GPU-enhanced SimpleWhisperXCLI service."""

    print("🎯 === GPU-ENHANCED SERVICE COMPREHENSIVE TEST ===")

    # Test audio files
    test_files = [
        {
            "path": "/home/karlsoro/Projects/TranscribeMS/test_data/audio/multi_speaker.wav",
            "description": "Small multi-speaker test file",
            "expected_min_duration": 10
        }
    ]

    # Check if large test file exists
    large_file = Path("/home/karlsoro/Projects/TranscribeMS/large_audio_converted.wav")
    if large_file.exists():
        test_files.append({
            "path": str(large_file),
            "description": "Large test file (111MB)",
            "expected_min_duration": 1800  # 30+ minutes
        })

    results = []

    for test_file in test_files:
        if not Path(test_file["path"]).exists():
            print(f"⚠️  Skipping {test_file['description']} - file not found")
            continue

        print(f"\n📁 Testing: {test_file['description']}")
        print(f"   File: {test_file['path']}")

        # Test 1: GPU mode (auto-detected)
        print("\n🚀 Test 1: GPU Mode (Auto-detected)")
        cli_gpu = SimpleWhisperXCLI()

        start_time = time.time()
        try:
            result_gpu = await cli_gpu.transcribe_audio(
                audio_path=test_file["path"],
                output_dir=f"/home/karlsoro/Projects/TranscribeMS/test_gpu_auto_{Path(test_file['path']).stem}",
                model="base",  # Use base model for faster testing
                language="en",
                enable_diarization=True,
                timeout_minutes=30
            )
            gpu_time = time.time() - start_time

            print(f"✅ GPU test completed in {gpu_time:.1f}s")
            print(f"   Device used: {result_gpu.get('device_used', 'unknown')}")
            print(f"   GPU available: {result_gpu.get('gpu_available', False)}")
            print(f"   Realtime factor: {result_gpu.get('realtime_factor', 0):.2f}x")
            print(f"   Speakers: {result_gpu.get('speakers_count', 0)}")
            print(f"   Segments: {result_gpu.get('segments_count', 0)}")

            results.append({
                "file": test_file["description"],
                "mode": "GPU Auto",
                "success": result_gpu.get("success", False),
                "time": gpu_time,
                "device": result_gpu.get('device_used', 'unknown'),
                "realtime_factor": result_gpu.get('realtime_factor', 0),
                "speakers": result_gpu.get('speakers_count', 0),
                "segments": result_gpu.get('segments_count', 0)
            })

        except Exception as e:
            print(f"❌ GPU test failed: {e}")
            results.append({
                "file": test_file["description"],
                "mode": "GPU Auto",
                "success": False,
                "error": str(e),
                "time": time.time() - start_time
            })

        # Test 2: Force CPU mode
        print(f"\n💻 Test 2: CPU Mode (Forced)")
        cli_cpu = SimpleWhisperXCLI()

        start_time = time.time()
        try:
            result_cpu = await cli_cpu.transcribe_audio(
                audio_path=test_file["path"],
                output_dir=f"/home/karlsoro/Projects/TranscribeMS/test_cpu_forced_{Path(test_file['path']).stem}",
                model="base",
                language="en",
                enable_diarization=True,
                timeout_minutes=30,
                device="cpu",  # Force CPU
                compute_type="float32",
                batch_size=1
            )
            cpu_time = time.time() - start_time

            print(f"✅ CPU test completed in {cpu_time:.1f}s")
            print(f"   Device used: {result_cpu.get('device_used', 'unknown')}")
            print(f"   Realtime factor: {result_cpu.get('realtime_factor', 0):.2f}x")
            print(f"   Speakers: {result_cpu.get('speakers_count', 0)}")
            print(f"   Segments: {result_cpu.get('segments_count', 0)}")

            results.append({
                "file": test_file["description"],
                "mode": "CPU Forced",
                "success": result_cpu.get("success", False),
                "time": cpu_time,
                "device": result_cpu.get('device_used', 'unknown'),
                "realtime_factor": result_cpu.get('realtime_factor', 0),
                "speakers": result_cpu.get('speakers_count', 0),
                "segments": result_cpu.get('segments_count', 0)
            })

            # Performance comparison
            if 'result_gpu' in locals() and result_gpu.get("success") and result_cpu.get("success"):
                speedup = cpu_time / gpu_time if gpu_time > 0 else 0
                print(f"\n⚡ Performance Comparison:")
                print(f"   GPU time: {gpu_time:.1f}s")
                print(f"   CPU time: {cpu_time:.1f}s")
                print(f"   GPU speedup: {speedup:.1f}x faster than CPU")

        except Exception as e:
            print(f"❌ CPU test failed: {e}")
            results.append({
                "file": test_file["description"],
                "mode": "CPU Forced",
                "success": False,
                "error": str(e),
                "time": time.time() - start_time
            })

    # Test 3: GPU capabilities check
    print(f"\n🔍 Test 3: GPU Capabilities Check")
    cli_check = SimpleWhisperXCLI()
    print(f"   GPU available: {cli_check._gpu_available}")

    try:
        import torch
        print(f"   PyTorch version: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   GPU count: {torch.cuda.device_count()}")
            print(f"   GPU name: {torch.cuda.get_device_name(0)}")
    except Exception as e:
        print(f"   PyTorch check failed: {e}")

    # Summary
    print(f"\n📊 === TEST SUMMARY ===")
    success_count = sum(1 for r in results if r.get("success", False))
    total_tests = len(results)

    print(f"Total tests: {total_tests}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_tests - success_count}")
    print(f"Success rate: {success_count/total_tests*100:.1f}%" if total_tests > 0 else "No tests run")

    if results:
        print(f"\nDetailed Results:")
        for i, result in enumerate(results, 1):
            status = "✅" if result.get("success", False) else "❌"
            print(f"  {i}. {status} {result['file']} - {result['mode']}")
            if result.get("success"):
                print(f"     Time: {result['time']:.1f}s, Device: {result['device']}")
                print(f"     Realtime: {result['realtime_factor']:.2f}x, Speakers: {result['speakers']}, Segments: {result['segments']}")
            else:
                print(f"     Error: {result.get('error', 'Unknown error')}")

    return results


async def main():
    """Main test execution."""
    try:
        results = await test_gpu_enhanced_service()

        # Return code based on success
        success_count = sum(1 for r in results if r.get("success", False))
        if success_count == len(results) and len(results) > 0:
            print(f"\n🎉 All tests passed! GPU-enhanced service is working perfectly.")
            return 0
        else:
            print(f"\n⚠️  Some tests failed or no tests were run.")
            return 1

    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)