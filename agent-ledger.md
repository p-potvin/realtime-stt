# Agent Ledger

## 2026-05-05: NumPy Array Object Methods Over Global Functions
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
**Decision:** Removed unused `import queue` and a redundant `else: pass` block with "not implemented" comments in `vaultwares_realtime/engine_orchestrator.py`.
**Reason:** Unused imports and dead code/comments reduce readability and increase noise. Following the "No Dead Code" policy from the project manifest.

## 2026-05-08: Strict Input Validation for Configuration (CSS Injection Prevention)
**Goal:** Improve application security by mitigating PySide6 CSS Injection vulnerabilities.
**Decision:** Implemented a `_get_validated` helper in `SettingsWindow` to enforce type, bounds, and regex validation on all values loaded from `config.json` before they mutate application state or get used in `setStyleSheet()`.
**Reason:** Unvalidated user configurations loaded from disk and injected directly into PySide6 stylesheets can lead to CSS Injection attacks, allowing arbitrary UI manipulation or potential file reads. Treating local config files as an untrusted boundary ensures robust security.

## 2026-05-09: Add Accessibility Labels and Tooltips to UI Controls
**Goal:** Improve PySide6 UI Accessibility and Usability
**Decision:** Added `setToolTip()` and `setAccessibleName()` to single-character and icon-only `QPushButton` instances (Bold, Italic, Underline, Text Color, Outline Color) in `SettingsWindow`.
**Reason:** Buttons with only single letters (e.g., "B", "I", "U", "A") or no text at all are poorly supported by screen readers and provide insufficient context for visually impaired or regular users. Providing explicit tooltips and accessible names enhances both keyboard/mouse UX and assistive technology compatibility without altering the visual layout.

## 2026-05-11 - Palette: Add accessibility context to engine dropdown
**Goal:** Palette: Add accessibility context to engine dropdown
**Decision:** Added `setToolTip` and `setAccessibleName` to `engine_combo`.
**Reason:** Following the rule in `.jules/palette.md` to provide screen reader context and visual hover context for QComboBoxes.

## 2026-05-15: Security Fix - Remove Global Monkey-Patching of subprocess.Popen
**Goal:** Fix security vulnerability related to global state mutation.
**Decision:** Removed the global monkey-patch of `subprocess.Popen` in `vaultwares_realtime/parakeet_wrapper.py`. Replaced it with a `hush_subprocess` context manager for localized patching during NeMo model initialization and updated `vault_sync.py` to use explicit `creationflags`.
**Reason:** Global monkey-patching of standard library modules is a security risk and can lead to unintended side effects across the entire application. Localizing the behavior ensures that only the necessary calls are affected.

## 2026-05-18 - Add Keyboard Shortcuts and Focus Styles to Settings UI
**Goal:** Enhance keyboard accessibility and user interaction speed in the Settings window.
**Decision:** Added keyboard shortcuts (`Ctrl+B`, `Ctrl+I`, `Ctrl+U`) to formatting buttons and updated their tooltips. Additionally, explicitly defined `:focus` pseudo-states in the QSS for interactive widgets (`QCheckBox`, `QComboBox`, `QFontComboBox`, `QSpinBox`, `QPushButton`).
**Reason:** Adding keyboard shortcuts speeds up power-user interactions, while explicit `:focus` states are necessary because custom Qt stylesheets often remove default OS focus indicators, breaking WCAG keyboard navigation compliance.

## 2026-05-14 - Palette: Keyboard Focus Styles in PySide6 Custom Stylesheets
**Goal:** Improve Keyboard Navigation Accessibility.
**Decision:** Added explicit `:focus` pseudo-state selectors to the custom QSS stylesheet in `gui_overlay/overlay_window.py` for interactive widgets like `QCheckBox`, `QComboBox`, `QFontComboBox`, `QSpinBox`, and `QPushButton`. Also included `outline: none;` to suppress conflicting OS-level outlines.
**Reason:** In PySide6, applying a custom stylesheet often overrides and removes the default OS-provided focus outlines. This breaks accessibility for keyboard users who rely on visual indicators to navigate the interface. Defining `:focus` styling ensures WCAG compliance and provides necessary visual feedback.

## 2026-05-19: Visual Duplication Comment Cleanup
**Goal:** Clarify documentation for the rolling caption display logic.
**Decision:** Consolidated and reworded the two-line comment in `update_caption` within `gui_overlay/overlay_window.py` to: "Rolling 2-line display prevents visual duplication by ensuring a stable top-to-bottom flow."
**Reason:** The original comment used "fixes" in a way that could be mistaken for an actionable TODO or a recent bug fix, whereas it actually describes an intentional, stable feature. Rewording ensures clarity for future maintenance.

## 2026-05-19: Contextual Suffixes and Tooltips for Micro-UX
**Goal:** Improve UX of settings spinboxes and drag handle.
**Decision:** Added 'pt' and 'px' suffixes to size spinboxes (`self.size_spin` and `self.outline_width_spin`) and added a tooltip and accessible name to the invisible drag handle in `SubtitleWindow`.
**Reason:** Adding unit suffixes to compact numeric inputs provides immediate visual context without requiring external labels. Adding tooltips and accessible names to invisible functional elements (like a drag handle) drastically improves discoverability and accessibility for screen readers.

## 2026-05-20: Feature Registry Synchronization and PII Redaction Pipeline Proposal
**Goal:** Agent Routine Execution (Ziegler) - Continuous Improvement
**Decision:** Updated `README.md` features section with recent accomplishments (Fault-Tolerant Hardware Management, Multi-segment handling optimization, Dynamic Peak AGC). Proposing a new security feature: Real-Time PII Redaction Pipeline.
**Reason:** Adhering to the agent's core operational loop (Step 2 and Step 3b). The project lacks active feature branches, so a new high-value security feature is proposed. The PII redaction pipeline aligns with VaultWares' privacy-first philosophy, ensuring sensitive data like SSNs or credit cards aren't inadvertently broadcasted or logged during real-time transcription.
## 2026-05-20
- Goal: Improve form accessibility and keyboard navigation in SettingsWindow
- Decision: Used `QLabel.setBuddy()` and mnemonics (`&`) for form labels next to comboboxes, spinboxes, and buttons in `gui_overlay/overlay_window.py`.
- Reason: Setting a buddy on a QLabel links it to an input field semantically, allowing screen readers to announce the label when the field is focused. The ampersand mnemonic adds quick Alt+Key navigation shortcuts for keyboard users.
