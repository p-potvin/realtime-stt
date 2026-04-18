import time
import sys
import unittest.mock as mock

sys.modules['faster_whisper'] = mock.MagicMock()

from stt_engine.faster_whisper_wrapper import FasterWhisperWrapper

class DummySegment:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text

def generate_dummy_segments(num_segments):
    return [
        DummySegment(start=float(i), end=float(i + 1), text=f"This is dummy segment number {i}.")
        for i in range(num_segments)
    ]

def run_benchmark():
    wrapper = FasterWhisperWrapper()
    num_segments = 500000
    segments = generate_dummy_segments(num_segments)

    print(f"Benchmarking with {num_segments} segments...")
    start_time = time.time()
    result = wrapper.format_to_srt(segments)
    end_time = time.time()

    elapsed = end_time - start_time
    print(f"Elapsed time: {elapsed:.4f} seconds")
    return elapsed

if __name__ == "__main__":
    run_benchmark()
