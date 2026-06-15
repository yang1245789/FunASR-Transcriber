import sys
import os
import threading

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QFileDialog, QTabWidget, QScrollArea, QFrame,
    QProgressBar, QTextEdit,
    QGroupBox, QFormLayout, QStackedWidget, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QLinearGradient, QBrush
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import load_config, save_config
from main import TranscriptionEngine, RealtimeRecorder
from model_manager import ModelManager
from subtitle_overlay import SubtitleOverlay
from tts_engine import TTSManager, TTSResult, MODEL_TTS_INFO

STYLESHEET = """
QMainWindow { background-color: #0a0a1a; }
QWidget { background-color: transparent; }
QFrame#mainFrame { background-color: #0a0a1a; border-radius: 12px; }
QFrame#sidebar {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0d1b2a, stop:1 #1b263b);
    border-radius: 12px 0 0 12px;
    border-right: 1px solid #00FF8833;
}
QFrame#contentArea { background-color: #0a0a1a; border-radius: 0 12px 12px 0; }
QPushButton#navBtn {
    background-color: transparent; color: #8899aa; border: none;
    padding: 12px 16px; text-align: left; font-size: 14px; border-radius: 8px; font-weight: bold;
}
QPushButton#navBtn:hover { background-color: #00FF8822; color: #00FF88; }
QPushButton#navBtn:checked {
    background-color: #00FF8833; color: #00FF88; border-left: 3px solid #00FF88;
}
QPushButton#actionBtn {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FF88, stop:1 #00cc6a);
    color: #0a0a1a; border: none; padding: 12px 24px; border-radius: 8px;
    font-size: 14px; font-weight: bold;
}
QPushButton#actionBtn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00cc6a, stop:1 #00FF88);
}
QPushButton#actionBtn:disabled { background-color: #333344; color: #666677; }
QPushButton#dangerBtn {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff4444, stop:1 #cc3333);
    color: white; border: none; padding: 8px 16px; border-radius: 6px; font-size: 12px;
}
QPushButton#secondaryBtn {
    background-color: #1b263b; color: #00FF88; border: 1px solid #00FF8844;
    padding: 8px 16px; border-radius: 6px; font-size: 12px;
}
QPushButton#secondaryBtn:hover { background-color: #00FF8822; border-color: #00FF88; }
QLabel { color: #e0e0e0; font-size: 13px; }
QLabel#title { color: #00FF88; font-size: 24px; font-weight: bold; }
QLabel#subtitle { color: #8899aa; font-size: 12px; }
QLabel#sectionTitle { color: #00FF88; font-size: 16px; font-weight: bold; }
QGroupBox {
    color: #00FF88; border: 1px solid #00FF8833; border-radius: 8px;
    margin-top: 8px; padding-top: 12px; font-weight: bold;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #1b263b; color: #e0e0e0;
    border: 1px solid #00FF8833; border-radius: 6px; padding: 6px 10px; font-size: 13px;
}
QComboBox:hover, QSpinBox:hover, QLineEdit:hover { border-color: #00FF88; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow {
    image: none; border-left: 5px solid transparent;
    border-right: 5px solid transparent; border-top: 6px solid #00FF88; margin-right: 8px;
}
QTextEdit {
    background-color: #0d1b2a; color: #00FF88;
    border: 1px solid #00FF8833; border-radius: 8px;
    font-family: 'Consolas', 'Courier New', monospace; font-size: 13px;
}
QProgressBar {
    background-color: #1b263b; border: none; border-radius: 6px; height: 8px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FF88, stop:1 #00cc6a);
    border-radius: 6px;
}
QCheckBox { color: #e0e0e0; spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border: 2px solid #00FF8844;
    border-radius: 4px; background-color: #1b263b;
}
QCheckBox::indicator:checked { background-color: #00FF88; border-color: #00FF88; }
QScrollBar:vertical { background: #0d1b2a; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #00FF8844; border-radius: 4px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: #00FF8888; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
"""

class GlowButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("actionBtn")
        self.glow_intensity = 0
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.update_glow)
        self.glow_timer.start(50)

    def update_glow(self):
        self.glow_intensity = (self.glow_intensity + 1) % 360
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.isEnabled():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            alpha = int(30 + 20 * (0.5 + 0.5 * ((self.glow_intensity % 180) / 180 - 0.5)))
            gradient.setColorAt(0, QColor(0, 255, 136, alpha))
            gradient.setColorAt(1, QColor(0, 204, 106, alpha))
            painter.setPen(QColor(0, 255, 136, alpha))
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 6, 6)

class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        title = QLabel("FunASR 多语言转写系统")
        title.setObjectName("title")
        layout.addWidget(title)
        subtitle = QLabel("支持阿拉伯语、英语、日语、波斯语、俄语等30+语种 → 中文")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        features = [
            ("🎙️", "文件转写", "上传音频文件，自动识别并转写为中文"),
            ("📡", "实时转写", "麦克风实时录音，流式转写为文字"),
            ("💬", "悬浮字幕", "全屏视频/会议时显示实时字幕"),
            ("🌍", "多语言", "支持30+语种自动识别"),
            ("🔄", "翻译功能", "外语自动翻译为中文"),
            ("⚙️", "智能配置", "VAD自动分段 + 标点预测")
        ]
        for icon, title_text, desc in features:
            frame = QFrame()
            frame.setStyleSheet("QFrame { background-color: #0d1b2a; border: 1px solid #00FF8822; border-radius: 8px; }")
            f_layout = QHBoxLayout(frame)
            f_layout.setContentsMargins(16, 12, 16, 12)
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 24px;")
            f_layout.addWidget(icon_label)
            text_layout = QVBoxLayout()
            t_label = QLabel(title_text)
            t_label.setStyleSheet("color: #00FF88; font-size: 14px; font-weight: bold;")
            text_layout.addWidget(t_label)
            d_label = QLabel(desc)
            d_label.setObjectName("subtitle")
            text_layout.addWidget(d_label)
            f_layout.addLayout(text_layout)
            f_layout.addStretch()
            layout.addWidget(frame)
        layout.addStretch()

class SettingsPage(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()

    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        title = QLabel("系统设置")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        model_group = QGroupBox("模型设置")
        model_layout = QFormLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "iic/SenseVoiceSmall",
            "FunAudioLLM/Fun-ASR-Nano-2512",
            "iic/SenseVoiceLarge"
        ])
        current = self.config.get("model_name", "iic/SenseVoiceSmall")
        idx = self.model_combo.findText(current)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        model_layout.addRow("主模型:", self.model_combo)

        self.device_combo = QComboBox()
        self.device_combo.addItems(["cuda:0", "cpu"])
        self.device_combo.setCurrentText(self.config.get("device", "cuda:0"))
        model_layout.addRow("运行设备:", self.device_combo)

        self.lang_combo = QComboBox()
        languages = [
            ("auto", "自动检测"), ("zh", "中文"), ("en", "英语"),
            ("ja", "日语"), ("ar", "阿拉伯语"), ("fa", "波斯语"),
            ("ru", "俄语"), ("ko", "韩语"), ("fr", "法语"), ("de", "德语")
        ]
        for code, name in languages:
            self.lang_combo.addItem(name, code)
        idx = self.lang_combo.findData(self.config.get("language", "auto"))
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        model_layout.addRow("识别语言:", self.lang_combo)

        self.trans_combo = QComboBox()
        self.trans_combo.addItem("内置翻译", "builtin")
        self.trans_combo.addItem("本地翻译模型", "local")
        self.trans_combo.addItem("API翻译", "api")
        idx = self.trans_combo.findData(self.config.get("translation_mode", "builtin"))
        if idx >= 0:
            self.trans_combo.setCurrentIndex(idx)
        model_layout.addRow("翻译模式:", self.trans_combo)

        self.itn_check = QCheckBox("开启数字/日期规整")
        self.itn_check.setChecked(self.config.get("use_itn", True))
        model_layout.addRow("", self.itn_check)

        self.punc_check = QCheckBox("开启标点预测")
        self.punc_check.setChecked(self.config.get("use_punc", True))
        model_layout.addRow("", self.punc_check)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        rec_group = QGroupBox("录音设置")
        rec_layout = QFormLayout()
        self.sr_spin = QSpinBox()
        self.sr_spin.setRange(8000, 48000)
        self.sr_spin.setValue(self.config.get("recording", {}).get("sample_rate", 16000))
        self.sr_spin.setSuffix(" Hz")
        rec_layout.addRow("采样率:", self.sr_spin)
        self.chunk_spin = QSpinBox()
        self.chunk_spin.setRange(1, 30)
        self.chunk_spin.setValue(self.config.get("recording", {}).get("chunk_duration", 5))
        self.chunk_spin.setSuffix(" 秒")
        rec_layout.addRow("分段时长:", self.chunk_spin)
        self.device_index_spin = QSpinBox()
        self.device_index_spin.setRange(-1, 10)
        self.device_index_spin.setValue(self.config.get("recording", {}).get("device_index", -1))
        self.device_index_spin.setSpecialValueText("默认设备")
        rec_layout.addRow("录音设备:", self.device_index_spin)
        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)

        sub_group = QGroupBox("字幕设置")
        sub_layout = QFormLayout()
        sub_cfg = self.config.get("subtitle", {})
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(12, 72)
        self.font_size_spin.setValue(sub_cfg.get("font_size", 28))
        sub_layout.addRow("字体大小:", self.font_size_spin)
        self.color_edit = QLineEdit()
        self.color_edit.setText(sub_cfg.get("font_color", "#00FF88"))
        sub_layout.addRow("字体颜色:", self.color_edit)
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0.0, 1.0)
        self.opacity_spin.setSingleStep(0.1)
        self.opacity_spin.setValue(sub_cfg.get("bg_opacity", 0.3))
        sub_layout.addRow("背景透明度:", self.opacity_spin)
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setRange(1, 5)
        self.max_lines_spin.setValue(sub_cfg.get("max_lines", 3))
        sub_layout.addRow("最大行数:", self.max_lines_spin)
        self.auto_hide_spin = QSpinBox()
        self.auto_hide_spin.setRange(0, 30)
        self.auto_hide_spin.setValue(sub_cfg.get("auto_hide_seconds", 5))
        self.auto_hide_spin.setSuffix(" 秒")
        sub_layout.addRow("自动隐藏:", self.auto_hide_spin)
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItem("纯文本（无标签）", "clean")
        self.display_mode_combo.addItem("文本 + 情绪状态", "emotion")
        self.display_mode_combo.addItem("文本 + 音频事件", "events")
        self.display_mode_combo.addItem("文本 + 情绪 + 事件", "emotion_events")
        self.display_mode_combo.addItem("原始输出（含标签）", "raw")
        idx = self.display_mode_combo.findData(sub_cfg.get("display_mode", "clean"))
        if idx >= 0:
            self.display_mode_combo.setCurrentIndex(idx)
        sub_layout.addRow("字幕显示:", self.display_mode_combo)
        sub_group.setLayout(sub_layout)
        layout.addWidget(sub_group)

        self.save_btn = GlowButton("保存设置")
        self.save_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_btn)
        layout.addStretch()
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def save_settings(self):
        self.config["model_name"] = self.model_combo.currentText()
        self.config["device"] = self.device_combo.currentText()
        self.config["language"] = self.lang_combo.currentData()
        self.config["translation_mode"] = self.trans_combo.currentData()
        self.config["use_itn"] = self.itn_check.isChecked()
        self.config["use_punc"] = self.punc_check.isChecked()
        self.config["recording"] = {
            "sample_rate": self.sr_spin.value(),
            "chunk_duration": self.chunk_spin.value(),
            "device_index": self.device_index_spin.value()
        }
        self.config["subtitle"] = {
            **self.config.get("subtitle", {}),
            "font_size": self.font_size_spin.value(),
            "font_color": self.color_edit.text(),
            "bg_opacity": self.opacity_spin.value(),
            "max_lines": self.max_lines_spin.value(),
            "auto_hide_seconds": self.auto_hide_spin.value(),
            "display_mode": self.display_mode_combo.currentData()
        }
        save_config(self.config)
        self.save_btn.setText("已保存!")
        QTimer.singleShot(2000, lambda: self.save_btn.setText("保存设置"))


class TranscribePage(QWidget):
    result_signal = pyqtSignal(str)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.engine = None
        self.recorder = None
        self.subtitle_overlay = None
        self.init_ui()
        self.result_signal.connect(self._handle_result, type=Qt.ConnectionType.UniqueConnection)

    def _handle_result(self, text):
        if text == "__DONE__":
            self.transcribe_btn.setEnabled(True)
            self.live_btn.setEnabled(True)
            return
        if text == "__START_RECORDING__":
            self._start_recording()
            return
        if text.startswith("__MODEL__"):
            model_name = text[9:]
            self.output.append(f"当前模型: {model_name}")
            return
        self.output.append(text)
        if self.subtitle_overlay and self.subtitle_overlay.isVisible():
            self.subtitle_overlay.update_text(text)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        title = QLabel("转写控制台")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabBar::tab {
                background-color: #0d1b2a; color: #8899aa; padding: 8px 16px;
                border: 1px solid #00FF8822; border-radius: 6px 6px 0 0;
            }
            QTabBar::tab:selected { background-color: #00FF8822; color: #00FF88; }
        """)
        tab_widget.addTab(self.create_file_tab(), "文件转写")
        tab_widget.addTab(self.create_live_tab(), "实时转写")
        tab_widget.addTab(self.create_subtitle_tab(), "悬浮字幕")
        layout.addWidget(tab_widget)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("转写结果将显示在这里...")
        layout.addWidget(self.output)

    def create_file_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.file_label = QLabel("未选择文件")
        self.file_label.setObjectName("subtitle")
        layout.addWidget(self.file_label)
        btn_layout = QHBoxLayout()
        self.browse_btn = QPushButton("选择文件")
        self.browse_btn.setObjectName("secondaryBtn")
        self.browse_btn.clicked.connect(self.browse_file)
        btn_layout.addWidget(self.browse_btn)
        self.transcribe_btn = GlowButton("开始转写")
        self.transcribe_btn.clicked.connect(self.start_file_transcribe)
        btn_layout.addWidget(self.transcribe_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()
        return tab

    def create_subtitle_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        info = QLabel("悬浮字幕将显示为置顶透明窗口，适合全屏视频/会议使用")
        info.setWordWrap(True)
        info.setObjectName("subtitle")
        layout.addWidget(info)
        self.subtitle_btn = GlowButton("启动悬浮字幕")
        self.subtitle_btn.clicked.connect(self.toggle_subtitle)
        layout.addWidget(self.subtitle_btn)
        self.subtitle_status = QLabel("状态: 未运行")
        self.subtitle_status.setObjectName("subtitle")
        layout.addWidget(self.subtitle_status)
        layout.addStretch()
        return tab

    def create_live_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("音频源:"))
        self.source_combo = QComboBox()
        self.source_combo.addItem("麦克风", "mic")
        self.source_combo.addItem("电脑音频（内录）", "loopback")
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        layout.addWidget(self.source_combo)
        layout.addWidget(QLabel("录音设备:"))
        self.device_combo = QComboBox()
        self.device_combo.addItem("默认设备", -1)
        layout.addWidget(self.device_combo)
        self._on_source_changed(0)
        self.live_btn = GlowButton("开始录音转写")
        self.live_btn.clicked.connect(self.toggle_live)
        layout.addWidget(self.live_btn)
        self.live_status = QLabel("状态: 未运行")
        self.live_status.setObjectName("subtitle")
        layout.addWidget(self.live_status)
        layout.addStretch()
        return tab

    def _on_source_changed(self, idx):
        source = self.source_combo.currentData()
        self.device_combo.clear()
        self.device_combo.addItem("默认设备", -1)
        if source == "loopback":
            devices = RealtimeRecorder.get_loopback_devices()
        else:
            devices = RealtimeRecorder.get_available_devices()
        for d in devices:
            self.device_combo.addItem(d['name'], d['index'])

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "",
            "音频文件 (*.mp3 *.wav *.m4a *.flac *.ogg *.aac)"
        )
        if file_path:
            self.file_label.setText(file_path)
            self.file_label.setProperty("file_path", file_path)

    def start_file_transcribe(self):
        file_path = self.file_label.property("file_path")
        if not file_path:
            self.output.append("请先选择音频文件")
            return

        fresh_config = load_config()
        model_name = fresh_config.get("model_name", "iic/SenseVoiceSmall")
        device = fresh_config.get("device", "cuda:0")

        self.transcribe_btn.setEnabled(False)
        self.output.clear()
        self.output.append(f"正在转写: {file_path}")
        self.output.append(f"使用模型: {model_name}")

        def run():
            try:
                if not self.engine:
                    self.engine = TranscriptionEngine(fresh_config)
                else:
                    self.engine.config = fresh_config
                    if self.engine._last_model_name != model_name or self.engine._last_device != device:
                        self.engine.reset_for_new_model()

                self.result_signal.emit("正在加载模型，请稍候...")
                self.engine.init_model(model_name=model_name, device=device)
                self.result_signal.emit(f"__MODEL__{self.engine._last_model_name or '?'}")

                result = self.engine.transcribe_file(file_path)
                self.result_signal.emit(result)
            except Exception as e:
                import traceback
                self.result_signal.emit(f"错误: {str(e)}\n{traceback.format_exc()}")
            finally:
                self.result_signal.emit("__DONE__")

        threading.Thread(target=run, daemon=True).start()

    def toggle_live(self):
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop()
            self.live_btn.setText("开始录音转写")
            self.live_status.setText("状态: 已停止")
            return

        fresh_config = load_config()
        model_name = fresh_config.get("model_name", "iic/SenseVoiceSmall")
        device = fresh_config.get("device", "cuda:0")

        self.live_btn.setEnabled(False)
        self.live_status.setText("状态: 正在初始化模型...")

        def init_and_start():
            try:
                if not self.engine:
                    self.engine = TranscriptionEngine(fresh_config)
                else:
                    self.engine.config = fresh_config
                    if self.engine._last_model_name != model_name or self.engine._last_device != device:
                        self.engine.reset_for_new_model()

                self.result_signal.emit("正在加载模型，请稍候...")
                self.engine.init_model(model_name=model_name, device=device)
                self.result_signal.emit(f"__MODEL__{self.engine._last_model_name or '?'}")
                self.result_signal.emit("__START_RECORDING__")
            except Exception as e:
                import traceback
                self.result_signal.emit(f"模型初始化失败: {str(e)}\n{traceback.format_exc()}")
                self.result_signal.emit("__DONE__")

        threading.Thread(target=init_and_start, daemon=True).start()

    def _start_recording(self):
        fresh_config = load_config()
        self.recorder = RealtimeRecorder(self.engine, fresh_config)
        device_idx = self.device_combo.currentData()
        source = self.source_combo.currentData()
        is_loopback = (source == "loopback")
        self.recorder.on_result = lambda text: self.result_signal.emit(text)
        try:
            self.recorder.start(
                device_index=device_idx if device_idx != -1 else None,
                loopback=is_loopback
            )
            self.live_btn.setEnabled(True)
            self.live_btn.setText("停止录音转写")
            self.live_status.setText("状态: 录音中...")
        except Exception as e:
            self.output.append(f"启动录音失败: {e}")
            self.live_btn.setEnabled(True)
            self.live_btn.setText("开始录音转写")
            self.live_status.setText("状态: 启动失败")
            self.recorder = None

    def toggle_subtitle(self):
        if self.subtitle_overlay and self.subtitle_overlay.isVisible():
            self.subtitle_overlay.close()
            self.subtitle_btn.setText("启动悬浮字幕")
            self.subtitle_status.setText("状态: 已关闭")
        else:
            self.subtitle_overlay = SubtitleOverlay()
            self.subtitle_overlay.show()
            self.subtitle_btn.setText("关闭悬浮字幕")
            self.subtitle_status.setText("状态: 运行中")


class ModelCard(QWidget):
    def __init__(self, model_info, parent=None):
        super().__init__(parent)
        self.model_info = model_info
        self.is_installed = False
        self.selected = False
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        self.setStyleSheet("ModelCard { background-color: #0d1b2a; border: 1px solid #00FF8822; border-radius: 8px; }")
        self.check = QCheckBox()
        self.check.setStyleSheet("QCheckBox::indicator { width: 20px; height: 20px; }")
        self.check.stateChanged.connect(self.on_check)
        layout.addWidget(self.check)
        content = QVBoxLayout()
        content.setSpacing(4)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)
        self.status_icon = QLabel("⬜")
        self.status_icon.setStyleSheet("font-size: 16px;")
        top_layout.addWidget(self.status_icon)
        name_label = QLabel(self.model_info["name"])
        name_label.setStyleSheet("color: #00FF88; font-size: 14px; font-weight: bold;")
        top_layout.addWidget(name_label)
        if self.model_info.get("recommended", False):
            rec = QLabel("推荐")
            rec.setStyleSheet("color: #0a0a1a; background-color: #00FF88; font-size: 10px; padding: 2px 6px; border-radius: 4px;")
            top_layout.addWidget(rec)
        size_label = QLabel(self.model_info["size"])
        size_label.setObjectName("subtitle")
        top_layout.addStretch()
        top_layout.addWidget(size_label)
        content.addLayout(top_layout)
        desc_label = QLabel(self.model_info["description"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #8899aa; font-size: 12px;")
        content.addWidget(desc_label)
        cat_label = QLabel(self.model_info.get("category", ""))
        cat_label.setStyleSheet("color: #667788; font-size: 11px;")
        content.addWidget(cat_label)
        layout.addLayout(content)

    def on_check(self, state):
        self.selected = (state == 2)

    def set_installed(self, installed):
        self.is_installed = installed
        self.status_icon.setText("✅" if installed else "⬜")
        self.check.setChecked(installed)


class ModelPage(QWidget):
    dl_progress = pyqtSignal(str, int, str)
    dl_done = pyqtSignal(str, str)

    def __init__(self, model_manager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.model_cards = []
        self.init_ui()
        self.dl_progress.connect(self._on_dl_progress)
        self.dl_done.connect(self._on_dl_done)
        self.refresh_model_list()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        title = QLabel("模型管理")
        title.setObjectName("sectionTitle")
        main_layout.addWidget(title)
        info_layout = QHBoxLayout()
        self.usage_label = QLabel("已使用: " + self.model_manager.format_size(self.model_manager.get_disk_usage()))
        self.usage_label.setObjectName("subtitle")
        info_layout.addWidget(self.usage_label)
        info_layout.addStretch()
        self.model_count_label = QLabel("")
        self.model_count_label.setObjectName("subtitle")
        info_layout.addWidget(self.model_count_label)
        main_layout.addLayout(info_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(8)
        scroll.setWidget(self.cards_container)
        main_layout.addWidget(scroll)
        self.status_label = QLabel("")
        self.status_label.setObjectName("subtitle")
        main_layout.addWidget(self.status_label)
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.clicked.connect(self.refresh_model_list)
        btn_layout.addWidget(refresh_btn)
        cleanup_btn = QPushButton("清理空间")
        cleanup_btn.setObjectName("secondaryBtn")
        cleanup_btn.clicked.connect(self.cleanup_disk)
        btn_layout.addWidget(cleanup_btn)
        self.download_btn = QPushButton("下载选中")
        self.download_btn.setObjectName("actionBtn")
        self.download_btn.clicked.connect(self.download_selected)
        btn_layout.addWidget(self.download_btn)
        delete_btn = QPushButton("删除选中")
        delete_btn.setObjectName("dangerBtn")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)
        main_layout.addLayout(btn_layout)

    def refresh_model_list(self):
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.model_cards = []
        status_list = self.model_manager.get_model_status()
        models = self.model_manager.get_available_models()
        categories = {}
        for model_id, info in models.items():
            cat = info.get("category", "其他")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(model_id)
        installed_count = 0
        for cat, model_ids in categories.items():
            cat_label = QLabel(cat)
            cat_label.setStyleSheet("color: #00FF88; font-size: 13px; font-weight: bold; padding: 8px 0 4px 0;")
            self.cards_layout.addWidget(cat_label)
            for model_id in model_ids:
                info = models[model_id]
                is_installed = any(s["id"] == model_id and s["status"] == "installed" for s in status_list)
                if is_installed:
                    installed_count += 1
                card = ModelCard(info)
                card.set_installed(is_installed)
                card.model_id = model_id
                self.model_cards.append(card)
                self.cards_layout.addWidget(card)
        self.usage_label.setText("已使用: " + self.model_manager.format_size(self.model_manager.get_disk_usage()))
        self.model_count_label.setText("已安装: " + str(installed_count) + " / " + str(len(status_list)))
        self.cards_layout.addStretch()

    def download_selected(self):
        to_download = []
        for card in self.model_cards:
            if card.check.isChecked() and not card.is_installed:
                if not self.model_manager.is_model_downloaded(card.model_id):
                    to_download.append(card.model_id)
        if not to_download:
            self.status_label.setText("没有可下载的模型")
            return
        self._download_queue = to_download
        self.status_label.setText(f"开始批量下载 {len(to_download)} 个模型...")
        self._start_next_download()

    def _start_next_download(self):
        if not hasattr(self, '_download_queue') or not self._download_queue:
            self.status_label.setText("全部下载完成")
            self.refresh_model_list()
            return
        model_id = self._download_queue.pop(0)
        self.status_label.setText("正在下载: " + model_id)
        def on_done(mid, status):
            if status == "success":
                self.dl_done.emit(mid, status)
            else:
                self.dl_done.emit(mid, status)
            QTimer.singleShot(500, self._start_next_download)
        self.model_manager.download_model(
            model_id,
            lambda mid, pct, msg: self.dl_progress.emit(mid, pct, msg),
            on_done,
        )

    def _on_dl_progress(self, mid, pct, msg):
        self.status_label.setText(msg)

    def _on_dl_done(self, mid, status):
        self.refresh_model_list()
        if status == "success":
            self.status_label.setText("下载完成: " + mid)
        else:
            self.status_label.setText("下载失败: " + status)

    def delete_selected(self):
        deleted_any = False
        for card in self.model_cards:
            if card.check.isChecked() and card.is_installed:
                if self.model_manager.delete_model(card.model_id):
                    card.check.setChecked(False)
                    deleted_any = True
        if deleted_any:
            self.refresh_model_list()

    def cleanup_disk(self):
        freed = self.model_manager.deep_cleanup()
        self.status_label.setText(f"已释放 {self.model_manager.format_size(freed)}")
        self.refresh_model_list()


class TTSPage(QWidget):
    tts_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tts_manager = TTSManager()
        self._current_audio = None
        self._clone_mode = False
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self._on_media_status)
        self.init_ui()
        self.tts_signal.connect(self._handle_result)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("文字转语音 (TTS)")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在此输入要转为语音的文字...")
        self.text_edit.setMaximumHeight(200)
        self.text_edit.setStyleSheet("background-color: #0d1b2a; color: #e0e0e0; border: 1px solid #00FF8822; border-radius: 6px; padding: 8px; font-size: 14px;")
        layout.addWidget(self.text_edit)

        engine_layout = QHBoxLayout()
        engine_layout.addWidget(QLabel("引擎:"))
        self.engine_combo = QComboBox()
        for eid, ename in self.tts_manager.get_engines():
            self.engine_combo.addItem(ename, eid)
        self.engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        engine_layout.addWidget(self.engine_combo, 1)
        layout.addLayout(engine_layout)

        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("语音:"))
        self.voice_combo = QComboBox()
        for vid, vname in self.tts_manager.win_tts.get_voices():
            self.voice_combo.addItem(vname, vid)
        voice_layout.addWidget(self.voice_combo, 1)

        self.model_combo = QComboBox()
        for mid, minfo in MODEL_TTS_INFO.items():
            self.model_combo.addItem(minfo["name"] + "  " + minfo["size"], mid)
        self.model_combo.setVisible(False)
        voice_layout.addWidget(self.model_combo, 1)
        layout.addLayout(voice_layout)

        self.clone_check = QCheckBox("人声复刻 (提供参考音频进行语音克隆)")
        self.clone_check.stateChanged.connect(self._on_clone_toggled)
        self.clone_check.setVisible(False)
        layout.addWidget(self.clone_check)

        clone_group = QGroupBox("人声复刻设置")
        clone_group.setVisible(False)
        clone_layout = QFormLayout(clone_group)

        audio_btn_layout = QHBoxLayout()
        self.clone_audio_path = QLineEdit()
        self.clone_audio_path.setPlaceholderText("选择参考音频文件 (3-10秒人声)")
        self.clone_audio_path.setReadOnly(True)
        audio_btn_layout.addWidget(self.clone_audio_path)
        self.browse_clone_btn = QPushButton("浏览...")
        self.browse_clone_btn.setObjectName("secondaryBtn")
        self.browse_clone_btn.clicked.connect(self._browse_clone_audio)
        audio_btn_layout.addWidget(self.browse_clone_btn)
        clone_layout.addRow("参考音频:", audio_btn_layout)

        self.clone_prompt_text = QLineEdit()
        self.clone_prompt_text.setPlaceholderText("参考音频中说话的内容（可选，有助于提升克隆质量）")
        clone_layout.addRow("参考文本:", self.clone_prompt_text)

        clone_info = QLabel("支持 wav/mp3/m4a 格式，建议 16kHz 单声道，时长 3-10 秒")
        clone_info.setObjectName("subtitle")
        clone_layout.addRow("", clone_info)
        self.clone_group = clone_group
        layout.addWidget(clone_group)

        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("语速:"))
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(-50, 50)
        self.rate_spin.setValue(0)
        self.rate_spin.setSuffix(" %")
        param_layout.addWidget(self.rate_spin)
        param_layout.addStretch()
        layout.addLayout(param_layout)

        btn_layout = QHBoxLayout()
        self.gen_btn = QPushButton("生成并播放")
        self.gen_btn.setObjectName("actionBtn")
        self.gen_btn.clicked.connect(self.generate_speech)
        btn_layout.addWidget(self.gen_btn)

        self.play_btn = QPushButton("播放")
        self.play_btn.setObjectName("secondaryBtn")
        self.play_btn.clicked.connect(self.play_audio)
        self.play_btn.setEnabled(False)
        btn_layout.addWidget(self.play_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setObjectName("dangerBtn")
        self.stop_btn.clicked.connect(self.stop_audio)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        self.save_btn = QPushButton("保存到文件")
        self.save_btn.setObjectName("secondaryBtn")
        self.save_btn.clicked.connect(self.save_audio)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("subtitle")
        layout.addWidget(self.status_label)

        info = QLabel("提示: Windows 内置 TTS 离线可用；模型 TTS 使用 CosyVoice 3.0 (~1.1GB)，支持人声复刻")
        info.setObjectName("subtitle")
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addStretch()

    def _on_engine_changed(self, idx):
        self.stop_audio()
        engine = self.engine_combo.currentData()
        is_win = (engine == "win")
        self.voice_combo.setVisible(is_win)
        self.model_combo.setVisible(not is_win and not self._clone_mode)
        self.clone_check.setVisible(not is_win)
        self.rate_spin.setVisible(is_win)
        if not is_win:
            self.clone_group.setVisible(self._clone_mode)

    def _on_clone_toggled(self, state):
        self._clone_mode = (state == 2)
        self.model_combo.setVisible(not self._clone_mode)
        self.clone_group.setVisible(self._clone_mode)

    def _browse_clone_audio(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择参考音频", "",
            "音频文件 (*.wav *.mp3 *.m4a *.flac *.ogg)"
        )
        if path:
            self.clone_audio_path.setText(path)

    def generate_speech(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            self.status_label.setText("请输入文字")
            return
        if len(text) > 5000:
            self.status_label.setText("文本过长，请限制在 5000 字符以内")
            return

        self.stop_audio()
        engine = self.engine_combo.currentData()
        self.gen_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.status_label.setText("正在生成语音...")

        def run():
            try:
                if engine == "win":
                    voice = self.voice_combo.currentData()
                    rate = self.rate_spin.value()
                    result = self.tts_manager.synthesize(text, engine="win", voice=voice, rate=rate)
                elif engine == "model" and self._clone_mode:
                    audio_path = self.clone_audio_path.text()
                    if not audio_path:
                        self.tts_signal.emit(TTSResult(success=False, error="请选择参考音频"))
                        return
                    prompt_text = self.clone_prompt_text.text().strip()
                    model_id = self.model_combo.currentData()
                    result = self.tts_manager.synthesize_with_prompt(
                        text, prompt_audio_path=audio_path,
                        prompt_text=prompt_text, model_name=model_id,
                    )
                else:
                    model_id = self.model_combo.currentData()
                    result = self.tts_manager.synthesize(text, engine="model", model_name=model_id)
                self.tts_signal.emit(result)
            except Exception as e:
                self.tts_signal.emit(TTSResult(success=False, error=str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _handle_result(self, result):
        self.gen_btn.setEnabled(True)
        if result.success:
            if self._current_audio and result.audio_path != self._current_audio:
                try:
                    os.unlink(self._current_audio)
                except OSError:
                    pass
            self._current_audio = result.audio_path
            self.play_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            dur = result.duration
            self.status_label.setText(f"生成完成 ({dur:.1f}s)")
            self.play_audio()
        else:
            self.status_label.setText("失败: " + result.error)

    def play_audio(self):
        if not self._current_audio or not os.path.exists(self._current_audio):
            self.status_label.setText("没有可播放的音频")
            return
        self.player.setSource(QUrl.fromLocalFile(self._current_audio))
        self.player.play()
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("播放中...")

    def stop_audio(self):
        self.player.stop()
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("已停止")

    def _on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            if self._current_audio and os.path.exists(self._current_audio):
                self.status_label.setText("播放完成")

    def save_audio(self):
        if not self._current_audio or not os.path.exists(self._current_audio):
            self.status_label.setText("没有可保存的音频，请先生成语音")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存语音", "output.wav", "音频文件 (*.wav)")
        if path:
            try:
                import shutil
                shutil.copy2(self._current_audio, path)
                self.status_label.setText("已保存: " + path)
            except Exception as e:
                self.status_label.setText("保存失败: " + str(e))


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.model_manager = ModelManager()
        self.init_ui()

    def closeEvent(self, event):
        transcribe = self.pages.get("transcribe")
        if transcribe:
            if transcribe.recorder and transcribe.recorder.is_recording:
                transcribe.recorder.stop()
            if transcribe.subtitle_overlay and transcribe.subtitle_overlay.isVisible():
                transcribe.subtitle_overlay.close()
        tts = self.pages.get("tts")
        if tts:
            tts.stop_audio()
            tts._current_audio = None
        event.accept()

    def init_ui(self):
        self.setWindowTitle("FunASR 多语言转写系统")
        self.resize(900, 720)
        self.setStyleSheet(STYLESHEET)
        central = QWidget()
        central.setObjectName("mainFrame")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(8)
        logo = QLabel("🎙️ FunASR")
        logo.setStyleSheet("color: #00FF88; font-size: 20px; font-weight: bold; padding: 10px 0;")
        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(20)

        self.nav_buttons = {}
        nav_items = [("home", "🏠 首页"), ("transcribe", "🎙️ 转写"), ("tts", "🔊 语音合成"), ("model", "📦 模型"), ("settings", "⚙️ 设置")]
        for page_id, label in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, pid=page_id: self.switch_page(pid))
            self.nav_buttons[page_id] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        version = QLabel("v2.0.0")
        version.setObjectName("subtitle")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(version)
        main_layout.addWidget(sidebar)

        content = QFrame()
        content.setObjectName("contentArea")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        self.stacked = QStackedWidget()
        self.pages = {
            "home": HomePage(self),
            "transcribe": TranscribePage(self.config, self),
            "tts": TTSPage(self),
            "model": ModelPage(self.model_manager, self),
            "settings": SettingsPage(self.config, self),
        }
        for page in self.pages.values():
            self.stacked.addWidget(page)
        content_layout.addWidget(self.stacked)
        main_layout.addWidget(content)
        self.switch_page("home")

    def switch_page(self, page_id):
        for pid, btn in self.nav_buttons.items():
            btn.setChecked(pid == page_id)
        self.stacked.setCurrentWidget(self.pages[page_id])


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
