import os
import torch
import numpy as np
import logging
import subprocess
from typing import Optional
from contextlib import contextmanager


@contextmanager
def hush_subprocess():
    """
    Context manager to locally patch subprocess.Popen to suppress console
    windows on Windows only for the duration of the wrapped block.
    """
    if os.name == 'nt':
        original_popen = subprocess.Popen
        class HushPopen(original_popen):
            def __init__(self, *args, **kwargs):
                if 'creationflags' not in kwargs:
                    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW | getattr(subprocess, 'DETACHED_PROCESS', 0x00000008)
                super().__init__(*args, **kwargs)
        subprocess.Popen = HushPopen
        try:
            yield
        finally:
            subprocess.Popen = original_popen
    else:
        yield


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
            with hush_subprocess():
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
                # Direct Tensor Inference: Bypass File System completely
                audio_tensor = torch.from_numpy(audio_data).unsqueeze(0).to(DEVICE)
                audio_len = torch.tensor([audio_tensor.shape[1]], dtype=torch.long).to(DEVICE)

                # Send directly to the encoder/forward block
                forward_out = self.model.forward(input_signal=audio_tensor, input_signal_length=audio_len)

                # Differentiate between CTC and RNNT architectures
                if hasattr(self.model, 'decoding'):
                    if hasattr(self.model.decoding, 'ctc_decoder_predictions_tensor'):
                        # CTC Decode
                        greedy_predictions = forward_out[2]
                        encoded_len = forward_out[1]
                        hypotheses, _ = self.model.decoding.ctc_decoder_predictions_tensor(
                            greedy_predictions, predictions_len=encoded_len
                        )
                        curr_hyp = hypotheses[0][0] if isinstance(hypotheses[0], list) else hypotheses[0]
                        return curr_hyp.text if hasattr(curr_hyp, 'text') else str(curr_hyp)
                        
                    elif hasattr(self.model.decoding, 'rnnt_decoder_predictions_tensor'):
                        # RNNT Decode
                        encoder_output = forward_out[0]
                        encoded_len = forward_out[1]
                        hypotheses, _ = self.model.decoding.rnnt_decoder_predictions_tensor(
                            encoder_output, encoded_len
                        )
                        return hypotheses[0].text if hasattr(hypotheses[0], 'text') else str(hypotheses[0])

                return ""
                
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
