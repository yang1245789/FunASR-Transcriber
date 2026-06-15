# Changelog

## v2.0 — Current (2026-06-15)

### Major changes since v1.x

- **CosyVoice 3.0-0.5B replaces 300M/SFT/Instruct**: Single model (~1.1 GB) 
  replaces three old models (~18 GB total). Supports 9 languages + 18 Chinese 
  dialects, zero-shot voice cloning, emotion/dialect control.
- **Voice cloning (人声复刻)**: `synthesize_with_prompt()` in `tts_engine.py`. 
  Reference audio + prompt text → cloned voice output.
- **Thread-safety fix**: Model download progress now uses `pyqtSignal` instead 
  of calling Qt widgets from worker threads (PyQt6 violation).
- **Disk cleanup**: `ModelManager.deep_cleanup()` removes temp caches, stale 
  download directories, and duplicate model copies.
- **Config caching**: `utils.load_config()` caches with TTL to avoid repeated
  disk I/O.
- **Buffer overflow protection**: WASAPI loopback buffer capped at 60 seconds;
  overflow triggers discard.
- **Batch model download**: "下载选中" now queues all checked models instead of 
  only downloading the first one.
- **Resource cleanup**: Temp audio files cleaned on new TTS generation. 
  Subtitle overlay and recorder stopped on app close.
- **Model scanning robustness**: `PermissionError` and missing directories 
  handled during model scan and disk usage calculation.
- **Config save error handling**: `subtitle_overlay.py` `save_config` calls all 
  wrapped in try/except.
- **Unused imports removed**: `json`, `queue`, `Path`, `QCursor`, `QIcon`, 
  `QSlider`, `QObject` from `launcher.py`; `queue` from `main.py`.
- **Documentation**: README.md, DEPLOY.md, MODEL_GUIDE.md rewritten. Added 
  LICENSE (MIT) and NOTICE.md (third-party licenses and disclaimers).

### Fixes since v1.x

- Long audio (>60 s) no longer falls through to full-file path when chunking 
  produces empty results.
- Duration parsing handles `HH:MM:SS.mmm` format.
- Removed `callback_queue` dead code (was never read, grew unbounded).
- `_sounddevice_start` returns success/failure; `start()` checks before 
  spawning processing thread.
- `pyttsx3` engine locked with `self._lock` in `WindowsTTS.synthesize`.
- `QApplication.primaryScreen()` nullable guard in `subtitle_overlay`.
- `event.globalPosition()` deprecation workaround for older PyQt6.
- `tempfile.mktemp()` replaced with `NamedTemporaryFile`.

---

## v1.x — Initial Development (2026-05-21 ~ 2026-06-06)

### v1.3 — TTS (2026-06-06)

- Added `tts_engine.py` with WindowsTTS (SAPI5) and ModelTTS (CosyVoice).
- Added TTS page in GUI with engine/voice selection and playback controls.
- Replaced `edge-tts` with `pyttsx3` in `requirements.txt`.

### v1.2 — Deployment (2026-06-04)

- Batch file encoding fix (CRLF + GBK instead of UTF-8).
- Model card checkbox auto-select for installed models.
- First packaging test on clean Windows machine.
- Hard-coded paths removed from `config.json`.
- DEPLOY.md and CHANGELOG.md created.

### v1.1 — Core Features (2026-05-31)

- Engine singleton, model switching, file transcription with chunking.
- Real-time recording via sounddevice and WASAPI loopback.
- Translation (builtin / local).
- Floating subtitle overlay with 5 display modes.
- Model manager with download/delete/scan.
- Chinese path compatibility via temp cache.

### v1.0 — Initial (2026-05-21)

- Project scaffold, ffmpeg bundling, venv setup.
- Fun-ASR-Nano-2512 registration fix.
- Qwen3-0.6B download and Chinese path workaround.