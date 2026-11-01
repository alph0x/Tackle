"""Reads the export the desk prints each morning: a header line, then one row per line."""


def read_header(text):
    lines = text.splitlines()
    return [name.strip() for name in lines[0].split(',')]


def read_rows(text):
    header = read_header(text)
    rows = []
    for line in text.splitlines()[1:]:
        if line.strip():
            rows.append(dict(zip(header, [cell.strip() for cell in line.split(',')])))
    return rows
