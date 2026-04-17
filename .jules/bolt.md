
- **Redundant Numpy Array Operations**: Be cautious of recalculating `np.max(np.abs(array))` if the array is not modified. Store the result in a variable to avoid O(N) re-computation overhead. This yielded a ~50% performance improvement (from 0.127s to 0.066s over 10000 iterations) in `stt_engine/audio_capture.py` when running audio processing tasks.
