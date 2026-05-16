import os
import torch
import numpy as np
import logging

# Check for CUDA availability
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class FastConformerWrapper:
    """
    Worker for running nvidia/stt_en_fastconformer_ctc_large.
    """
    def __init__(self, model_name: str = "nvidia/stt_en_fastconformer_ctc_large"):
        import nemo.collections.asr as nemo_asr  # type: ignore
        self.logger = logging.getLogger("vaultwares.astconformer_wrapper")
        self.logger.info(f"Initializing FastConformer with model: {model_name} on {DEVICE}")
        
        try:
            # Use ASRModel which detects appropriate subclass based on checkpoint
            self.model = nemo_asr.models.ASRModel.from_pretrained(model_name=model_name)
            self.model = self.model.to(DEVICE)
            self.model.eval()
            self.logger.info("FastConformer model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load FastConformer model: {e}")
            raise

    def transcribe(self, audio_data: np.ndarray, source_lang: str = "en", target_lang: str = "en") -> str:
        """
        Transcribes a NumPy audio buffer (16kHz float32) directly through VRAM.
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
            self.logger.error(f"FastConformer transcription error: {e}")
            return f"[Error: {e}]"
