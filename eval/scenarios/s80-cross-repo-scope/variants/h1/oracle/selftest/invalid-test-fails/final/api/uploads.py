"""Uploads."""
from chunks import chunk_count  # noqa: F401
from limits import MAX_UPLOAD_MB  # noqa: F401


def check_upload(size_bytes):
    """Chunks needed for an upload; ValueError when it is empty or over the limit."""
    raise NotImplementedError("check upload")


def upload_limit_label():
    """The upload limit in the wording the upload page uses."""
    raise NotImplementedError("upload limit label")
