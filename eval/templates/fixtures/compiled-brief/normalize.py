import json
from pathlib import Path


def write_results(directory):
    directory = Path(directory)
    (directory / "result.csv").write_bytes(b"name,score\nBo,3\nAda,2\n")
    (directory / "result.json").write_text(json.dumps({"name": "Bo", "score": 3}))
