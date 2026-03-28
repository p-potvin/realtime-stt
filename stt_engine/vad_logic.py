import torch
import numpy as np
import logging

class SileroVADWrapper:
    """
    A lightweight and reusable wrapper for Silero VAD, providing efficient 
    speech activity detection for real-time applications.
    
    Optimized to minimize CPU usage while filtering non-speech background noise.
    """
    def __init__(self, model_name="silero_vad", samplerate=16000, device="cpu", logger_name="vaultwares.vad", bypass=False):
        self.model_name = model_name
        self.samplerate = samplerate
        self.device = torch.device(device)
        self.logger = logging.getLogger(logger_name)
        self.model = None
        self.utils = None
        self.bypass = bypass
        if not self.bypass:
            self._initialize_model()

    def _initialize_model(self):
        """Loads the Silero VAD model via torch.hub. Tries CPU, falls back to CUDA."""
        try:
            self.logger.info(f"Attempting to initialize Silero VAD (initial target: {self.device})...")

            torch.set_num_threads(1)  # Limit to 1 thread for VAD to reduce CPU contention
            # Cache handled locally in ~/.cache/torch/hub/
            self.model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad', 
                model=self.model_name, 
                force_reload=False,
                trust_repo=True
            )

            
            # Attempt move to device (CPU by default)
            try:
                self.model.to(self.device)
                self.logger.info(f"Silero VAD successfully moved to {self.device}.")
            except (RuntimeError, Exception) as e:
                if self.device.type == "cuda":
                    self.logger.warning(f"VAD CUDA move failed (OOM/Error): {e}. Falling back to CPU...")
                    self.device = torch.device("cpu")
                    self.model.to(self.device)
                else:
                    raise

            self.logger.info(f"Silero VAD initialized on {self.device}.")
        except Exception as e:
            self.logger.error(f"Failed to initialize Silero VAD: {e}")
            raise RuntimeError(f"Could not load VAD model: {e}")

    def get_speech_prob(self, audio_chunk):
        """
        Returns the probability of speech in the given audio chunk.
        
        Args:
            audio_chunk (np.ndarray): 1D float32 numpy array.
            
        Returns:
            float: Probability (0.0 to 1.0).
        """
        try:
            # Ensure audio is properly normalized float32
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
                
            # Convert numpy chunk to tensor
            audio_tensor = torch.from_numpy(audio_chunk).to(self.device)
            
            # Forward pass through the model
            with torch.no_grad():
                speech_prob = self.model(audio_tensor, self.samplerate).item()                
            
            self.logger.debug(f"Speech probability: {speech_prob:.4f}")
            return speech_prob
        except Exception as e:
            self.logger.warning(f"Error calculating speech probability: {e}")
            return 0.0

    def is_speech(self, audio_chunk, threshold=0.4):
        """
        Simple boolean check for speech activity.
        
        Args:
            audio_chunk (np.ndarray): 1D float32 numpy array.
            threshold (float): Detection threshold (default 0.4).
            
        Returns:
            bool: True if probability >= threshold.
        """
        prob = self.get_speech_prob(audio_chunk)
        return prob >= threshold

if __name__ == "__main__":
    # Test with dummy silent audio
    logging.basicConfig(level=logging.INFO)
    vad = SileroVADWrapper()
    silent_audio = np.zeros(16000, dtype=np.float32)
    print(f"Silent speech probability: {vad.get_speech_prob(silent_audio)}")
    print(f"Is silent speech detected? {vad.is_speech(silent_audio)}")

