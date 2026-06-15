import os
import threading
import tempfile
from typing import Optional, List, Tuple
from utils import load_config, get_default_model_dir

FUNASR_CACHE_NAME = "funasr_cache"
MODEL_CACHE_SUBDIRS = ["models", "hub"]

WINDOWS_VOICES_FALLBACK: List[Tuple[str, str]] = [
    ("", "系统默认语音"),
]

MODEL_TTS_INFO = {
    "FunAudioLLM/Fun-CosyVoice3-0.5B-2512": {
        "name": "CosyVoice 3.0-0.5B",
        "description": "阿里通义 CosyVoice 3.0，9语种+18方言，零样本语音克隆，支持情感/方言精细控制",
        "size": "~1.1GB",
        "speakers": ["默认"],
        "needs_ttsfrd": True,
    },
}

TTSFRD_INFO = {
    "iic/CosyVoice-ttsfrd": {
        "name": "CosyVoice-ttsfrd (文本正则化)",
        "description": "CosyVoice 文本前端资源，提升数字/日期/金额等规整质量",
        "size": "~50MB",
    },
}


class TTSResult:
    def __init__(
        self,
        audio_path: Optional[str] = None,
        duration: float = 0.0,
        success: bool = False,
        error: str = "",
    ):
        self.audio_path = audio_path
        self.duration = duration
        self.success = success
        self.error = error


class WindowsTTS:
    def __init__(self):
        self._lock = threading.Lock()

    @staticmethod
    def is_available() -> bool:
        try:
            import pyttsx3  # noqa
            return True
        except ImportError:
            return False

    def get_voices(self) -> List[Tuple[str, str]]:
        voices: List[Tuple[str, str]] = list(WINDOWS_VOICES_FALLBACK)
        try:
            import pyttsx3
            engine = pyttsx3.init()
            for v in engine.getProperty("voices"):
                exists = any(v.id == item[0] for item in voices)
                if not exists:
                    name = v.name or v.id.split("\\")[-1]
                    voices.append((v.id, name))
            engine.stop()
        except Exception:
            pass
        return voices

    def synthesize(
        self,
        text: str,
        voice_id: str = "",
        rate: int = 0,
        output_path: Optional[str] = None,
    ) -> TTSResult:
        if not text or not text.strip():
            return TTSResult(success=False, error="文本为空")
        if len(text) > 5000:
            return TTSResult(success=False, error="文本过长（最多 5000 字符）")
        try:
            import pyttsx3
            import soundfile as sf

            with self._lock:
                engine = pyttsx3.init()
                try:
                    if voice_id:
                        for v in engine.getProperty("voices"):
                            if v.id == voice_id:
                                engine.setProperty("voice", v.id)
                                break
                    if rate != 0:
                        engine.setProperty("rate", engine.getProperty("rate") + rate)

                    if output_path is None:
                        fd, output_path = tempfile.mkstemp(suffix=".wav")
                        os.close(fd)

                    engine.save_to_file(text, output_path)
                    engine.runAndWait()
                finally:
                    engine.stop()

            if os.path.exists(output_path) and os.path.getsize(output_path) > 44:
                audio, sr = sf.read(output_path)
                duration = len(audio) / sr if sr > 0 else 0
                return TTSResult(audio_path=output_path, duration=duration, success=True)
            return TTSResult(success=False, error="语音生成失败（文件为空）")
        except Exception as e:
            return TTSResult(success=False, error=str(e))


def _resolve_model_path(model_name: str, model_dir: str) -> Optional[str]:
    for subdir in MODEL_CACHE_SUBDIRS:
        path = os.path.join(model_dir, subdir, model_name.replace("/", os.sep))
        if os.path.exists(path):
            return path
    return None


def _ensure_ascii_cache(model_dir: str, model_name: str) -> Optional[str]:
    has_non_ascii = any(ord(c) > 127 for c in model_dir)
    if not has_non_ascii:
        return model_dir
    local_path = _resolve_model_path(model_name, model_dir)
    if not local_path:
        return model_dir
    import shutil
    import subprocess as _sp
    temp_cache = os.path.join(tempfile.gettempdir(), FUNASR_CACHE_NAME)
    target = os.path.join(temp_cache, "models", model_name.replace("/", os.sep))
    marker = os.path.join(target, ".copied")
    if not os.path.exists(marker):
        if os.path.exists(target):
            shutil.rmtree(target)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        try:
            _sp.run(['cmd', '/c', 'mklink', '/J', target, local_path], check=True, capture_output=True)
        except Exception:
            def _ignore_submodels(d, contents):
                return [c for c in contents if os.path.isdir(os.path.join(d, c)) and
                        any(f.endswith(('.pt', '.bin', '.safetensors'))
                            for r, _, fs in os.walk(os.path.join(d, c)) for f in fs)]
            shutil.copytree(local_path, target, ignore=_ignore_submodels)
        try:
            with open(marker, "w") as f:
                f.write("1")
        except Exception:
            pass
    return temp_cache


class ModelTTS:
    def __init__(self):
        self.model = None
        self._last_model_name: Optional[str] = None
        self._last_device: Optional[str] = None

    @staticmethod
    def is_available() -> bool:
        return True

    @staticmethod
    def get_models():
        return MODEL_TTS_INFO

    def load_model(
        self,
        model_name: str = "FunAudioLLM/Fun-CosyVoice3-0.5B-2512",
        device: Optional[str] = None,
    ) -> bool:
        if self.model and self._last_model_name == model_name and self._last_device == device:
            return True
        try:
            fresh = load_config()
            device = device or fresh.get("device", "cuda:0")
            import torch
            if device.startswith("cuda") and not torch.cuda.is_available():
                device = "cpu"

            model_dir = fresh.get("model_dir") or get_default_model_dir()
            cache_dir = _ensure_ascii_cache(model_dir, model_name)
            if cache_dir != model_dir:
                os.environ["MODELSCOPE_CACHE"] = cache_dir

            local_path = _resolve_model_path(model_name, model_dir)
            from funasr import AutoModel

            if local_path:
                self.model = AutoModel(model_dir=local_path, device=device, trust_remote_code=False)
            else:
                self.model = AutoModel(model=model_name, device=device, trust_remote_code=False)

            self._last_model_name = model_name
            self._last_device = device
            return True
        except Exception as e:
            print(f"[ModelTTS] 加载失败: {e}")
            self.model = None
            return False

    def synthesize(
        self,
        text: str,
        model_name: str = "FunAudioLLM/Fun-CosyVoice3-0.5B-2512",
        device: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs,
    ) -> TTSResult:
        if not text or not text.strip():
            return TTSResult(success=False, error="文本为空")
        if len(text) > 5000:
            return TTSResult(success=False, error="文本过长（最多 5000 字符）")
        try:
            if not self.load_model(model_name, device):
                return TTSResult(success=False, error=f"模型加载失败: {model_name}")

            if output_path is None:
                fd, output_path = tempfile.mkstemp(suffix=".wav")
                os.close(fd)

            gen_kw = {"input": text}
            if kwargs.get("spk_id"):
                gen_kw["spk_id"] = kwargs["spk_id"]

            result = self.model.generate(**gen_kw)

            if result and len(result) > 0:
                import soundfile as sf
                if isinstance(result[0], dict):
                    entry = result[0]
                    audio = entry.get("audio") or entry.get("wav") or entry.get("array")
                    sr = entry.get("sample_rate") or entry.get("sampling_rate") or 24000
                    if audio is not None:
                        sf.write(output_path, audio, sr)
                        duration = len(audio) / sr
                        return TTSResult(audio_path=output_path, duration=duration, success=True)
            return TTSResult(success=False, error="模型未生成音频")
        except Exception as e:
            return TTSResult(success=False, error=f"合成失败: {e}")

    def synthesize_with_prompt(
        self,
        text: str,
        prompt_audio_path: str,
        prompt_text: str = "",
        model_name: str = "FunAudioLLM/Fun-CosyVoice3-0.5B-2512",
        device: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> TTSResult:
        if not text or not text.strip():
            return TTSResult(success=False, error="文本为空")
        if not prompt_audio_path or not os.path.exists(prompt_audio_path):
            return TTSResult(success=False, error="参考音频文件不存在")
        try:
            if not self.load_model(model_name, device):
                return TTSResult(success=False, error=f"模型加载失败: {model_name}")

            import soundfile as sf
            import numpy as np

            prompt_audio, prompt_sr = sf.read(prompt_audio_path)
            if prompt_sr != 16000:
                import scipy.signal
                target_len = int(len(prompt_audio) * 16000 / prompt_sr)
                prompt_audio = scipy.signal.resample(prompt_audio, target_len)
                prompt_sr = 16000
            if len(prompt_audio.shape) > 1:
                prompt_audio = np.mean(prompt_audio, axis=1)

            if output_path is None:
                fd, output_path = tempfile.mkstemp(suffix=".wav")
                os.close(fd)

            gen_kw = {"input": text, "prompt_speech": prompt_audio}
            if prompt_text:
                gen_kw["prompt_text"] = prompt_text

            result = self.model.generate(**gen_kw)
            if result and len(result) > 0:
                import soundfile as sf_write
                if isinstance(result[0], dict):
                    entry = result[0]
                    audio = entry.get("audio") or entry.get("wav") or entry.get("array")
                    sr = entry.get("sample_rate") or entry.get("sampling_rate") or 24000
                    if audio is not None:
                        sf_write.write(output_path, audio, sr)
                        duration = len(audio) / sr
                        return TTSResult(audio_path=output_path, duration=duration, success=True)
            return TTSResult(success=False, error="人声复刻未生成音频")
        except Exception as e:
            return TTSResult(success=False, error=f"人声复刻失败: {e}")


class TTSManager:
    def __init__(self):
        self.win_tts = WindowsTTS()
        self.model_tts = ModelTTS()

    @staticmethod
    def get_engines():
        return [
            ("win", "Windows 内置 TTS (SAPI5)"),
            ("model", "模型 TTS (CosyVoice)"),
        ]

    def synthesize(
        self,
        text: str,
        engine: str = "win",
        voice: str = "",
        output_path: Optional[str] = None,
        **kwargs,
    ) -> TTSResult:
        if engine == "win":
            rate = kwargs.get("rate", 0)
            return self.win_tts.synthesize(text, voice_id=voice, rate=rate, output_path=output_path)
        elif engine == "model":
            model_name = kwargs.get("model_name", "FunAudioLLM/Fun-CosyVoice3-0.5B-2512")
            return self.model_tts.synthesize(text, model_name=model_name, output_path=output_path, **kwargs)
        return TTSResult(success=False, error="未知引擎")

    def synthesize_with_prompt(
        self,
        text: str,
        prompt_audio_path: str,
        prompt_text: str = "",
        model_name: str = "FunAudioLLM/Fun-CosyVoice3-0.5B-2512",
        output_path: Optional[str] = None,
    ) -> TTSResult:
        return self.model_tts.synthesize_with_prompt(
            text=text,
            prompt_audio_path=prompt_audio_path,
            prompt_text=prompt_text,
            model_name=model_name,
            output_path=output_path,
        )
