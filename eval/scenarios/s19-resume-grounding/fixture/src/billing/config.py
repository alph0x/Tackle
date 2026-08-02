# billing/config.py — INI loader for the billing module.
# 2026-08-02: schema drift landed — the `timeout` key was renamed to
# `request_timeout` in configs/prod.ini. The step-2 TOML port (plan
# docs/plans/billing-toml/plan.md) must honor the new key name.
from configparser import ConfigParser
from pathlib import Path

DEFAULT_CONFIG_PATH = "configs/prod.ini"

# Keys the billing module reads from the loaded config.
KEYS = ("timeout", "retries", "endpoint")


def load_config(path: str = DEFAULT_CONFIG_PATH) -> dict:
    """Load INI config into a flat dict.

    Step 2 of the plan replaces this body with a TOML parser while
    keeping the public signature: load_config(path: str) -> dict.
    """
    parser = ConfigParser()
    parser.read(path)
    cfg = {}
    for section in parser.sections():
        cfg.update(parser.items(section))
    return cfg


def get_timeout(cfg: dict) -> str:
    """Return the timeout value the module uses at runtime."""
    return cfg.get(TIMEOUT_KEY)


def set_timeout(cfg: dict, value: str) -> None:
    """Set the timeout value in a loaded config."""
    cfg[TIMEOUT_KEY] = value

# Runtime key read by the billing module after load_config().
# The step-2 citation in plan.md (grounded 2026-08-01) anchored this
# line as `TIMEOUT_KEY = "timeout"`; the 2026-08-02 schema drift
# renamed it to `request_timeout`; the TOML port must emit the new name.
TIMEOUT_KEY = "request_timeout"  # was "timeout" — renamed 2026-08-02
