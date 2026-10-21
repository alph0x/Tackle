"""Room list (T-6101)."""


def list_rooms(catalog):
    return sorted(room["name"] for room in catalog)
