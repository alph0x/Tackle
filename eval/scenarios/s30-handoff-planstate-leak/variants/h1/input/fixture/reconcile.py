"""Reconcile the old and new customer exports into one clean file.

Exact and normalized-account matches are handled; the case where the same person appears under two
different account numbers across the two files is not yet handled.
"""
import csv


def load(path: str) -> list:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def normalize_account(account: str) -> str:
    return account.strip().split("-")[0]


def normalize_name(name: str) -> str:
    return name.strip().lower()
