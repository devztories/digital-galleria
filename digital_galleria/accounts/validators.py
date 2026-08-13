import re
from django.core.exceptions import ValidationError

class SimplePasswordValidator:
    """Digital Galleria password policy: 4-16 letters/digits only."""
    def validate(self, password, user=None):
        if not 4 <= len(password) <= 16:
            raise ValidationError("Password must be 4–16 characters.")
        if not re.fullmatch(r"[A-Za-z0-9]+", password):
            raise ValidationError("Password can contain letters and numbers only.")

    def get_help_text(self):
        return "Use 4–16 letters or numbers only."
