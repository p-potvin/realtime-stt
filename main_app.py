import sys
import threading
import queue
import numpy as np
import time
from PySide6.QtWidgets import QApplication
from stt_engine.audio_capture import AudioRecorder
from stt_engine.vad_logic import SileroVADWrapper
from stt_engine.faster_whisper_wrapper import FasterWhisperWrapper
from gui_overlay.overlay_window import TransparentOverlay

class RealTimeSTTApp:
    def __init__(self, model_size="base", device="cuda"):
        self.audio_queue = queue.Queue()
        self.is_running = False
        
        # Initialize Core Components
        self.vad = SileroVADWrapper()
        self.stt = FasterWhisperWrapper(model_size=model_size, device=device)
        self.recorder = AudioRecorder(samplerate=16000)
        
        # Buffer for speech data
        self.speech_buffer = []

    def audio_callback(self, indata, frames, time, status):
        """Standard sounddevice callback."""
        if status:
            print(f"Audio Status: {status}")
        self.audio_queue.put(indata.copy().flatten())

    def processing_thread_func(self, gui_signal):
        """
        The main processing loop:
        1. Listens for audio chunks.
        2. Filters via VAD.
        3. Transcribes via Faster-Whisper.
        4. Updates GUI signal.
        """
        while self.is_running:
            try:
                # 0.5s chunks for responsive VAD/STT
                chunk = self.audio_queue.get(timeout=1.0)
                
                if self.vad.is_speech(chunk, threshold=0.4):
                    self.speech_buffer.append(chunk)
                    
                    # If we have enough speech (e.g., 2-3 seconds)
                    if len(self.speech_buffer) >= 6:  # 6 * 0.5s = 3s approx (depends on buffer size)
                        full_audio = np.concatenate(self.speech_buffer)
                        text, info = self.stt.transcribe_chunk(full_audio)
                        
                        if text:
                            print(f"Transcribed: {text}")
                            gui_signal(text)
                        
                        # Clear buffer or slide window (simple clear for now)
                        # To keep context, we'd overlap buffers
                        self.speech_buffer = self.speech_buffer[-2:] 
                else:
                    # If silence detected after speech, flush the remaining buffer
                    if self.speech_buffer:
                        full_audio = np.concatenate(self.speech_buffer)
                        text, info = self.stt.transcribe_chunk(full_audio)
                        if text:
                            gui_signal(text)
                        self.speech_buffer = []

            except queue.Empty:
                continue

    def run(self):
        # Initialize GUI in main thread
        app = QApplication(sys.argv)
        overlay = TransparentOverlay()
        overlay.show()

        self.is_running = True
        
        # Start Audio Capture
        self.recorder.start_recording(self.audio_callback)
        
        # Start Processing Thread
        proc_thread = threading.Thread(
            target=self.processing_thread_func, 
            args=(overlay.update_caption,), 
            daemon=True
        )
        proc_thread.start()

        # Run UI Loop
        try:
            sys.exit(app.exec())
        finally:
            self.is_running = False
            self.recorder.stop_recording()

if __name__ == "__main__":
    # VaultWares: CorrelationId would be initialized here or in logs
    app_instance = RealTimeSTTApp(model_size="base")
    app_instance.run()
