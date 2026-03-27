import sounddevice as sd
import numpy as np
import queue
import logging

class AudioRecorder:
    """
    A robust audio recorder using sounddevice with WASAPI loopback support.
    Designed for real-time capture from virtual cables (e.g., VoiceMeeter).
    """
    def __init__(self, device_index=None, samplerate=16000, channels=1, blocksize=4000):
        self.device_index = device_index
        self.samplerate = samplerate
        self.channels = channels
        self.blocksize = blocksize  # ~250ms at 16kHz
        self.stream = None
        self.audio_queue = queue.Queue()
        self.logger = logging.getLogger("vaultwares.audio")

    def list_audio_devices(self):
        """Lists all available audio input devices (WASAPI loopback included)."""
        devices = sd.query_devices()
        input_devices = []
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append((i, device['name']))
                
        return input_devices

    def _audio_callback(self, indata, frames, time, status):
        """Standard sounddevice callback, pushing data to a queue."""
        if status:
            self.logger.warning(f"Audio status: {status}")
        
        # Flatten and copy to ensure thread safety
        data = indata.copy().flatten()
        self.logger.debug(f"Captured audio chunk: {len(data)} samples")
        self.audio_queue.put(data)

    def start_recording(self):
        """Starts the audio stream using the internal callback."""
        try:
            self.stream = sd.InputStream(
                device=self.device_index, 
                samplerate=self.samplerate, 
                channels=self.channels, 
                blocksize=self.blocksize,
                callback=self._audio_callback
            )
            self.stream.start()
            self.logger.info(f"Audio recording started on device {self.device_index or 'default'}.")
        except Exception as e:
            self.logger.error(f"Failed to start audio recording: {e}")
            raise

    def stop_recording(self):
        """Gracefully stops the audio stream."""
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
                self.logger.info("Audio recording stopped.")
            except Exception as e:
                self.logger.error(f"Error stopping audio recording: {e}")

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
            time.sleep(0.5)
    finally:
        recorder.stop_recording()

