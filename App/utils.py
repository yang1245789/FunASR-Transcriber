import os
import sys
import json
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

_config_cache = None
_config_mtime = 0
_config_ttl = 0

def get_app_dir():
    return APP_DIR

def get_config_path():
    return CONFIG_PATH

def get_default_model_dir():
    env_cache = os.environ.get("MODELSCOPE_CACHE")
    if env_cache and os.path.isdir(env_cache):
        return env_cache
    local = os.path.join(APP_DIR, "models")
    if os.path.isdir(local):
        return local
    os.makedirs(local, exist_ok=True)
    return local

def get_default_config():
    return {
        "model_dir": "",
        "model_name": "iic/SenseVoiceSmall",
        "device": "cuda:0",
        "language": "auto",
        "target_language": "zh",
        "translation_mode": "builtin",
        "use_itn": True,
        "use_punc": True,
        "batch_size": 1,
        "vad_max_segment": 30000,
        "recording": {"sample_rate": 16000, "chunk_duration": 5, "device_index": -1},
        "subtitle": {
            "font_size": 28, "font_color": "#00FF88", "bg_opacity": 0.3,
            "max_lines": 3, "auto_hide_seconds": 5, "display_mode": "clean",
            "width": 800, "height": 120
        }
    }

def load_config(force_reload=False):
    global _config_cache, _config_mtime, _config_ttl
    now = time.time()
    if not force_reload and _config_cache is not None and now < _config_ttl:
        return _config_cache
    if os.path.exists(CONFIG_PATH):
        try:
            mtime = os.path.getmtime(CONFIG_PATH)
            if not force_reload and _config_cache is not None and mtime <= _config_mtime:
                _config_ttl = now + 2
                return _config_cache
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if not cfg.get("model_dir"):
                cfg["model_dir"] = get_default_model_dir()
            _config_cache = cfg
            _config_mtime = mtime
            _config_ttl = now + 2
            return cfg
        except Exception:
            pass
    cfg = get_default_config()
    cfg["model_dir"] = get_default_model_dir()
    _config_cache = cfg
    return cfg

def save_config(config):
    global _config_cache, _config_ttl
    _config_cache = config
    _config_ttl = time.time() + 2
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
