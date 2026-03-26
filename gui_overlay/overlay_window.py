import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPalette

class TransparentOverlay(QMainWindow):
    """
    A transparent, frameless, and "always-on-top" caption window for real-time STT.
    Adheres to VaultWares Glass UI and Solarized styling standards.
    """
    def __init__(self, theme="dark"):
        super().__init__()
        self.theme = theme
        self._init_ui()

    def _init_ui(self):
        # Frameless and translucent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool  # Prevents showing in taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Click-through

        # Main layout container
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        # Caption label styling
        self.caption_label = QLabel("Real-time captions will appear here...")
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        
        # Segoe UI Semilight as per VaultWares standards
        font = QFont("Segoe UI Semilight", 24)
        self.caption_label.setFont(font)
        
        # Solarized-inspired colors
        if self.theme == "dark":
            self.caption_label.setStyleSheet("color: #cc9b21; background-color: rgba(74, 84, 89, 150); border-radius: 10px; padding: 15px;")
        else:
            self.caption_label.setStyleSheet("color: #cc9b21; background-color: rgba(253, 246, 227, 200); border-radius: 10px; padding: 15px;")
            
        self.layout.addWidget(self.caption_label)

        # Sizing and positioning (bottom center of screen)
        screen_geometry = QApplication.primaryScreen().geometry()
        width = int(screen_geometry.width() * 0.8)
        height = 150
        self.setGeometry(
            (screen_geometry.width() - width) // 2, 
            int(screen_geometry.height() * 0.8), 
            width, 
            height
        )

    def update_caption(self, text):
        """Updates the text displayed in the overlay."""
        self.caption_label.setText(text)

    def set_theme(self, theme):
        """Toggles between dark and light themes."""
        self.theme = theme
        self._init_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentOverlay()
    window.show()
    sys.exit(app.exec())
