"""
GPU detection and management service for WhisperX processing.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import gc

import torch

from src.core.logging import get_logger


logger = get_logger(__name__)


class GPUService:
    """
    Service for GPU detection, selection, and memory management.
    """

    def __init__(self):
        """Initialize GPU service."""
        self._device_cache = {}
        self._initialize_cuda_info()

    def _initialize_cuda_info(self) -> None:
        """Initialize CUDA information and cache device details."""
        try:
            if torch.cuda.is_available():
                logger.info(f"CUDA available with {torch.cuda.device_count()} device(s)")
                logger.info(f"CUDA version: {torch.version.cuda}")

                # Cache device information
                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    self._device_cache[i] = {
                        "name": props.name,
                        "total_memory": props.total_memory,
                        "major": props.major,
                        "minor": props.minor,
                        "multi_processor_count": props.multi_processor_count
                    }
            else:
                logger.info("CUDA not available, using CPU")

        except Exception as e:
            logger.warning(f"Error initializing CUDA info: {e}")

    def is_gpu_available(self) -> bool:
        """
        Check if GPU is available for processing.

        Returns:
            bool: True if GPU is available
        """
        return torch.cuda.is_available()

    def detect_gpus(self) -> Dict[str, Any]:
        """
        Detect and return information about available GPUs.

        Returns:
            Dict containing GPU information
        """
        gpu_info = {
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "devices": [],
            "fallback_device": "cpu"
        }

        if torch.cuda.is_available():
            for device_id in range(torch.cuda.device_count()):
                try:
                    props = torch.cuda.get_device_properties(device_id)
                    device_info = {
                        "device_id": device_id,
                        "name": props.name,
                        "memory_gb": round(props.total_memory / (1024**3), 2),
                        "compute_capability": f"{props.major}.{props.minor}",
                        "multi_processor_count": props.multi_processor_count,
                        "is_available": True
                    }
                    gpu_info["devices"].append(device_info)

                except Exception as e:
                    logger.warning(f"Error getting info for GPU {device_id}: {e}")

        logger.debug(f"Detected GPU configuration: {gpu_info}")
        return gpu_info

    def select_optimal_device(self) -> Optional[Dict[str, Any]]:
        """
        Select the optimal GPU device for processing.

        Returns:
            Optional[Dict]: Information about the selected device, or None if no GPU
        """
        if not torch.cuda.is_available():
            return None

        gpu_info = self.detect_gpus()
        if not gpu_info["devices"]:
            return None

        # Score devices based on memory and compute capability
        best_device = None
        best_score = 0

        for device in gpu_info["devices"]:
            # Score based on memory (70%) and compute capability (30%)
            memory_score = device["memory_gb"] / 48  # Normalize to 48GB (high-end GPU)
            compute_score = (float(device["compute_capability"]) - 6.0) / 2.0  # Normalize from 6.0-8.0

            total_score = (memory_score * 0.7) + (compute_score * 0.3)

            if total_score > best_score:
                best_score = total_score
                best_device = device

        if best_device:
            logger.info(f"Selected optimal GPU device: {best_device['name']} "
                       f"({best_device['memory_gb']}GB)")

        return best_device

    def get_memory_usage(self, device_id: int = 0) -> Dict[str, Any]:
        """
        Get memory usage information for a specific GPU.

        Args:
            device_id: GPU device ID

        Returns:
            Dict containing memory usage information
        """
        if not torch.cuda.is_available() or device_id >= torch.cuda.device_count():
            return {
                "error": "GPU not available or invalid device ID",
                "device_id": device_id
            }

        try:
            # Get memory information
            allocated = torch.cuda.memory_allocated(device_id)
            reserved = torch.cuda.memory_reserved(device_id)

            props = torch.cuda.get_device_properties(device_id)
            total = props.total_memory

            free = total - allocated
            utilization = (allocated / total) * 100

            memory_info = {
                "device_id": device_id,
                "allocated_gb": round(allocated / (1024**3), 2),
                "reserved_gb": round(reserved / (1024**3), 2),
                "total_gb": round(total / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "utilization_percent": round(utilization, 2)
            }

            logger.debug(f"GPU {device_id} memory usage: {memory_info}")
            return memory_info

        except Exception as e:
            logger.error(f"Error getting memory usage for GPU {device_id}: {e}")
            return {
                "error": str(e),
                "device_id": device_id
            }

    def cleanup_memory(self, device_id: Optional[int] = None) -> None:
        """
        Clean up GPU memory caches.

        Args:
            device_id: Specific GPU to clean, or None for all
        """
        if not torch.cuda.is_available():
            return

        try:
            if device_id is not None:
                with torch.cuda.device(device_id):
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                logger.debug(f"Cleaned GPU {device_id} memory cache")
            else:
                torch.cuda.empty_cache()
                logger.debug("Cleaned all GPU memory caches")

        except Exception as e:
            logger.warning(f"Error cleaning GPU memory: {e}")

    def check_cuda_compatibility(self) -> Dict[str, Any]:
        """
        Check CUDA version compatibility.

        Returns:
            Dict containing compatibility information
        """
        compatibility_info = {
            "cuda_available": torch.cuda.is_available(),
            "pytorch_version": torch.__version__,
            "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
            "cudnn_version": torch.backends.cudnn.version() if torch.cuda.is_available() else None,
            "is_compatible": False,
            "recommendations": []
        }

        if torch.cuda.is_available():
            cuda_version = torch.version.cuda

            # Check for compatible versions
            if cuda_version:
                cuda_major = int(cuda_version.split('.')[0])
                cuda_minor = int(cuda_version.split('.')[1])

                # WhisperX typically works with CUDA 11.8+ or 12.x
                if cuda_major >= 12 or (cuda_major == 11 and cuda_minor >= 8):
                    compatibility_info["is_compatible"] = True
                else:
                    compatibility_info["recommendations"].append(
                        f"Consider upgrading CUDA from {cuda_version} to 11.8+ or 12.x"
                    )

            # Check compute capabilities
            for device_id in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(device_id)
                compute_capability = f"{props.major}.{props.minor}"

                # WhisperX generally requires compute capability 6.0+
                if props.major < 6:
                    compatibility_info["recommendations"].append(
                        f"GPU {device_id} has compute capability {compute_capability}, "
                        f"which may not be optimal for WhisperX (6.0+ recommended)"
                    )

        else:
            compatibility_info["recommendations"].append(
                "CUDA not available. Install CUDA-capable PyTorch for GPU acceleration."
            )

        return compatibility_info

    def get_performance_recommendations(self) -> Dict[str, Any]:
        """
        Get performance optimization recommendations based on available hardware.

        Returns:
            Dict containing performance recommendations
        """
        recommendations = {
            "recommendations": [],
            "optimal_settings": {},
            "warnings": []
        }

        if not torch.cuda.is_available():
            recommendations["recommendations"].append(
                "GPU not available. Performance will be significantly slower on CPU."
            )
            recommendations["optimal_settings"] = {
                "batch_size": 1,
                "chunk_length": 30,
                "compute_type": "float32"
            }
            return recommendations

        # Analyze each GPU
        for device_id in range(torch.cuda.device_count()):
            memory_info = self.get_memory_usage(device_id)

            if "error" in memory_info:
                continue

            total_memory = memory_info["total_gb"]

            # Memory-based recommendations
            if total_memory < 6:
                recommendations["recommendations"].append(
                    f"GPU {device_id} has limited memory ({total_memory}GB). "
                    f"Consider using smaller model size or reducing batch size."
                )
                recommendations["optimal_settings"][f"gpu_{device_id}_batch_size"] = 8

            elif total_memory < 12:
                recommendations["recommendations"].append(
                    f"GPU {device_id} has moderate memory ({total_memory}GB). "
                    f"Should handle medium models well."
                )
                recommendations["optimal_settings"][f"gpu_{device_id}_batch_size"] = 16

            else:
                recommendations["recommendations"].append(
                    f"GPU {device_id} has ample memory ({total_memory}GB). "
                    f"Can handle large models with higher batch sizes."
                )
                recommendations["optimal_settings"][f"gpu_{device_id}_batch_size"] = 32

            # Compute capability recommendations
            if device_id in self._device_cache:
                device_info = self._device_cache[device_id]
                compute_capability = f"{device_info['major']}.{device_info['minor']}"

                if device_info["major"] >= 8:
                    recommendations["recommendations"].append(
                        f"GPU {device_id} supports tensor cores for improved performance."
                    )
                    recommendations["optimal_settings"][f"gpu_{device_id}_compute_type"] = "float16"
                elif device_info["major"] >= 7:
                    recommendations["optimal_settings"][f"gpu_{device_id}_compute_type"] = "float16"
                else:
                    recommendations["optimal_settings"][f"gpu_{device_id}_compute_type"] = "float32"
                    recommendations["warnings"].append(
                        f"GPU {device_id} compute capability {compute_capability} may limit performance"
                    )

        return recommendations

    def handle_cuda_error(self, error: Exception) -> None:
        """
        Handle CUDA-related errors with helpful suggestions.

        Args:
            error: The CUDA error exception

        Raises:
            RuntimeError: With helpful error message
        """
        error_msg = str(error).lower()

        if "out of memory" in error_msg or "cuda out of memory" in error_msg:
            # Get memory info for context
            memory_suggestions = []

            for device_id in range(torch.cuda.device_count()):
                memory_info = self.get_memory_usage(device_id)
                if "error" not in memory_info:
                    memory_suggestions.append(
                        f"GPU {device_id}: {memory_info['allocated_gb']}GB/"
                        f"{memory_info['total_gb']}GB used"
                    )

            suggestion_msg = (
                "CUDA out of memory. Try:\n"
                "1. Reduce batch size\n"
                "2. Use smaller model (e.g., 'medium' instead of 'large')\n"
                "3. Process shorter audio chunks\n"
                "4. Clear GPU memory with cleanup_memory()\n"
                f"Current usage: {'; '.join(memory_suggestions)}"
            )

            raise RuntimeError(suggestion_msg)

        elif "device-side assert" in error_msg:
            raise RuntimeError(
                "CUDA device assertion failed. This may indicate:\n"
                "1. Invalid tensor operations\n"
                "2. Index out of bounds\n"
                "3. Model compatibility issues\n"
                "Try running on CPU to get more detailed error information."
            )

        else:
            raise RuntimeError(f"CUDA error: {error}")

    def get_multi_gpu_config(self) -> Dict[str, Any]:
        """
        Get configuration for multi-GPU setup.

        Returns:
            Dict containing multi-GPU configuration
        """
        device_count = torch.cuda.device_count() if torch.cuda.is_available() else 0

        config = {
            "total_devices": device_count,
            "supports_multi_gpu": device_count > 1,
            "device_allocation": {}
        }

        if device_count > 1:
            # Simple round-robin allocation strategy
            for i in range(device_count):
                config["device_allocation"][f"device_{i}"] = {
                    "suggested_use": f"Worker {i % 2}" if device_count == 2 else f"Worker {i}",
                    "memory_gb": self.get_memory_usage(i).get("total_gb", 0)
                }

            config["recommendations"] = [
                "Multi-GPU detected. Consider using data parallelism for large batches.",
                "Assign different workers to different GPUs for optimal throughput."
            ]

        return config