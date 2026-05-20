import sys
import threading
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from gui_overlay.overlay_window import SubtitleWindow, SettingsWindow
from vaultwares_realtime.stt_strategies import WhisperStrategy

class VaultWaresGUIController:
    def __init__(self, stt_app):
        self.stt_app = stt_app
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.settings_window = SettingsWindow(theme_idx=self.stt_app.theme_idx)
        self.subtitle_window = SubtitleWindow()

        self.stt_app.bridge.update_caption_signal.connect(self.subtitle_window.update_caption)
        self.settings_window.debug_toggle_signal.connect(self.stt_app._toggle_debug_logs)
        self.settings_window.simulate_lag_signal.connect(self.stt_app._set_simulate_lag)
        self.settings_window.settings_changed_signal.connect(self._handle_settings_change)

        self.app.aboutToQuit.connect(self.stt_app.stop)
        self._setup_tray_icon()

    def _setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self._create_tray_icon(), self.app)
        self.tray_icon.setToolTip("VaultWares VaultWares Realtime")
        
        tray_menu = QMenu()
        settings_action = tray_menu.addAction("Settings")
        settings_action.triggered.connect(self.settings_window.showNormal)
        quit_action = tray_menu.addAction("Exit")
        quit_action.triggered.connect(self.app.quit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        self.tray_icon.activated.connect(
            lambda reason: self.settings_window.showNormal() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )

    def _create_tray_icon(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("transparent"))
        painter = QPainter(pixmap)
        painter.setBrush(QColor("#00FFCC"))
        painter.drawEllipse(2, 2, 28, 28)
        painter.end()
        return QIcon(pixmap)

    def _handle_settings_change(self, settings_dict):
        self.stt_app.on_settings_changed(settings_dict)
        if "is_visible" in settings_dict:
            if settings_dict["is_visible"]:
                self.subtitle_window.show()
            else:
                self.subtitle_window.hide()
        self.subtitle_window.apply_styles(settings_dict)

    def run(self):
        self.settings_window.show()
        if self.settings_window.subtitles_visible:
            self.subtitle_window.show()
        else:
            self.subtitle_window.hide()
        
        self._handle_settings_change(self.settings_window.get_current_settings())
        
        self.stt_app.is_running = True
        self.stt_app.start()

        if self.stt_app.active_engine == self.stt_app.ENGINE_WHISPER and getattr(self.stt_app, "sttEngine", None) is None:
            self.stt_app.logger.info("Spawning background thread to eagerly load Faster-Whisper Engine...")  
            
            def load_and_set():
                self.stt_app.logger.info("Background Thread: Preparing to load model into RAM/VRAM.")
                self.stt_app.sttEngine = WhisperStrategy(self.stt_app.device)
                self.stt_app.logger.info("Background Thread: Whisper Engine eager load complete.")
                
            threading.Thread(target=load_and_set, daemon=True).start()

        self.stt_app.logger.info(f"Application running. Target Language: {self.stt_app.language}")
        self.stt_app.logger.info("Tray icon active. Press Ctrl+C in terminal or exit from tray to close.")
        
        try:
            sys.exit(self.app.exec())
        except KeyboardInterrupt:
            self.stt_app.logger.info("Keyboard interrupt received.")
        finally:
            self.stt_app.stop()
