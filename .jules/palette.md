## 2026-05-09 - Accessible Tooltips for PySide6 Minimal Buttons
**Learning:** In PySide6 applications where space constraints lead to single-character buttons (like "B", "I", "U" for font styling) or empty color-picker buttons, screen readers cannot infer the button's purpose, and users miss context. Qt's built-in `setAccessibleName()` provides screen reader context, while `setToolTip()` provides visual hover context.
**Action:** Always provide both `setToolTip()` and `setAccessibleName()` for any `QPushButton` or interactive widget that relies on an icon, a single character, or lacks descriptive visual text. This ensures compliance with accessibility standards (WCAG) while maintaining compact UI designs.
## 2026-05-10 - Added Tooltips and Accessible Names to Settings UI Comboboxes and Spinboxes
**Learning:** PySide6 combo boxes and spin boxes used in control panels lack contextual names when read by screen readers. Providing both tooltips for visual feedback and accessible names for a11y ensures a much better experience for users.
**Action:** When implementing new PySide6 UI widgets (specifically inputs like QComboBox, QSpinBox), always add `setToolTip` and `setAccessibleName` for better context.
## 2026-05-12 - Accessible Tooltips for PySide6 Checkboxes
**Learning:** PySide6 checkboxes often lack contextual names when read by screen readers. Providing both tooltips for visual feedback and accessible names for a11y ensures a much better experience for users.
**Action:** When implementing new PySide6 UI widgets (specifically interactive elements like QCheckBox), always add `setToolTip` and `setAccessibleName` for better context.
## 2026-05-18 - Missing Focus Indicators with Custom Qt Stylesheets
**Learning:** When applying custom stylesheets (QSS) to PySide6/Qt widgets (like `QPushButton`, `QComboBox`, etc.), the default OS-level focus indicators are often completely removed. This breaks keyboard navigation accessibility, as users relying on the `Tab` key cannot see which element has focus.
**Action:** Always explicitly define `:focus` pseudo-states in Qt stylesheets when overriding default styles to ensure keyboard navigation remains visible and WCAG compliant.
## 2026-05-14 - Palette: Keyboard Focus Styles in PySide6 Custom Stylesheets
**Learning:** When creating fully custom PySide6 QSS stylesheets that define the layout and background for controls like QComboBox, QCheckBox, or QPushButton, the OS-level default focus outline is completely stripped away. Users navigating entirely via keyboard lose track of where they are on the page.
**Action:** When restyling components using QSS, ALWAYS append explicit pseudo-state `:focus` declarations (e.g., `QCheckBox:focus, QComboBox:focus`) to re-introduce a visible focus indicator (like an accent-colored border). Additionally, explicitly declare `outline: none;` to prevent duplicate or conflicting focus artifacts on some platforms.
## 2026-05-19 - Contextual Suffixes for Numeric Inputs in PySide6
**Learning:** Numeric inputs (QSpinBox) in compact toolbars often lack space for descriptive labels. The visual value itself lacks context (e.g., "13" instead of "13 pt"), causing cognitive friction.
**Action:** Always use `setSuffix()` (e.g., " pt", " px") on `QSpinBox` elements to provide immediate visual context for the unit of measurement without requiring external labels.
## 2026-05-20 - Qt QLabel Buddy for Form Accessibility and Keyboard Navigation
**Learning:** In PySide6 interfaces, using standalone `QLabel` instances adjacent to input fields (like `QComboBox` or `QSpinBox`) mimics visual form labels but lacks semantic association. This prevents screen readers from automatically announcing the label when the input is focused, and deprives keyboard users of quick navigation shortcuts (Alt+Key).
**Action:** Always use `QLabel.setBuddy()` to semantically link a `QLabel` to its corresponding input widget, akin to the HTML `<label for="...">` attribute. Additionally, prefix the label text with `&` (e.g., `&Theme:`) to automatically assign an Alt-key shortcut for faster keyboard navigation.
