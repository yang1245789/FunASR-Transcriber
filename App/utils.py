import os
import threading
import json
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

FUNASR_CACHE_NAME = "funasr_cache"
MODEL_SUBDIR_NAMES = ("models", "hub")

_config_lock = threading.Lock()
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


def get_temp_cache_dir():
    return os.path.join(os.environ.get("TEMP", os.path.join(APP_DIR, "Temp")),
                        FUNASR_CACHE_NAME)


def model_subdirs(model_dir):
    return [os.path.join(model_dir, d) for d in MODEL_SUBDIR_NAMES]


def model_safe_name(model_id):
    return model_id.replace("/", os.sep)


def resolve_model_path(model_id, model_dir):
    name = model_safe_name(model_id)
    for sub in model_subdirs(model_dir):
        path = os.path.join(sub, name)
        if os.path.exists(path):
            return path
    return None


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
        "recording": {"sample_rate": 16000, "chunk_duration": 5,
                       "device_index": -1},
        "subtitle": {
            "font_size": 28, "font_color": "#00FF88", "bg_opacity": 0.3,
            "max_lines": 3, "auto_hide_seconds": 5, "display_mode": "clean",
            "width": 800, "height": 120
        }
    }


def load_config(force_reload=False):
    global _config_cache, _config_mtime, _config_ttl
    now = time.time()
    with _config_lock:
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
            except json.JSONDecodeError:
                print("[Config] config.json 格式错误，使用默认配置")
            except Exception as e:
                print(f"[Config] 读取 config.json 失败: {e}")
        cfg = get_default_config()
        cfg["model_dir"] = get_default_model_dir()
        _config_cache = cfg
        _config_ttl = now + 2
        return cfg


def save_config(config):
    global _config_cache, _config_ttl
    with _config_lock:
        _config_cache = config
        _config_ttl = time.time() + 2
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[Config] 保存 config.json 失败: {e}")
