# Agent Ledger

## 2025-05-05: NumPy Array Object Methods Over Global Functions
**Goal:** Real-time Engine & Model Optimization
**Decision:** Changed usages of `np.max(np.abs(chunk))` to `np.abs(chunk).max()` in real-time hot paths (`audio_capture.py`, `vad_logic.py`, `main_app.py`).
**Reason:** Benchmarks show `np.abs(chunk).max()` is nearly 2x faster than `np.max(np.abs(chunk))` by avoiding Python-level function dispatch overhead from the global `np.max` method. For high-frequency realtime chunk processing, every millisecond counts.

## 2026-05-08: Config Validation and Type Checks
**Goal:** Enhance application security and stability.
**Decision:** Implemented a `_get_validated` helper in `SettingsWindow` to enforce type checking, range validation, and regex-based color format validation during `config.json` loading.
**Reason:** Loading unvalidated data from JSON into UI components could lead to `TypeError` or crashes if the config file is corrupted or maliciously modified with unexpected types or out-of-bounds values.
## 2026-05-08: O(1) Theme Lookup in VaultThemeManager
**Goal:** Optimize theme retrieval performance
**Decision:** Replaced O(N) list iteration in `get_theme` and `get_theme_by_name` with O(1) dictionary lookups using a name-to-theme mapping initialized during constructor.
**Reason:** In applications with frequent theme switching or UI component initialization, repeated O(N) lookups introduce unnecessary latency. Dictionary lookups provide a significant speedup (~2.7x in microbenchmarks) with negligible memory overhead.

## 2026-05-08: Code Cleanup in STT Engine Orchestrator
**Goal:** Improve maintainability and reduce clutter.
**Decision:** Removed unused `import queue` and a redundant `else: pass` block with "not implemented" comments in `stt_engine/engine_orchestrator.py`.
**Reason:** Unused imports and dead code/comments reduce readability and increase noise. Following the "No Dead Code" policy from the project manifest.

## 2026-05-08: Strict Input Validation for Configuration (CSS Injection Prevention)
**Goal:** Improve application security by mitigating PySide6 CSS Injection vulnerabilities.
**Decision:** Implemented a `_get_validated` helper in `SettingsWindow` to enforce type, bounds, and regex validation on all values loaded from `config.json` before they mutate application state or get used in `setStyleSheet()`.
**Reason:** Unvalidated user configurations loaded from disk and injected directly into PySide6 stylesheets can lead to CSS Injection attacks, allowing arbitrary UI manipulation or potential file reads. Treating local config files as an untrusted boundary ensures robust security.

## 2026-05-09: Add Accessibility Labels and Tooltips to UI Controls
**Goal:** Improve PySide6 UI Accessibility and Usability
**Decision:** Added `setToolTip()` and `setAccessibleName()` to single-character and icon-only `QPushButton` instances (Bold, Italic, Underline, Text Color, Outline Color) in `SettingsWindow`.
**Reason:** Buttons with only single letters (e.g., "B", "I", "U", "A") or no text at all are poorly supported by screen readers and provide insufficient context for visually impaired or regular users. Providing explicit tooltips and accessible names enhances both keyboard/mouse UX and assistive technology compatibility without altering the visual layout.

## 2026-05-10: Update Feature Registry and Propose Encrypted WebSocket
**Goal:** Synchronize documentation with current capabilities and plan next security-focused feature.
**Decision:** Updated README.md to include recently completed features (Dynamic Logging, Background Tray, AGC, Engine Strategy) and proposed the implementation of an Encrypted WebSocket Endpoint (wss://) with token-based authentication.
**Reason:** Maintaining an accurate feature registry is critical for the VaultWares ecosystem. The proposed Encrypted WebSocket feature addresses a missing capability mentioned in the README while adhering strictly to the privacy-first and secure-by-default philosophy required by the security standards.
