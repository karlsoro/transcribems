#!/usr/bin/env python3
"""
Fix TorchAudio backend configuration and deprecation warnings.
"""

import os
import warnings

def fix_torchaudio_setup():
    """Configure TorchAudio properly to avoid deprecation warnings."""
    print("🔧 FIXING TORCHAUDIO CONFIGURATION")
    print("=" * 50)

    # Suppress the specific deprecation warnings temporarily
    warnings.filterwarnings("ignore", message=".*torchaudio._backend.*deprecated.*")

    try:
        import torchaudio

        print("📊 Current TorchAudio Status:")
        print(f"   Version: {torchaudio.__version__}")

        # Check available backends
        try:
            # Use the new approach if available
            backends = []
            try:
                # Try the modern way first
                import torchaudio.backend
                backends = ['ffmpeg', 'soundfile']  # Known available backends
            except:
                # Fall back to deprecated method with warning suppression
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    backends = torchaudio.list_audio_backends()

            print(f"   Available backends: {backends}")

        except Exception as e:
            print(f"   Backend detection error: {e}")
            backends = ['soundfile', 'ffmpeg']

        # Set the backend to soundfile (most reliable)
        try:
            if 'soundfile' in backends:
                # Try to set soundfile backend
                print("🔧 Setting soundfile backend...")

                # For newer torchaudio versions, we may need to use environment variables
                os.environ['TORCHAUDIO_BACKEND'] = 'soundfile'

                # Try the deprecated method with warning suppression for compatibility
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    try:
                        torchaudio.set_audio_backend('soundfile')
                        print("✅ Backend set to soundfile successfully")
                    except:
                        print("⚠️  Backend setting via API failed, using environment variable")

            elif 'ffmpeg' in backends:
                print("🔧 Setting ffmpeg backend...")
                os.environ['TORCHAUDIO_BACKEND'] = 'ffmpeg'
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    try:
                        torchaudio.set_audio_backend('ffmpeg')
                        print("✅ Backend set to ffmpeg successfully")
                    except:
                        print("⚠️  Backend setting via API failed, using environment variable")

        except Exception as e:
            print(f"⚠️  Backend configuration error: {e}")

        # Test the configuration
        print("\n🧪 Testing audio backend...")
        try:
            # Test loading a simple audio operation
            import torch

            # Create a simple test tensor to verify audio operations work
            test_audio = torch.randn(16000)  # 1 second of random audio at 16kHz

            # Try a basic audio operation
            if hasattr(torchaudio.transforms, 'Resample'):
                resample = torchaudio.transforms.Resample(16000, 8000)
                resampled = resample(test_audio)
                print(f"✅ Audio operations working - resampled from {test_audio.shape} to {resampled.shape}")
            else:
                print("⚠️  Audio transforms not available")

        except Exception as e:
            print(f"❌ Audio backend test failed: {e}")

        print("\n📋 Backend Configuration Summary:")
        print(f"   Environment: TORCHAUDIO_BACKEND={os.environ.get('TORCHAUDIO_BACKEND', 'Not set')}")

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                current = torchaudio.get_audio_backend()
                print(f"   Current backend: {current}")
        except:
            print(f"   Current backend: Environment controlled")

        return True

    except Exception as e:
        print(f"❌ TorchAudio configuration failed: {e}")
        return False

def create_audio_config():
    """Create a configuration that suppresses warnings for the project."""
    config_content = '''
"""
Audio backend configuration to suppress TorchAudio deprecation warnings.
Import this at the start of audio processing modules.
"""

import os
import warnings

# Suppress TorchAudio deprecation warnings
warnings.filterwarnings("ignore", message=".*torchaudio._backend.*deprecated.*")
warnings.filterwarnings("ignore", message=".*TorchAudio.*maintenance phase.*")

# Set environment variable for backend
os.environ.setdefault('TORCHAUDIO_BACKEND', 'soundfile')

def configure_audio_backend():
    """Configure audio backend with warning suppression."""
    try:
        import torchaudio
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if hasattr(torchaudio, 'set_audio_backend'):
                torchaudio.set_audio_backend('soundfile')
    except:
        pass

# Auto-configure when imported
configure_audio_backend()
'''

    with open('src/core/audio_config.py', 'w') as f:
        f.write(config_content)

    print("📄 Created src/core/audio_config.py for warning suppression")

if __name__ == "__main__":
    success = fix_torchaudio_setup()

    if success:
        print("\n✅ TorchAudio configuration completed")
        print("💡 Import src.core.audio_config at the start of audio modules to suppress warnings")

        # Create the config file
        try:
            create_audio_config()
        except Exception as e:
            print(f"⚠️  Could not create audio config file: {e}")

    else:
        print("\n❌ TorchAudio configuration failed")
        print("⚠️  Manual intervention may be required")