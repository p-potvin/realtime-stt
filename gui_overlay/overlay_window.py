import sys
from PySide6.QtWidgets import (
    QApplication, QGraphicsDropShadowEffect, QMainWindow, QLabel, QVBoxLayout, QWidget, QCheckBox, 
    QComboBox, QHBoxLayout, QFrame, QGridLayout, QSlider, QStyle, QPushButton, QSizePolicy,
    QColorDialog, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, Property, QPropertyAnimation, QEasingCurve, Signal, QPoint
from PySide6.QtGui import QFont, QColor, QPalette, QCursor
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
        self.font_size = 18
        self.text_color = "#FFFFFF" # White as requested
        self.outline_color = "#000000" # Black as requested
        self._dragging = False
        self._drag_pos = QPoint()
        self._resizing = False
        self._resize_pos = QPoint()
        self.shadow = QGraphicsDropShadowEffect(blurRadius=2, color=QColor(self.outline_color), offset=QPoint(0, 0))
        self._init_ui()

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
        # Small background for context but mostly transparent
        self.top_bar.setStyleSheet("background: rgba(255, 255, 255, 10); border-top-left-radius: 5px; border-top-right-radius: 5px;")
        
        # Drag Handle (Text or just space)
        self.drag_handle = QLabel("   ")
        self.drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        self.drag_handle.setToolTip("Drag to move the window")
        self.top_bar_layout.addWidget(self.drag_handle, 1) # Expanding to fill space

        self.settings_toggle = QCheckBox("Show Controls")
        self.settings_toggle.toggled.connect(lambda b: self.control_panel.setVisible(b))
        self.settings_toggle.setChecked(True)
        self.top_bar_layout.addWidget(self.settings_toggle)

        self.exit_x_btn = QPushButton("×")
        self.exit_x_btn.setFixedSize(24, 24)
        self.exit_x_btn.setStyleSheet("""
            QPushButton { 
                background: transparent; color: #800020; font-size: 18pt; font-weight: bold; border: none;
            }
            QPushButton:hover { color: #FF0000; }
        """)
        self.exit_x_btn.clicked.connect(self._on_exit_clicked)
        self.top_bar_layout.addWidget(self.exit_x_btn)
        
        self.main_layout.addWidget(self.top_bar)

        # Control Panel (Collapsible/Thin)
        self.control_panel = QFrame()
        self.control_layout = QGridLayout(self.control_panel)
        self.control_panel.setFixedHeight(120)
        self.apply_panel_style()

        # Theme Dropdown
        self.control_layout.addWidget(QLabel("Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        for t in self.theme_manager.get_themes():
            self.theme_combo.addItem(t.name)
        self.theme_combo.setCurrentIndex(self.current_theme_idx - 1)
        self.theme_combo.currentIndexChanged.connect(self._update_theme)
        self.control_layout.addWidget(self.theme_combo, 0, 1)

        # Font Size Spinner
        self.control_layout.addWidget(QLabel("Font size:"), 1, 0)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(12, 72)
        self.size_spin.setValue(self.font_size)
        self.size_spin.valueChanged.connect(self._update_font_size)
        self.control_layout.addWidget(self.size_spin, 1, 1)

        # Text Color Picker
        self.control_layout.addWidget(QLabel("Text Color:"), 0, 2)
        self.text_color_btn = QPushButton()
        self.text_color_btn.setFixedSize(40, 20)
        self.text_color_btn.clicked.connect(self._pick_text_color)
        self._update_color_btn_style(self.text_color_btn, self.text_color)
        self.control_layout.addWidget(self.text_color_btn, 0, 3)

        # Outline Color Picker
        self.control_layout.addWidget(QLabel("Outline:"), 1, 2)
        self.outline_color_btn = QPushButton()
        self.outline_color_btn.setFixedSize(40, 20)
        self.outline_color_btn.clicked.connect(self._pick_outline_color)
        self._update_color_btn_style(self.outline_color_btn, self.outline_color)
        self.control_layout.addWidget(self.outline_color_btn, 1, 3)

        # Outline Thickness Spinner
        self.control_layout.addWidget(QLabel("Width:"), 0, 4)
        self.outline_width_spin = QSpinBox()
        self.outline_width_spin.setRange(0, 15)
        self.outline_width_spin.setValue(int(self.shadow.blurRadius()))
        self.outline_width_spin.valueChanged.connect(self._update_outline_width)
        self.control_layout.addWidget(self.outline_width_spin, 0, 5)

        # Debug Checkbox
        self.debug_checkbox = QCheckBox("Debug Logs")
        self.debug_checkbox.stateChanged.connect(self._on_debug_toggled)
        self.control_layout.addWidget(self.debug_checkbox, 1, 4)

        # Wrap control panel in a layout that keeps it centered and fit-to-content
        self.panel_container = QWidget()
        self.panel_container_layout = QHBoxLayout(self.panel_container)
        self.panel_container_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_container_layout.addWidget(self.control_panel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.panel_container)
        
        # Caption label area
        self.caption_container = QFrame()
        self.caption_layout = QVBoxLayout(self.caption_container)
        self.caption_label = QLabel("Real-time captions will appear here...")
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption_label.setWordWrap(True)
        
        # Highlight logic for the shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(2)
        self.shadow.setColor(QColor(self.outline_color))
        self.shadow.setOffset(0, 0)
        self.caption_label.setGraphicsEffect(self.shadow)

        self.caption_layout.addWidget(self.caption_label)
        self.main_layout.addWidget(self.caption_container)

        self._apply_styles()

        # Sizing and Window Positioning
        self._set_default_window_pos()

    def _set_default_window_pos(self):
        """Sets window width to 100vw and positions it above the taskbar."""
        screen = QApplication.primaryScreen()
        screen_geo = screen.geometry()
        work_geo = screen.availableGeometry()
        
        # Width: 100vw (Full screen width)
        width = screen_geo.width()
        height = 200
        
        # X: 0 (Left edge)
        x = 0
        
        # Calculate taskbar height (approximate)
        # On Windows, work_geo is the space available for apps. 
        # The difference is normally the taskbar.
        taskbar_height = screen_geo.height() - work_geo.height()
        
        # Offset: The user noted it was at half the taskbar height (y_offset = taskbar_height / 2?)
        # and wants to "double it". doubling 0.5 taskbar height = 1 full taskbar height gap.
        # We start Y at the top of the taskbar (work_geo.height()) and subtract the window height
        # plus one taskbar height as padding to "double" the previous position.
        y = work_geo.height() - height - taskbar_height
        
        self.setGeometry(x, y, width, height)

    def apply_panel_style(self):
        t = self.theme_manager.get_theme(self.current_theme_idx - 1)
        primary = t.primary
        accent = t.accent
        is_dark = t.mode == "dark"
        
        # Transparent but visible background for control panel
        # We use a lower alpha (160) for light themes to ensure readability/see-through
        bg_alpha = 200 if is_dark else 160
        bg_rgba = self.theme_manager.get_glass_rgba(primary, bg_alpha)
        
        # Text/Widget colors based on theme
        widget_bg = "rgba(0, 0, 0, 40)" if is_dark else "rgba(255, 255, 255, 100)"
        text_color = accent
        
        self.control_panel.setStyleSheet(f"""
            QFrame {{
                background: {bg_rgba};
                border: 1px solid {accent}44;
                border-radius: 12px;
                padding: 10px;
            }}
            QLabel {{ 
                color: {text_color}; 
                font-family: 'Segoe UI Semilight'; 
                font-size: 10pt; 
                background: transparent; 
            }}
            QComboBox, QSpinBox, QCheckBox {{ 
                background: {widget_bg}; 
                color: {text_color}; 
                border-radius: 4px; 
                padding: 2px;
                border: 1px solid {accent}22;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.control_panel.setContentsMargins(10, 10, 10, 10)
        self.control_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Update Exit Button to match theme accent
        if hasattr(self, 'exit_x_btn'):
            self.exit_x_btn.setStyleSheet(f"""
                QPushButton {{ 
                    background: transparent; color: {accent}; font-size: 18pt; font-weight: bold; border: none;
                }}
                QPushButton:hover {{ color: #FF0000; }}
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we clicked the top bar (drag area)
            if self.top_bar.underMouse() and not self.exit_x_btn.underMouse() and not self.settings_toggle.underMouse():
                self._dragging = True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            # Check if we are at the right edge for resizing
            elif event.position().x() > self.width() - 20:
                self._resizing = True
                self._resize_pos = event.globalPosition().toPoint()
                event.accept()

    def mouseDoubleClickEvent(self, event):
        """Reset to default position when double-clicking top bar."""
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
        
        # Cursor feedback for resizing and dragging
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
        
        # Background: Transparent/None as requested for captions but with glass-ui touch
        primary = t.primary
        accent = t.accent
        
        # Use primary for background container logic if visible
        bg_alpha = 150 if t["mode"] == "dark" else 180
        
        self.caption_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color};
                font-family: 'Segoe UI Semilight';
                font-size: {self.font_size}pt;
                background-color: transparent;
                padding: 10px;
                font-weight: 500;
            }}
        """)
        
        # The container should have the theme colors
        self.caption_container.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: 15px;
            }}
        """)
        
        # Apply accent to UI elements
        self.theme_combo.setStyleSheet(f"background: {primary}; color: {accent};")
        self.settings_toggle.setStyleSheet(f"color: {accent}; font-family: 'Segoe UI Semilight';")

    def _update_theme(self, index):
        self.current_theme_idx = index + 1
        self._apply_styles()
        self.apply_panel_style()

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
        self._apply_styles()

    def update_caption(self, text):
        self.caption_label.setText(text)

    def _on_debug_toggled(self, state):
        is_checked = (state == Qt.CheckState.Checked.value)
        self.debug_toggle_signal.emit(is_checked)

    def set_theme(self, theme_idx):
        self.current_theme_idx = theme_idx
        self._update_theme(theme_idx - 1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentOverlay()
    window.show()
    sys.exit(app.exec())
