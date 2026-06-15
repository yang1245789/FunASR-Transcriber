import os
import json
import threading
import shutil
import tempfile
import re
import importlib
from pathlib import Path
from utils import get_config_path, get_default_model_dir

DEFAULT_CONFIG_PATH = get_config_path()

AVAILABLE_MODELS = {
    "FunAudioLLM/Fun-ASR-Nano-2512": {
        "name": "Fun-ASR-Nano-2512 (多语言主模型)",
        "description": "FunAudioLLM 官方多语言语音识别模型，支持中文普通话/方言/英语/日语/波斯语/俄语等30+语种，具备情感识别、时间戳和说话人日志能力。推荐作为主模型使用。",
        "size": "~3GB",
        "type": "asr",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/FunAudioLLM/Fun-ASR-Nano-2512",
        "category": "核心模型",
        "recommended": True,
        "can_realtime": True,
        "realtime_note": "下载后可直接用于实时转写"
    },
    "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch": {
        "name": "FSMN-VAD (语音活动检测)",
        "description": "阿里达摩院语音活动检测模型，自动检测语音段起止，切分长音频，提升识别准确率。配合主模型使用，支持16kHz音频。",
        "size": "~50MB",
        "type": "vad",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
        "category": "核心模型",
        "recommended": True,
        "can_realtime": True,
        "realtime_note": "实时转写必备，自动分段更精准"
    },
    "iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch": {
        "name": "CT-PUNC (标点预测)",
        "description": "阿里达摩院标点预测模型，为语音识别结果自动添加标点符号（逗号、句号、问号等），使输出更易读。支持中文。",
        "size": "~300MB",
        "type": "punc",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
        "category": "核心模型",
        "recommended": True,
        "can_realtime": True,
        "realtime_note": "实时转写推荐，输出带标点更易读"
    },
    "iic/SenseVoiceSmall": {
        "name": "SenseVoice-Small (轻量多语言)",
        "description": "阿里达摩院轻量级多语言语音识别模型，支持中/英/日/韩/粤语识别，具备情感识别和事件检测能力。速度快，适合实时转写场景。",
        "size": "~300MB",
        "type": "asr",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/iic/SenseVoiceSmall",
        "category": "核心模型",
        "recommended": True,
        "can_realtime": True,
        "realtime_note": "下载后可直接用于实时转写，速度更快"
    },
    "openai-mirror/whisper-large-v3-turbo": {
        "name": "Whisper-large-v3-turbo (OpenAI 快速版)",
        "description": "OpenAI Whisper 大模型 v3 的 turbo 版本，支持99种语言语音识别与翻译，具备强大的多语言能力和抗噪性能。魔塔社区镜像，下载速度更快。",
        "size": "~1.6GB",
        "type": "asr",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/openai-mirror/whisper-large-v3-turbo",
        "category": "第三方模型",
        "recommended": False,
        "can_realtime": False,
        "realtime_note": "需额外配置 Whisper 依赖，暂不支持实时转写"
    },
    "qwen/Qwen-Audio-Chat": {
        "name": "Qwen-Audio-Chat (通义千问音频对话)",
        "description": "通义千问多模态音频大模型，支持语音理解、多轮对话、音频内容分析、音乐理解等。可进行语音问答、音频摘要等高级任务。",
        "size": "~20GB",
        "type": "audio-llm",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/qwen/Qwen-Audio-Chat",
        "category": "第三方模型",
        "recommended": False,
        "can_realtime": False,
        "realtime_note": "大语言模型，需 transformers 框架，不支持实时转写"
    },
    "qwen/Qwen2-Audio-7B-Instruct": {
        "name": "Qwen2-Audio-7B-Instruct (通义千问2音频)",
        "description": "通义千问第二代音频大模型 7B 指令版，支持语音对话、音频分析、多语言语音理解。相比一代性能更强、效率更高。",
        "size": "~15GB",
        "type": "audio-llm",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/qwen/Qwen2-Audio-7B-Instruct",
        "category": "第三方模型",
        "recommended": False,
        "can_realtime": False,
        "realtime_note": "大语言模型，需 transformers 框架，不支持实时转写"
    },
    "iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch": {
        "name": "Paraformer-Large (中文高精度识别)",
        "description": "阿里达摩院 Paraformer 大模型，专注中文普通话识别，16kHz采样，8404词表。集成VAD和标点预测，适合高精度中文转写场景。",
        "size": "~900MB",
        "type": "asr",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        "category": "FunASR 官方模型",
        "recommended": False,
        "can_realtime": True,
        "realtime_note": "下载后可用于实时转写，中文精度更高"
    },
    "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch": {
        "name": "Seaco-Paraformer-Large (热词增强版)",
        "description": "基于 Paraformer 的热词增强模型，支持自定义热词列表，提升特定词汇识别率。适合专业术语、人名、品牌名等场景。",
        "size": "~1GB",
        "type": "asr",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        "category": "FunASR 官方模型",
        "recommended": False,
        "can_realtime": True,
        "realtime_note": "下载后可用于实时转写，热词场景推荐"
    },
    "iic/speech_campplus_sv_zh-cn_16k-common": {
        "name": "CAM++ 声纹识别 (说话人区分)",
        "description": "阿里达摩院声纹识别模型，16kHz中文场景，可识别不同说话人声音特征，用于说话人日志和说话人区分任务。",
        "size": "~10MB",
        "type": "speaker",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/iic/speech_campplus_sv_zh-cn_16k-common",
        "category": "FunASR 官方模型",
        "recommended": False,
        "can_realtime": False,
        "realtime_note": "辅助模型，用于说话人区分，不直接用于转写"
    },
    "iic/speech_timestamp_xlsr-pytorch": {
        "name": "XLSR 时间戳模型",
        "description": "基于 Facebook XLSR 的时间戳对齐模型，为识别结果提供精确的词语级时间戳，用于字幕对齐和卡拉OK效果。",
        "size": "~1GB",
        "type": "timestamp",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/iic/speech_timestamp_xlsr-pytorch",
        "category": "FunASR 官方模型",
        "recommended": False,
        "can_realtime": False,
        "realtime_note": "辅助模型，用于时间戳对齐，不直接用于转写"
    },
    "iic/SenseVoiceLarge": {
        "name": "SenseVoice-Large (高精度多语言)",
        "description": "SenseVoice 大参数版本，相比 Small 版本识别精度更高，支持更多语种和更复杂场景。适合对准确率要求极高的场景。",
        "size": "~2GB",
        "type": "asr",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/iic/SenseVoiceLarge",
        "category": "核心模型",
        "recommended": False,
        "can_realtime": True,
        "realtime_note": "下载后可用于实时转写，精度更高但速度较慢"
    },
    "FunAudioLLM/Fun-CosyVoice3-0.5B-2512": {
        "name": "CosyVoice 3.0-0.5B (语音合成)",
        "description": "阿里通义 CosyVoice 3.0 多语言语音合成模型(0.5B)，支持9种语言+18种中文方言，零样本语音克隆/情感/方言控制。需同时下载 ttsfrd 资源包。",
        "size": "~1.1GB",
        "type": "tts",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/FunAudioLLM/Fun-CosyVoice3-0.5B-2512",
        "category": "TTS 模型",
        "recommended": True,
        "can_realtime": False,
        "realtime_note": "仅用于语音合成，不支持实时转写"
    },
    "iic/CosyVoice-ttsfrd": {
        "name": "CosyVoice-ttsfrd (文本正则化资源)",
        "description": "CosyVoice 文本前端处理资源包，提升数字/日期/金额等文本规整质量。CosyVoice 3.0 的可选增强资源。",
        "size": "~50MB",
        "type": "tts",
        "source": "modelscope",
        "url": "https://modelscope.cn/models/iic/CosyVoice-ttsfrd",
        "category": "TTS 模型",
        "recommended": False,
        "can_realtime": False,
        "realtime_note": "仅用于语音合成文本前端处理"
    },
}

class ModelManager:
    def __init__(self, config_path=None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        self.model_dir = self.config.get("model_dir") or get_default_model_dir()
        os.environ['MODELSCOPE_CACHE'] = self.model_dir
        self._download_threads = {}
        self._local_models = {}
        self._disk_usage_cache = -1
        self._scan_local_models()

    def _get_modelscope_paths(self, model_id):
        model_folder = model_id.replace("/", os.sep)
        return [
            os.path.join(self.model_dir, "hub", model_folder),
            os.path.join(self.model_dir, "models", model_folder),
            os.path.join(self.model_dir, model_folder),
        ]

    def _find_model_dir(self, model_id):
        for path in self._get_modelscope_paths(model_id):
            if self._is_valid_model_dir(path):
                return path
        if "/" in model_id:
            org_name, model_name = model_id.split("/", 1)
            model_norm = re.sub(r'[^a-z0-9]', '', model_name.lower())
            for prefix in [os.path.join(self.model_dir, "hub"), os.path.join(self.model_dir, "models"), self.model_dir]:
                org_dir = os.path.join(prefix, org_name)
                if not os.path.isdir(org_dir):
                    continue
                try:
                    for entry in os.listdir(org_dir):
                        entry_full = os.path.join(org_dir, entry)
                        if not os.path.isdir(entry_full):
                            continue
                        if re.sub(r'[^a-z0-9]', '', entry.lower()) == model_norm:
                            if self._is_valid_model_dir(entry_full):
                                return entry_full
                except PermissionError:
                    continue
        return None

    def _is_valid_model_dir(self, path):
        if not os.path.isdir(path):
            return False
        has_config = os.path.exists(os.path.join(path, "configuration.json")) or os.path.exists(os.path.join(path, "config.json"))
        try:
            names = os.listdir(path)
        except PermissionError:
            return False
        has_model = any(f.endswith(('.pt', '.bin', '.safetensors', '.onnx')) for f in names if os.path.isfile(os.path.join(path, f)))
        return has_config or has_model

    def _scan_local_models(self):
        for known_id in AVAILABLE_MODELS:
            path = self._find_model_dir(known_id)
            if path:
                self._local_models[known_id] = path

    def get_local_models(self):
        return self._local_models

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, PermissionError):
                pass
        return {}

    def _save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def set_model_dir(self, path):
        self.model_dir = path
        self.config["model_dir"] = path
        self._save_config()
        os.environ['MODELSCOPE_CACHE'] = path
        self._local_models.clear()
        self._scan_local_models()

    def get_model_dir(self):
        return self.model_dir

    def get_available_models(self):
        return AVAILABLE_MODELS

    def is_model_downloaded(self, model_id):
        if model_id in self._local_models:
            return True
        path = self._find_model_dir(model_id)
        if path:
            self._local_models[model_id] = path
            return True
        return False

    def get_downloaded_models(self):
        downloaded = []
        for model_id, info in AVAILABLE_MODELS.items():
            if self.is_model_downloaded(model_id):
                downloaded.append({"id": model_id, **info, "status": "installed"})
        return downloaded

    def get_model_status(self):
        status = []
        for model_id, info in AVAILABLE_MODELS.items():
            is_dl = self.is_model_downloaded(model_id)
            status.append({
                "id": model_id,
                **info,
                "status": "installed" if is_dl else "available"
            })
        return status

    def download_model(self, model_id, progress_callback=None, complete_callback=None):
        if model_id not in AVAILABLE_MODELS:
            raise ValueError("未知模型: " + model_id)

        if self.is_model_downloaded(model_id):
            if complete_callback:
                complete_callback(model_id, "已安装")
            return

        os.environ['MODELSCOPE_CACHE'] = self.model_dir

        def _download():
            try:
                from modelscope import snapshot_download
                if progress_callback:
                    progress_callback(model_id, 0, "开始下载...")
                snapshot_download(model_id)
                if progress_callback:
                    progress_callback(model_id, 100, "下载完成")
                self._local_models.clear()
                self._disk_usage_cache = -1
                self._scan_local_models()
                if complete_callback:
                    complete_callback(model_id, "success")
            except Exception as e:
                if progress_callback:
                    progress_callback(model_id, -1, "下载失败: " + str(e))
                if complete_callback:
                    complete_callback(model_id, "error: " + str(e))

        thread = threading.Thread(target=_download, daemon=True)
        self._download_threads[model_id] = thread
        thread.start()

    def delete_model(self, model_id):
        deleted = False
        for path in self._get_modelscope_paths(model_id):
            if os.path.exists(path):
                shutil.rmtree(path)
                deleted = True
        if model_id in self._local_models:
            del self._local_models[model_id]
        self._disk_usage_cache = -1
        return deleted

    def deep_cleanup(self):
        freed = 0
        temp_dir = os.path.join(tempfile.gettempdir(), "funasr_cache")
        if os.path.exists(temp_dir):
            try:
                total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(temp_dir) for f in fs)
                shutil.rmtree(temp_dir)
                freed += total
            except Exception:
                pass
        for root, dirs, _ in os.walk(self.model_dir):
            for d in dirs:
                if d.startswith(".") and ("temp" in d or "_temp" in d):
                    path = os.path.join(root, d)
                    try:
                        total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(path) for f in fs)
                        shutil.rmtree(path)
                        freed += total
                    except Exception:
                        pass
        qwen_dup = os.path.join(self.model_dir, "Qwen")
        if os.path.exists(qwen_dup):
            try:
                total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(qwen_dup) for f in fs)
                shutil.rmtree(qwen_dup)
                freed += total
            except Exception:
                pass
        self._local_models.clear()
        self._disk_usage_cache = -1
        self._scan_local_models()
        return freed

    def get_disk_usage(self, force_recalc=False):
        if not force_recalc and self._disk_usage_cache >= 0:
            return self._disk_usage_cache
        total = 0
        if not os.path.isdir(self.model_dir):
            self._disk_usage_cache = total
            return total
        for item in os.listdir(self.model_dir):
            item_path = os.path.join(self.model_dir, item)
            if item.startswith(".") or not os.path.isdir(item_path):
                continue
            for dirpath, _, filenames in os.walk(item_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        if os.path.exists(fp):
                            total += os.path.getsize(fp)
                    except OSError:
                        pass
        self._disk_usage_cache = total
        return total

    @staticmethod
    def format_size(size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
