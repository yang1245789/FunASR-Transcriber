# FunASR Multi-Language Transcription System

A desktop GUI application for multi-language speech recognition and
text-to-speech, built on FunASR + PyQt6.

## Features

- **File Transcription** — MP3/WAV/M4A/FLAC/OGG/AAC. Audio > 60 s is
  automatically split into 30 s chunks with 1 s overlap.
- **Real-time Transcription** — Microphone or WASAPI loopback (system audio
  capture without Stereo Mix).
- **Translation** — Auto-detect language; non-Chinese text is translated to
  Chinese (built-in model translation or local translation model).
- **Floating Subtitles** — Always-on-top transparent overlay. 5 display modes
  (clean text / emotion / audio events / combined / raw). Font size, color and
  opacity adjustable via right-click menu.
- **Model Manager** — 12 ASR + 2 TTS models, one-click download / delete /
  disk cleanup. Installed models are auto-detected.
- **Text-to-Speech (TTS)** — Windows built-in SAPI5 (offline) +
  CosyVoice 3.0-0.5B model (high-quality, 9 languages, voice cloning).
- **Smart config** — VAD segmentation, punctuation prediction, number/date
  normalization (ITN).
- **GPU Acceleration** — Auto-detect CUDA; fall back to CPU if unavailable.
- **Portable** — Copy the folder to any Windows machine with Python 3.10+ and
  double-click `启动器.bat`.

## System Requirements

| Item | Requirement |
|------|-------------|
| OS | Windows 10/11 64-bit |
| Python | 3.10+ (check "Add Python to PATH" during install) |
| GPU (optional) | NVIDIA GPU + CUDA 12.1 driver |
| Disk | ~20 GB free (for models) |
| RAM | 8 GB+ (16 GB recommended) |

> ffmpeg is pre-bundled. No separate installation needed.

## Quick Start

### On a new machine

```
1. Install Python 3.10+ (tick "Add Python to PATH")
2. Copy the entire App folder to the new machine
3. Double-click 启动器.bat
4. First run auto-creates venv → installs dependencies → downloads PyTorch → launches GUI
```

### Manual setup

```bash
cd App
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python launcher.py
```

## Usage

### File Transcription

1. Go to "转写控制台" → "文件转写"
2. Click "选择文件" to pick an audio file
3. Click "开始转写"

Supported formats: MP3, WAV, M4A, FLAC, OGG, AAC.

### Real-time Transcription

1. Go to "转写控制台" → "实时转写"
2. Choose source: Microphone or System Audio (loopback)
3. Click "开始录音转写"
4. Audio is auto-segmented (default 5 s chunks); results appear in real time.

> Loopback uses Windows WASAPI to capture system audio output without affecting
> playback.

### Floating Subtitles

1. Go to "转写控制台" → "悬浮字幕"
2. Click "启动悬浮字幕"
3. The overlay window: always on top, drag to reposition, right-click for
   display mode / font size / color / opacity settings.

### Model Management

1. Go to "模型管理"
2. Installed models are auto-checked. Check models you want to download or
   delete.
3. Click "下载选中" / "删除选中" / "清理空间"

### Text-to-Speech (TTS)

1. Go to "语音合成"
2. Choose engine: Windows SAPI5 (offline) or CosyVoice (model, needs download)
3. Enter text, pick voice, adjust speed
4. Click "生成并播放" or "保存到文件"

### Settings

- **Model**: main ASR model, device (CUDA/CPU), language, translation mode
- **Recording**: sample rate, chunk duration, input device index
- **Subtitles**: font size, color, background opacity, max lines, auto-hide delay

## Project Structure

```
App/
├── 启动器.bat              ← self-healing launcher script
├── requirements.txt        ← Python dependencies
├── ffmpeg.exe              ← pre-bundled ffmpeg
├── launcher.py             ← PyQt6 GUI
├── main.py                 ← transcription engine + recorder
├── utils.py                ← config management (paths relative to __file__)
├── model_manager.py        ← model download / delete / cleanup / scan
├── subtitle_overlay.py     ← floating subtitle overlay
├── tts_engine.py           ← Windows SAPI5 + CosyVoice TTS
└── models/                 ← model cache (created automatically)
```

## Configuration

`config.json` is generated at first run and stored in `App/`. All paths are
relative — the config is portable across machines.

| Key | Description | Default |
|-----|-------------|---------|
| `model_dir` | Model storage directory | `""` (resolves to App/models) |
| `model_name` | Main ASR model ID | `iic/SenseVoiceSmall` |
| `device` | Inference device | `cuda:0` |
| `language` | Recognition language | `auto` |
| `target_language` | Translation target | `zh` |
| `translation_mode` | builtin / local / api | `builtin` |
| `use_itn` | Number/date normalization | `true` |
| `use_punc` | Punctuation prediction | `true` |
| `recording.*` | Sample rate, chunk duration, device | 16000, 5 s, -1 |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Chinese path causes model failure | Models are auto-copied to an ASCII temp directory |
| CUDA not available | Auto-fall to CPU; check with `python -c "import torch; print(torch.cuda.is_available())"` |
| Broken venv | Delete `venv/` and re-run `启动器.bat` |
| Translation not working | `builtin` depends on ASR model capability; `local` / `api` require additional setup |
| Duplicate models wasting disk | Click "清理空间" in Model Manager |

## Tech Stack

| Component | Purpose |
|-----------|---------|
| FunASR 1.3.1 | Speech recognition framework |
| ModelScope 1.36.0 | Model download manager |
| PyQt6 | GUI framework |
| PyTorch 2.5.1+cu121 | GPU inference |
| sounddevice | Audio recording |
| pycaw | WASAPI loopback |
| comtypes | Windows COM interface |
| pyttsx3 | Windows SAPI5 TTS |

## License & Third-Party Notices

- **This project**: [MIT License](LICENSE)
- **Third-party licenses**: See [NOTICE.md](NOTICE.md)
- **Model copyrights** belong to their respective owners (Alibaba Damo Academy,
  FunAudioLLM, OpenAI, etc.). Model licenses are listed in NOTICE.md.

## Disclaimer

This software is provided for research and educational purposes. Users are
solely responsible for compliance with applicable laws, including those
governing voice cloning and personal data protection.