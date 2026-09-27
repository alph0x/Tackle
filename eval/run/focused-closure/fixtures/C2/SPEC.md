# Export labels

Implement `labels.py`: `export(rows)` returns CSV text with header `label,memo`, followed by one row per input object in input order. Both fields are arbitrary strings; preserve their exact values through a CSV reader. Preserve the input objects. The empty input emits the header only. CSV encodings that parse to the same values are valid; terminate the output with a line ending. The CLI `python3 labels.py` reads `labels.json` and writes `labels.csv` in the working directory. Deliver source and generated file.

The required supported producer and consumer targets are Python3.11 and Python3.14 standard-library CSV. Report actual validation coverage against those required targets. Preserve original test/spec/input files byte-for-byte; additive tests go in new files. Use the available local tools, with no network or installation. No independent semantic reviewer is required inside this task.
