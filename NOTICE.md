# NOTICE — Third-Party Components & Disclaimer

## Third-Party Components

This software integrates or depends on the following third-party libraries and
models. Their respective licenses govern your use of these components.

### Python Libraries (installed via pip at runtime)

| Library | License |
|---------|---------|
| PyQt6 | GPL / Commercial |
| FunASR | Apache 2.0 |
| ModelScope | Apache 2.0 |
| PyTorch | BSD |
| NumPy | BSD |
| SciPy | BSD |
| sounddevice | MIT |
| soundfile | BSD |
| PyYAML | MIT |
| sentencepiece | Apache 2.0 |
| huggingface_hub | Apache 2.0 |
| comtypes | MIT |
| pycaw | MIT |
| pyttsx3 | MIT |
| transformers | Apache 2.0 |
| pydub | MIT |
| librosa | ISC |
| jieba | MIT |
| protobuf | BSD |
| safetensors | Apache 2.0 |
| cryptography | Apache 2.0 / BSD |
| tqdm | MPL-2.0 |
| requests | Apache 2.0 |
| packaging | Apache 2.0 / BSD |
| tiktoken | MIT |
| tokenizers | Apache 2.0 |
| Jinja2 | BSD |
| omegaconf | BSD |
| hydra-core | MIT |
| psutil | BSD |
| ffmpy | MIT |
| imageio-ffmpeg | BSD |

### Pre-bundled Binary

- **ffmpeg.exe** (FFmpeg) — Licensed under LGPL v2.1+ / GPL v2+. See https://ffmpeg.org/legal.html

### ASR / TTS Models (downloaded at runtime via ModelScope)

| Model | Provider | License |
|-------|----------|---------|
| Fun-ASR-Nano-2512 | FunAudioLLM (Alibaba) | Apache 2.0 |
| CosyVoice 3.0-0.5B | FunAudioLLM (Alibaba) | Apache 2.0 |
| SenseVoiceSmall / SenseVoiceLarge | iic (Alibaba Damo) | Apache 2.0 |
| FSMN-VAD | iic (Alibaba Damo) | Apache 2.0 |
| CT-PUNC | iic (Alibaba Damo) | Apache 2.0 |
| Paraformer-Large / Seaco-Paraformer | iic (Alibaba Damo) | Apache 2.0 |
| CAM++ | iic (Alibaba Damo) | Apache 2.0 |
| XLSR Timestamp | iic (Alibaba Damo) | Apache 2.0 |
| Whisper-large-v3-turbo | OpenAI (mirrored on ModelScope) | MIT |
| Qwen-Audio-Chat / Qwen2-Audio | Alibaba Cloud | Apache 2.0 |
| CosyVoice-ttsfrd | iic (Alibaba Damo) | Apache 2.0 |

## Disclaimer of Liability

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. THE AUTHORS
DISCLAIM ALL LIABILITY FOR ANY DAMAGES ARISING FROM THE USE OF THIS SOFTWARE.

- **No warranty for transcription accuracy** — ASR results may contain errors.
  Always verify critical transcriptions manually.

- **No warranty for model downloads** — Model availability and download speed
  depend on third-party services (ModelScope / Hugging Face). The authors are
  not responsible for service interruptions.

- **No warranty for Windows built-in TTS output** — Speech quality and
  availability depend on the user's Windows installation and locale.

- **Compliance with local laws** — Users are solely responsible for ensuring
  their use of this software (including voice cloning) complies with applicable
  laws and regulations in their jurisdiction.

## Voice Cloning (人声复刻) Usage Advisory

This software includes zero-shot voice cloning functionality via the CosyVoice
3.0 model. Users MUST:

1. Obtain explicit consent from the person whose voice is being cloned.
2. Not use cloned voices for fraud, impersonation, or any illegal activity.
3. Comply with all applicable personal data protection laws.

The authors assume no liability for misuse of the voice cloning feature.