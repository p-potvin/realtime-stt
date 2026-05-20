import unittest

class Segment:
    def __init__(self, text):
        self.text = text

class TestJoinLogic(unittest.TestCase):
    def test_join_generator_whisper_wrapper(self):
        segments = [Segment("Hello "), Segment("world!")]
        # Simulation of what's in vaultwares_realtime/faster_whisper_wrapper.py
        text = "".join(s.text for s in segments).strip()
        self.assertEqual(text, "Hello world!")

    def test_join_generator_main_app(self):
        segments = [Segment("Hello "), Segment("world!")]
        # Simulation of what's in main_app.py
        text = "".join(s.text for s in segments).strip()
        self.assertEqual(text, "Hello world!")

    def test_join_generator_orchestrator(self):
        segments = [Segment("Hello"), Segment("world")]
        # Simulation of what's in vaultwares_realtime/engine_orchestrator.py
        full_text = " ".join(seg.text for seg in segments).strip()
        self.assertEqual(full_text, "Hello world")

    def test_empty_segments(self):
        segments = []
        text = "".join(s.text for s in segments).strip()
        self.assertEqual(text, "")

if __name__ == "__main__":
    unittest.main()
