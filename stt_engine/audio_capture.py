import soundcard as sc
import numpy as np
import threading
import queue
import logging

class AudioRecorder:
    """
    A robust audio recorder using soundcard (WASAPI).
    Captures system audio output using loopback without requiring virtual cables.
    """
    def __init__(self, device_name=None, samplerate=16000, channels=1, blocksize=512):
        self.device_name = device_name
        self.samplerate = samplerate
        self.channels = channels
        self.blocksize = blocksize  # ~32ms at 16kHz
        self.audio_queue = queue.Queue()
        self.logger = logging.getLogger("vaultwares.audio")
        self.is_recording = False
        self._thread = None

    def list_audio_devices(self):
        """Lists all available loopback and input devices."""
        devices = sc.all_microphones(include_loopback=True)
        return [(i, dev.name) for i, dev in enumerate(devices)]

    def _record_loop(self):
        # We need default speaker if not provided
        target_id = self.device_name
        if target_id is None:
            try:
                target_id = sc.default_speaker().name
                self.logger.info(f"Targeting default speaker: {target_id}")
            except Exception as e:
                self.logger.error(f"Could not get default speaker: {e}")
                self.is_recording = False
                return

        try:
            mic = sc.get_microphone(id=target_id, include_loopback=True)
        except Exception as e:
            self.logger.error(f"Could not attach to microphone/loopback: {e}")
            self.is_recording = False
            return

        try:
            with mic.recorder(samplerate=self.samplerate, channels=self.channels) as recorder:
                self.logger.info(f"Audio recording started on loopback device: {mic.name}")
                while self.is_recording:
                    data = recorder.record(numframes=self.blocksize)
                    # Convert to flattened mono, ensure float32
                    mono_data = data.mean(axis=1).astype(np.float32)
                    
                    # Log peak volume every 100 chunks (~3 seconds) to verify audio flow
                    if not hasattr(self, '_log_counter'): self._log_counter = 0
                    self._log_counter += 1
                    
                    # Software Gain: If the signal is consistently quiet (due to Windows background throttling)
                    # we apply a slight boost here to ensure the VAD and STT get a healthy signal.
                    peak = np.max(np.abs(mono_data))
                    if 0 < peak < 0.2:
                        # Apply a 2x boost (approx 6dB) to compensate for potential OS attenuation
                        # This is a safe baseline boost for loopback.
                        mono_data = mono_data * 2.5
                        # Re-calculate peak for debugging
                        peak = np.max(np.abs(mono_data))

                    if self._log_counter % 100 == 0:
                        self.logger.debug(f"Audio Flow Check - Chunk: {self._log_counter} | Peak Volume: {peak:.5f}")

                    self.audio_queue.put(mono_data)
        except Exception as e:
            self.logger.error(f"Exception during recording: {e}")
            self.is_recording = False

    def start_recording(self):
        """Starts the audio stream using soundcard loopback."""
        if self.is_recording:
            return
        self.is_recording = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def stop_recording(self):
        """Gracefully stops the audio stream."""
        self.is_recording = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.logger.info("Audio recording stopped.")

    def get_chunk(self, timeout=None):
        """Retrieves a chunk from the audio queue."""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    recorder = AudioRecorder()
    print("Available devices:")
    for idx, name in recorder.list_audio_devices():
        print(f"{idx}: {name}")
    
    recorder.start_recording()
    try:
        import time
        for _ in range(10):
            chunk = recorder.get_chunk(timeout=1.0)
            if chunk is not None:
                print(f"Captured chunk: {len(chunk)} samples")
            time.sleep(0.3)
    finally:
        recorder.stop_recording()

