import os


def confine(path, root):
    base = os.path.realpath(root)
    target = os.path.realpath(path)
    return target != base and os.path.commonpath([base, target]) == base
