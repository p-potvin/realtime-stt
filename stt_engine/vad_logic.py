import os
import torch
import numpy as np

class SileroVADWrapper:
    """
    A lightweight wrapper for Silero VAD, providing efficient speech activity detection.
    Helps isolate speech and ignore background noise before transcription.
    """
    def __init__(self, model_name="silero_vad", samplerate=16000, device="cpu"):
        self.model_name = model_name
        self.samplerate = samplerate
        self.device = torch.device(device)
        self.model = None
        self.utils = None
        self._initialize_model()

    def _initialize_model(self):
        print(f"Initializing Silero VAD on {self.device}...")
        self.model, self.utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad', 
            model=self.model_name, 
            force_reload=False
        )
        self.model.to(self.device)
        print("VAD model initialized successfully.")

    def is_speech(self, audio_chunk, threshold=0.5):
        """
        Returns True if speech is detected in the audio chunk based on the probability threshold.
        audio_chunk is expected to be a numpy array of floats (1D).
        """
        # Convert numpy buffer to tensor
        audio_tensor = torch.from_numpy(audio_chunk).to(self.device)
        
        # Forward pass through the model
        with torch.no_grad():
            speech_prob = self.model(audio_tensor, self.samplerate).item()
            
        return speech_prob >= threshold

    def filter_speech_segments(self, audio_data, threshold=0.5):
        """
        Processes a full audio buffer and returns only the parts containing speech.
        Useful for batch or chunk processing if needed.
        """
        # Implementation details depend on the specific streaming requirements.
        # This could return timestamps or a concatenated speech buffer.
        pass
