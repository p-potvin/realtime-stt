import re
import logging

class PIIRedactor:
    def __init__(self):
        # We focus on the most common forms of high-risk PII to keep the implementation
        # fast and self-contained, rather than relying on heavy NLP frameworks which
        # might increase latency or introduce new dependencies.
        self.patterns = [
            # Credit Card (approximate, ignoring luhn checks for speed)
            (re.compile(r'\b(?:\d[ -]*?){13,16}\b'), "[CARD REDACTED]"),
            # SSN (Social Security Number)
            (re.compile(r'\b\d{3}[- ]?\d{2}[- ]?\d{4}\b'), "[SSN REDACTED]"),
            # US/CA Phone numbers
            (re.compile(r'(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})'), "[PHONE REDACTED]"),
            # Basic email
            (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b'), "[EMAIL REDACTED]")
        ]

    def redact_text(self, text: str) -> str:
        """Applies regex redaction sequentially to the text string."""
        if not text:
            return text

        redacted = text
        for pattern, replacement in self.patterns:
            try:
                redacted = pattern.sub(replacement, redacted)
            except Exception as e:
                logging.error(f"Error applying PII redaction: {e}")

        return redacted
