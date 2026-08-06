# Output formatting (P-port-output): plain-text done; JSON + table pending.
def render(data: dict, fmt: str) -> str:
    if fmt == "plain":
        return "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    raise NotImplementedError(fmt)
