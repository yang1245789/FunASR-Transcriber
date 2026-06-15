# Model Guide

12 ASR models + 2 TTS models are available via ModelScope (魔搭社区).
"Integrated" means the model is wired into the transcription/TTS pipeline and
works out of the box. "Download only" means you can download it but it is not
yet connected to the GUI pipeline.

> Windows built-in TTS requires no model download — just `pyttsx3` from
> `requirements.txt`.

## Core ASR Models (recommended)

| Model | Size | Real-time | Status | Notes |
|-------|------|-----------|--------|-------|
| **SenseVoice-Small** `iic/SenseVoiceSmall` | ~1 GB | Yes | Integrated (default) | Lightweight multi-language (ZH/EN/JA/KO/Yue) |
| **Fun-ASR-Nano-2512** `FunAudioLLM/Fun-ASR-Nano-2512` | ~3 GB | Yes | Integrated | 30+ languages, emotion, timestamps, speaker diarisation |
| **FSMN-VAD** `iic/speech_fsmn_vad_zh-cn-16k-common-pytorch` | ~50 MB | Yes | Integrated | Voice Activity Detection, auto-segmentation |
| **CT-PUNC** `iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch` | ~300 MB | Yes | Integrated | Punctuation prediction |
| **SenseVoice-Large** `iic/SenseVoiceLarge` | ~2 GB | Yes | Download only | Higher accuracy version of Small |

## Third-party Models (download only)

| Model | Size | Real-time | Notes |
|-------|------|-----------|-------|
| **Whisper-large-v3-turbo** `openai-mirror/whisper-large-v3-turbo` | ~1.6 GB | No | OpenAI 99 languages; needs `openai-whisper` |
| **Qwen-Audio-Chat** `qwen/Qwen-Audio-Chat` | ~20 GB | No | Qwen audio chat; needs `transformers` |
| **Qwen2-Audio-7B-Instruct** `qwen/Qwen2-Audio-7B-Instruct` | ~15 GB | No | Second-gen audio LLM |

## FunASR Official Models (download only)

| Model | Size | Real-time | Notes |
|-------|------|-----------|-------|
| **Paraformer-Large** | ~900 MB | Yes | Chinese high-accuracy; loadable via AutoModel |
| **Seaco-Paraformer-Large** | ~1 GB | Yes | Hot-word enhanced version |
| **CAM++** | ~10 MB | No | Speaker verification; standalone model |
| **XLSR Timestamp** | ~1 GB | No | Word-level timestamp alignment |

## TTS Models

| Model | Size | Status | Notes |
|-------|------|--------|-------|
| **CosyVoice 3.0-0.5B** `FunAudioLLM/Fun-CosyVoice3-0.5B-2512` | ~1.1 GB | Integrated | 9 languages + 18 Chinese dialects, zero-shot voice cloning, emotion control |
| **CosyVoice-ttsfrd** `iic/CosyVoice-ttsfrd` | ~50 MB | Optional resource | Text front-end for number/date normalisation |

## Integrated ASR Model Details

### SenseVoice-Small (default)

- Alibaba Damo Academy CosyVoice series
- Languages: ZH / EN / JA / KO / Cantonese
- Features: ASR + emotion recognition + audio event detection
- Path: `models/models/iic/SenseVoiceSmall/`
- VAD + PUNC are auto-attached when `use_punc=true`

### Fun-ASR-Nano-2512 (multi-language)

- FunAudioLLM official multi-language ASR model
- 30+ languages including: ZH (Mandarin + dialects), EN, JA, FA, RU
- Features: ASR + emotion + timestamps + speaker diarisation
- Extra dependency: Qwen3-0.6B weights (~1.5 GB), bundled within the model
  download
- Registration: manual import in `init_model()` because `__init__.py` does not
  self-register

### FSMN-VAD + CT-PUNC

- Auxiliary modules auto-attached to non-FunAudioLLM models
- VAD: detects speech start/end; real-time auto-segmentation
- PUNC: adds commas, periods, question marks

## Model Cache Paths

Models are stored under `App/models/`. The system scans three locations:

1. `models/hub/<org>/<model>/` — ModelScope `snapshot_download` default
2. `models/models/<org>/<model>/` — when MODELSCOPE_CACHE points to models/
3. `models/<org>/<model>/` — alternative cache layout

Duplicate paths can be cleaned via the "清理空间" button in Model Manager.

## Chinese Path Compatibility

When the project path contains non-ASCII characters, `sentencepiece` (C++
backend) cannot read from it. The engine:

1. Detects non-ASCII characters in `model_dir`
2. Copies models to `%TEMP%\funasr_cache\` (ASCII path)
3. Sets `MODELSCOPE_CACHE` to the temp directory
4. Fun-ASR-Nano additionally copies Qwen3-0.6B weights
5. FunASR loads from the temp cache

> Use an ASCII-only project path to avoid this one-time copy.