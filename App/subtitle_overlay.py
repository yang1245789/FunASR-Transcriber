import sys
import os
import re
import json
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMenu
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction
from utils import load_config, save_config, get_config_path

class SubtitleOverlay(QWidget):
    DISPLAY_MODES = {
        "raw": "原始输出（含标签）",
        "clean": "纯文本（无标签）",
        "emotion": "文本 + 情绪状态",
        "events": "文本 + 音频事件",
        "emotion_events": "文本 + 情绪 + 事件",
    }
    EMOTION_MAP = {
        "HAPPY": "\U0001f60a", "SAD": "\U0001f622", "ANGRY": "\U0001f620",
        "NEUTRAL": "\U0001f610", "FEARFUL": "\U0001f628", "DISGUSTED": "\U0001f922",
        "SURPRISED": "\U0001f632", "EMO_UNKNOWN": "",
    }
    EVENT_MAP = {
        "BGM": "\U0001f3b5", "speech": "\U0001f5e3", "Applause": "\U0001f44f",
        "Laughter": "\U0001f602",
    }

    def __init__(self, config=None):
        super().__init__()
        self.config = config or load_config()
        self.subtitle_config = self.config.get("subtitle", {})
        self.current_text = ""
        self.text_history = []
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.hide_text)
        self.dragging = False
        self.drag_position = None
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        sub_cfg = self.subtitle_config
        x = sub_cfg.get("x", 100)
        y = sub_cfg.get("y", -100)
        width = sub_cfg.get("width", 800)
        height = sub_cfg.get("height", 120)

        if y < 0:
            screen = QApplication.primaryScreen()
            if screen is not None:
                y = screen.geometry().height() + y
            else:
                y = 600 + y

        self.setGeometry(x, y, width, height)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.label.setWordWrap(True)
        self.update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.addWidget(self.label)

    def update_style(self):
        sub_cfg = self.subtitle_config
        font_size = sub_cfg.get("font_size", 28)
        font_color = sub_cfg.get("font_color", "#00FF88")
        bg_opacity = sub_cfg.get("bg_opacity", 0.3)
        self.label.setStyleSheet("""
            QLabel {{
                color: {0};
                background-color: rgba(0, 0, 0, {1});
                border-radius: 8px;
                padding: 8px 16px;
                font-size: {2}px;
                font-weight: bold;
            }}
        """.format(font_color, int(bg_opacity * 255), font_size))
        self.label.setFont(QFont("Microsoft YaHei UI", font_size, QFont.Weight.Bold))

    def update_text(self, text):
        self.current_text = text
        mode = self.subtitle_config.get("display_mode", "clean")
        display_text = self._filter_text(text, mode)

        if display_text:
            if not self.text_history or display_text != self.text_history[-1]:
                self.text_history.append(display_text)
                if len(self.text_history) > 20:
                    self.text_history = self.text_history[-20:]

        self._update_display()
        self.show()
        self.hide_timer.stop()
        auto_hide = self.subtitle_config.get("auto_hide_seconds", 5)
        if auto_hide > 0:
            self.hide_timer.start(auto_hide * 1000)

    def _update_display(self):
        if not self.text_history:
            self.label.setText("")
            return

        max_lines = self.subtitle_config.get("max_lines", 3)
        font_size = self.subtitle_config.get("font_size", 28)

        lines_to_show = self.text_history[-max_lines:]
        display = "\n".join(lines_to_show)

        self.label.setText(display)
        line_height = font_size + 4
        self.setMinimumHeight(min(400, max_lines * line_height + 20))

    def hide_text(self):
        self.hide_timer.stop()
        self.label.setText("")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            gpos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
            self.drag_position = gpos - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            gpos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
            self.move(gpos - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            sub_cfg = self.subtitle_config
            sub_cfg["x"] = self.x()
            screen = QApplication.primaryScreen()
            screen_h = screen.geometry().height() if screen else 1080
            sub_cfg["y"] = self.y() - screen_h
            self.config["subtitle"] = sub_cfg
            try:
                save_config(self.config)
            except Exception:
                pass

    def _filter_text(self, raw, mode):
        if mode == "raw" or not raw:
            return raw
        emotions = []
        events = []
        text_parts = []
        tag_pattern = re.compile(r'<\|([^|]+)\|>')
        pos = 0
        for m in tag_pattern.finditer(raw):
            if m.start() > pos:
                text_parts.append(raw[pos:m.start()])
            tag = m.group(1)
            if tag in self.EMOTION_MAP:
                emotions.append(tag)
            elif tag in self.EVENT_MAP:
                events.append(tag)
            pos = m.end()
        if pos < len(raw):
            text_parts.append(raw[pos:])
        clean_text = "".join(text_parts).strip()
        clean_text = re.sub(r'\s+', '', clean_text)
        prefix = ""
        if mode in ("emotion", "emotion_events"):
            seen = set()
            for e in emotions:
                if e not in seen:
                    seen.add(e)
                    icon = self.EMOTION_MAP.get(e, e)
                    if icon:
                        prefix += icon + " "
        if mode in ("events", "emotion_events"):
            seen = set()
            for e in events:
                if e not in seen:
                    seen.add(e)
                    icon = self.EVENT_MAP.get(e, e)
                    if icon:
                        prefix += icon + " "
        if mode == "clean":
            return clean_text
        return (prefix + clean_text).strip()

    def _set_display_mode(self, mode):
        sub_cfg = self.subtitle_config
        sub_cfg["display_mode"] = mode
        self.config["subtitle"] = sub_cfg
        try:
            save_config(self.config)
        except Exception:
            pass
        self.text_history.clear()
        if self.current_text:
            self.update_text(self.current_text)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1a1a2e; color: #00FF88; border: 1px solid #00FF88; border-radius: 8px; padding: 5px; }
            QMenu::item:selected { background-color: #00FF88; color: #1a1a2e; }
            QMenu::separator { background-color: #00FF8844; height: 1px; margin: 4px 8px; }
        """)
        current_mode = self.subtitle_config.get("display_mode", "clean")
        for mode_id, mode_label in self.DISPLAY_MODES.items():
            action = QAction(mode_label, menu)
            action.setCheckable(True)
            action.setChecked(mode_id == current_mode)
            action.triggered.connect(lambda checked, m=mode_id: self._set_display_mode(m))
            menu.addAction(action)
        menu.addSeparator()
        menu.addAction(QAction("增大字体", menu)).triggered.connect(lambda: self._change_font(2))
        menu.addAction(QAction("减小字体", menu)).triggered.connect(lambda: self._change_font(-2))
        menu.addSeparator()
        menu.addAction(QAction("绿色字幕", menu)).triggered.connect(lambda: self._set_color("#00FF88"))
        menu.addAction(QAction("黄色字幕", menu)).triggered.connect(lambda: self._set_color("#FFD700"))
        menu.addAction(QAction("白色字幕", menu)).triggered.connect(lambda: self._set_color("#FFFFFF"))
        menu.addSeparator()
        menu.addAction(QAction("增加透明度", menu)).triggered.connect(lambda: self._change_opacity(0.1))
        menu.addAction(QAction("降低透明度", menu)).triggered.connect(lambda: self._change_opacity(-0.1))
        menu.addSeparator()
        menu.addAction(QAction("关闭", menu)).triggered.connect(self.close)
        menu.exec(event.globalPos())

    def _change_font(self, delta):
        sub_cfg = self.subtitle_config
        sub_cfg["font_size"] = max(12, min(72, sub_cfg.get("font_size", 28) + delta))
        self.config["subtitle"] = sub_cfg
        self.update_style()
        try:
            save_config(self.config)
        except Exception:
            pass

    def _set_color(self, color):
        sub_cfg = self.subtitle_config
        sub_cfg["font_color"] = color
        self.config["subtitle"] = sub_cfg
        self.update_style()
        try:
            save_config(self.config)
        except Exception:
            pass

    def _change_opacity(self, delta):
        sub_cfg = self.subtitle_config
        sub_cfg["bg_opacity"] = max(0.0, min(1.0, sub_cfg.get("bg_opacity", 0.3) + delta))
        self.config["subtitle"] = sub_cfg
        self.update_style()
        try:
            save_config(self.config)
        except Exception:
            pass

    def update_config(self, config):
        self.config = config
        self.subtitle_config = config.get("subtitle", {})
        self.update_style()
