import logging
import sys
import os
import json
import re
from PySide6.QtWidgets import (
    QApplication, QGraphicsDropShadowEffect, QMainWindow, QLabel, QVBoxLayout, QWidget, QCheckBox, 
    QComboBox, QHBoxLayout, QFrame, QGridLayout, QPushButton, QSizePolicy,
    QColorDialog, QSpinBox, QFontComboBox
)
from PySide6.QtCore import QTimer, Qt, Signal, Slot, QPoint
from PySide6.QtGui import QColor, QCursor, QFont
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
            Qt.WindowType.NoDropShadowWindowHint | # Prevents ugly OS-level ghost borders
            Qt.WindowType.BypassWindowManagerHint | # Avoids taskbar icon and alt-tab presence on Windows
            Qt.WindowType.X11BypassWindowManagerHint | # Same for Linux/X11
            Qt.WindowType.BypassGraphicsProxyWidget | # Avoids some weird Qt rendering issues on certain platforms
            #Qt.WindowType.NoFocus | # Prevents stealing focus on click, but still allows interaction for dragging and context menu if needed
            Qt.WindowType.ToolTip # Ensures the window is treated as a tooltip for better compatibility with various window managers and to avoid focus issues
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_X11BypassTransientForHint, True)
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setStyleSheet("QMainWindow { background: transparent; border: none; margin: 0; padding: 0; }")

        # Draggable state
        self._dragging = False
        self._drag_pos = QPoint()

        self.central_widget = QWidget()
        """ self.central_widget.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.NoDropShadowWindowHint | # Prevents ugly OS-level ghost borders
            Qt.WindowType.BypassWindowManagerHint | # Avoids taskbar icon and alt-tab presence on Windows
            Qt.WindowType.X11BypassWindowManagerHint | # Same for Linux/X11
            Qt.WindowType.BypassGraphicsProxyWidget | # Avoids some weird Qt rendering issues on certain platforms
            Qt.WindowType.ToolTip # Ensures the window is treated as a tooltip for better compatibility with various window managers and to avoid focus issues
        ) """
        self.central_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        #self.central_widget.setAttribute(Qt.WidgetAttribute.WA_X11BypassTransientForHint, True)
        #self.central_widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.central_widget.setStyleSheet("QWidget { background: transparent; border: none; margin: 0; padding: 0; }")
        
        self.main_layout = QVBoxLayout(self.central_widget)
        #self.main_layout.setContentsMargins(10, 10, 10, 10) # Padding for click area
        #self.main_layout.setStyleSheet("QVBoxLayout { background: transparent; border: none; margin: 0; padding: 0; }")
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.central_widget)

        self.caption_label = QLabel("Real-time STT Active...")
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption_label.setWordWrap(True)

        # Determine 90% of screen width as a max width to keep text readable
        screen = QApplication.primaryScreen()
        work_geo = screen.availableGeometry()
        self.caption_label.setMaximumWidth(int(work_geo.width() * 0.9))
        self.caption_label.setMinimumWidth(int(work_geo.width() * 0.7)) # Prevent excessive shrinking on short text

        self._prev_text = ""

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(4)
        self.shadow.setOffset(2, 2)
        self.caption_label.setGraphicsEffect(self.shadow)

        self.main_layout.addWidget(self.caption_label)

        self.caption_label_2 = QLabel("")
        self.caption_label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption_label_2.setWordWrap(True)
        self.caption_label_2.setMaximumWidth(int(work_geo.width() * 0.9))
        self.caption_label_2.setMinimumWidth(int(work_geo.width() * 0.7))

        self.shadow_2 = QGraphicsDropShadowEffect()
        self.shadow_2.setBlurRadius(4)
        self.shadow_2.setOffset(2, 2)
        self.caption_label_2.setGraphicsEffect(self.shadow_2)
        
        self.main_layout.addWidget(self.caption_label_2)

        # Tiny drag handle at top right to allow dragging when text is empty
        self.drag_handle = QLabel()
        self.drag_handle.setFixedSize(12, 12)
        self.drag_handle.setStyleSheet("background-color: transparent; border: 2px solid #000000; border-radius: 6px;")
        self.drag_handle.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.drag_handle.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.drag_handle.setToolTip("Drag to reposition subtitles")
        self.drag_handle.setAccessibleName("Drag Handle")
        
        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.drag_handle)
        
        # Insert drag handle layout above labels
        self.main_layout.insertLayout(0, self.top_layout)

        # Clear timer: 3000ms silence clearing
        self.clear_timer = QTimer(self)
        self.clear_timer.setInterval(3000)
        self.clear_timer.timeout.connect(self._clear_caption)
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

    @Slot()
    def _clear_caption(self):
        """Clears the subtitles when silence duration is reached."""
        self.caption_label.setText("")
        self.caption_label_2.setText("")
        self.caption_label.adjustSize()
        self.caption_label_2.adjustSize()
        self.adjustSize()
        self.clear_timer.stop()

    def update_caption(self, text: str, label_idx: int = 0):
        # Rolling 2-line display: previous sentence on top, current on bottom.
        # This fixes the visual 'duplication' by ensuring a stable top-to-bottom flow.
        if not text.strip():
            return

        if text == self._prev_text:
            return

        display = f"{self._prev_text}\n{text}" if self._prev_text else text
        self.caption_label.setText(display)
        self.caption_label_2.setText("") # Clear second label to avoid confusion
        
        self._prev_text = text
        self.caption_label.adjustSize()
        self.adjustSize()

        # Restart the silence timer
        self.clear_timer.start(3000)

    def apply_styles(self, styles: dict):
        # Explicit QFont assignment fixes stylesheet bounding box truncation bugs (especially 12pt bold)
        font = QFont(styles.get('font_family', 'Segoe UI Semilight'))
        font.setPointSize(styles.get('font_size', 13))
        font.setBold(styles.get('font_weight', 700) >= 700)
        font.setItalic(bool(styles.get('font_italic', False)))
        font.setUnderline(bool(styles.get('font_underline', False)))
        self.caption_label.setFont(font)

        self.caption_label_2.setStyleSheet(f"""QLabel {{ color: {styles.get('text_color', '#00FF00')}; }}""")
        self.caption_label_2.setFont(font)
        
        # Clean refresh to apply bold/italic immediately
        self.caption_label.style().unpolish(self.caption_label)
        self.caption_label.style().polish(self.caption_label)
        self.caption_label_2.style().unpolish(self.caption_label_2)
        self.caption_label_2.style().polish(self.caption_label_2)
        
        bg_color = styles.get("bg_color", "transparent")
        """ self.caption_label.setStyleSheet(f
            QLabel {{
                color: {styles.get('text_color', '#FFFFFF')};
                background-color: {bg_color};
                padding: 8px 16px;
                margin: 4px;
                border-radius: 8px;
                border: none;
            }}
        ) """
        
        # Update shadow
        outline_color = styles.get('outline_color', '#000000')
        self.shadow.setColor(QColor(outline_color))
        self.shadow.setBlurRadius(styles.get('outline_width', 4))
        self.shadow_2.setColor(QColor(outline_color))
        self.shadow_2.setBlurRadius(styles.get('outline_width', 4))
        
        # Update drag handle color
        self.drag_handle.setStyleSheet(f"background-color: transparent; border: 2px solid {outline_color}; border-radius: 6px;")
        
        # Force layout recalculation after font changes
        self.caption_label.adjustSize()
        self.caption_label_2.adjustSize()
        self.adjustSize()


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
        self.font_size = 13
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

    def _get_validated(self, value, expected_type, default_value, min_val=None, max_val=None, regex_pattern=None):
        """Helper to validate data types, bounds, and regex constraints."""
        if value is None:
            return default_value
        if not isinstance(value, expected_type):
            return default_value

        if expected_type in (int, float):
            if min_val is not None and value < min_val:
                return default_value
            if max_val is not None and value > max_val:
                return default_value

        if expected_type == str and regex_pattern:
            if not re.match(regex_pattern, value):
                return default_value

        return value

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)

                # Validate and load settings
                self.current_theme_idx = self._get_validated(data.get("theme_idx"), int, self.current_theme_idx, min_val=1, max_val=10)

                # Using a generic alphanumeric + space regex for font family to prevent injection
                self.font_family = self._get_validated(data.get("font_family"), str, self.font_family, regex_pattern=r"^[\w\s\-]+$")

                self.font_size = self._get_validated(data.get("font_size"), int, self.font_size, min_val=8, max_val=120)
                self.font_weight = self._get_validated(data.get("font_weight"), int, self.font_weight, min_val=100, max_val=900)
                self.font_italic = self._get_validated(data.get("font_italic"), bool, self.font_italic)
                self.font_underline = self._get_validated(data.get("font_underline"), bool, self.font_underline)

                # Regex for #RRGGBB colors
                hex_color_pattern = r"^#[0-9a-fA-F]{6}$"
                self.text_color = self._get_validated(data.get("text_color"), str, self.text_color, regex_pattern=hex_color_pattern)
                self.outline_color = self._get_validated(data.get("outline_color"), str, self.outline_color, regex_pattern=hex_color_pattern)

                self.outline_width = self._get_validated(data.get("outline_width"), int, self.outline_width, min_val=0, max_val=30)

                self.show_subtitle_bg = self._get_validated(data.get("show_subtitle_bg"), bool, self.show_subtitle_bg)
                self.skip_vad = self._get_validated(data.get("skip_vad"), bool, self.skip_vad)
                self.subtitles_visible = self._get_validated(data.get("subtitles_visible"), bool, self.subtitles_visible)

                self.active_engine = data.get("active_engine", "Parakeet")
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
        self.setMinimumWidth(500)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Logo / Header
        self.header_layout = QHBoxLayout()
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(32, 32)
        self.logo_label.setScaledContents(True)
        self.header_layout.addWidget(self.logo_label)
        
        self.title_label = QLabel("VaultWares STT Settings")
        font = QFont("Segoe UI", 14)
        font.setBold(True)
        self.title_label.setFont(font)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.main_layout.addLayout(self.header_layout)

        # Control Panel Wrapper
        self.control_panel = QFrame()
        self.control_panel.setObjectName("ControlPanel")
        self.control_layout = QGridLayout(self.control_panel)
        self.control_layout.setContentsMargins(15, 15, 15, 15)
        self.control_layout.setHorizontalSpacing(15)
        self.control_layout.setVerticalSpacing(15)
        
        row = 0
        # Theme
        self.control_layout.addWidget(QLabel("Theme:"), row, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.setToolTip("Theme Selection")
        self.theme_combo.setAccessibleName("Theme Selection")
        # Make combo boxes act more like web dropdowns
        self.theme_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for t in self.theme_manager.get_themes():
            self.theme_combo.addItem(t.name)
        self.theme_combo.setCurrentIndex(self.current_theme_idx - 1)
        self.theme_combo.currentIndexChanged.connect(self._update_theme)
        self.control_layout.addWidget(self.theme_combo, row, 1, 1, 3)
        
        row += 1
        # Visibility & BG
        self.visibility_checkbox = QCheckBox("Show Subtitles")
        self.visibility_checkbox.setToolTip("Toggle Subtitle Visibility")
        self.visibility_checkbox.setAccessibleName("Toggle Subtitle Visibility")
        self.visibility_checkbox.setChecked(self.subtitles_visible)
        self.visibility_checkbox.toggled.connect(self._on_visibility_toggled)
        self.control_layout.addWidget(self.visibility_checkbox, row, 0, 1, 2)

        self.bg_checkbox = QCheckBox("Subtitle Canvas")
        self.bg_checkbox.setToolTip("Toggle Subtitle Canvas Background")
        self.bg_checkbox.setAccessibleName("Toggle Subtitle Canvas Background")
        self.bg_checkbox.setChecked(self.show_subtitle_bg)
        self.bg_checkbox.toggled.connect(self._on_bg_toggled)
        self.control_layout.addWidget(self.bg_checkbox, row, 2, 1, 2)

        row += 1
        # Adv Toggles
        self.skip_vad_checkbox = QCheckBox("Skip VAD")
        self.skip_vad_checkbox.setToolTip("Skip Voice Activity Detection")
        self.skip_vad_checkbox.setAccessibleName("Skip Voice Activity Detection")
        self.skip_vad_checkbox.setChecked(self.skip_vad)
        self.skip_vad_checkbox.toggled.connect(self._on_skip_vad_toggled)
        self.control_layout.addWidget(self.skip_vad_checkbox, row, 0, 1, 1)

        self.debug_checkbox = QCheckBox("Debug Logs")
        self.debug_checkbox.setToolTip("Toggle Debug Logs")
        self.debug_checkbox.setAccessibleName("Toggle Debug Logs")
        self.debug_checkbox.setChecked(True)
        self.debug_checkbox.stateChanged.connect(self._on_debug_toggled)
        self.control_layout.addWidget(self.debug_checkbox, row, 1, 1, 1)

        self.simulate_lag_checkbox = QCheckBox("Simulate Lag")
        self.simulate_lag_checkbox.setToolTip("Simulate Network Lag")
        self.simulate_lag_checkbox.setAccessibleName("Simulate Network Lag")
        self.simulate_lag_checkbox.stateChanged.connect(self._on_simulate_lag_toggled)
        self.control_layout.addWidget(self.simulate_lag_checkbox, row, 2, 1, 2)
        
        row += 1
        # Engine Selection
        self.control_layout.addWidget(QLabel("STT Engine:"), row, 0)
        self.engine_combo = QComboBox()
        self.engine_combo.setToolTip("STT Engine Selection")
        self.engine_combo.setAccessibleName("STT Engine Selection")
        self.engine_combo.addItems(["Whisper", "Parakeet"])
        self.engine_combo.setCurrentText(self.active_engine)
        self.engine_combo.currentTextChanged.connect(self._on_engine_changed)
        self.control_layout.addWidget(self.engine_combo, row, 1, 1, 3)
        
        row += 1
        # Font settings
        self.control_layout.addWidget(QLabel("Font:"), row, 0)
        self.font_combo = QFontComboBox()
        self.font_combo.setToolTip("Font Family")
        self.font_combo.setAccessibleName("Font Family")
        self.font_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.font_combo.setCurrentFont(QFont(self.font_family))
        self.font_combo.currentFontChanged.connect(self._update_font_family)
        self.control_layout.addWidget(self.font_combo, row, 1, 1, 3)

        row += 1
        self.control_layout.addWidget(QLabel("Style:"), row, 0)
        
        style_layout = QHBoxLayout()
        self.size_spin = QSpinBox()
        self.size_spin.setToolTip("Font Size")
        self.size_spin.setAccessibleName("Font Size")
        self.size_spin.setRange(8, 120)
        self.size_spin.setSuffix(" pt")
        self.size_spin.setValue(self.font_size)
        self.size_spin.valueChanged.connect(self._update_font_size)
        style_layout.addWidget(self.size_spin)

        self.bold_btn = QPushButton("B")
        self.bold_btn.setToolTip("Bold Text (Ctrl+B)")
        self.bold_btn.setAccessibleName("Bold Text")
        self.bold_btn.setShortcut("Ctrl+B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setChecked(self.font_weight > 400)
        f_bold = QFont(); f_bold.setBold(True); self.bold_btn.setFont(f_bold)
        self.bold_btn.clicked.connect(self._toggle_bold)
        style_layout.addWidget(self.bold_btn)

        self.italic_btn = QPushButton("I")
        self.italic_btn.setToolTip("Italic Text (Ctrl+I)")
        self.italic_btn.setAccessibleName("Italic Text")
        self.italic_btn.setShortcut("Ctrl+I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setChecked(self.font_italic)
        f_italic = QFont(); f_italic.setItalic(True); self.italic_btn.setFont(f_italic)
        self.italic_btn.clicked.connect(self._toggle_italic)
        style_layout.addWidget(self.italic_btn)

        self.under_btn = QPushButton("U")
        self.under_btn.setToolTip("Underline Text (Ctrl+U)")
        self.under_btn.setAccessibleName("Underline Text")
        self.under_btn.setShortcut("Ctrl+U")
        self.under_btn.setCheckable(True)
        self.under_btn.setChecked(self.font_underline)
        f_under = QFont(); f_under.setUnderline(True); self.under_btn.setFont(f_under)
        self.under_btn.clicked.connect(self._toggle_underline)
        style_layout.addWidget(self.under_btn)

        self.text_color_btn = QPushButton("A")
        self.text_color_btn.setToolTip("Text Color")
        self.text_color_btn.setAccessibleName("Text Color")
        f_color = QFont(); f_color.setBold(True); self.text_color_btn.setFont(f_color)
        self.text_color_btn.clicked.connect(self._pick_text_color)
        style_layout.addWidget(self.text_color_btn)
        
        self.control_layout.addLayout(style_layout, row, 1, 1, 3)
        
        row += 1
        # Shadow / Outline Controls
        self.control_layout.addWidget(QLabel("Shadow:"), row, 0)
        shadow_layout = QHBoxLayout()
        
        self.outline_color_btn = QPushButton("Color")
        self.outline_color_btn.setToolTip("Outline Color")
        self.outline_color_btn.setAccessibleName("Outline Color")
        self.outline_color_btn.clicked.connect(self._pick_outline_color)
        shadow_layout.addWidget(self.outline_color_btn)

        self.outline_width_spin = QSpinBox()
        self.outline_width_spin.setToolTip("Outline Width")
        self.outline_width_spin.setAccessibleName("Outline Width")
        self.outline_width_spin.setRange(0, 30)
        self.outline_width_spin.setValue(self.outline_width)
        self.outline_width_spin.setPrefix("Blur width: ")
        self.outline_width_spin.setSuffix(" px")
        self.outline_width_spin.blockSignals(True)
        self.outline_width_spin.valueChanged.connect(self._update_outline_width)
        self.outline_width_spin.blockSignals(False)
        shadow_layout.addWidget(self.outline_width_spin)
        
        self.control_layout.addLayout(shadow_layout, row, 1, 1, 3)
        
        self.main_layout.addWidget(self.control_panel)
        self.main_layout.addStretch()
        self.apply_panel_style()

    def _emit_current_styles(self):
        engine_val = "nvidia" if self.active_engine == "Parakeet" else "whisper"
        new_state = {
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
        
        # Prevent spamming signals if state hasn't actually mutated
        if getattr(self, '_last_emitted_state', None) == new_state:
            return
            
        self._last_emitted_state = new_state
        self.settings_version += 1
        new_state["version"] = self.settings_version
        
        self._save_config()
        self.settings_changed_signal.emit(new_state)

    def apply_panel_style(self):
        t = self.theme_manager.get_theme(index=int(self.current_theme_idx) - 1)
        primary = t.primary
        accent = t.accent
        text = getattr(t, 'text', '#FFFFFF')
        border = getattr(t, 'border', f"{accent}22")
        is_dark = t.mode == "dark"
        widget_bg = "rgba(0, 0, 0, 40)" if is_dark else "rgba(255, 255, 255, 100)"

        self.setStyleSheet(f"QMainWindow {{ background-color: {primary}; }}")
        
        # update logo and favicon dynamically based on theme mode
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(base_dir, "vault_themes", "assets")
        
        logo_name = "vaultwares-minimal-gold-filled.png" if is_dark else "vaultwares-minimal-ink-filled.png"
        icon_name = "vaultwares-favicon-gold-filled-64.png" if is_dark else "vaultwares-favicon-ink-64.png"
        
        from PySide6.QtGui import QIcon, QPixmap
        pixmap_path = os.path.join(assets_dir, "logos", logo_name)
        icon_path = os.path.join(assets_dir, "favicons", icon_name)

        if os.path.exists(pixmap_path):
            self.logo_label.setPixmap(QPixmap(pixmap_path))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.title_label.setStyleSheet(f"color: {accent};")

        self.control_panel.setStyleSheet(f"""
            QFrame#ControlPanel {{
                background-color: {getattr(t, 'surface', 'transparent')};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLabel {{ color: {text}; font-family: 'Segoe UI Semilight'; font-size: 10pt; }}
            QCheckBox {{ color: {text}; font-family: 'Segoe UI Semilight'; }}
            QCheckBox:focus {{
                background-color: {accent}22;
                border-radius: 4px;
            }}
            QComboBox, QFontComboBox, QSpinBox {{
                background: {widget_bg}; color: {text}; border-radius: 4px; padding: 4px 8px; 
                border: 1px solid {border}; min-height: 24px;
            }}
            QComboBox:focus, QFontComboBox:focus, QSpinBox:focus {{
                border: 2px solid {accent};
            }}
            QPushButton {{
                background: {widget_bg}; color: {text}; border-radius: 4px; 
                border: 1px solid {border}; font-weight: bold; padding: 6px;
            }}
            QPushButton:hover {{
                border: 1px solid {accent};
            }}
            QPushButton:focus {{
                border: 2px solid {accent};
                outline: none;
            }}
            QPushButton:checked {{ background: {accent}; color: {primary}; border: 1px solid {accent}; }}
            QCheckBox:focus, QComboBox:focus, QFontComboBox:focus, QSpinBox:focus, QPushButton:focus {{
                border: 1px solid {accent};
                outline: none;
            }}
        """)

    def _update_theme(self, index):
        self.current_theme_idx = index + 1
        self.apply_panel_style()
        self._emit_current_styles()

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

    def _on_engine_changed(self, text):
        self.active_engine = text
        self._emit_current_styles()
