## 🛡️-05-08 - PySide6 CSS Injection via Unvalidated Configuration
**Vulnerability:** The application loaded style preferences (colors, font sizes, etc.) directly from `config.json` without validation, injecting them straight into `setStyleSheet()`. A malicious local file edit to `config.json` could result in PySide6 CSS Injection, allowing arbitrary UI manipulation or potential local file read/exfiltration using CSS `url(file://...)` constructs.
**Learning:** PySide6/Qt stylesheets are powerful enough to be dangerous if populated with untrusted/unvalidated data. Settings files (`config.json`), even if local, should be treated as untrusted input boundaries because they can be modified by other processes or malware.
**Prevention:** Always validate configuration data when parsing it from disk before updating application state or passing it to rendering functions. Implement strict type checking, bounds constraints (e.g., limits on font sizes or outline widths), and regex validation for structured strings like hex colors.

## 🛡️-05-20 - [PII Leakage in Local Transcriptions]
**Vulnerability:** Real-time STT processes raw audio into text which might contain sensitive PII (Personally Identifiable Information) like credit card numbers or SSNs. This text is then pushed to UI overlays or WebSocket streams without redaction, creating a localized exposure risk even if processing is offline.
**Learning:** Local-first processing guarantees data doesn't leave the machine, but it doesn't prevent accidental local broadcasting (e.g., screen sharing the STT overlay during a meeting) or downstream logging of sensitive information.
**Prevention:** Implement a local, low-latency PII redaction middleware step between the STT inference output and the final display/broadcast sinks.
