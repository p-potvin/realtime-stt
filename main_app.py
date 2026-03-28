import sys
import threading
import numpy as np
import logging
import random
import string
import argparse
import vault_sync
import soundfile as sf
from PySide6.QtWidgets import QApplication

# Run vault synchronization at startup
vault_sync.sync_vault_dependencies()

from PySide6.QtCore import Signal, QObject
from stt_engine.audio_capture import AudioRecorder
from stt_engine.vad_logic import SileroVADWrapper
from stt_engine.faster_whisper_wrapper import FasterWhisperWrapper
from stt_engine.parakeet_wrapper import ParakeetV3Wrapper
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
    def __init__(self, model_size="medium", device="cpu", language="en", theme_idx=2):
        self.correlation_id = "c" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.logger = logging.getLogger("vaultwares.main")
        self.logger.info(f"Starting realtime-stt app (CorrelationId: {self.correlation_id})")
        
        self.language = language
        self.theme_idx = theme_idx
        self.device = device
        self.active_engine = "whisper" # Default
        self.skip_vad = False
        
        # Pre-initialize Core components
        self.vad = SileroVADWrapper(device="cpu" if device == "cpu" else "cuda")
        self.stt = FasterWhisperWrapper(
            model_size=model_size, 
            device=device,
            compute_type="float16" if device == "cuda" else "int8"
        )
        self.stt.get_model()
        
        # Parakeet V3 (NVIDIA) engine - initialized on demand or at start
        self.parakeet = ParakeetV3Wrapper(model_name="nvidia/canary-1b")
        
        # Determine the correct device index for VB-Audio Virtual Cable
        # Based on user input, we need to listen to the virtual output cable.
        device_index = None
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                # We look for "CABLE Output" which is the recording end of the virtual cable
                if "CABLE Output" in dev['name'] and dev['max_input_channels'] > 0:
                    device_index = i
                    self.logger.info(f"Automatically selected VB-Audio device: {dev['name']} (Index: {i})")
                    break
        except Exception as e:
            self.logger.warning(f"Could not auto-detect audio device: {e}")

        self.recorder = AudioRecorder(device_index=device_index, samplerate=16000, blocksize=512)
        
        self.is_running = False
        self.speech_buffer = []
        self.bridge = CommunicationBridge()
        
        # Sliding window parameters
        self.max_buffer_size = 15  # ~3 seconds of audio (90 * 32ms chunks)
        self.min_speech_trigger = 15 # ~2 second minimum to attempt transcription

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
        max_silence_chunks = 0.5 * self.max_buffer_size # ~1.0 seconds of silence to flush buffer
        
        while self.is_running:
            chunk = self.recorder.get_chunk(timeout=0)
            if chunk is None:
                continue
            
            # VAD logic
            if self.skip_vad:
                speech_prob = 1.0 # Always on
            else:
                speech_prob = self.vad.get_speech_prob(chunk)
            
            if speech_prob >= 0.4:
                self.speech_buffer.append(chunk)
                silence_counter = 0
                
                # If we've accumulated significant speech, perform partial transcription
                if len(self.speech_buffer) >= self.max_buffer_size:
                    self._request_transcription()
                    # Slide the window (keep 32 ms overlap for context)
                    self.speech_buffer = self.speech_buffer[-1:]
                    #self.vad.model.reset_states()  # Reset internal states for next chunk
            else:
                silence_counter += 1
                if silence_counter >= max_silence_chunks and self.speech_buffer:
                    # Minimum trigger check here to prevent tiny ghost audio
                    if len(self.speech_buffer) >= self.min_speech_trigger:
                        self._request_transcription()
                    self.speech_buffer = []
                    #self.vad.model.reset_states()  # Reset internal states for next chunk

    def start(self):
        """Starts the capture and processing threads."""
        self.is_running = True
        self.recorder.start_recording()       
        
        self.thread = threading.Thread(target=self.processing_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stops the app and cleans up."""
        self.is_running = False
        self.recorder.stop_recording()
        if hasattr(self, 'thread'):
            self.thread.join(timeout=0)

    def _request_transcription(self):
        """Combines buffer and runs the active STT engine."""
        if not self.speech_buffer:
            return
            
        try:
            full_audio = np.concatenate(self.speech_buffer)            

            if self.active_engine == "nvidia":
                # Ray-based Parakeet / Canary (v3 / v2)
                text = self.parakeet.transcribe(full_audio)
            else:
                # Faster-Whisper
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
                self.logger.info(f"Transcription ({self.language}) [{self.active_engine}]: {text}")
                self.bridge.update_caption_signal.emit(text)
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")

    def _toggle_debug_logs(self, state):
        """Toggles logging level (INFO/DEBUG)"""
        if state:
            logging.getLogger().setLevel(logging.DEBUG)
            self.logger.debug("Debug logs enabled.")
        else:
            logging.getLogger().setLevel(logging.INFO)
            self.logger.info("Debug logs disabled.")

    def on_settings_changed(self, settings_dict: dict):
        """Callback for GUI settings changes."""
        if "skip_vad" in settings_dict:
            self.skip_vad = settings_dict["skip_vad"]
            self.logger.info(f"VAD Bypass set to: {self.skip_vad}")
        
        if "active_engine" in settings_dict:
            self.active_engine = settings_dict["active_engine"]
            self.logger.info(f"Active engine changed to: {self.active_engine}")
    
    def run(self):
        """Initializes GUI, Audio and starts processing thread."""
        app = QApplication(sys.argv)
        
        # Create and show the overlay with initial theme
        self.overlay = TransparentOverlay(theme_idx=self.theme_idx)
        self.overlay.show()
        
        # Connect signals
        self.bridge.update_caption_signal.connect(self.overlay.update_caption)
        self.overlay.debug_toggle_signal.connect(self._toggle_debug_logs)
        self.overlay.settings_changed_signal.connect(self.on_settings_changed)
        self.overlay.exit_requested_signal.connect(app.quit)
        
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

