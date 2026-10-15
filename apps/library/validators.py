from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files import File


ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_file_extension(file: File) -> None:
    """Allow only study-material file types."""
    extension = Path(file.name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValidationError(f"Unsupported file type. Allowed types: {allowed}")


def validate_file_size(file: File) -> None:
    """Reject files bigger than MAX_FILE_SIZE."""
    if file.size > MAX_FILE_SIZE:
        raise ValidationError("File is too large. Maximum size is 10 MB.")
