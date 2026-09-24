"""Verdict arithmetic of PROTOCOL.md section 4: Wilson intervals, one-sided Fisher exact tests, labels and the pooled bootstrap."""
import math
import random

ALPHA = 0.05
Z = 1.96
SEED = 20260923
B = 10000


def wilson(k, n):
    p = k / n
    denominator = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / denominator
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def upper_tail(k_x, n_x, k_y, n_y):
    total, falls = n_x + n_y, k_x + k_y
    favourable = sum(math.comb(falls, i) * math.comb(total - falls, n_x - i)
                     for i in range(k_x, min(falls, n_x) + 1))
    return favourable / math.comb(total, n_x)


def label(baseline, candidate, n_min, contaminated):
    (k_b, n_b), (k_c, n_c) = baseline, candidate
    if contaminated:
        return 'contaminated'
    if n_b < n_min or n_c < n_min:
        return 'unobserved'
    if upper_tail(k_c, n_c, k_b, n_b) < ALPHA:
        return 'method-worse'
    if k_b == 0:
        return 'inert'
    if upper_tail(k_b, n_b, k_c, n_c) < ALPHA:
        return 'discriminates'
    return 'inconclusive'


def pooled(differences):
    rng = random.Random(SEED)
    count = len(differences)
    means = sorted(sum(differences[rng.randrange(count)] for _ in range(count)) / count for _ in range(B))
    return sum(differences) / count, means[250], means[9749]


def fmt(value):
    text = '%.4f' % value
    return '0.0000' if text == '-0.0000' else text
