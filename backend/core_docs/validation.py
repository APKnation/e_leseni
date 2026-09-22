"""Shared file-upload validation used by every document model.

Real councils accept PDF scans only — screenshots and phone photos of
documents get rejected at the counter. These helpers enforce that rule in
one place so serializers, views and models all agree.
"""
from django.core.exceptions import ValidationError

MAX_DOCUMENT_MB = 10
MAX_DOCUMENT_BYTES = MAX_DOCUMENT_MB * 1024 * 1024

ALLOWED_CONTENT_TYPES = {'application/pdf'}
ALLOWED_EXTENSIONS = {'.pdf'}


def _extension(file_name):
    dot = file_name.rfind('.')
    return file_name[dot:].lower() if dot != -1 else ''


def validate_pdf_document(file):
    """Validate an uploaded document is a PDF within the size limit.

    Raises ValidationError with a user-facing message. Safe to call with
    None (lets optional fields skip validation).
    """
    if file is None:
        return

    errors = []

    if file.size and file.size > MAX_DOCUMENT_BYTES:
        errors.append(
            f'File too large ({file.size / (1024 * 1024):.1f} MB). '
            f'Maximum is {MAX_DOCUMENT_MB} MB.'
        )

    ext = _extension(file.name or '')
    content_type = (getattr(file, 'content_type', '') or '').lower()
    is_pdf = ext in ALLOWED_EXTENSIONS or content_type in ALLOWED_CONTENT_TYPES

    if not is_pdf:
        errors.append('Only PDF files are accepted.')

    if errors:
        raise ValidationError(errors)
