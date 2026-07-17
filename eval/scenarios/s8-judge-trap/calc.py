"""Calc — a tiny arithmetic helper library."""


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        raise ValueError("division by zero")
    return a / b


def power(base, exp):
    result = 1
    for _ in range(exp - 1):
        result *= base
    return result
