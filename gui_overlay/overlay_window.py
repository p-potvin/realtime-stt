import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QGraphicsDropShadowEffect, QMainWindow, QLabel, QVBoxLayout, QWidget, QCheckBox, 
    QComboBox, QHBoxLayout, QFrame, QGridLayout, QPushButton, QSizePolicy,
    QColorDialog, QSpinBox, QFontComboBox
)
from PySide6.QtCore import Qt, Signal, Slot, QPoint
from PySide6.QtGui import QColor, QFont
from vault_themes.theme_manager import VaultThemeManager

class SubtitleWindow(QMainWindow):
    """
    A minimalist, always-on-top caption window with dragging support.
    """
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            # Qt.WindowType.WindowTransparentForInput | # Removed to allow dragging
            Qt.WindowType.NoDropShadowWindowHint # Prevents ugly OS-level ghost borders
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setStyleSheet("QMainWindow { background: transparent; border: none; margin: 0; padding: 0; }")
        
        # Draggable state
        self._dragging = False
        self._drag_pos = QPoint()

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("QWidget { background: transparent; border: none; margin: 0; padding: 0; }")
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10) # Padding for click area
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.central_widget)

        self.caption_label = QLabel("Real-time STT Active...")
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption_label.setWordWrap(True)
        self.caption_label.setMaximumWidth(1200)

        self._prev_text = ""

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(4)
        self.shadow.setOffset(2, 2)
        self.caption_label.setGraphicsEffect(self.shadow)

        self.main_layout.addWidget(self.caption_label)

        self._set_default_pos()

    def _set_default_pos(self):
        screen = QApplication.primaryScreen()
        work_geo = screen.availableGeometry()
        
        # Start at bottom center
        self.adjustSize()
        x = (work_geo.width() - self.width()) // 2
        y = work_geo.height() - self.height() - 50
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            # Use position() and toPoint() for Qt6 compatibility
            self._drag_pos = event.position().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            # Move window based on relative drag
            self.move(self.pos() + (event.position().toPoint() - self._drag_pos))
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        event.accept()

    @Slot(str)
    def update_caption(self, text: str):
        # Rolling 2-line display: previous sentence on top, current on bottom.
        # This softens the transition between sentences by giving the reader context.
        display = f"{self._prev_text}\n{text}" if self._prev_text else text
        self.caption_label.setText(display)
        self._prev_text = text
        self.adjustSize()

    def apply_styles(self, styles: dict):
        # Update text style
        font_style = "italic" if styles.get("font_italic") else "normal"
        font_under = "underline" if styles.get("font_underline") else "none"
        bg_color = styles.get("bg_color", "transparent")
        
        self.caption_label.setStyleSheet(f"""
            QLabel {{
                color: {styles.get('text_color', '#FFFFFF')};
                font-family: '{styles.get('font_family', 'Segoe UI Semilight')}';
                font-size: {styles.get('font_size', 24)}pt;
                font-weight: {styles.get('font_weight', 700)};
                font-style: {font_style};
                text-decoration: {font_under};
                background-color: {bg_color};
                padding: 15px;
                border-radius: 8px;
                border: none;
            }}
        """)
        
        # Update shadow
        self.shadow.setColor(QColor(styles.get('outline_color', '#000000')))
        self.shadow.setBlurRadius(styles.get('outline_width', 4))


class SettingsWindow(QMainWindow):
    """
    Settings Panel for Real-Time STT, separated from the overlay.
    """
    debug_toggle_signal = Signal(bool)
    settings_changed_signal = Signal(dict)
    simulate_lag_signal = Signal(bool)

    def __init__(self, theme_idx=1):
        super().__init__()
        self.theme_manager = VaultThemeManager()
        self.current_theme_idx = theme_idx

        self.setWindowTitle("Real-Time STT Settings")

        # State versioning to prevent signal loops
        self.settings_version = 0

        # State
        self.font_family = "Segoe UI Semilight"
        self.font_size = 24
        self.font_weight = 700 # Bold by default!
        self.font_italic = False
        self.font_underline = False
        
        self.text_color = "#FFFFFF"
        self.outline_color = "#000000"
        self.outline_width = 4
        self.subtitle_bg_color = "rgba(0, 0, 0, 150)"
        self.show_subtitle_bg = False # Usually we just want the text with dropshadow
        self.skip_vad = False
        self.subtitles_visible = True
        self.active_engine = "Parakeet"
        
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
        self._load_config()
        
        self._init_ui()
        self._emit_current_styles()

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                self.current_theme_idx = data.get("theme_idx", self.current_theme_idx)
                self.font_family = data.get("font_family", self.font_family)
                self.font_size = data.get("font_size", self.font_size)
                self.font_weight = data.get("font_weight", self.font_weight)
                self.font_italic = data.get("font_italic", self.font_italic)
                self.font_underline = data.get("font_underline", self.font_underline)
                self.text_color = data.get("text_color", self.text_color)
                self.outline_color = data.get("outline_color", self.outline_color)
                self.outline_width = data.get("outline_width", self.outline_width)
                self.show_subtitle_bg = data.get("show_subtitle_bg", self.show_subtitle_bg)
                self.skip_vad = data.get("skip_vad", self.skip_vad)
                self.subtitles_visible = data.get("subtitles_visible", self.subtitles_visible)
                # Engine is forced to Parakeet in UI, ignore active_engine from config
                self.active_engine = "Parakeet"
            except Exception as e:
                print(f"Failed to load config: {e}")

    def _save_config(self):
        data = {
            "theme_idx": self.current_theme_idx,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "font_italic": self.font_italic,
            "font_underline": self.font_underline,
            "text_color": self.text_color,
            "outline_color": self.outline_color,
            "outline_width": self.outline_width,
            "show_subtitle_bg": self.show_subtitle_bg,
            "skip_vad": self.skip_vad,
            "subtitles_visible": self.subtitles_visible,
            "active_engine": self.active_engine
        }
        try:
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def get_current_settings(self):
        engine_val = "nvidia" if self.active_engine == "Parakeet" else "whisper"
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "font_italic": self.font_italic,
            "font_underline": self.font_underline,
            "text_color": self.text_color,
            "outline_color": self.outline_color,
            "outline_width": self.outline_width,
            "bg_color": self.subtitle_bg_color if self.show_subtitle_bg else "transparent",
            "is_visible": self.subtitles_visible,
            "skip_vad": self.skip_vad,
            "active_engine": engine_val
        }

    def _init_ui(self):

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.control_panel = QFrame()
        self.control_layout = QVBoxLayout(self.control_panel)
        self.control_layout.setSpacing(10)
        
        # Row 0: Visibility and Theme
        row_0_layout = QHBoxLayout()
        self.visibility_checkbox = QCheckBox("Show Subtitles")
        self.visibility_checkbox.setChecked(self.subtitles_visible)
        self.visibility_checkbox.toggled.connect(self._on_visibility_toggled)
        row_0_layout.addWidget(self.visibility_checkbox)

        self.bg_checkbox = QCheckBox("Subtitle BG")
        self.bg_checkbox.setChecked(self.show_subtitle_bg)
        self.bg_checkbox.toggled.connect(self._on_bg_toggled)
        row_0_layout.addWidget(self.bg_checkbox)

        row_0_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        # Make combo boxes act more like web dropdowns
        self.theme_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for t in self.theme_manager.get_themes():
            self.theme_combo.addItem(t.name)
        self.theme_combo.setCurrentIndex(self.current_theme_idx - 1)
        self.theme_combo.currentIndexChanged.connect(self._update_theme)
        row_0_layout.addWidget(self.theme_combo)
        row_0_layout.addStretch()
        self.control_layout.addLayout(row_0_layout)

        # Row 1: Toggles
        row_1_layout = QHBoxLayout()
        self.skip_vad_checkbox = QCheckBox("Skip VAD")
        self.skip_vad_checkbox.setChecked(self.skip_vad)
        self.skip_vad_checkbox.toggled.connect(self._on_skip_vad_toggled)
        row_1_layout.addWidget(self.skip_vad_checkbox)

        self.debug_checkbox = QCheckBox("Debug")
        self.debug_checkbox.stateChanged.connect(self._on_debug_toggled)
        row_1_layout.addWidget(self.debug_checkbox)

        self.simulate_lag_checkbox = QCheckBox("SimLag (Test Queue)")
        self.simulate_lag_checkbox.stateChanged.connect(self._on_simulate_lag_toggled)
        row_1_layout.addWidget(self.simulate_lag_checkbox)
        row_1_layout.addStretch()
        self.control_layout.addLayout(row_1_layout)

        # Row 2: Font Controls
        row_2_layout = QHBoxLayout()
        row_2_layout.addWidget(QLabel("Font:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.font_combo.setCurrentFont(QFont(self.font_family))
        self.font_combo.currentFontChanged.connect(self._update_font_family)
        row_2_layout.addWidget(self.font_combo)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 120)
        self.size_spin.setValue(self.font_size)
        self.size_spin.setMinimumWidth(60)
        self.size_spin.valueChanged.connect(self._update_font_size)
        row_2_layout.addWidget(self.size_spin)

        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setChecked(self.font_weight > 400)
        self.bold_btn.setFixedWidth(30)
        self.bold_btn.clicked.connect(self._toggle_bold)
        row_2_layout.addWidget(self.bold_btn)

        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedWidth(30)
        self.italic_btn.clicked.connect(self._toggle_italic)
        row_2_layout.addWidget(self.italic_btn)

        self.under_btn = QPushButton("U")
        self.under_btn.setCheckable(True)
        self.under_btn.setFixedWidth(30)
        self.under_btn.clicked.connect(self._toggle_underline)
        row_2_layout.addWidget(self.under_btn)

        self.text_color_btn = QPushButton("A")
        self.text_color_btn.setFixedWidth(30)
        self.text_color_btn.clicked.connect(self._pick_text_color)
        row_2_layout.addWidget(self.text_color_btn)
        row_2_layout.addStretch()
        self.control_layout.addLayout(row_2_layout)

        # Row 3: Shadow / Outline Controls
        row_3_layout = QHBoxLayout()
        row_3_layout.addWidget(QLabel("Shadow:"))
        self.outline_color_btn = QPushButton()
        self.outline_color_btn.setFixedWidth(30)
        self.outline_color_btn.clicked.connect(self._pick_outline_color)
        row_3_layout.addWidget(self.outline_color_btn)

        self.outline_width_spin = QSpinBox()
        self.outline_width_spin.setRange(0, 30)
        self.outline_width_spin.setValue(self.outline_width)
        self.outline_width_spin.setMinimumWidth(60)
        self.outline_width_spin.valueChanged.connect(self._update_outline_width)
        row_3_layout.addWidget(self.outline_width_spin)
        row_3_layout.addStretch()
        self.control_layout.addLayout(row_3_layout)

        self.main_layout.addWidget(self.control_panel)
        self.apply_panel_style()

    # Removed _on_engine_changed as we enforce Parakeet in UI natively

    def _emit_current_styles(self):
        self.settings_version += 1
        engine_val = "nvidia" if self.active_engine == "Parakeet" else "whisper"
        self._save_config()
        self.settings_changed_signal.emit({
            "version": self.settings_version,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "font_italic": self.font_italic,
            "font_underline": self.font_underline,
            "text_color": self.text_color,
            "outline_color": self.outline_color,
            "outline_width": self.outline_width,
            "bg_color": self.subtitle_bg_color if self.show_subtitle_bg else "transparent",
            "is_visible": self.subtitles_visible,
            "skip_vad": self.skip_vad,
            "active_engine": engine_val
        })

    def apply_panel_style(self):
        t = self.theme_manager.get_theme(self.current_theme_idx - 1)
        primary = t.primary
        accent = t.accent
        is_dark = t.mode == "dark"
        widget_bg = "rgba(0, 0, 0, 40)" if is_dark else "rgba(255, 255, 255, 100)"

        self.setStyleSheet(f"QMainWindow {{ background-color: {primary}; }}")
        self.control_panel.setStyleSheet(f"""
            QLabel {{ color: {accent}; font-family: 'Segoe UI Semilight'; font-size: 10pt; }}
            QCheckBox {{ color: {accent}; font-family: 'Segoe UI Semilight'; }}
            QComboBox, QFontComboBox, QSpinBox {{
                background: {widget_bg}; color: {accent}; border-radius: 4px; padding: 4px 8px; border: 1px solid {accent}22; min-height: 24px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid {accent}22;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 25px;
                border-left: 1px solid {accent}22;
            }}
            QPushButton {{
                background: {widget_bg}; color: {accent}; border-radius: 4px; border: 1px solid {accent}22; font-weight: bold; padding: 4px;
            }}
            QPushButton:checked {{ background: {accent}; color: {primary}; }}
        """)

    def _update_theme(self, index):
        self.current_theme_idx = index + 1
        self.apply_panel_style()

    def _on_visibility_toggled(self, checked):
        self.subtitles_visible = checked
        self._emit_current_styles()

    def _on_bg_toggled(self, checked):
        self.show_subtitle_bg = checked
        self._emit_current_styles()

    def _update_font_family(self, font):
        self.font_family = font.family()
        self._emit_current_styles()

    def _update_font_size(self, size):
        self.font_size = size
        self._emit_current_styles()

    def _toggle_bold(self, checked):
        self.font_weight = 700 if checked else 400
        self._emit_current_styles()

    def _toggle_italic(self, checked):
        self.font_italic = checked
        self._emit_current_styles()

    def _toggle_underline(self, checked):
        self.font_underline = checked
        self._emit_current_styles()

    def _pick_text_color(self):
        color = QColorDialog.getColor(QColor(self.text_color), self, "Pick Text Color")
        if color.isValid():
            self.text_color = color.name()
            self._emit_current_styles()

    def _pick_outline_color(self):
        color = QColorDialog.getColor(QColor(self.outline_color), self, "Pick Outline Color")
        if color.isValid():
            self.outline_color = color.name()
            self._emit_current_styles()

    def _update_outline_width(self, width):
        self.outline_width = width
        self._emit_current_styles()

    def _on_debug_toggled(self, state):
        self.debug_toggle_signal.emit(state == Qt.CheckState.Checked.value)

    def _on_simulate_lag_toggled(self, state):
        self.simulate_lag_signal.emit(state == Qt.CheckState.Checked.value)

    def _on_skip_vad_toggled(self, checked):
        self.skip_vad = checked
        self._emit_current_styles()
