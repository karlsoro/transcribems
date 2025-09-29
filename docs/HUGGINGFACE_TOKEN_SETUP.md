# HuggingFace Token Setup for Speaker Diarization

TranscribeMS uses HuggingFace models for advanced speaker diarization. To enable this feature, you need to configure a HuggingFace access token.

## Why is a HuggingFace token needed?

The speaker diarization feature uses the `pyannote/speaker-diarization-3.1` model from HuggingFace Hub. This model requires authentication to access.

## How to get a HuggingFace token

1. Go to [https://huggingface.co/](https://huggingface.co/)
2. Create an account or log in
3. Go to your [Settings > Access Tokens](https://huggingface.co/settings/tokens)
4. Click "New token"
5. Give it a name (e.g., "TranscribeMS")
6. Select "Read" access level
7. Copy the token

## How to configure the token

### Method 1: Environment Variable (Recommended)

Set the `HUGGINGFACE_HUB_TOKEN` environment variable:

```bash
export HUGGINGFACE_HUB_TOKEN="your_token_here"
```

Add this to your `~/.bashrc` or `~/.zshrc` for persistence.

### Method 2: Pass to WhisperXService

```python
from src.services.whisperx_service import WhisperXService

service = WhisperXService(
    model_size="base",
    hf_token="your_token_here"
)
```

### Method 3: Configuration File

Create a `.env` file in the project root:

```
HUGGINGFACE_HUB_TOKEN=your_token_here
```

**Note: Never commit your token to version control!**

## Verifying token setup

Test speaker diarization with a token:

```python
import asyncio
from src.services.whisperx_service import WhisperXService

async def test_diarization():
    service = WhisperXService(
        model_size="base",
        hf_token="your_token_here"
    )

    result = await service.transcribe_audio(
        "your_audio_file.wav",
        enable_speaker_diarization=True
    )

    print(f"Found {len(result['speakers'])} speakers")
    return result

# Run the test
result = asyncio.run(test_diarization())
```

## Without HuggingFace token

If no token is provided:
- Speaker diarization will be **disabled**
- The system will still perform transcription
- Warning message: "No Hugging Face token provided, speaker diarization disabled"

## Security best practices

1. **Never hardcode tokens** in source code
2. **Use environment variables** for production
3. **Restrict token permissions** to "Read" only
4. **Rotate tokens** periodically
5. **Add .env to .gitignore** if using config files

## Troubleshooting

### Token not working
- Verify token is correct
- Check you have access to `pyannote/speaker-diarization-3.1`
- Ensure internet connection for model download

### Model download issues
- First run requires internet to download the model
- Model is cached locally after first download
- Check HuggingFace Hub status if downloads fail

### Permission errors
- Ensure token has "Read" access
- Some models may require accepting terms of use on HuggingFace Hub

## Current token usage in TranscribeMS

The token is used in:
- `src/services/whisperx_service.py` - Main transcription service
- `src/services/speaker_service.py` - Speaker identification service

Search for `hf_token` or `use_auth_token` in the codebase to see all usage locations.