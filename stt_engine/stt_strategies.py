from stt_engine.faster_whisper_wrapper import FasterWhisperWrapper
from stt_engine.parakeet_wrapper import ParakeetV3Wrapper

class STTStrategy:
    def transcribe(self, audio, language, logger):
        raise NotImplementedError

class WhisperStrategy(STTStrategy):
    def __init__(self, device):
        self.engine = FasterWhisperWrapper(
            model_size="distil-small.en",
            device=device,
            compute_type="float16" if device == "cuda" else "int8"
        )
        self.engine.get_model()
        
    def transcribe(self, audio, language, logger):
        logger.debug("Calling FasterWhisper transcribe with VAD-filtered block.")
        segments, info = self.engine.transcribe(
            audio, beam_size=1, vad_filter=False, language=language,
            word_timestamps=False, condition_on_previous_text=False, initial_prompt=""
        )
        return "".join([s.text for s in segments]).strip()

class ParakeetStrategy(STTStrategy):
    def __init__(self):
        self.engine = ParakeetV3Wrapper(model_name="nvidia/parakeet-tdt-0.6b-v3")
        
    def transcribe(self, audio, language, logger):
        return self.engine.transcribe(audio)
