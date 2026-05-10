import os
import torch
import numpy as np
import logging
import soundfile as sf
import tempfile

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
                # Direct Tensor Inference: Bypass File System completely
                audio_tensor = torch.from_numpy(audio_data).unsqueeze(0).to(DEVICE)
                audio_len = torch.tensor([audio_tensor.shape[1]], dtype=torch.long).to(DEVICE)

                # Send directly to the encoder/forward block
                forward_out = self.model.forward(input_signal=audio_tensor, input_signal_length=audio_len)
                
                # Model returns (log_probs, encoded_len, greedy_predictions)
                greedy_predictions = forward_out[2]
                encoded_len = forward_out[1]

                # Decode into raw text using NeMo's native decoder
                hypotheses, _ = self.model.decoding.ctc_decoder_predictions_tensor(
                    greedy_predictions, predictions_len=encoded_len
                )
                
                # Check hypotheses packing variation
                if hasattr(hypotheses[0], 'text'):
                    return hypotheses[0].text
                elif isinstance(hypotheses[0], list):
                    return hypotheses[0][0]
                else:
                    return str(hypotheses[0])
                
        except Exception as e:
            self.logger.error(f"FastConformer transcription error: {e}")
            return f"[Error: {e}]"
