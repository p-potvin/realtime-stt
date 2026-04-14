import logging
import sys
import types
import unittest
import numpy as np

# Stub optional audio dependency before importing engine module.
sys.modules.setdefault("soundcard", types.SimpleNamespace())

from stt_engine.engine_orchestrator import RealtimeSTTEngine


class _DummyRecorder:
    def __init__(self):
        self.started = False
        self.stopped = False

    def start_recording(self):
        self.started = True

    def stop_recording(self):
        self.stopped = True

    def get_chunk(self, timeout=0.1):
        return None


class RealtimeEngineFlushTests(unittest.TestCase):
    def test_process_loop_flushes_buffered_audio_on_shutdown(self):
        engine = RealtimeSTTEngine.__new__(RealtimeSTTEngine)
        engine.logger = logging.getLogger("test.engine")
        engine.running = False
        engine.audio_buffer = [np.ones(3200, dtype=np.float32)]
        engine.speech_detected = True
        engine.vad_threshold = 0.5
        engine.min_samples = 10
        engine.max_samples = 100000
        engine.callback = None
        engine.recorder = _DummyRecorder()

        called = {"count": 0}

        def _fake_trigger():
            called["count"] += 1
            engine.audio_buffer = []

        engine._trigger_transcription = _fake_trigger

        engine._process_loop()

        self.assertTrue(engine.recorder.started)
        self.assertTrue(engine.recorder.stopped)
        self.assertEqual(called["count"], 1)


if __name__ == "__main__":
    unittest.main()
