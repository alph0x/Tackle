"""Chunking."""
from limits import CHUNK_MB


def chunk_count(size_bytes):
    """Number of chunks an upload of this size is split into."""
    if size_bytes <= 0:
        return 0
    return -(-size_bytes // (CHUNK_MB * 1024 * 1024))
