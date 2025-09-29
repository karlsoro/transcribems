"""
Contract test for GPU detection and usage functionality.
This test defines the expected behavior and must FAIL initially (TDD approach).
"""

import pytest
from unittest.mock import Mock, patch


class TestGPUDetectionContract:
    """Contract tests for GPU detection and utilization."""

    @pytest.fixture
    def mock_torch_cuda(self):
        """Mock PyTorch CUDA functionality."""
        with patch('torch.cuda') as mock_cuda:
            yield mock_cuda

    def test_gpu_detection_identifies_available_gpus(self, mock_torch_cuda):
        """
        Contract: Should detect and report available GPU devices.
        """
        # Mock CUDA availability
        mock_torch_cuda.is_available.return_value = True
        mock_torch_cuda.device_count.return_value = 2
        mock_torch_cuda.get_device_name.side_effect = lambda x: f"NVIDIA GeForce RTX 308{x}"

        # Mock device properties with proper attributes
        def mock_properties(device_id):
            mock_props = Mock()
            mock_props.name = f"NVIDIA GeForce RTX 308{device_id}"
            mock_props.total_memory = 12*1024**3  # 12GB
            mock_props.major = 8
            mock_props.minor = 6
            mock_props.multi_processor_count = 84
            return mock_props

        mock_torch_cuda.get_device_properties.side_effect = mock_properties

        from src.services.gpu_service import GPUService
        gpu_service = GPUService(defer_initialization=True)

        # This will fail until GPUService is implemented
        gpu_info = gpu_service.detect_gpus()

        assert gpu_info["cuda_available"] is True
        assert gpu_info["device_count"] == 2
        assert len(gpu_info["devices"]) == 2
        assert "NVIDIA GeForce RTX 3080" in gpu_info["devices"][0]["name"]
        assert gpu_info["devices"][0]["memory_gb"] == 12

    def test_gpu_detection_handles_no_gpu_available(self, mock_torch_cuda):
        """
        Contract: Should gracefully handle systems without GPU.
        """
        mock_torch_cuda.is_available.return_value = False
        mock_torch_cuda.device_count.return_value = 0

        from src.services.gpu_service import GPUService
        gpu_service = GPUService(defer_initialization=True)

        gpu_info = gpu_service.detect_gpus()

        assert gpu_info["cuda_available"] is False
        assert gpu_info["device_count"] == 0
        assert gpu_info["devices"] == []
        assert gpu_info["fallback_device"] == "cpu"

    def test_gpu_service_selects_optimal_device(self, mock_torch_cuda):
        """
        Contract: Should select the best available GPU device for processing.
        """
        mock_torch_cuda.is_available.return_value = True
        mock_torch_cuda.device_count.return_value = 3

        # Mock different GPU capabilities
        def mock_get_device_properties(device_id):
            properties = Mock()
            properties.name = f"GPU_{device_id}"
            properties.multi_processor_count = 80
            if device_id == 0:
                properties.total_memory = 8 * 1024**3  # 8GB
                properties.major = 7
                properties.minor = 5
            elif device_id == 1:
                properties.total_memory = 24 * 1024**3  # 24GB - Best option
                properties.major = 8
                properties.minor = 6
            elif device_id == 2:
                properties.total_memory = 12 * 1024**3  # 12GB
                properties.major = 8
                properties.minor = 0
            return properties

        mock_torch_cuda.get_device_properties.side_effect = mock_get_device_properties

        from src.services.gpu_service import GPUService
        gpu_service = GPUService(defer_initialization=True)

        optimal_device = gpu_service.select_optimal_device()

        # Should select device 1 (24GB, newest architecture)
        assert optimal_device["device_id"] == 1
        assert optimal_device["memory_gb"] == 24

    def test_gpu_service_monitors_memory_usage(self, mock_torch_cuda):
        """
        Contract: Should monitor and report GPU memory usage.
        """
        mock_torch_cuda.is_available.return_value = True
        mock_torch_cuda.device_count.return_value = 1
        mock_torch_cuda.memory_allocated.return_value = 4 * 1024**3  # 4GB used
        mock_torch_cuda.memory_reserved.return_value = 6 * 1024**3   # 6GB reserved
        def mock_memory_props(device_id):
            mock_props = Mock()
            mock_props.total_memory = 12 * 1024**3  # 12GB total
            return mock_props
        mock_torch_cuda.get_device_properties.side_effect = mock_memory_props

        from src.services.gpu_service import GPUService
        gpu_service = GPUService(defer_initialization=True)

        memory_info = gpu_service.get_memory_usage(device_id=0)

        assert memory_info["allocated_gb"] == 4
        assert memory_info["reserved_gb"] == 6
        assert memory_info["total_gb"] == 12
        assert memory_info["free_gb"] == 8  # 12 - 4 allocated
        assert memory_info["utilization_percent"] == pytest.approx(33.33, abs=0.1)

    def test_gpu_service_handles_memory_cleanup(self, mock_torch_cuda):
        """
        Contract: Should provide memory cleanup functionality.
        """
        mock_torch_cuda.is_available.return_value = True
        mock_torch_cuda.device_count.return_value = 1
        mock_torch_cuda.empty_cache = Mock()

        from src.services.gpu_service import GPUService
        gpu_service = GPUService(defer_initialization=True)

        # Before cleanup
        mock_torch_cuda.memory_allocated.return_value = 4 * 1024**3
        _ = gpu_service.get_memory_usage(device_id=0)  # Unused usage

        # Perform cleanup
        gpu_service.cleanup_memory()

        # Verify cleanup was called
        mock_torch_cuda.empty_cache.assert_called_once()

    def test_whisperx_service_uses_gpu_when_available(self, mock_torch_cuda):
        """
        Contract: WhisperX service should utilize GPU when available.
        """
        mock_torch_cuda.is_available.return_value = True
        mock_torch_cuda.device_count.return_value = 1

        # Mock the GPU service to return proper device selection
        with patch('src.services.whisperx_service.GPUService') as mock_gpu_service_class:
            mock_gpu_service = Mock()
            mock_gpu_service.is_gpu_available.return_value = True
            mock_gpu_service.select_optimal_device.return_value = {"device_id": 0}
            mock_gpu_service.get_memory_usage.return_value = {
                "device_id": 0,
                "allocated_gb": 2.0,
                "total_gb": 8.0
            }
            mock_gpu_service_class.return_value = mock_gpu_service

            from src.services.whisperx_service import WhisperXService
            whisperx_service = WhisperXService(device="auto")

        device_info = whisperx_service.get_device_info()

        assert device_info["device_type"] == "cuda"
        assert device_info["gpu_available"] is True

    def test_whisperx_service_falls_back_to_cpu(self, mock_torch_cuda):
        """
        Contract: WhisperX service should fall back to CPU when GPU unavailable.
        """
        mock_torch_cuda.is_available.return_value = False

        from src.services.whisperx_service import WhisperXService
        whisperx_service = WhisperXService(device="cpu")

        device_info = whisperx_service.get_device_info()

        assert device_info["device_type"] == "cpu"
        assert device_info["gpu_available"] is False

    def test_gpu_service_validates_cuda_compatibility(self, mock_torch_cuda):
        """
        Contract: Should validate CUDA version compatibility.
        """
        mock_torch_cuda.is_available.return_value = True
        mock_torch_cuda.device_count.return_value = 1

        # Mock device properties for compatibility check
        def mock_compat_props(device_id):
            mock_props = Mock()
            mock_props.major = 8
            mock_props.minor = 6
            return mock_props
        mock_torch_cuda.get_device_properties.side_effect = mock_compat_props

        # Mock CUDA version check
        with patch('torch.version.cuda', '12.1'):
            from src.services.gpu_service import GPUService
            gpu_service = GPUService(defer_initialization=True)

            compatibility = gpu_service.check_cuda_compatibility()

            assert compatibility["cuda_version"] == "12.1"
            assert compatibility["is_compatible"] is True

    def test_gpu_service_provides_performance_recommendations(self, mock_torch_cuda):
        """
        Contract: Should provide GPU performance optimization recommendations.
        """
        mock_torch_cuda.is_available.return_value = True
        mock_torch_cuda.device_count.return_value = 1
        def mock_perf_props(device_id):
            mock_props = Mock()
            mock_props.total_memory = 4 * 1024**3  # 4GB - Limited memory to trigger batch warning
            mock_props.major = 7  # Older architecture
            mock_props.minor = 5
            return mock_props
        mock_torch_cuda.get_device_properties.side_effect = mock_perf_props

        from src.services.gpu_service import GPUService
        gpu_service = GPUService(defer_initialization=True)
        # Manually populate device cache for the test with limited memory to trigger batch recommendation
        gpu_service._device_cache[0] = {
            "name": "Test GPU",
            "total_memory": 4 * 1024**3,  # 4GB - Limited memory to trigger batch warning
            "major": 7,
            "minor": 5,
            "multi_processor_count": 40
        }

        recommendations = gpu_service.get_performance_recommendations()

        assert "recommendations" in recommendations
        assert isinstance(recommendations["recommendations"], list)
        # Debug: print actual recommendations
        print(f"Actual recommendations: {recommendations['recommendations']}")
        # Should recommend smaller batch sizes for limited memory
        assert any("batch" in rec.lower() for rec in recommendations["recommendations"])

    def test_gpu_error_handling_for_out_of_memory(self, mock_torch_cuda):
        """
        Contract: Should handle CUDA out-of-memory errors gracefully.
        """
        mock_torch_cuda.is_available.return_value = True
        mock_torch_cuda.device_count.return_value = 1

        # Mock CUDA OOM error
        cuda_oom_error = RuntimeError("CUDA out of memory")

        from src.services.gpu_service import GPUService
        gpu_service = GPUService(defer_initialization=True)

        # Should provide helpful error handling
        with pytest.raises(RuntimeError) as exc_info:
            gpu_service.handle_cuda_error(cuda_oom_error)

        error_msg = str(exc_info.value)
        assert "memory" in error_msg.lower()
        assert any(word in error_msg.lower() for word in ["reduce", "cleanup", "smaller"])

    def test_gpu_service_supports_multi_gpu_setup(self, mock_torch_cuda):
        """
        Contract: Should support multi-GPU configurations.
        """
        mock_torch_cuda.is_available.return_value = True
        mock_torch_cuda.device_count.return_value = 4

        from src.services.gpu_service import GPUService
        gpu_service = GPUService(defer_initialization=True)

        multi_gpu_config = gpu_service.get_multi_gpu_config()

        assert multi_gpu_config["total_devices"] == 4
        assert multi_gpu_config["supports_multi_gpu"] is True
        assert "device_allocation" in multi_gpu_config
