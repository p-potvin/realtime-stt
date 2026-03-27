import sys
from PySide6.QtWidgets import (
    QApplication, QGraphicsDropShadowEffect, QMainWindow, QLabel, QVBoxLayout, QWidget, QCheckBox, 
    QComboBox, QHBoxLayout, QFrame, QGridLayout, QPushButton, QSizePolicy,
    QColorDialog, QSpinBox, QFontComboBox
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor, QFont
from vault_themes.theme_manager import VaultThemeManager

class TransparentOverlay(QMainWindow):
    """
    A transparent, frameless, and "always-on-top" caption window for real-time STT.
    Includes persistent settings for style and themes as per VaultWares Standards.
    """
    debug_toggle_signal = Signal(bool)
    settings_changed_signal = Signal(dict)
    exit_requested_signal = Signal()

    def __init__(self, theme_idx=1): # Default: Cyberpunk Cinder
        super().__init__()
        self.theme_manager = VaultThemeManager()
        self.current_theme_idx = theme_idx
        
        # New Font defaults
        self.font_family = "Segoe UI Semilight"
        self.font_size = 18
        self.font_weight = 500 # Medium-ish
        self.font_italic = False
        self.font_underline = False
        
        self.text_color = "#FFFFFF" # White
        self.outline_color = "#000000" # Black
        self.subtitle_bg_color = "rgba(0, 0, 0, 128)" # Default semi-transparent black
        self.show_subtitle_bg = True
        
        self._dragging = False
        self._drag_pos = QPoint()
        self._resizing = False
        self._resize_pos = QPoint()
        
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(2)
        self.shadow.setColor(QColor(self.outline_color))
        self.shadow.setOffset(0, 0)
        
        self._init_ui()

    def update_caption(self, text: str):
        """Thread-safe method to update the displayed text."""
        self.caption_label.setText(text)

    def _init_ui(self):
        # Frameless and translucent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool 
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        # Container for everything
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setCentralWidget(self.central_widget)

        # Drag Handle + UI Controls (TOP BAR)
        self.top_bar = QFrame()
        self.top_bar_layout = QHBoxLayout(self.top_bar)
        self.top_bar_layout.setContentsMargins(5, 0, 10, 0)
        self.top_bar_layout.setSpacing(10)
        self.top_bar.setFixedHeight(30)
        self.top_bar.setStyleSheet("background: rgba(255, 255, 255, 10); border-top-left-radius: 5px; border-top-right-radius: 5px;")
        
        # Drag Handle
        self.drag_handle = QLabel("   ")
        self.drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        self.drag_handle.setToolTip("Drag to move the window")
        self.top_bar_layout.addWidget(self.drag_handle, 1)

        # Control Panel (Grid Layout)
        self.control_panel = QFrame()
        self.control_layout = QGridLayout(self.control_panel)
        self.control_panel.setFixedHeight(180) # Increased height for grouping

        self.settings_toggle = QCheckBox("Show Controls")
        self.settings_toggle.toggled.connect(lambda b: self.control_panel.setVisible(b))
        self.settings_toggle.setChecked(True)
        self.top_bar_layout.addWidget(self.settings_toggle)

        self.exit_x_btn = QPushButton("×")
        self.exit_x_btn.setFixedSize(24, 24)
        self.exit_x_btn.clicked.connect(self._on_exit_clicked)
        self.top_bar_layout.addWidget(self.exit_x_btn)
        
        self.main_layout.addWidget(self.top_bar)

        # Row 0: Theme and Background
        self.control_layout.addWidget(QLabel("Global:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for t in self.theme_manager.get_themes():
            self.theme_combo.addItem(t.name)
        self.theme_combo.setCurrentIndex(self.current_theme_idx - 1)
        self.theme_combo.currentIndexChanged.connect(self._update_theme)
        self.control_layout.addWidget(self.theme_combo, 0, 1)

        self.bg_checkbox = QCheckBox("Subtitle BG")
        self.bg_checkbox.setChecked(self.show_subtitle_bg)
        self.bg_checkbox.toggled.connect(self._on_bg_toggled)
        self.control_layout.addWidget(self.bg_checkbox, 0, 2)

        self.debug_checkbox = QCheckBox("Debug Logs")
        self.debug_checkbox.stateChanged.connect(self._on_debug_toggled)
        self.control_layout.addWidget(self.debug_checkbox, 0, 3)

        # Row 1-2: Consolidated Font/Style (Word Style)
        self.control_layout.addWidget(QLabel("Font:"), 1, 0)
        
        # Font Family
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.font_family))
        self.font_combo.currentFontChanged.connect(self._update_font_family)
        self.control_layout.addWidget(self.font_combo, 1, 1, 1, 2)

        # Font Size
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 120)
        self.size_spin.setValue(self.font_size)
        self.size_spin.valueChanged.connect(self._update_font_size)
        self.control_layout.addWidget(self.size_spin, 1, 3)

        # Row 2: B / I / U buttons + Color
        self.style_layout = QHBoxLayout()
        self.style_layout.setSpacing(2)

        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(24, 24)
        self.bold_btn.setChecked(self.font_weight > 400)
        self.bold_btn.clicked.connect(self._toggle_bold)
        self.style_layout.addWidget(self.bold_btn)

        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedSize(24, 24)
        self.italic_btn.clicked.connect(self._toggle_italic)
        self.style_layout.addWidget(self.italic_btn)

        self.under_btn = QPushButton("U")
        self.under_btn.setCheckable(True)
        self.under_btn.setFixedSize(24, 24)
        self.under_btn.clicked.connect(self._toggle_underline)
        self.style_layout.addWidget(self.under_btn)

        self.text_color_btn = QPushButton("A")
        self.text_color_btn.setFixedSize(24, 24)
        self.text_color_btn.clicked.connect(self._pick_text_color)
        self._update_color_btn_style(self.text_color_btn, self.text_color)
        self.style_layout.addWidget(self.text_color_btn)

        self.control_layout.addLayout(self.style_layout, 2, 1)

        # Outline & Shadows (Grouped)
        self.control_layout.addWidget(QLabel("Shadow:"), 3, 0)
        
        self.shadow_layout = QHBoxLayout()
        self.shadow_layout.setSpacing(5)

        self.outline_color_btn = QPushButton()
        self.outline_color_btn.setFixedSize(24, 24)
        self.outline_color_btn.clicked.connect(self._pick_outline_color)
        self._update_color_btn_style(self.outline_color_btn, self.outline_color)
        self.shadow_layout.addWidget(self.outline_color_btn)

        self.outline_width_spin = QSpinBox()
        self.outline_width_spin.setRange(0, 30)
        self.outline_width_spin.setValue(int(self.shadow.blurRadius()))
        self.outline_width_spin.valueChanged.connect(self._update_outline_width)
        self.shadow_layout.addWidget(self.outline_width_spin)

        self.control_layout.addLayout(self.shadow_layout, 3, 1)

        # Centering Panel
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.control_panel)
        self.main_layout.addWidget(container)
        
        # Caption label area
        self.caption_container = QFrame()
        self.caption_layout = QVBoxLayout(self.caption_container)
        self.caption_label = QLabel("Real-time captions will appear here...")
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption_label.setWordWrap(True)
        self.caption_label.setGraphicsEffect(self.shadow)

        self.caption_layout.addWidget(self.caption_label)
        self.main_layout.addWidget(self.caption_container)

        self.apply_panel_style()
        self._apply_styles()
        self._set_default_window_pos()

    def _set_default_window_pos(self):
        """Sets window width to 100vw and positions it above the taskbar."""
        screen = QApplication.primaryScreen()
        screen_geo = screen.geometry()
        work_geo = screen.availableGeometry()
        
        width = screen_geo.width()
        height = 240
        x = 0
        y = work_geo.height() - height
        self.setGeometry(x, y, width, height)

    def apply_panel_style(self):
        t = self.theme_manager.get_theme(self.current_theme_idx - 1)
        primary = t.primary
        accent = t.accent
        is_dark = t.mode == "dark"
        
        bg_alpha = 200 if is_dark else 160
        bg_rgba = self.theme_manager.get_glass_rgba(primary, bg_alpha)
        widget_bg = "rgba(0, 0, 0, 40)" if is_dark else "rgba(255, 255, 255, 100)"
        
        self.control_panel.setStyleSheet(f"""
            QFrame {{
                background: {bg_rgba};
                border: 1px solid {accent}44;
                border-radius: 12px;
                padding: 10px;
            }}
            QLabel {{ 
                color: {accent}; 
                font-family: 'Segoe UI Semilight'; 
                font-size: 10pt; 
                background: transparent; 
            }}
            QComboBox, QFontComboBox, QSpinBox, QCheckBox {{ 
                background: {widget_bg}; 
                color: {accent}; 
                border-radius: 4px; 
                padding: 2px;
                border: 1px solid {accent}22;
            }}
            QPushButton {{
                background: {widget_bg}; 
                color: {accent}; 
                border-radius: 4px; 
                border: 1px solid {accent}22;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background: {accent};
                color: {primary};
            }}
            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                border: none;
                background: transparent;
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                border: none;
                background: transparent;
            }}
            QSpinBox::up-arrow, QSpinBox::down-arrow {{
                width: 8px;
                height: 8px;
            }}
            QSpinBox::up-arrow {{ 
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 4px solid {accent};
            }}
            QSpinBox::down-arrow {{ 
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {accent};
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.control_panel.setContentsMargins(10, 10, 10, 10)
        self.control_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.exit_x_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent; color: {accent}; font-size: 18pt; font-weight: bold; border: none;
            }}
            QPushButton:hover {{ color: #FF0000; }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.top_bar.underMouse() and not self.exit_x_btn.underMouse() and not self.settings_toggle.underMouse():
                self._dragging = True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            elif event.position().x() > self.width() - 20:
                self._resizing = True
                self._resize_pos = event.globalPosition().toPoint()
                event.accept()

    def mouseDoubleClickEvent(self, event):
        if self.top_bar.underMouse() and not self.exit_x_btn.underMouse() and not self.settings_toggle.underMouse():
            self._set_default_window_pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        elif self._resizing:
            diff = event.globalPosition().toPoint() - self._resize_pos
            new_width = self.width() + diff.x()
            new_height = self.height() + diff.y()
            self.resize(max(new_width, 400), max(new_height, 100))
            self._resize_pos = event.globalPosition().toPoint()
            event.accept()
        
        if not self._dragging and not self._resizing:
            if event.position().x() > self.width() - 20:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif self.top_bar.underMouse() and not self.exit_x_btn.underMouse() and not self.settings_toggle.underMouse():
                 self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._resizing = False
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _on_exit_clicked(self):
        self.exit_requested_signal.emit()

    def _apply_styles(self):
        t = self.theme_manager.get_theme(self.current_theme_idx - 1)
        accent = t.accent
        
        bg_style = self.subtitle_bg_color if self.show_subtitle_bg else "transparent"
        font_italic_style = "italic" if self.font_italic else "normal"
        font_under_style = "underline" if self.font_underline else "none"
        
        self.caption_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color};
                font-family: '{self.font_family}';
                font-size: {self.font_size}pt;
                font-weight: {self.font_weight};
                font-style: {font_italic_style};
                text-decoration: {font_under_style};
                background-color: {bg_style};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        
        self.caption_container.setStyleSheet("QFrame { background-color: transparent; border-radius: 15px; }")
        self.settings_toggle.setStyleSheet(f"color: {accent}; font-family: 'Segoe UI Semilight';")

    def _update_font_family(self, font):
        self.font_family = font.family()
        self._apply_styles()

    def _toggle_bold(self, checked):
        self.font_weight = 700 if checked else 400
        self._apply_styles()

    def _toggle_italic(self, checked):
        self.font_italic = checked
        self._apply_styles()

    def _toggle_underline(self, checked):
        self.font_underline = checked
        self._apply_styles()

    def _update_font_size(self, size):
        self.font_size = size
        self._apply_styles()

    def _update_color_btn_style(self, btn, color):
        btn.setStyleSheet(f"background-color: {color}; border: 1px solid #555; border-radius: 4px;")

    def _pick_text_color(self):
        color = QColorDialog.getColor(QColor(self.text_color), self, "Pick Text Color")
        if color.isValid():
            self.text_color = color.name()
            self._update_color_btn_style(self.text_color_btn, self.text_color)
            self._apply_styles()

    def _pick_outline_color(self):
        color = QColorDialog.getColor(QColor(self.outline_color), self, "Pick Outline Color")
        if color.isValid():
            self.outline_color = color.name()
            self.shadow.setColor(color)
            self._update_color_btn_style(self.outline_color_btn, self.outline_color)
            self._apply_styles()

    def _update_outline_width(self, width):
        self.shadow.setBlurRadius(width)

    def _on_debug_toggled(self, state):
        self.debug_toggle_signal.emit(state == Qt.CheckState.Checked.value)

    def _on_bg_toggled(self, checked):
        self.show_subtitle_bg = checked
        self._apply_styles()

    def set_theme(self, theme_idx):
        self.current_theme_idx = theme_idx
        if hasattr(self, 'theme_combo'):
            self.theme_combo.setCurrentIndex(theme_idx - 1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentOverlay()
    window.show()
    sys.exit(app.exec())
