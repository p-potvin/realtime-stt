import sys
import threading
import queue
import numpy as np
import time
import logging
import random
import string
import argparse
import vault_sync
from PySide6.QtWidgets import QApplication

# Run vault synchronization at startup
vault_sync.sync_vault_dependencies()

from PySide6.QtCore import Signal, QObject
from stt_engine.audio_capture import AudioRecorder
from stt_engine.vad_logic import SileroVADWrapper
from stt_engine.faster_whisper_wrapper import FasterWhisperWrapper
from gui_overlay.overlay_window import TransparentOverlay

# Configure root logger for the application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    stream=sys.stdout
)

class CommunicationBridge(QObject):
    """Bridge for cross-thread signals to the PySide6 UI."""
    update_caption_signal = Signal(str)

class RealTimeSTTApp:
    """
    Core Application orchestrating audio capture, VAD filtering, 
    Faster-Whisper transcription, and GUI overlay updates.
    """
    def __init__(self, model_size="large-v3", device="cuda", language="en", theme_idx=2):
        self.correlation_id = "c" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.logger = logging.getLogger("vaultwares.main")
        self.logger.info(f"Starting realtime-stt app (CorrelationId: {self.correlation_id})")
        self.language = language
        self.theme_idx = theme_idx
        
        # Initialize Core components with VaultWares standard logging
        # Silero VAD is lightweight - attempt CUDA, fall back to CPU if needed (handled in wrapper)
        self.vad = SileroVADWrapper(device="cuda" if device == "cuda" else "cpu")
        
        # Faster-Whisper on RTX 3060 CUDA by default, fallback handled inside get_model()
        self.stt = FasterWhisperWrapper(
            model_size=model_size, 
            device=device,
            compute_type="float16" if device == "cuda" else "int8"
        )
        
        # Audio capturing at 16kHz Mono
        # Silero VAD requires specific chunk sizes (512, 1024, or 1536 samples at 16kHz)
        # We'll use 512 samples (~32ms) to minimize latency and satisfy VAD requirements
        self.recorder = AudioRecorder(samplerate=16000, blocksize=512)
        
        self.is_running = False
        self.speech_buffer = []
        self.bridge = CommunicationBridge()
        
        # Sliding window parameters
        self.max_buffer_size = 96  # ~3 seconds of audio (96 * 32ms chunks)
        self.min_speech_trigger = 16 # ~500ms minimum to attempt transcription

    def processing_loop(self):
        """
        Refined processing thread:
        1. Pulls chunks (32ms / 512 samples) from recorder.
        2. Filters using VAD.
        3. Accumulates speech chunks.
        4. Transcribes and emits window signals.
        """
        self.logger.info("Processing loop started.")
        
        silence_counter = 0
        max_silence_chunks = 45 # ~1.4 seconds of silence to flush buffer (45 * 32ms)
        
        while self.is_running:
            chunk = self.recorder.get_chunk(timeout=1.0)
            if chunk is None:
                continue
            
            # Normalize chunk (SoundDevice already returns float32 generally)
            speech_prob = self.vad.get_speech_prob(chunk)
            
            if speech_prob >= 0.4:
                self.speech_buffer.append(chunk)
                silence_counter = 0
                
                # If we've accumulated significant speech, perform partial transcription
                if len(self.speech_buffer) >= self.max_buffer_size:
                    self._request_transcription()
                    # Slide the window (keep ~1 sec overlap for context)
                    self.speech_buffer = self.speech_buffer[-32:] 
            else:
                silence_counter += 1
                
                # If we were processing speech and now it's silent, flush
                if self.speech_buffer and silence_counter >= max_silence_chunks:
                    self._request_transcription()
                    self.speech_buffer = []
                    silence_counter = 0

    def _request_transcription(self):
        """Combines buffer and runs Whisper transcription."""
        if not self.speech_buffer or len(self.speech_buffer) < self.min_speech_trigger:
            return
            
        try:
            full_audio = np.concatenate(self.speech_buffer)
            # Use the specialized chunk method for speed, pass language
            # Faster-Whisper's model.transcribe handles language
            segments, info = self.stt.transcribe(
                full_audio,
                beam_size=1,
                vad_filter=False,  # Already filtered by our VAD
                language=self.language,
                word_timestamps=False
            )
            
            text = "".join([s.text for s in segments]).strip()
            
            if text and len(text.strip()) > 1:
                self.logger.info(f"Transcription ({self.language}): {text}")
                self.bridge.update_caption_signal.emit(text)
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")

    def run(self):
        """Initializes GUI, Audio and starts processing thread."""
        app = QApplication(sys.argv)
        
        # Create and show the overlay with initial theme
        overlay = TransparentOverlay(theme_idx=self.theme_idx)
        overlay.show()
        
        # Connect signals
        self.bridge.update_caption_signal.connect(overlay.update_caption)
        overlay.debug_toggle_signal.connect(self._toggle_debug_logs)
        overlay.exit_requested_signal.connect(app.quit)
        
        self.is_running = True
        
        # Start Threads
        self.recorder.start_recording()
        
        worker_thread = threading.Thread(target=self.processing_loop, daemon=True)
        worker_thread.start()
        
        self.logger.info(f"Application running. Target Language: {self.language}")
        self.logger.info("Press Ctrl+C in this terminal or use 'EXIT PLAYER' in the GUI to close.")
        
        try:
            sys.exit(app.exec())
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received.")
        finally:
            self.logger.info("Exiting application...")
            self.is_running = False
            self.recorder.stop_recording()

    def _toggle_debug_logs(self, enabled):
        """Toggles logging levels across all components."""
        level = logging.DEBUG if enabled else logging.INFO
        
        # Update app-level logger
        logging.getLogger("vaultwares").setLevel(level)
        
        # Explicitly update sub-loggers
        self.vad.logger.setLevel(level)
        self.stt.logger.setLevel(level)
        self.recorder.logger.setLevel(level)
        
        self.logger.info(f"Global Debug Logging: {'ENABLED' if enabled else 'DISABLED'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VaultWares Real-Time STT")
    parser.add_argument("--model", type=str, default="large-v3", help="Faster-Whisper model size")
    parser.add_argument("--device", type=str, default="cuda", help="Execution device (cuda/cpu)")
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

