"""File security and upload validation utilities."""

import os
from typing import BinaryIO, Union

from datasentinel.core.config import CONFIG
from datasentinel.core.exceptions import FileSecurityError

# Dangerous executable file headers (magic bytes) to reject
DANGEROUS_MAGIC_BYTES = [
    b"MZ",  # DOS/Windows Executable
    b"\x7fELF",  # Linux ELF Executable
    b"\xfe\xed\xfa",  # Mach-O binary
    b"\xcf\xfa\xed",  # Mach-O 64-bit binary
    b"PK\x03\x04\x14\x00\x08\x00",  # Sometimes zip/jar/exe bundle, we only allow explicit csv/parquet
]


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and strip unsafe characters."""
    base = os.path.basename(filename)
    # Remove null bytes and non-printable characters
    cleaned = "".join(ch for ch in base if ch.isprintable() and ch not in '<>:"/\\|?*\x00')
    if not cleaned:
        cleaned = "dataset.csv"
    return cleaned


def validate_file_safety(
    file_buffer: Union[BinaryIO, bytes],
    filename: str,
    max_size_bytes: int = CONFIG.MAX_UPLOAD_SIZE_BYTES,
) -> int:
    """Verify file extension, size constraints, and header safety.

    Returns the verified byte size of the file.
    Raises FileSecurityError if any validation check fails.
    """
    safe_name = sanitize_filename(filename)
    _, ext = os.path.splitext(safe_name.lower())

    if ext not in CONFIG.ALLOWED_EXTENSIONS:
        raise FileSecurityError(
            f"Unsupported file extension '{ext}'. Only CSV (.csv) and Parquet (.parquet) are permitted."
        )

    # Determine size and inspect initial bytes
    if isinstance(file_buffer, bytes):
        size = len(file_buffer)
        header = file_buffer[:16]
    else:
        # Seekable stream
        file_buffer.seek(0, os.SEEK_END)
        size = file_buffer.tell()
        file_buffer.seek(0)
        header = file_buffer.read(16)
        file_buffer.seek(0)

    if size == 0:
        raise FileSecurityError(f"Uploaded file '{safe_name}' is empty (0 bytes).")

    if size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        curr_mb = size / (1024 * 1024)
        raise FileSecurityError(
            f"File size ({curr_mb:.1f} MB) exceeds maximum allowed upload limit ({max_mb:.0f} MB)."
        )

    # Check for executable magic bytes
    for magic in DANGEROUS_MAGIC_BYTES:
        if header.startswith(magic):
            raise FileSecurityError(
                f"File '{safe_name}' contains potentially unsafe executable binary headers."
            )

    return size
