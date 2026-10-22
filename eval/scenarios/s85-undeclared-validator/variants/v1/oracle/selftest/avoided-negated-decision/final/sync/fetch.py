"""Feed fetch (T-3201)."""


def fetch_feed(url, opener):
    with opener(url) as response:
        return response.read().decode("utf-8")
