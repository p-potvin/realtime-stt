import pytest
from vaultwares_realtime.pii_redaction import PIIRedactor

def test_pii_redaction():
    redactor = PIIRedactor()

    # Test Credit Card
    assert redactor.redact_text("My card is 1234-5678-9012-3456") == "My card is [CARD REDACTED]"
    assert redactor.redact_text("Here is 1234567890123456.") == "Here is [CARD REDACTED]."

    # Test SSN
    assert redactor.redact_text("His SSN is 123-45-6789 today.") == "His SSN is [SSN REDACTED] today."

    # Test Phone
    assert redactor.redact_text("Call me at 555-123-4567.") == "Call me at [PHONE REDACTED]."
    assert redactor.redact_text("Or (555) 123-4567.") == "Or [PHONE REDACTED]."
    assert redactor.redact_text("Also +1 555 123 4567.") == "Also [PHONE REDACTED]."

    # Test Email
    assert redactor.redact_text("Email me at test@example.com") == "Email me at [EMAIL REDACTED]"

    # Test Normal Text (No False Positives on short numbers)
    normal = "I bought 2 apples for 4 dollars."
    assert redactor.redact_text(normal) == normal

    # Test Mixed
    mixed = "Contact john.doe@email.com or call 555-987-6543."
    assert redactor.redact_text(mixed) == "Contact [EMAIL REDACTED] or call [PHONE REDACTED]."
