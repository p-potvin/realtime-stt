# Performance Learnings

- **String Concatenation in Faster-Whisper Wrapper**: Replacing `+=` string concatenation with `"".join(...)` and generator expressions in `FasterWhisperWrapper.format_to_srt` prevents O(N^2) memory reallocation. Even though CPython has internal optimizations that make `+=` perform relatively well for single-reference strings, explicit `.join()` guarantees O(N) allocation scaling and avoids unpredictable performance drop-offs at larger list sizes, improving overall scalability and conforming to best practices in the transcription code path.
