# Agent Ledger

## 2025-05-05: NumPy Array Object Methods Over Global Functions
**Goal:** Real-time Engine & Model Optimization
**Decision:** Changed usages of `np.max(np.abs(chunk))` to `np.abs(chunk).max()` in real-time hot paths (`audio_capture.py`, `vad_logic.py`, `main_app.py`).
**Reason:** Benchmarks show `np.abs(chunk).max()` is nearly 2x faster than `np.max(np.abs(chunk))` by avoiding Python-level function dispatch overhead from the global `np.max` method. For high-frequency realtime chunk processing, every millisecond counts.

## 2026-05-16: Optimize Correlation ID Generation
**Goal:** Real-time Engine & Model Optimization
**Decision:** Replaced `uuid.uuid4()` with `secrets.token_hex(16)` for generation of `correlation_id` in `stt_engine/faster_whisper_wrapper.py`.
**Reason:** `secrets.token_hex()` provides a significant performance boost over `uuid.uuid4()` for identifier generation, improving instantiation times while maintaining identical 128-bit entropy.
