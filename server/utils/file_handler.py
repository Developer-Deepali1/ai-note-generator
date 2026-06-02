"""Secure file handling utilities for uploads and storage."""

from __future__ import annotations

import hashlib
import mimetypes
import os
import re
import shutil
from pathlib import Path
from typing import BinaryIO

from utils.constants import MAX_AUDIO_FILE_SIZE_BYTES, SUPPORTED_AUDIO_EXTENSIONS


class FileHandlingError(ValueError):
    """Raised when file handling validation fails."""



_FILENAME_PATTERN = re.compile(r'[^A-Za-z0-9._-]+')



def sanitize_filename(filename: str, *, default: str = 'upload.bin') -> str:
    """Sanitize file names to avoid unsafe characters and traversal."""
    name = Path(filename or '').name
    name = _FILENAME_PATTERN.sub('_', name).strip('._')
    if not name:
        return default
    return name[:255]



def validate_file_type(filename: str, *, allowed_extensions: tuple[str, ...] = SUPPORTED_AUDIO_EXTENSIONS) -> str:
    """Validate extension against an allow-list."""
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed_extensions:
        raise FileHandlingError(f'Unsupported file type: {suffix}')
    return suffix



def secure_join(base_directory: str, user_path: str) -> Path:
    """Securely join paths and prevent directory traversal."""
    base = Path(base_directory).resolve()
    candidate = (base / user_path).resolve()
    if base not in [candidate, *candidate.parents]:
        raise FileHandlingError('Path traversal detected.')
    return candidate



def save_upload(stream: BinaryIO, filename: str, destination_directory: str) -> Path:
    """Save uploaded content safely with basic quota validation."""
    clean_name = sanitize_filename(filename)
    validate_file_type(clean_name)

    destination = secure_join(destination_directory, clean_name)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open('wb') as handle:
        shutil.copyfileobj(stream, handle)

    size = destination.stat().st_size
    if size > MAX_AUDIO_FILE_SIZE_BYTES:
        destination.unlink(missing_ok=True)
        raise FileHandlingError('File exceeds maximum allowed size.')

    return destination



def compute_file_checksum(path: str, *, algorithm: str = 'sha256') -> str:
    """Compute file checksum for integrity tracking."""
    hasher = hashlib.new(algorithm)
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()



def extract_file_metadata(path: str) -> dict[str, object]:
    """Extract filesystem metadata for uploaded files."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileHandlingError('File not found.')

    mime_type = mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream'
    return {
        'name': file_path.name,
        'path': str(file_path.resolve()),
        'size_bytes': file_path.stat().st_size,
        'mime_type': mime_type,
        'checksum': compute_file_checksum(str(file_path)),
    }



def cleanup_temporary_files(directory: str, *, older_than_seconds: int) -> int:
    """Delete temporary files older than threshold and return deleted count."""
    root = Path(directory)
    if not root.exists():
        return 0

    now = os.path.getmtime(root)
    deleted = 0
    for file_path in root.glob('*'):
        if not file_path.is_file():
            continue
        age = now - file_path.stat().st_mtime
        if age >= older_than_seconds:
            file_path.unlink(missing_ok=True)
            deleted += 1
    return deleted
