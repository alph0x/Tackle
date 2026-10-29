from pathlib import Path


def confine(path, root):
    base = Path(root).resolve()
    target = Path(path).resolve()
    return target != base and base in target.parents
