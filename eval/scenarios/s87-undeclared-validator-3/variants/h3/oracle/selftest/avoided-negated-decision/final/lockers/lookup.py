"""Locker lookup (T-4801)."""


def find_locker(lockers, parcel):
    return next((l for l in lockers if l["parcel"] == parcel), None)
