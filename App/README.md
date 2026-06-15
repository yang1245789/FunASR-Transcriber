# FunASR Multi-Language Transcription System

A desktop GUI application for multi-language speech recognition and
text-to-speech, built on FunASR + PyQt6.

## Features

- **File Transcription** — MP3/WAV/M4A/FLAC/OGG/AAC. Audio > 60 s is
  automatically split into 30 s chunks with 1 s overlap.
- **Real-time Transcription** — Microphone or WASAPI loopback (system audio
  capture without Stereo Mix).
- **Translation** — Auto-detect language; non-Chinese text is translated to
  Chinese.
- **Floating Subtitles** — Always-on-top transparent overlay. 5 display modes
  (clean text / emotion / audio events / combined / raw).
- **Model Manager** — 12 ASR + 2 TTS models, one-click download / delete /
  disk cleanup.
- **Text-to-Speech** — Windows built-in SAPI5 (offline) + CosyVoice 3.0-0.5B
  model (9 languages, voice cloning).
- **GPU Acceleration** — Auto-detect CUDA; fall back to CPU if unavailable.

## Quick Start

```
1. Install Python 3.10+ (tick "Add Python to PATH")
2. Double-click 启动器.bat
3. First run auto-creates venv → installs dependencies → launches GUI
```

See [root README](../README.md) for full documentation.

## License

This project is licensed under MIT. See [../LICENSE](../LICENSE).
Third-party license info: [../NOTICE.md](../NOTICE.md).