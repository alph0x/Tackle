"""Blogroll — link helpers for the daily digest."""

import re

PROTOCOLS = ("http://", "https://")


def is_link(url):
    return url.startswith(PROTOCOLS) or url.startswith("//")


def canonical(url):
    url = url.strip()
    if url.startswith("//"):
        return url
    return url.rstrip("/").lower()


def host(url):
    m = re.match(r"^(?:(?:https?:)?//)?([^/]+)", url)
    return m.group(1) if m else ""


def main():
    feed = ["https://a.example/x/", "//b.example/y", "http://c.example/z"]
    for u in feed:
        print(f"{u} -> {canonical(u)}")


if __name__ == "__main__":
    main()
