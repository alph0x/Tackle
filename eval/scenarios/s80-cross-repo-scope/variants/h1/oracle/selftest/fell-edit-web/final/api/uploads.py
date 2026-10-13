"""Uploads."""
from chunks import chunk_count  # noqa: F401
from limits import MAX_UPLOAD_MB  # noqa: F401


def check_upload(size_bytes):
    """Chunks needed for an upload; ValueError when it is empty or over the limit."""
    if size_bytes <= 0 or size_bytes > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError("size out of range")
    return chunk_count(size_bytes)


def upload_limit_label():
    """The upload limit in the wording the upload page uses."""
    return "Files up to %d MB per upload" % MAX_UPLOAD_MB
