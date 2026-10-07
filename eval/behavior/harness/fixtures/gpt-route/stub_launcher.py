"""Fixed fixture launcher control, explicitly not an OS sandbox."""
import hashlib
import os
from pathlib import Path
import sys

VERSION = 'tackle-gpt-stub-launcher/1'
# Packaged fixture identities are filled at authoring, never supplied by candidate config.
TRUSTED = {'stub_cli.py': 'd0c1673bf9f20e4c03deb32cf0dec1038795aaf884e54e795dadfda6aac47699', 'sentinel_helper.py': 'c5a9149e2bb34fbe12332a66b34c8c1d72573c6b26421353deb171462f6e3bd2', 'oracle/check.py': 'aff0b5f2af644826bbb4b439176e359ba4c5ed50cc6a5f5cd38d27698c473211'}


def main():
    argv = sys.argv[1:]
    if len(argv) < 3 or argv[1] != '-B':
        raise SystemExit('unsupported synthetic argv')
    interpreter = Path(argv[0])
    target = Path(argv[2])
    here = Path(__file__).resolve().parent
    relative = target.relative_to(here).as_posix() if target.is_relative_to(here) else None
    if (interpreter != Path(sys.executable).resolve() or target.is_symlink()
            or relative not in TRUSTED or hashlib.sha256(target.read_bytes()).hexdigest() != TRUSTED[relative]):
        raise SystemExit('untrusted synthetic executable')
    # The oracle and helper are fixed fixture programs, never arbitrary config code.
    os.execve(str(interpreter), argv, dict(os.environ))


if __name__ == '__main__':
    main()
