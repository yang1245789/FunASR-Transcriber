# Changelog

## v2.1.0 — Path Centralization & Robustness (2026-06-16)

### Breaking changes (source only)
- All hardcoded path strings (`"models"`, `"hub"`, `"funasr_cache"`, `"Qwen"`,
  etc.) have been replaced with shared helpers from `utils.py`.
- `utils.py` now exports: `model_subdirs()`, `model_safe_name()`,
  `resolve_model_path()`, `get_temp_cache_dir()`.

### Fixes
- ModelScope encoding fix: models downloaded with `___` in directory names
  (e.g. `Fun-CosyVoice3-0___5B-2512`) are now correctly recognized via fuzzy
  directory scanning.
- CosyVoice 3.0 model loading now attempts the `cosyvoice` Python package API
  instead of `funasr.AutoModel`.
- Config cache (`_config_cache`) protected by `threading.Lock()`.
- Model manager `_local_models` protected by `_models_lock`.
- Batch download: checking multiple models and clicking "下载选中" now
  downloads all of them sequentially instead of only the first.
- Temp audio files cleaned up on re-generation and on app close.
- `save_config()` no longer crashes on disk-full or permission errors.
- `subtitle_overlay` save operations all guarded with try/except.
- `QApplication.primaryScreen()` nullable guard for headless/startup edge cases.
- `event.globalPosition()` backward-compatible with `event.globalPos()`.
- `transcribe_stream` exception adds CUDA OOM detection and log instead of
  silent pass.
- `_init_model_impl` weight detection now scans for all formats (`.pt`,
  `.bin`, `.safetensors`, `.onnx`) instead of only `.pt`.
- Unused imports removed across all files.

---

## v2.0 — CosyVoice 3.0 Release (2026-06-15)

### Major
- **CosyVoice 3.0-0.5B** replaces three 300M/SFT/Instruct models.
- **Voice cloning** with `synthesize_with_prompt()`.
- Thread safety for download progress via `pyqtSignal`.
- `ModelManager.deep_cleanup()` for disk space recovery.
- Config caching with TTL to reduce disk I/O.
- WASAPI buffer overflow protection (capped at 60 s).

### Docs
- README.md / DEPLOY.md / MODEL_GUIDE.md rewritten.
- LICENSE (MIT) and NOTICE.md added.

---

## v1.x — Initial Development (2026-05-21 ~ 2026-06-06)

### v1.3 — TTS
- `tts_engine.py` with WindowsTTS (SAPI5) and ModelTTS.
- TTS page in GUI.

### v1.2 — Deployment
- Batch file encoding fix (CRLF + GBK).
- Model card checkbox auto-select.
- First packaging test on clean Windows machine.

### v1.1 — Core Features
- Engine singleton, model switching, chunked file transcription.
- Real-time recording (sounddevice + WASAPI loopback).
- Translation, floating subtitle overlay, model manager.

### v1.0 — Initial
- Project scaffold, ffmpeg bundling, venv setup.
- Fun-ASR-Nano-2512 registration fix.