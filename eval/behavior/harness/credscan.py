"""Finds where a credential's value leaked into other text, without ever revealing it.

Guarantees:
- secret_values() extracts the candidate secret strings held in a credential file.
- encodings() enumerates the forms one of those values could take after common
  transport-level re-encodings (base64, hex, URL-encoding, JSON string escaping).
- find() reports only the *names* of the locations that contain a leak. It never
  returns, prints or logs the secret text itself.
"""

import base64
import json
import urllib.parse
from pathlib import Path


def _collect_string_leaves(node, out):
    """Recursively collect string leaves (>=16 chars) through dict values and list
    items. Dict keys and non-string scalars (numbers, bools, null) are never leaves."""
    if isinstance(node, dict):
        for value in node.values():
            _collect_string_leaves(value, out)
    elif isinstance(node, list):
        for item in node:
            _collect_string_leaves(item, out)
    elif isinstance(node, str):
        if len(node) >= 16:
            out.append(node)


def secret_values(data: bytes) -> list:
    """Secrets in a credential file. If it parses as JSON: every string leaf with 16 or
    more characters (recursively through dict values and list items); if there is none,
    the whole stripped content. Otherwise: the stripped UTF-8 content. Values shorter
    than 8 characters are dropped. Deduplicated, sorted by length descending."""
    text = data.decode('utf-8', errors='replace')
    stripped = text.strip()
    try:
        parsed = json.loads(text)
    except ValueError:
        values = [stripped]
    else:
        leaves = []
        _collect_string_leaves(parsed, leaves)
        values = leaves if leaves else [stripped]
    filtered = [value for value in values if len(value) >= 8]
    return sorted(set(filtered), key=lambda value: (-len(value), value))


def encodings(value: str) -> list:
    """value itself, standard and URL-safe base64 of its UTF-8 bytes (with and without
    '=' padding), lowercase and uppercase hex, urllib.parse.quote(value, safe=''), and
    the JSON-escaped form json.dumps(value)[1:-1]. Deduplicated."""
    raw = value.encode('utf-8')
    std_b64 = base64.b64encode(raw).decode('ascii')
    url_b64 = base64.urlsafe_b64encode(raw).decode('ascii')
    hex_lower = raw.hex()
    candidates = [
        value,
        std_b64,
        std_b64.rstrip('='),
        url_b64,
        url_b64.rstrip('='),
        hex_lower,
        hex_lower.upper(),
        urllib.parse.quote(value, safe=''),
        json.dumps(value)[1:-1],
    ]
    seen = []
    for candidate in candidates:
        if candidate not in seen:
            seen.append(candidate)
    return seen


def find(credential_path, texts: dict) -> list:
    """texts maps a location name (for example 'argv', 'env:NAME', 'prompt:01',
    'file:work/notes.md') to text (str or bytes; bytes are searched as bytes and as
    UTF-8 with replacement). Returns the sorted location names whose text contains any
    encoding of any secret value, or the credential path as a string (str(path) and its
    resolved form). Never returns, prints or logs a secret.

    Raises if the credential file cannot be read: silently treating an unreadable
    credential as "nothing leaked" would be an unsafe default.
    """
    path = Path(credential_path)
    data = path.read_bytes()

    needles_str = set()
    for value in secret_values(data):
        needles_str.update(encodings(value))
    needles_str.add(str(credential_path))
    needles_str.add(str(path.resolve()))
    needles_bytes = [needle.encode('utf-8') for needle in needles_str]

    hits = []
    for name, text in texts.items():
        if isinstance(text, bytes):
            if any(needle in text for needle in needles_bytes):
                hits.append(name)
                continue
            decoded = text.decode('utf-8', errors='replace')
            if any(needle in decoded for needle in needles_str):
                hits.append(name)
        else:
            if any(needle in text for needle in needles_str):
                hits.append(name)
    return sorted(hits)
