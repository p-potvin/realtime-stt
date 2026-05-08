# Agent Ledger

## 2025-05-05: NumPy Array Object Methods Over Global Functions
**Goal:** Real-time Engine & Model Optimization
**Decision:** Changed usages of `np.max(np.abs(chunk))` to `np.abs(chunk).max()` in real-time hot paths (`audio_capture.py`, `vad_logic.py`, `main_app.py`).
**Reason:** Benchmarks show `np.abs(chunk).max()` is nearly 2x faster than `np.max(np.abs(chunk))` by avoiding Python-level function dispatch overhead from the global `np.max` method. For high-frequency realtime chunk processing, every millisecond counts.

## 2026-05-08: Code Cleanup in STT Engine Orchestrator
**Goal:** Improve maintainability and reduce clutter.
**Decision:** Removed unused `import queue` and a redundant `else: pass` block with "not implemented" comments in `stt_engine/engine_orchestrator.py`.
**Reason:** Unused imports and dead code/comments reduce readability and increase noise. Following the "No Dead Code" policy from the project manifest.
