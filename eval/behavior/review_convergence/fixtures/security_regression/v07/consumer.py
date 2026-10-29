def confine(path, root):
    return '..' not in path and not path.startswith(root + '.')
