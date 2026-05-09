import unittest
from unittest.mock import MagicMock, patch
from stt_engine.faster_whisper_wrapper import FasterWhisperWrapper

class TestFasterWhisperWrapper(unittest.TestCase):
    def setUp(self):
        # We don't want to actually load a model for these tests
        with patch('stt_engine.faster_whisper_wrapper.WhisperModel', return_value=MagicMock()):
            self.wrapper = FasterWhisperWrapper()

    def test_format_timestamp_zero(self):
        self.assertEqual(self.wrapper._format_timestamp(0.0), "00:00:00,000")

    def test_format_timestamp_subseconds(self):
        self.assertEqual(self.wrapper._format_timestamp(0.123), "00:00:00,123")

    def test_format_timestamp_seconds(self):
        self.assertEqual(self.wrapper._format_timestamp(45.678), "00:00:45,678")

    def test_format_timestamp_minutes(self):
        # 125.456 seconds = 2 minutes, 5 seconds, 456 ms
        self.assertEqual(self.wrapper._format_timestamp(125.456), "00:02:05,456")

    def test_format_timestamp_hours(self):
        # 3661.001 seconds = 1 hour, 1 minute, 1 second, 1 ms
        self.assertEqual(self.wrapper._format_timestamp(3661.001), "01:01:01,001")

    def test_format_timestamp_truncation(self):
        # The current implementation uses int(seconds * 1000) which truncates
        self.assertEqual(self.wrapper._format_timestamp(1.2349), "00:00:01,234")

    def test_format_timestamp_large_values(self):
        # 360000.0 seconds = 100 hours
        self.assertEqual(self.wrapper._format_timestamp(360000.0), "100:00:00,000")

if __name__ == "__main__":
    unittest.main()
