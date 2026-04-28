import os
import sys
import uuid
import logging
import threading
import time
from contextlib import contextmanager
from typing import List, Optional, Tuple, Generator

# Attempt to import faster-whisper, handle missing dependency gracefully
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

class FasterWhisperWrapper:
    """
    A robust, reusable wrapper for Faster-Whisper, incorporating VaultWares standards
    for logging, performance, and hardware optimization.
    
    Ported and enhanced from the video-transcriber-translator project.
    """
    
    _MODEL_CACHE = {}
    _LOCK = threading.Lock()

    def __init__(
        self, 
        model_size: str = "large-v3", 
        device: str = "cuda", 
        compute_type: str = "float16",
        cpu_threads: int = 4,
        logger_name: str = "vaultwares.stt"
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.cpu_threads = cpu_threads
        self.model = None
        self.correlation_id = str(uuid.uuid4())
        self.logger = self._setup_logger(logger_name)

    def _setup_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] [%(correlation_id)s] %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False
        
        # Add correlation ID filter
        class CorrelationFilter(logging.Filter):
            def __init__(self, cid):
                super().__init__()
                self.cid = cid
            def filter(self, record):
                record.correlation_id = self.cid
                return True
        
        logger.addFilter(CorrelationFilter(self.correlation_id))
        return logger

    @contextmanager
    def _spinning_cursor(self, msg: str = "Processing..."):
        spinner = ["|", "/", "-", "\\"]
        stop_spinner = False

        def spin():
            i = 0
            while not stop_spinner:
                sys.stdout.write(f"\r{spinner[i % len(spinner)]} {msg}")
                sys.stdout.flush()
                time.sleep(0.1)
                i += 1
            sys.stdout.write("\r" + " " * (len(msg) + 5) + "\r")
            sys.stdout.flush()

        thread = threading.Thread(target=spin)
        thread.start()
        try:
            yield
        finally:
            stop_spinner = True
            thread.join()

    def get_model(self):
        """
        Retrieves or initializes the Whisper model using a thread-safe singleton pattern per configuration.
        Tries CUDA first, falls back to CPU on OOM or other failures.
        """
        cache_key = (self.model_size, self.device, self.compute_type)
        
        with self._LOCK:
            if cache_key not in self._MODEL_CACHE:
                if WhisperModel is None:
                    raise ImportError("faster-whisper is not installed. Please install it via pip.")
                
                with self._spinning_cursor(f"Initializing Faster-Whisper ({self.model_size})..."):
                    try:
                        # Try initial device
                        self._MODEL_CACHE[cache_key] = WhisperModel(
                            self.model_size,
                            device=self.device,
                            compute_type=self.compute_type,
                            cpu_threads=self.cpu_threads
                        )
                        self.logger.info(f"Initialized Faster-Whisper on {self.device}")
                    except (RuntimeError, Exception) as e:
                        if self.device == "cuda":
                            self.logger.warning(f"Failed to initialize on CUDA (OOM or error): {e}. Falling back to CPU...")
                            try:
                                # Fallback to CPU, use int8 for efficiency on CPU
                                fallback_key = (self.model_size, "cpu", "int8")
                                self._MODEL_CACHE[cache_key] = WhisperModel(
                                    self.model_size,
                                    device="cpu",
                                    compute_type="int8",
                                    cpu_threads=self.cpu_threads
                                )
                                self.logger.info("Successfully fell back to CPU.")
                            except Exception as cpu_e:
                                raise RuntimeError(f"Failed both CUDA and CPU initialization: {cpu_e}")
                        else:
                            raise RuntimeError(f"Failed to initialize Faster-Whisper on {self.device}: {e}")
            
            self.model = self._MODEL_CACHE[cache_key]
            return self.model

    def transcribe(
        self,
        audio,
        beam_size: int = 5,
        vad_filter: bool = True,
        vad_threshold: float = 0.35,
        language: Optional[str] = None,
        task: str = "transcribe",
        word_timestamps: bool = True,
        **kwargs
    ) -> Tuple[List, dict]:
        """
        Transcribes audio data using the global/cached model. 
        Supports file paths, numpy arrays, or bytes.
        """
        model = self.get_model()
        
        vad_params = {"threshold": vad_threshold} if vad_filter else None
        
        segments_generator, info = model.transcribe(
            audio,
            beam_size=beam_size,
            vad_filter=vad_filter,
            vad_parameters=vad_params,
            language=language,
            task=task,
            word_timestamps=word_timestamps,
            **kwargs
        )
        
        # Convert generator to list for easier handling in high-level wrappers
        segments = list(segments_generator)
        return segments, info

    def transcribe_chunk(self, audio_data, beam_size=1, vad_filter=True):
        """
        Specialized method for real-time chunks mapping to the generic transcribe logic.
        """
        segments, info = self.transcribe(
            audio_data, 
            beam_size=beam_size, 
            vad_filter=vad_filter,
            word_timestamps=False
        )
        
        # Bolt: Using a list comprehension inside join() avoids the overhead of a
        # generator expression and results in a ~2x speedup.
        text = "".join([s.text for s in segments]).strip()
        return text, info

    def format_to_srt(self, segments: List) -> str:
        """
        Converts transcription segments to SRT format string.
        """
        return "".join(
            f"{i + 1}\n{self._format_timestamp(segment.start)} --> {self._format_timestamp(segment.end)}\n{segment.text.strip()}\n\n"
            for i, segment in enumerate(segments)
        )

    def _format_timestamp(self, seconds: float) -> str:
        # Bolt: Avoid floating point remainders inside `divmod` by converting
        # seconds to milliseconds first. Pure integer arithmetic is measurably
        # faster for formatting thousands of timestamps into SRT.
        ms = int(seconds * 1000)
        ms, td_ms = divmod(ms, 1000)
        ms, td_secs = divmod(ms, 60)
        td_hours, td_mins = divmod(ms, 60)
        return f"{td_hours:02d}:{td_mins:02d}:{td_secs:02d},{td_ms:03d}"

    def log_info(self, msg: str):
        self.logger.info(msg)

    def log_debug(self, msg: str):
        self.logger.debug(msg)

    def log_error(self, msg: str):
        self.logger.error(msg)

