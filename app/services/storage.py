import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import FileValidationException

MAGIC_NUMBERS = {
    "application/pdf": [b"%PDF-"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
}

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


class StorageService:
    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and shell injection."""
        if not filename:
            return "unnamed_document"
        clean_name = os.path.basename(filename)
        # Allow alphanumeric, spaces, dots, parentheses, underscores, hyphens
        clean_name = re.sub(r'[^\w\s\.\(\)-]', '_', clean_name)
        clean_name = re.sub(r'\.+', '.', clean_name)
        clean_name = clean_name.strip()
        return clean_name or "document"

    def detect_mime_type(self, file_bytes: bytes, filename: str) -> str:
        ext = os.path.splitext(filename.lower())[1]
        expected_mime = ALLOWED_EXTENSIONS.get(ext)

        if not expected_mime:
            raise FileValidationException(
                f"Unsupported file extension '{ext}'. Allowed extensions: {list(ALLOWED_EXTENSIONS.keys())}"
            )

        detected_mime = None
        for mime, signatures in MAGIC_NUMBERS.items():
            for sig in signatures:
                if file_bytes.startswith(sig):
                    if mime == "image/webp" and len(file_bytes) >= 12:
                        if file_bytes[8:12] != b"WEBP":
                            continue
                    detected_mime = mime
                    break
            if detected_mime:
                break

        if not detected_mime:
            raise FileValidationException(
                "File signature (magic bytes) does not match any allowed format. File may be corrupted or disguised."
            )

        if detected_mime != expected_mime:
            if detected_mime == "image/jpeg" and expected_mime == "image/jpeg":
                pass
            else:
                raise FileValidationException(
                    f"MIME type mismatch: extension suggests '{expected_mime}' but file content is '{detected_mime}'"
                )

        return detected_mime

    async def validate_and_save(self, upload_file: UploadFile) -> Tuple[str, str, str, int, str]:
        sanitized_name = self.sanitize_filename(upload_file.filename or "uploaded_file")
        content = await upload_file.read()
        file_size = len(content)

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise FileValidationException(
                f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB"
            )

        if file_size == 0:
            raise FileValidationException("Uploaded file is empty (0 bytes).")

        mime_type = self.detect_mime_type(content, sanitized_name)
        sha256_hash = hashlib.sha256(content).hexdigest()

        ext = os.path.splitext(sanitized_name)[1].lower()
        storage_filename = f"{uuid.uuid4().hex}{ext}"
        storage_path = (self.base_dir / storage_filename).resolve()

        if not str(storage_path).startswith(str(self.base_dir)):
            raise FileValidationException("Path traversal attempt detected.")

        with open(storage_path, "wb") as f:
            f.write(content)

        return sanitized_name, str(storage_path), mime_type, file_size, sha256_hash

    def get_file_bytes(self, storage_path: str) -> bytes:
        path = Path(storage_path).resolve()
        if not str(path).startswith(str(self.base_dir)):
            raise FileValidationException("Unauthorized file path access.")
        if not path.exists():
            raise FileValidationException("Stored file not found on disk.")
        with open(path, "rb") as f:
            return f.read()


storage_service = StorageService()
