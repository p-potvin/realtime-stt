## 2025-02-18 - SRT Timestamp Formatting Optimization
**Learning:** Formatting timestamps with `divmod(seconds, 3600)` using floating-point math inside list comprehensions or generators for SRT generation introduces a small but measurable overhead. When processing thousands of timestamps, converting `seconds` into an integer representation of milliseconds upfront and using purely integer `divmod` arithmetic is ~15-20% faster.
**Action:** Use integer arithmetic instead of floating-point `divmod` for repetitive timestamp conversions.
## 2025-02-18 - Redundant PyTorch Tensor Conversions in NeMo
**Learning:** High-level wrapper methods like `transcribe` in NVIDIA NeMo models (e.g., Canary/Parakeet) natively accept paths or raw NumPy buffers and handle PyTorch conversions and device transfers internally. Creating PyTorch tensors and manually sending them to the target `DEVICE` before calling these methods is redundant, blocks the hot path, and causes unused memory allocation overhead.
**Action:** Always check if a library's method natively accepts NumPy arrays or paths before manually converting inputs into PyTorch tensors and performing device transfers.
