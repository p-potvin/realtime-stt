import sounddevice as sd
import numpy as np

def list_audio_devices():
    """Lists all available audio input devices (WASAPI loopback included)."""
    devices = sd.query_devices()
    input_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append((i, device['name']))
            
    return input_devices

class AudioRecorder:
    def __init__(self, device_index=None, samplerate=16000, channels=1):
        self.device_index = device_index
        self.samplerate = samplerate
        self.channels = channels
        self.stream = None
        self.audio_buffer = []

    def start_recording(self, callback):
        """Starts the audio stream and triggers the callback for each block."""
        self.stream = sd.InputStream(
            device=self.device_index, 
            samplerate=self.samplerate, 
            channels=self.channels, 
            callback=callback
        )
        self.stream.start()
        print("Audio recording started.")

    def stop_recording(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            print("Audio recording stopped.")

# Example callback (to be integrated with the processing thread)
# def audio_callback(indata, frames, time, status):
#     if status:
#         print(status, flush=True)
#     # indata is the recorded block as a numpy array
#     indata_copy = indata.copy()
#     # add to processing queue...
