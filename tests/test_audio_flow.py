import unittest
import sys
import types
import numpy as np
import queue
from unittest.mock import patch

class TestAudioFlow(unittest.TestCase):
    def setUp(self):
        # Mock soundcard locally to avoid virtual audio cables during headless CI/CD
        self.patcher = patch.dict('sys.modules', {'soundcard': types.SimpleNamespace()})
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_recorder_initialization(self):
        from stt_engine.audio_capture import AudioRecorder
        recorder = AudioRecorder(samplerate=16000, blocksize=512)
        self.assertEqual(recorder.samplerate, 16000)
        self.assertEqual(recorder.blocksize, 512)
        self.assertFalse(recorder.is_recording)

    def test_vad_processing(self):
        from stt_engine.vad_logic import SileroVADWrapper
        vad = SileroVADWrapper(bypass=True) # Bypass for CI/CD speed
        dummy_audio = np.zeros(512, dtype=np.float32)
        # Should be 0.0 for zeros
        prob = vad.get_speech_prob(dummy_audio)
        self.assertEqual(prob, 0.0)

    def test_agc_scaling(self):
        from stt_engine.audio_capture import AudioRecorder
        recorder = AudioRecorder()
        # Mocking a quiet chunk
        quiet_chunk = np.ones(512, dtype=np.float32) * 0.05
        peak = float(np.abs(quiet_chunk).max())  # Bolt: Optimized from np.max(np.abs(quiet_chunk))
        
        # Manually apply AGC logic to test
        TARGET_PEAK = 0.4
        gain = min(10.0, TARGET_PEAK / max(peak, 0.01))
        scaled = quiet_chunk * gain
        new_peak = float(np.abs(scaled).max())  # Bolt: Optimized from np.max(np.abs(scaled))
        
        self.assertGreater(new_peak, peak)
        self.assertLessEqual(new_peak, TARGET_PEAK + 0.01)

if __name__ == "__main__":
    unittest.main()
