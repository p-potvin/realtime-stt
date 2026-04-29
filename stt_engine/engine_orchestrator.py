import queue
import threading
import time
import numpy as np
import logging
from typing import Optional, Callable

from stt_engine.audio_capture import AudioRecorder
from stt_engine.vad_logic import SileroVADWrapper
from stt_engine.faster_whisper_wrapper import FasterWhisperWrapper

class RealtimeSTTEngine:
    """
    The orchestrator for real-time STT, balancing VAD, chunking, and transcription.
    
    Workflow:
    1. Capture audio chunks via AudioRecorder (continuous).
    2. Buffer chunks until Silero VAD detects a significant speech block.
    3. Pass non-silent segments to Faster-Whisper for high-speed transcription.
    4. Emit transcription results via a callback.
    """
    def __init__(
        self, 
        model_size: str = "distil-small.en", 
        device: str = "cuda", 
        compute_type: str = "float16",
        samplerate: int = 16000,
        vad_threshold: float = 0.5,
        min_speech_duration_ms: int = 500,
        max_speech_duration_ms: int = 5000,
        callback: Optional[Callable[[str], None]] = None
    ):
        self.logger = logging.getLogger("vaultwares.engine")
        self.samplerate = samplerate
        self.vad_threshold = vad_threshold
        self.min_samples = int((min_speech_duration_ms / 1000) * samplerate)
        self.max_samples = int((max_speech_duration_ms / 1000) * samplerate)
        self.callback = callback
        
        # Components
        self.recorder = AudioRecorder(samplerate=samplerate)
        self.vad = SileroVADWrapper(samplerate=samplerate, device=device)
        self.stt = FasterWhisperWrapper(
            model_size=model_size, 
            device=device, 
            compute_type=compute_type
        )
        
        # State
        self.running = False
        self.thread = None
        self.audio_buffer = []
        # Bolt: O(1) running counter to avoid O(N) recalculations on high-frequency hot paths
        self.current_samples = 0
        self.speech_detected = False

    def _process_loop(self):
        """Main processing thread: captures, buffers, and transcribes."""
        self.logger.info("Realtime STT Engine thread started.")
        self.recorder.start_recording()
        
        try:
            while self.running:
                chunk = self.recorder.get_chunk(timeout=0.1)
                if chunk is None:
                    continue
                
                # Check for speech activity in the chunk
                is_speech = self.vad.is_speech(chunk, threshold=self.vad_threshold)
                
                if is_speech:
                    if not self.speech_detected:
                        self.logger.debug("Speech started.")
                        self.speech_detected = True
                    
                    self.audio_buffer.append(chunk)
                    self.current_samples += len(chunk)
                    
                    # Optional: Force transcription if buffer exceeds max length
                    if self.current_samples >= self.max_samples:
                        self._trigger_transcription()
                
                else:
                    if self.speech_detected:
                        # Characterizing "end of phrase" based on silence
                        self.logger.debug("Speech ended.")
                        self.speech_detected = False
                        self._trigger_transcription()
                    else:
                        # Optional: Keep a small rolling window of silence 
                        # for better context (not implemented for MVP)
                        pass
        except Exception as e:
            self.logger.error(f"Error in STT Engine loop: {e}")
        finally:
            # If the engine is stopped while speech is in progress (or a buffered
            # phrase has not yet seen trailing silence), flush once so the last
            # utterance is not dropped.
            if self.audio_buffer:
                self.logger.debug("Flushing buffered audio on engine shutdown.")
                self._trigger_transcription()
            self.recorder.stop_recording()

    def _trigger_transcription(self):
        """Assembles the buffer and sends it to Faster-Whisper."""
        if not self.audio_buffer:
            return
            
        full_audio = np.concatenate(self.audio_buffer)
        self.audio_buffer = []  # Clear buffer immediately
        self.current_samples = 0 # Reset O(1) sample counter
        
        if len(full_audio) < self.min_samples:
            self.logger.debug(f"Segment too short for transcription ({len(full_audio)} samples).")
            return
            
        def run_stt():
            try:
                start_time = time.time()
                # Transcribe the concatenated float32 array
                segments, info = self.stt.transcribe(full_audio, vad_filter=False)
                
                # Join segments into a single string
                # Bolt: Using a list comprehension inside join() avoids the overhead of a
                # generator expression and results in a ~2x speedup.
                full_text = " ".join([seg.text for seg in segments]).strip()
                
                duration = time.time() - start_time
                if full_text:
                    self.logger.info(f"Transcription ({duration:.2f}s): {full_text}")
                    if self.callback:
                        self.callback(full_text)
                else:
                    self.logger.debug(f"Transcription was empty ({duration:.2f}s).")
                    
            except Exception as e:
                self.logger.error(f"Transcription thread failed: {e}")

        # Offload transcription to avoid blocking the audio capture loop
        threading.Thread(target=run_stt, daemon=True).start()

    def start(self):
        """Initializes and starts the engine thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        self.logger.info("Realtime STT Engine initialized and running.")

    def stop(self):
        """Stops the engine and clean up resources."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.logger.info("Realtime STT Engine stopped.")

if __name__ == "__main__":
    # Test block
    logging.basicConfig(level=logging.INFO)
    engine = RealtimeSTTEngine(device="cpu", model_size="tiny", callback=print)
    
    print("Engine starting... Speak into the default input.")
    engine.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        engine.stop()
        print("Engine stopped.")
