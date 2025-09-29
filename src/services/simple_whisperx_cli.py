"""
Simple WhisperX CLI wrapper - just call the command line directly.
No complexity, no assumptions, just what works.
"""

import asyncio
import json
import subprocess
import tempfile
import time
import signal
import os
from pathlib import Path
from typing import Dict, Any, Optional

from src.core.logging import get_logger

logger = get_logger(__name__)


class SimpleWhisperXCLI:
    """
    Simple wrapper that calls WhisperX CLI directly.
    Exactly like running from command line - no complexity.
    Includes process management and timeout protection.
    """

    def __init__(self, hf_token: Optional[str] = None):
        self.hf_token = hf_token or os.getenv("HUGGINGFACE_TOKEN", None)
        self._running_processes = set()  # Track running processes
        self._gpu_available = self._check_gpu_availability()
        logger.info(f"GPU available: {self._gpu_available}")

    def _check_gpu_availability(self) -> bool:
        """Check if GPU (CUDA) is available for transcription."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            logger.warning("PyTorch not available - GPU detection failed")
            return False
        except Exception as e:
            logger.warning(f"GPU availability check failed: {e}")
            return False

    async def transcribe_audio(
        self,
        audio_path: str,
        output_dir: Optional[str] = None,
        model: str = "base",
        language: str = "en",
        enable_diarization: bool = True,
        timeout_minutes: int = 30,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio using CLI WhisperX with automatic GPU detection.

        Args:
            audio_path: Path to audio file
            output_dir: Where to save results (default: temp dir)
            model: WhisperX model size (base, small, medium, large, large-v2)
            language: Language code (en, es, fr, etc.)
            enable_diarization: Enable speaker diarization
            timeout_minutes: Maximum processing time before timeout
            device: Force device ('cuda', 'cpu', or None for auto-detect)
            compute_type: Force compute type ('float16', 'float32', or None for auto)
            batch_size: Batch size for processing (None for auto)

        Returns:
            Dict with results, file paths, and performance metrics
        """
        start_time = time.time()
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Use provided output dir or create temp dir
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
        else:
            output_path = Path(tempfile.mkdtemp(prefix="whisperx_"))

        # Auto-detect optimal settings based on GPU availability
        if device is None:
            device = "cuda" if self._gpu_available else "cpu"

        if compute_type is None:
            compute_type = "float16" if device == "cuda" else "float32"

        if batch_size is None:
            batch_size = 16 if device == "cuda" else 1

        logger.info(f"Starting CLI WhisperX transcription: {audio_path}")
        logger.info(f"Output directory: {output_path}")
        logger.info(f"Device: {device}, Compute type: {compute_type}, Batch size: {batch_size}")

        # Build optimized WhisperX CLI command
        cmd = [
            "whisperx",
            str(audio_path),
            "--model", model,
            "--language", language,
            "--device", device,
            "--compute_type", compute_type,
            "--batch_size", str(batch_size),
            "--output_dir", str(output_path),
        ]

        # Add diarization if requested (like your working command)
        if enable_diarization and self.hf_token:
            cmd.extend([
                "--diarize",
                "--hf_token", self.hf_token
            ])

        logger.info(f"Running command: {' '.join(cmd)}")

        try:
            # Set optimized environment for CLI processing
            env = os.environ.copy()
            env['PYTHONWARNINGS'] = 'ignore:torchaudio._backend'

            # GPU optimizations
            if device == "cuda":
                env['CUDA_VISIBLE_DEVICES'] = '0'
                # CPU thread optimization for GPU processing
                env['OMP_NUM_THREADS'] = str(min(os.cpu_count() or 4, 8))
                env['MKL_NUM_THREADS'] = str(min(os.cpu_count() or 4, 8))
            else:
                # CPU optimizations for CPU-only processing
                env['OMP_NUM_THREADS'] = str(min(os.cpu_count() or 4, 8))
                env['MKL_NUM_THREADS'] = str(min(os.cpu_count() or 4, 8))
                env['NUMEXPR_NUM_THREADS'] = str(min(os.cpu_count() or 4, 8))

            # Check for existing WhisperX processes to prevent conflicts
            existing_processes = self._check_existing_whisperx_processes()
            if existing_processes:
                logger.warning(f"Found {len(existing_processes)} existing WhisperX processes")

            # Run the command exactly like CLI with proper environment
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(Path.cwd()),
                env=env  # Critical: Use the same environment as your CLI
            )

            # Track this process
            self._running_processes.add(process.pid)
            logger.info(f"Started WhisperX process PID: {process.pid}")

            # Use timeout to prevent hanging
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_minutes * 60
                )
                logger.info(f"WhisperX process {process.pid} completed normally")
            except asyncio.TimeoutError:
                logger.error(f"WhisperX process {process.pid} timed out after {timeout_minutes} minutes")
                # Kill the hanging process forcefully
                try:
                    process.kill()
                    await asyncio.wait_for(process.wait(), timeout=10)
                except Exception as e:
                    logger.error(f"Error killing timed-out process: {e}")
                raise RuntimeError(f"WhisperX process timed out after {timeout_minutes} minutes")
            finally:
                # Always remove from tracking
                self._running_processes.discard(process.pid)

            processing_time = time.time() - start_time

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"WhisperX CLI failed: {error_msg}")
                raise RuntimeError(f"WhisperX CLI failed: {error_msg}")

            # Find generated files
            base_name = audio_path.stem
            output_files = {
                "json": output_path / f"{base_name}.json",
                "txt": output_path / f"{base_name}.txt",
                "srt": output_path / f"{base_name}.srt",
                "vtt": output_path / f"{base_name}.vtt",
                "tsv": output_path / f"{base_name}.tsv"
            }

            # Check which files were generated
            generated_files = {}
            for format_name, file_path in output_files.items():
                if file_path.exists():
                    generated_files[format_name] = str(file_path)

            # Load JSON result if available for metadata
            transcript_data = {}
            if "json" in generated_files:
                try:
                    with open(generated_files["json"], 'r') as f:
                        transcript_data = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not load JSON result: {e}")

            # Load plain text if available
            full_text = ""
            if "txt" in generated_files:
                try:
                    with open(generated_files["txt"], 'r') as f:
                        full_text = f.read().strip()
                except Exception as e:
                    logger.warning(f"Could not load text result: {e}")

            # Extract metadata
            segments = transcript_data.get("segments", [])
            speakers = set()
            audio_duration = 0
            for segment in segments:
                if "speaker" in segment and segment["speaker"]:
                    speakers.add(segment["speaker"])
                if "end" in segment:
                    audio_duration = max(audio_duration, segment["end"])

            # Calculate performance metrics
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            realtime_factor = audio_duration / processing_time if processing_time > 0 else 0
            processing_speed_mb_per_sec = file_size_mb / processing_time if processing_time > 0 else 0

            result_data = {
                "success": True,
                "processing_time_minutes": processing_time / 60,
                "processing_time_seconds": processing_time,
                "audio_file": str(audio_path),
                "audio_duration_seconds": audio_duration,
                "file_size_mb": file_size_mb,
                "output_directory": str(output_path),
                "generated_files": generated_files,
                "text": full_text,
                "segments": segments,
                "speakers": list(speakers),
                "speakers_count": len(speakers),
                "segments_count": len(segments),
                "text_length": len(full_text),
                "cli_command": " ".join(cmd),
                "stdout": stdout.decode() if stdout else "",
                # Performance metrics
                "device_used": device,
                "compute_type_used": compute_type,
                "batch_size_used": batch_size,
                "gpu_available": self._gpu_available,
                "realtime_factor": realtime_factor,
                "processing_speed_mb_per_sec": processing_speed_mb_per_sec,
                "language_detected": transcript_data.get("language", language)
            }

            logger.info(f"CLI WhisperX completed successfully in {processing_time/60:.1f} minutes")
            logger.info(f"Device: {device}, GPU available: {self._gpu_available}")
            logger.info(f"Audio duration: {audio_duration:.1f}s, Realtime factor: {realtime_factor:.2f}x")
            logger.info(f"Processing speed: {processing_speed_mb_per_sec:.2f} MB/s")
            logger.info(f"Generated files: {list(generated_files.keys())}")
            logger.info(f"Speakers detected: {len(speakers)}")
            logger.info(f"Segments: {len(segments)}")

            return result_data

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"CLI WhisperX failed after {processing_time/60:.1f} minutes: {e}")
            raise RuntimeError(f"CLI WhisperX execution failed: {str(e)}")

    def _check_existing_whisperx_processes(self) -> list:
        """Check for existing WhisperX processes to prevent conflicts."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "whisperx"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip()]
                return pids
            return []
        except Exception as e:
            logger.warning(f"Could not check for existing WhisperX processes: {e}")
            return []

    def cleanup_processes(self):
        """Clean up any tracked processes."""
        for pid in list(self._running_processes):
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Terminated WhisperX process {pid}")
            except ProcessLookupError:
                # Process already dead
                pass
            except Exception as e:
                logger.error(f"Error terminating process {pid}: {e}")
        self._running_processes.clear()