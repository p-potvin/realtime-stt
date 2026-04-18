import sys
import os
import time
import threading
import numpy as np
import logging
import secrets
import string
import argparse
import subprocess
import secrets

import vault_sync
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from PySide6.QtCore import Signal, QObject

# Run vault synchronization at startup
vault_sync.sync_vault_dependencies()
# (Re-enabled after verification)

from stt_engine.audio_capture import AudioRecorder
from stt_engine.vad_logic import SileroVADWrapper
from stt_engine.faster_whisper_wrapper import FasterWhisperWrapper
from stt_engine.parakeet_wrapper import ParakeetV3Wrapper
from gui_overlay.overlay_window import SubtitleWindow, SettingsWindow

# Configure root logger for the application
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Create a file handler so debug logs can be seen even with pythonw
file_handler = logging.FileHandler("realtime_stt.log", mode="w", encoding="utf-8")
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)

# Create a stream handler for CLI runs
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

class CommunicationBridge(QObject):
    """Bridge for cross-thread signals to the PySide6 UI."""
    update_caption_signal = Signal(str, int)

class RealTimeSTTApp:
    """
    Core Application orchestrating audio capture, VAD filtering, 
    Faster-Whisper transcription, and GUI overlay updates.
    """
    def __init__(self, model_size="distil-small.en", device="cpu", language="en", theme_idx=2):
        self.correlation_id = "c" + "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        self.logger = logging.getLogger("vaultwares.main")
        self.logger.info(f"Starting realtime-stt app (CorrelationId: {self.correlation_id})")
        
        self.language = language
        self.theme_idx = theme_idx
        self.device = device
        self.active_engine = "whisper" # Default to Whisper
        self.skip_vad = False
        self.last_settings_version = -1       
        
        # Core components (Lazy initialized to speed up startup)
        self.vad = SileroVADWrapper(device="cpu" if self.device == "cpu" else "cuda")
        
        self.ENGINE_NVIDIA = "nvidia"
        self.ENGINE_WHISPER = "whisper"
        
        # We will hold the active STT engine wrapper in this single property
        self.sttEngine = None
        
        # We will use soundcard's default speaker loopback
        self.recorder = AudioRecorder(device_name=None, samplerate=16000, blocksize=512)
        
        self.is_running = False
        self.is_processing = True # Toggle to pause audio processing when subtitles hidden
        self.speech_buffer = []
        self.chunk_index = 0
        self._proc_counter = 0

        self.transcription_queue = []
        self.transcription_lock = threading.Lock()        
        self.stt_semaphore = threading.Semaphore(2) # Limit to 2 concurrent STT jobs        self.transcription_queue_threshold = 2 # Allow more backlog since chunks are much longer now
        
        self.bridge = CommunicationBridge()

        # Sliding window parameters optimized for highly concurrent real-time
        self.max_buffer_size = 75  # ~2.4 seconds of audio (75 * 32ms) to fire jobs faster but keep context
        self.min_speech_trigger = 5  # ~160ms minimum to attempt transcription
        self.simulate_lag = False # Initialize simulate_lag properly

    def _set_simulate_lag(self, state):
        self.simulate_lag = state
        self.logger.info(f"Simulate STT Lag enabled: {state}")

    def processing_loop(self):
        """
        Refined processing thread:
        1. Pulls chunks (32ms / 512 samples) from recorder.
        2. Filters using VAD.
        3. Accumulates speech chunks (including intra-speech silence) into a sliding window.
        4. Transcribes and emits window signals.
        """
        self.logger.info("Processing loop started.")
        self._proc_counter = 0


        silence_counter = 0
        # ~320 ms of consecutive silence needed to flush the buffer (10 × 32 ms chunks)
        max_silence_chunks = int(0.5 * self.max_buffer_size)

        max_silence_chunks = 25 # ~0.8 seconds of silence to flush buffer

        while self.is_running:
            if not self.is_processing:
                time.sleep(0.5)
                continue
                
            chunk = self.recorder.get_chunk(timeout=None)
            if chunk is None:
                continue

            self._proc_counter += 1
            if self._proc_counter % 100 == 0:
                self.logger.info(f"Processing Loop: Pulled chunk {self._proc_counter} from queue.")

            # VAD logic
            if self.skip_vad:
                speech_prob = 1.0
            else:
                if self.vad is None:
                    self.logger.info("Initializing VAD (Lazy Load)...")
                    self.vad = SileroVADWrapper(device="cpu" if self.device == "cpu" else "cuda")
                speech_prob = self.vad.get_speech_prob(chunk)

            if self._proc_counter % 20 == 0:
                peak_val = np.max(np.abs(chunk))
                self.logger.info(f"VAD Check - Prob: {speech_prob:.4f} (Threshold: 0.15) | Peak: {peak_val:.4f} | Buffer: {len(self.speech_buffer)}")

            is_in_speech = bool(self.speech_buffer)

            if speech_prob >= 0.15:
                if not is_in_speech:
                    self.logger.info(f"Speech Activity Detected (Prob: {speech_prob:.4f}) - Starting buffer accumulation.")
                self.speech_buffer.append(chunk)
                silence_counter = 0

                if len(self.speech_buffer) >= self.max_buffer_size:
                    # Only queue if the buffer actually has data (safety check for 'empty chunk' bug)
                    if self.speech_buffer:
                        self.logger.debug(f"Max buffer limit reached ({self.max_buffer_size}). Triggering transcription.")
                        self._queue_transcription(np.concatenate(self.speech_buffer))
                    # Keep 1-chunk overlap for context continuity
                    self.speech_buffer = self.speech_buffer[-1:]
            else:
                # Once speech has started, keep buffering even during brief pauses so that
                # natural word gaps don't fragment the audio fed to the STT model.
                if is_in_speech:
                    self.speech_buffer.append(chunk)
                silence_counter += 1

                if silence_counter >= max_silence_chunks:
                    if self.speech_buffer and len(self.speech_buffer) >= self.min_speech_trigger:
                        self._queue_transcription(np.concatenate(self.speech_buffer))
                    
                    else:
                        # Only log discarded tiny chunks on debug to reduce spam
                        self.logger.debug(f"Discarding audio buffer too small ({len(self.speech_buffer)} chunks) under min threshold.")
                    self.speech_buffer = []
                    silence_counter = 0

    def start(self):
        """Starts the capture and processing threads."""
        if getattr(self, '_threads_started', False):
            return
        self._threads_started = True
        
        self.recorder.start_recording()
        
        self.thread = threading.Thread(target=self.processing_loop, daemon=True)
        self.thread.start()
        
        self.transcription_thread = threading.Thread(target=self.transcription_loop, daemon=True)
        self.transcription_thread.start()

    def stop(self):
        """Stops the app and cleans up."""
        self.is_running = False
        self.recorder.stop_recording()
        if hasattr(self, 'thread'):
            self.thread.join(timeout=None)
        if hasattr(self, 'transcription_thread'):
            self.transcription_thread.join(timeout=None)

    def _queue_transcription(self, audio_data):
        """Pushes an audio block to the transcription queue."""
        self.logger.info(f"Queueing transcription chunk (Size: {len(audio_data)} samples)")
        with self.transcription_lock:
            self.transcription_queue.append(audio_data)

    def transcription_loop(self):
        """
        Background worker that processes accumulated audio blocks.
        Implements the heap/queue hybrid strategy.
        """
        self.logger.info("Transcription Loop Thread started.")
        while self.is_running:
            # Block here until a Whisper slot is available, rather than popping THEN waiting.
            self.stt_semaphore.acquire()
            
            audio_payload = None
            with self.transcription_lock:
                q_size = len(self.transcription_queue)
                if q_size > 0:
                    if q_size > self.transcription_queue_threshold:
                        # Too much backlog! Switch to Stack/LIFO for exactly 1 chunk
                        self.logger.warning(f"Queue threshold ({self.transcription_queue_threshold}) exceeded! Switching to LIFO for most recent subtitles.")
                        audio_payload = self.transcription_queue.pop(-1)
                        # Flush the buffer for all old tasks
                        self.transcription_queue.clear()
                    else:
                        # Normal Queue/FIFO
                        audio_payload = self.transcription_queue.pop(0)

            if audio_payload is not None:
                idx = self.chunk_index
                self.chunk_index = (self.chunk_index + 1) % 2
                
                def stt_worker(payload, l_idx):
                    try:
                        self.logger.info(f"Starting STT worker thread for chunk size {len(payload)}")
                        self._run_stt(payload, l_idx)
                    except Exception as e:
                        self.logger.error(f"Worker thread crashed: {e}")
                    finally:
                        self.logger.info("STT worker thread finished, releasing semaphore")
                        self.stt_semaphore.release()
                        
                threading.Thread(target=stt_worker, args=(audio_payload, idx), daemon=True).start()
            else:
                self.stt_semaphore.release()
                time.sleep(0.05)

    def _run_stt(self, full_audio, label_idx):
        try:
            log_dir = os.path.join(os.getcwd(), "audio_logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Generate a unique filename based on timestamp
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            audio_id = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))
            audio_path = os.path.join(log_dir, f"transcription_{timestamp}_{audio_id}.mp3")

            if self.simulate_lag:
                time.sleep(3.0) # Introduce artificial 3 second latency for testing

            text = ""
            if self.active_engine == self.ENGINE_NVIDIA:
                # Lazy initialization for Parakeet
                if not isinstance(self.sttEngine, ParakeetV3Wrapper):
                    self.logger.info("Initializing Parakeet Engine...")
                    self.sttEngine = ParakeetV3Wrapper(model_name="nvidia/canary-1b")
                
                text = self.sttEngine.transcribe(full_audio)
            else:
                # Lazy initialization for Faster-Whisper
                if not isinstance(self.sttEngine, FasterWhisperWrapper):
                    self.logger.info("Initializing Faster-Whisper Engine...")
                    self.sttEngine = FasterWhisperWrapper(
                        model_size="distil-small.en",
                        device=self.device,
                        compute_type="float16" if self.device == "cuda" else "int8"
                    )
                    self.sttEngine.get_model()

                # Use the specialized chunk method for speed, pass language
                # Faster-Whisper's model.transcribe handles language
                self.logger.debug("Calling FasterWhisper transcribe with VAD-filtered block.")
                segments, info = self.sttEngine.transcribe(
                    full_audio,
                    beam_size=1,
                    vad_filter=False,  # Already filtered by our VAD
                    language=self.language,
                    word_timestamps=False,
                    condition_on_previous_text=False, # Crucial for real-time speed to prevent context hallucinations
                    initial_prompt=""
                )
                self.logger.debug("FasterWhisper transcribe finished, extracting text.")
                text = "".join(s.text for s in segments).strip()
                self.logger.debug(f"FasterWhisper extracted text: '{text}'")

            if text and len(text.strip()) > 1:
                self.logger.info(f"Transcription ({self.language}) [{self.active_engine}]: {text}")
                self.bridge.update_caption_signal.emit(text, label_idx)
            else:
                self.logger.debug(f"Transcription output was effectively empty: '{text}'")
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")

    def _toggle_debug_logs(self, state):
        """Toggles logging level (INFO/DEBUG)"""
        level = logging.DEBUG if state else logging.INFO

        # Update root logger so handlers pick it up
        logging.getLogger().setLevel(level)

        # Update app-level logger
        logging.getLogger("vaultwares").setLevel(level)

        # Explicitly update sub-loggers
        if self.vad:
            self.vad.logger.setLevel(level)
        self.recorder.logger.setLevel(level)
        
        if self.sttEngine and hasattr(self.sttEngine, 'logger'):
            self.sttEngine.logger.setLevel(level)
            
        self.logger.info(f"Global Debug Logging: {'ENABLED' if state else 'DISABLED'}")

    def on_settings_changed(self, settings_dict: dict):
        """Callback for GUI settings changes."""
        # Fix for loop: Check version flag instead of whole object
        new_version = settings_dict.get("version", 0)
        if getattr(self, 'last_settings_version', -1) == new_version:
            return
        self.last_settings_version = new_version

        if "skip_vad" in settings_dict and self.skip_vad != settings_dict["skip_vad"]:
            self.skip_vad = settings_dict["skip_vad"]
            self.logger.info(f"VAD Bypass set to: {self.skip_vad}")
        
        if "active_engine" in settings_dict:
            new_engine = settings_dict["active_engine"].lower()
            if self.active_engine != new_engine:
                self.active_engine = new_engine
                self.logger.info(f"Active engine changed to: {self.active_engine}")

        if "is_visible" in settings_dict and self.is_processing != settings_dict["is_visible"]:
            visible = settings_dict["is_visible"]
            self.is_processing = visible
            if visible:
                self.subtitle_window.show()
                # If we paused recording, start it again
                if not self.recorder.is_recording:
                    self.recorder.start_recording()
            else:
                self.subtitle_window.hide()
                # Stop recording when subtitles are hidden to save resources
                self.recorder.stop_recording()
                
        # Forward style changes to the subtitle window
        if hasattr(self, 'subtitle_window'):
            self.subtitle_window.apply_styles(settings_dict)

    # Incorporate this with the submodule vault-themes later for dynamic theming support
    # and to reuse the same themes accross projects.
    def create_tray_icon(self):
        """Creates a simple colored icon for the tray"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("transparent"))
        painter = QPainter(pixmap)
        painter.setBrush(QColor("#00FFCC")) # Cyberpunk accent
        painter.drawEllipse(2, 2, 28, 28)
        painter.end()
        return QIcon(pixmap)
    
    def _eager_load_whisper(self):
        """Asynchronously initialize whisper to prevent freezing the PySide6 event loop."""
        self.logger.info("Background Thread: Preparing to load model into RAM/VRAM.")
        self.sttEngine = FasterWhisperWrapper(
            model_size="distil-small.en",
            device=self.device,
            compute_type="default"
        )
        self.sttEngine.get_model() # prime the model into memory
        self.logger.info("Background Thread: Whisper Engine eager load complete.")

    def run(self):
        """Initializes GUI, Audio and starts processing thread."""
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False) # Keep running when settings closed

        self.settings_window = SettingsWindow(theme_idx=self.theme_idx)
        self.subtitle_window = SubtitleWindow()

        # Connect signals FIRST so initialization emits are caught, though SettingsWindow already emited in init.
        self.bridge.update_caption_signal.connect(self.subtitle_window.update_caption)
        self.settings_window.debug_toggle_signal.connect(self._toggle_debug_logs)
        self.settings_window.simulate_lag_signal.connect(self._set_simulate_lag)
        self.settings_window.settings_changed_signal.connect(self.on_settings_changed)
 
        # Explicitly apply the loaded settings once
        self.on_settings_changed(self.settings_window.get_current_settings())
        
        # Tray Icon Setup
        self.tray_icon = QSystemTrayIcon(self.create_tray_icon(), app)
        self.tray_icon.setToolTip("VaultWares Real-Time STT")
        
        tray_menu = QMenu()
        settings_action = tray_menu.addAction("Settings")
        settings_action.triggered.connect(self.settings_window.showNormal)
        quit_action = tray_menu.addAction("Exit")
        quit_action.triggered.connect(app.quit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        self.tray_icon.activated.connect(
            lambda reason: self.settings_window.showNormal() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )

        # Initial display
        self.settings_window.show()
        if self.settings_window.subtitles_visible:
            self.subtitle_window.show()
        else:
            self.subtitle_window.hide()
        
        self.is_running = True

        # Start Threads
        self.start()

        # Eager load Whisper Model right after UI displays in background
        if self.active_engine == self.ENGINE_WHISPER and getattr(self, "sttEngine", None) is None:
            self.logger.info("Spawning background thread to eagerly load Faster-Whisper Engine...")  
            threading.Thread(target=self._eager_load_whisper, daemon=True).start()

        self.logger.info(f"Application running. Target Language: {self.language}")
        self.logger.info("Tray icon active. Press Ctrl+C in terminal or exit from tray to close.")
        
        try:
            sys.exit(app.exec())
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received.")
        finally:
            self.logger.info("Exiting application...")
            self.is_running = False
            self.recorder.stop_recording()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VaultWares Real-Time STT")
    parser.add_argument("--model", type=str, default="medium", help="Faster-Whisper model size")
    parser.add_argument("--device", type=str, default="cpu", help="Execution device (cuda/cpu)")
    parser.add_argument("--lang", type=str, default="en", help="Target language (e.g., en, fr, es)")
    parser.add_argument("--theme", type=int, default=2, help="Initial theme index (1-9)")
    args = parser.parse_args()

    app_instance = RealTimeSTTApp(
        model_size=args.model, 
        device=args.device,
        language=args.lang,
        theme_idx=args.theme
    )
    app_instance.run()

