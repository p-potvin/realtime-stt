## 2025-02-18 - SRT Timestamp Formatting Optimization
**Learning:** Formatting timestamps with `divmod(seconds, 3600)` using floating-point math inside list comprehensions or generators for SRT generation introduces a small but measurable overhead. When processing thousands of timestamps, converting `seconds` into an integer representation of milliseconds upfront and using purely integer `divmod` arithmetic is ~15-20% faster.
**Action:** Use integer arithmetic instead of floating-point `divmod` for repetitive timestamp conversions.
