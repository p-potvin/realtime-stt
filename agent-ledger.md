# Agent Ledger

## 2025-05-05: NumPy Array Object Methods Over Global Functions
**Goal:** Real-time Engine & Model Optimization
**Decision:** Changed usages of `np.max(np.abs(chunk))` to `np.abs(chunk).max()` in real-time hot paths (`audio_capture.py`, `vad_logic.py`, `main_app.py`).
**Reason:** Benchmarks show `np.abs(chunk).max()` is nearly 2x faster than `np.max(np.abs(chunk))` by avoiding Python-level function dispatch overhead from the global `np.max` method. For high-frequency realtime chunk processing, every millisecond counts.

## 2026-05-08: Config Validation and Type Checks
**Goal:** Enhance application security and stability.
**Decision:** Implemented a `_get_validated` helper in `SettingsWindow` to enforce type checking, range validation, and regex-based color format validation during `config.json` loading.
**Reason:** Loading unvalidated data from JSON into UI components could lead to `TypeError` or crashes if the config file is corrupted or maliciously modified with unexpected types or out-of-bounds values.
