from pathlib import Path


def confine(path, root):
    return str(Path(path)).startswith(str(Path(root)))
