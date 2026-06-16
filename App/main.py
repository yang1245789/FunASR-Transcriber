import os
import sys
import re
import threading
import time
import ctypes
import traceback
import numpy as np
import sounddevice as sd
from utils import (load_config, get_default_model_dir,
                   get_temp_cache_dir, model_subdirs, model_safe_name)


def _ensure_ffmpeg():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    app_ffmpeg = os.path.join(app_dir, "ffmpeg.exe")
    if os.path.exists(app_ffmpeg):
        parts = os.environ.get("PATH", "").split(os.pathsep)
        if app_dir not in parts:
            os.environ["PATH"] = app_dir + os.pathsep + os.environ.get("PATH", "")

_ensure_ffmpeg()


def _read_fresh_config():
    return load_config(force_reload=True)


class TranscriptionEngine:
    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls, config=None):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config=None):
        if self._initialized:
            return
        self.config = config or load_config()
        self.model = None
        self.translation_model = None
        self.tokenizer = None
        self._last_model_name = None
        self._last_device = None
        self._init_lock = threading.Lock()
        self._initialized = True

    def reset_for_new_model(self):
        self.model = None
        self.translation_model = None
        self.tokenizer = None
        self._last_model_name = None
        self._last_device = None

    def init_model(self, model_name=None, device=None, progress_callback=None):
        with self._init_lock:
            return self._init_model_impl(model_name, device, progress_callback)

    def _init_model_impl(self, model_name=None, device=None, progress_callback=None):
        import torch
        import shutil
        import tempfile
        from utils import model_subdirs, model_safe_name, get_temp_cache_dir

        fresh = _read_fresh_config()
        model_name = model_name or fresh.get("model_name", "iic/SenseVoiceSmall")
        device = device or fresh.get("device", "cuda:0")
        self.config = fresh

        if self._last_model_name == model_name and self._last_device == device and self.model:
            print(f"[Engine] 模型已加载且未变化: {model_name}, 跳过重新加载")
            return True

        is_audio_llm = "Fun-ASR" in model_name or "FunAudioLLM" in model_name
        model_dir = fresh.get("model_dir", get_default_model_dir())
        print(f"[Engine] 初始化模型: {model_name}, 设备: {device}")

        safe_name = model_safe_name(model_name)
        local_model_path = None
        for sub in model_subdirs(model_dir):
            p = os.path.join(sub, safe_name)
            if os.path.isdir(p):
                local_model_path = p
                break

        has_non_ascii = any(ord(c) > 127 for c in model_dir)

        if has_non_ascii and local_model_path:
            temp_cache = get_temp_cache_dir()
            temp_model_dir = os.path.join(temp_cache, safe_name)
            if not os.path.exists(os.path.join(temp_model_dir, "model.pt")):
                print("检测到中文路径，复制模型到临时目录...")
                if os.path.exists(temp_model_dir):
                    shutil.rmtree(temp_model_dir)
                os.makedirs(os.path.dirname(temp_model_dir), exist_ok=True)
                shutil.copytree(local_model_path, temp_model_dir)
            os.environ['MODELSCOPE_CACHE'] = temp_cache
        else:
            os.environ['MODELSCOPE_CACHE'] = model_dir

        if device.startswith("cuda"):
            if not torch.cuda.is_available():
                print("[Engine] CUDA不可用，回退到CPU")
                device = "cpu"
            else:
                cuda_count = torch.cuda.device_count()
                cuda_name = torch.cuda.get_device_name(0) if cuda_count > 0 else "unknown"
                print(f"CUDA: {cuda_count} devices, {cuda_name}")

        if is_audio_llm:
            try:
                from funasr.models.fun_asr_nano import model as _nano_model
                from funasr.models.fun_asr_nano import ctc as _nano_ctc
            except ImportError:
                print("[Engine] FunASRNano 模块导入失败，可能影响模型加载")

        model_kwargs = {
            "model": model_name,
            "device": device,
            "trust_remote_code": False,
        }
        if not is_audio_llm:
            model_kwargs["vad_model"] = "fsmn-vad"
            model_kwargs["vad_kwargs"] = {"max_single_segment_time": fresh.get("vad_max_segment", 30000)}
            if fresh.get("use_punc", True):
                model_kwargs["punc_model"] = "ct-punc-c"

        from funasr import AutoModel
        self.model = AutoModel(**model_kwargs)
        self._last_model_name = model_name
        self._last_device = device
        print(f"[Engine] 模型加载成功: {model_name}")
        return True

    @staticmethod
    def _deduplicate_text(text):
        if not text or len(text) < 10:
            return text
        pattern = re.compile(r'([一-鿿]{2,6})(?:[，,、\s]*\1){2,}')
        result = pattern.sub(lambda m: m.group(1), text)
        if len(result) > 5:
            for ch in set(result):
                if result.count(ch) > 20:
                    result = result.replace(ch * 20, '')
        if len(result) > 5000:
            result = result[:5000]
        return result

    def transcribe_file(self, audio_path, language=None):
        if not self.model:
            return "错误: 模型未初始化"
        if not os.path.exists(audio_path):
            return "错误: 文件不存在 - " + audio_path

        try:
            fresh = _read_fresh_config()
            lang = language or fresh.get("language", "auto")
            use_itn = fresh.get("use_itn", True)
            batch_size = fresh.get("batch_size", 1)

            import subprocess, tempfile
            total_duration = 0
            try:
                probe = subprocess.run(
                    ["ffmpeg", "-i", audio_path],
                    capture_output=True, timeout=10
                )
                stderr_text = probe.stderr.decode("utf-8", errors="replace") if probe.stderr else ""
                for line in stderr_text.split("\n"):
                    if "Duration:" in line:
                        parts = line.split("Duration:")[1].split(",")[0].strip()
                        parts_list = parts.split(":")
                        if len(parts_list) >= 3:
                            try:
                                total_duration = (float(parts_list[0]) * 3600 +
                                                  float(parts_list[1]) * 60 +
                                                  float(parts_list[2].split(".")[0]))
                            except ValueError:
                                total_duration = 0
                        break
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                print(f"[Engine] ffprobe 失败: {e}，使用原始路径识别")

            print(f"[Engine] 音频时长: {total_duration:.1f}s")

            if total_duration > 60:
                wav_tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
                try:
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", audio_path, "-ar", "16000",
                         "-ac", "1", "-f", "wav", wav_tmp],
                        capture_output=True, timeout=120
                    )
                    import soundfile as sf
                    audio, sr = sf.read(wav_tmp, dtype="float32")
                    if audio.ndim > 1:
                        audio = audio.mean(axis=1)
                    chunk_samples = int(30 * sr)
                    overlap_samples = int(1 * sr)
                    step_samples = chunk_samples - overlap_samples
                    texts = []
                    chunk_idx = 0
                    for start in range(0, len(audio), step_samples):
                        end = min(start + chunk_samples, len(audio))
                        chunk = audio[start:end]
                        if len(chunk) / sr < 1.0:
                            continue
                        chunk_tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
                        try:
                            sf.write(chunk_tmp, chunk, sr)
                            res = self.model.generate(
                                input=chunk_tmp, force_yes=True,
                                batch_size=batch_size, language=lang, use_itn=use_itn)
                            if res:
                                for r in res:
                                    if isinstance(r, dict) and "text" in r and r["text"].strip():
                                        texts.append(r["text"])
                            chunk_idx += 1
                        except Exception as e:
                            print(f"[Engine] 块 {chunk_idx} 失败: {e}")
                        finally:
                            try:
                                os.unlink(chunk_tmp)
                            except OSError:
                                pass
                    if texts:
                        combined = " ".join(texts)
                        return self._translate_if_needed(self._deduplicate_text(combined), lang)
                    return "识别结果为空"
                finally:
                    try:
                        os.unlink(wav_tmp)
                    except OSError:
                        pass

            res = self.model.generate(
                input=audio_path,
                force_yes=True,
                batch_size=batch_size,
                language=lang,
                use_itn=use_itn
            )
            if res and len(res) > 0:
                texts = []
                for r in res:
                    if isinstance(r, dict) and "text" in r:
                        texts.append(r["text"])
                if texts:
                    text = "\n".join(texts)
                    text = self._deduplicate_text(text)
                    return self._translate_if_needed(text, lang)
            return "识别结果为空"
        except Exception as e:
            return "识别出错: " + str(e) + "\n" + traceback.format_exc()

    def _translate_if_needed(self, text, source_lang):
        fresh = _read_fresh_config()
        if fresh.get("target_language") == "zh" and source_lang not in ("zh", "zh-CN", "zh-TW", "auto"):
            mode = fresh.get("translation_mode", "builtin")
            if mode == "builtin" and self.model:
                try:
                    if hasattr(self.model, 'generate'):
                        res = self.model.generate(input=text, language="zh", use_itn=False, batch_size=1)
                        if res and len(res) > 0:
                            translated_texts = []
                            for r in res:
                                if isinstance(r, dict) and "text" in r:
                                    translated_texts.append(r["text"])
                                elif isinstance(r, str):
                                    translated_texts.append(r)
                            if translated_texts:
                                translated = " ".join(translated_texts)
                                if translated and translated != text:
                                    return translated
                except Exception as e:
                    print(f"[Translate] 内置翻译失败: {e}")
            elif mode == "local" and self.translation_model:
                try:
                    inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                    outputs = self.translation_model.generate(**inputs, max_length=512)
                    return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                except Exception as e:
                    print(f"[Translate] 本地翻译失败: {e}")
        return text

    def transcribe_stream(self, audio_chunk, language=None):
        if not self.model:
            return ""
        try:
            fresh = _read_fresh_config()
            lang = language or fresh.get("language", "auto")
            use_itn = fresh.get("use_itn", True)
            res = self.model.generate(
                input=audio_chunk,
                force_yes=True,
                batch_size=1,
                language=lang,
                use_itn=use_itn
            )
            if res and len(res) > 0:
                texts = []
                for r in res:
                    if isinstance(r, dict) and "text" in r:
                        texts.append(r["text"])
                if texts:
                    combined = "".join(texts)
                    return self._translate_if_needed(combined, lang)
            return ""
        except Exception as e:
            if "CUDA out of memory" in str(e) or "OOM" in str(e):
                print(f"[Stream] CUDA内存不足: {e}")
            elif "KeyboardInterrupt" not in str(type(e).__name__):
                print(f"[Stream] 转写异常: {e}")
            return ""


class RealtimeRecorder:
    def __init__(self, engine, config=None):
        self.engine = engine
        self.config = config or load_config()
        self.recording_config = self.config.get("recording", {})
        self.sample_rate = self.recording_config.get("sample_rate", 16000)
        self.chunk_duration = self.recording_config.get("chunk_duration", 5)
        self.is_recording = False
        self.audio_buffer = []
        self._buffer_lock = threading.Lock()
        self.stream = None
        self._thread = None
        self.on_result = None
        self.loopback = False
        self._buffer_overflow_count = 0

    def start(self, device_index=None, loopback=False):
        if self.is_recording:
            return
        self.is_recording = True
        with self._buffer_lock:
            self.audio_buffer = []
        self.loopback = loopback
        ok = False
        if loopback:
            ok = self._wasapi_loopback_start(device_index)
        else:
            ok = self._sounddevice_start(device_index)
        if not ok:
            self.is_recording = False
            return
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        print("实时录音转写已启动" + (" (内录)" if loopback else ""))

    def _sounddevice_start(self, device_index):
        idx = device_index if device_index is not None else self.recording_config.get("device_index", -1)
        device_id = None if idx == -1 else idx
        channels = 1
        if device_id is not None:
            try:
                dev = sd.query_devices(device_id)
                channels = dev.get('max_input_channels', 1)
            except Exception:
                pass
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=channels,
                dtype=np.float32,
                device=device_id,
                callback=self._audio_callback
            )
            self.stream.start()
            return True
        except Exception as e:
            print(f"[SoundDevice] 启动录音失败: {e}")
            return False

    def _wasapi_loopback_start(self, device_index):
        try:
            import comtypes
            from comtypes import CLSCTX_ALL, GUID, COMMETHOD
            from comtypes.client import CreateObject
            from ctypes import byref, POINTER, c_uint32, c_uint64, c_ubyte, c_ulong
            from pycaw.api.mmdeviceapi import IMMDeviceEnumerator, IMMDevice
            from pycaw.api.audioclient import IAudioClient

            CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
            IID_IAudioCaptureClient = GUID("{C8ADBD64-E71E-48A0-A4DE-185C395CD317}")
            AUDCLNT_STREAMFLAGS_LOOPBACK = 0x00020000

            class IAudioCaptureClient(comtypes.IUnknown):
                _iid_ = IID_IAudioCaptureClient
                _methods_ = [
                    COMMETHOD([], c_ulong, "GetBuffer",
                        (["out"], POINTER(POINTER(c_ubyte)), "ppData"),
                        (["out"], POINTER(c_uint32), "pNumFramesToRead"),
                        (["out"], POINTER(c_uint32), "pdwFlags"),
                        (["out"], POINTER(c_uint64), "pu64DevicePosition"),
                        (["out"], POINTER(c_uint64), "pu64QPCPosition")),
                    COMMETHOD([], c_ulong, "ReleaseBuffer",
                        (["in"], c_uint32, "NumFramesRead")),
                ]

            enumerator = CreateObject(CLSID_MMDeviceEnumerator, interface=IMMDeviceEnumerator)
            device_ptr = enumerator.GetDefaultAudioEndpoint(0, 0)
            device = device_ptr.QueryInterface(IMMDevice)
            audio_unknown = device.Activate(byref(IAudioClient._iid_), CLSCTX_ALL, POINTER(c_ulong)())
            audio_client = audio_unknown.QueryInterface(IAudioClient)
            wf_ptr = audio_client.GetMixFormat()
            wf = wf_ptr.contents
            self._wasapi_samplerate = wf.nSamplesPerSec
            self._wasapi_channels = wf.nChannels
            REFERENCE_TIME = 10000000
            hr = audio_client.Initialize(0, AUDCLNT_STREAMFLAGS_LOOPBACK,
                                         100 * REFERENCE_TIME // 1000, 0, wf_ptr, POINTER(GUID)())
            if hr != 0:
                print(f"WASAPI loopback 初始化失败: 0x{hr & 0xFFFFFFFF:08x}")
                return False
            capture_unknown = audio_client.GetService(byref(IID_IAudioCaptureClient))
            capture_client = capture_unknown.QueryInterface(IAudioCaptureClient)
            audio_client.Start()
            self._wasapi_audio_client = audio_client
            self._wasapi_capture_client = capture_client
            self._wasapi_thread = threading.Thread(target=self._wasapi_capture_loop, daemon=True)
            self._wasapi_thread.start()
            return True
        except Exception as e:
            print(f"WASAPI 内录启动失败: {e}")
            return False

    def _wasapi_capture_loop(self):
        import scipy.signal
        max_buffer_seconds = 60
        while self.is_recording:
            try:
                data_ptr, nframes_val, flags_val, _, _ = self._wasapi_capture_client.GetBuffer()
                if nframes_val > 0:
                    if flags_val & 0x2:
                        self._wasapi_capture_client.ReleaseBuffer(nframes_val)
                        time.sleep(0.01)
                        continue
                    buf_ptr = ctypes.cast(data_ptr, ctypes.POINTER(ctypes.c_float))
                    total_samples = nframes_val * self._wasapi_channels
                    audio = np.ctypeslib.as_array(buf_ptr, shape=(total_samples,)).copy()
                    audio = audio.reshape(-1, self._wasapi_channels)
                    if self._wasapi_channels > 1:
                        audio = np.mean(audio, axis=1)
                    if self._wasapi_samplerate != self.sample_rate:
                        nsamples = int(len(audio) * self.sample_rate / self._wasapi_samplerate)
                        if nsamples > 0:
                            audio = scipy.signal.resample(audio, nsamples).astype(np.float32)
                    with self._buffer_lock:
                        max_samples = max_buffer_seconds * self.sample_rate
                        buffer_len = len(self.audio_buffer)
                        if buffer_len > max_samples * 0.9 and self._buffer_overflow_count == 0:
                            print(f"[WASAPI] 缓冲区即将占满 ({buffer_len/self.sample_rate:.0f}s)")
                            self._buffer_overflow_count += 1
                        if buffer_len > max_samples:
                            discard = buffer_len - int(max_buffer_seconds * 0.5 * self.sample_rate)
                            del self.audio_buffer[:discard]
                        self.audio_buffer.extend(audio.tolist())
                    self._wasapi_capture_client.ReleaseBuffer(nframes_val)
                else:
                    time.sleep(0.005)
            except Exception:
                time.sleep(0.01)

    def stop(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        if getattr(self, '_wasapi_audio_client', None):
            try:
                self._wasapi_audio_client.Stop()
            except Exception:
                pass
            self._wasapi_audio_client = None
            self._wasapi_capture_client = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        print("实时录音转写已停止")

    def _audio_callback(self, indata, frames, time_info, status):
        if self.is_recording:
            with self._buffer_lock:
                if self.loopback and indata.shape[1] > 1:
                    self.audio_buffer.extend(np.mean(indata, axis=1).tolist())
                else:
                    self.audio_buffer.extend(indata[:, 0].tolist())

    def _process_loop(self):
        chunk_samples = int(self.sample_rate * self.chunk_duration)
        while self.is_recording:
            chunk = None
            with self._buffer_lock:
                if len(self.audio_buffer) >= chunk_samples:
                    chunk = np.array(self.audio_buffer[:chunk_samples], dtype=np.float32)
                    del self.audio_buffer[:chunk_samples]
            if chunk is not None and np.abs(chunk).max() > 0.01:
                result = self.engine.transcribe_stream(chunk)
                if result and self.on_result:
                    self.on_result(result)
            else:
                time.sleep(0.1)

    @staticmethod
    def get_available_devices():
        devices = sd.query_devices()
        result = []
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                result.append({"index": i, "name": d['name'], "channels": d['max_input_channels']})
        return result

    @staticmethod
    def get_loopback_devices():
        result = []
        try:
            import comtypes
            from comtypes import CLSCTX_ALL, GUID
            from comtypes.client import CreateObject
            from pycaw.api.mmdeviceapi import IMMDeviceEnumerator
            from pycaw.constants import DEVICE_STATE

            CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
            enumerator = CreateObject(CLSID_MMDeviceEnumerator, interface=IMMDeviceEnumerator)
            devices = enumerator.EnumAudioEndpoints(0, DEVICE_STATE.ACTIVE.value)
            count = devices.GetCount()
            if count > 0:
                result.append({"index": -1, "name": "系统音频输出 (WASAPI内录)", "channels": 2})
        except Exception:
            pass
        return result


def transcribe_file_wrapper(audio_path, config=None, engine=None):
    cfg = config or _read_fresh_config()
    eng = engine or TranscriptionEngine(cfg)
    if not eng.model:
        eng.init_model()
    return eng.transcribe_file(audio_path)


if __name__ == "__main__":
    config = load_config()
    engine = TranscriptionEngine(config)
    engine.init_model()
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        result = engine.transcribe_file(audio_path)
        print(result)
    else:
        print("用法: python main.py <audio_file_path>")
