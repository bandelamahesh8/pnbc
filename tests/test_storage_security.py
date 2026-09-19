import io
import pytest
from fastapi import UploadFile
from app.core.exceptions import FileValidationException
from app.services.storage import StorageService


@pytest.fixture
def storage():
    return StorageService(base_dir="data/test_uploads")


def test_sanitize_filename(storage):
    assert storage.sanitize_filename("../../../etc/passwd") == "passwd"
    assert storage.sanitize_filename("..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert storage.sanitize_filename("my exam paper (final).pdf") == "my exam paper (final).pdf"
    assert storage.sanitize_filename("test..file...pdf") == "test.file.pdf"
    assert storage.sanitize_filename("") == "unnamed_document"


def test_magic_bytes_valid_pdf(storage):
    pdf_bytes = b"%PDF-1.4\n%test content\n"
    mime = storage.detect_mime_type(pdf_bytes, "document.pdf")
    assert mime == "application/pdf"


def test_magic_bytes_valid_png(storage):
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    mime = storage.detect_mime_type(png_bytes, "image.png")
    assert mime == "image/png"


def test_magic_bytes_valid_jpeg(storage):
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    mime = storage.detect_mime_type(jpeg_bytes, "photo.jpg")
    assert mime == "image/jpeg"


def test_magic_bytes_spoofed_extension_rejected(storage):
    fake_pdf = b"MZ\x90\x00\x03\x00\x00\x00"
    with pytest.raises(FileValidationException) as exc_info:
        storage.detect_mime_type(fake_pdf, "document.pdf")
    assert "File signature (magic bytes) does not match" in str(exc_info.value.message)


def test_unsupported_extension_rejected(storage):
    with pytest.raises(FileValidationException) as exc_info:
        storage.detect_mime_type(b"some text", "script.sh")
    assert "Unsupported file extension" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_empty_file_rejected(storage):
    empty_upload = UploadFile(filename="empty.pdf", file=io.BytesIO(b""))
    with pytest.raises(FileValidationException) as exc_info:
        await storage.validate_and_save(empty_upload)
    assert "Uploaded file is empty" in str(exc_info.value.message)
