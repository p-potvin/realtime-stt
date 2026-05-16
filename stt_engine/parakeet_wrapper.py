import os
import torch
import numpy as np
import logging
import subprocess
from typing import Optional

# Monkey-patch subprocess.Popen to NEVER open a console window on Windows
if os.name == 'nt':
    _original_popen = subprocess.Popen
    class _HushPopen(_original_popen):
        def __init__(self, *args, **kwargs):
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW | getattr(subprocess, 'DETACHED_PROCESS', 0x00000008)
            super().__init__(*args, **kwargs)
    subprocess.Popen = _HushPopen

# Check for CUDA availability
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class ParakeetWorker:
    """
    Dedicated worker for running NVIDIA Parakeet V3 / Canary V2 models.
    """
    def __init__(self, model_name: str = "nvidia/parakeet-tdt-0.6b-v3"):
        import nemo.collections.asr as nemo_asr  # type: ignore
        self.logger = logging.getLogger("vaultwares.parakeet_worker")
        self.logger.info(f"Initializing ParakeetWorker with model: {model_name} on {DEVICE}")
        
        # Load the model directly through general ASR wrapper
        try:
            self.model = nemo_asr.models.ASRModel.from_pretrained(model_name=model_name)
            self.model = self.model.to(DEVICE)
            self.model.eval()
            self.logger.info("Parakeet/Canary model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load Parakeet model: {e}")
            raise

    def transcribe(self, audio_data: np.ndarray, source_lang: str = "en", target_lang: str = "en") -> str:
        """
        Transcribes a NumPy audio buffer (16kHz float32).
        """
        if audio_data is None or len(audio_data) == 0:
            return ""

        try:
            with torch.no_grad():
                # Bolt: NeMo natively accepts NumPy arrays. Manually creating tensors
                # and sending to DEVICE blocks the hot path and causes unused memory overhead.
                # Use transcribe directly. audio should be wrapped in a list.
                transcriptions = self.model.transcribe(audio=[audio_data])

                if transcriptions and isinstance(transcriptions, list):
                    return str(transcriptions[0])
                elif isinstance(transcriptions, tuple) and len(transcriptions) > 0 and isinstance(transcriptions[0], list):
                    return str(transcriptions[0][0])
                return str(transcriptions)

        except Exception as e:
            self.logger.error(f"Parakeet transcription error: {e}")
            return f"[Error: {e}]"

class ParakeetV3Wrapper:
    """
    Main interface for the application to interact with Parakeet natively (no Ray).
    """
    def __init__(self, model_name: str = "nvidia/parakeet-tdt-0.6b-v3"):
        # Load worker directly into current thread
        self.worker = ParakeetWorker(model_name=model_name)
        self.logger = logging.getLogger("vaultwares.parakeet_wrapper")

    def transcribe(self, audio_data: np.ndarray, source_lang: str = "en", target_lang: str = "en") -> str:
        """
        Synchronous dispatch transcription to the worker.
        """
        return self.worker.transcribe(audio_data, source_lang, target_lang)

    def shutdown(self):
        pass
