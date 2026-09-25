"""Loading a roster of raw scores from a simple text file."""
from pathlib import Path


def load_scores(path) -> dict:
    """Read `name,score` lines (one per student) from `path` into a dict."""
    scores = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        name, _, raw_score = line.partition(",")
        scores[name.strip()] = float(raw_score)
    return scores
