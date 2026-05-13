## 2026-05-09 - Accessible Tooltips for PySide6 Minimal Buttons
**Learning:** In PySide6 applications where space constraints lead to single-character buttons (like "B", "I", "U" for font styling) or empty color-picker buttons, screen readers cannot infer the button's purpose, and users miss context. Qt's built-in `setAccessibleName()` provides screen reader context, while `setToolTip()` provides visual hover context.
**Action:** Always provide both `setToolTip()` and `setAccessibleName()` for any `QPushButton` or interactive widget that relies on an icon, a single character, or lacks descriptive visual text. This ensures compliance with accessibility standards (WCAG) while maintaining compact UI designs.
## 2024-05-10 - Added Tooltips and Accessible Names to Settings UI Comboboxes and Spinboxes
**Learning:** PySide6 combo boxes and spin boxes used in control panels lack contextual names when read by screen readers. Providing both tooltips for visual feedback and accessible names for a11y ensures a much better experience for users.
**Action:** When implementing new PySide6 UI widgets (specifically inputs like QComboBox, QSpinBox), always add `setToolTip` and `setAccessibleName` for better context.
## 2024-05-12 - Accessible Tooltips for PySide6 Checkboxes
**Learning:** PySide6 checkboxes often lack contextual names when read by screen readers. Providing both tooltips for visual feedback and accessible names for a11y ensures a much better experience for users.
**Action:** When implementing new PySide6 UI widgets (specifically interactive elements like QCheckBox), always add `setToolTip` and `setAccessibleName` for better context.
## 2024-05-18 - Missing Focus Indicators with Custom Qt Stylesheets
**Learning:** When applying custom stylesheets (QSS) to PySide6/Qt widgets (like `QPushButton`, `QComboBox`, etc.), the default OS-level focus indicators are often completely removed. This breaks keyboard navigation accessibility, as users relying on the `Tab` key cannot see which element has focus.
**Action:** Always explicitly define `:focus` pseudo-states in Qt stylesheets when overriding default styles to ensure keyboard navigation remains visible and WCAG compliant.
