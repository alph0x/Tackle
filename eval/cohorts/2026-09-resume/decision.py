"""The report-only decision rule for the `resume` comparison: one function, `resume_summary`, computed
only from this cohort's own tracked records (manifest.json, episodes.jsonl) -- never a scratchpad or an
episode path. This file's own sha256, and price-table.json's, are pinned inside the sealed pilot
manifest's `decision_rule` string at cohort-seal time (a tracked, committed field, covered by the
manifest's own seal_sha256); this script recomputes both hashes at run time and refuses if either has
drifted, so the rule cannot be adjusted after seeing results. The smoke manifest carries no such clause
and this script is never invoked against the smoke directory (its own decision_rule says so).

This decision gates nothing: it prints figures only, never PASS/FAIL or RULE/RECOMMENDATION-shaped, and
carries no tripwire variant -- both held-out variants are pooled into the one comparison's figure
unconditionally, since neither carries a prior finding that would pre-register it out of the pool.

Usage: python3 decision.py [<cohort-dir>]
Exit 0 whenever the one line is printed. Exit 1 only on a refusal (a hash mismatch, a missing seal
clause, a record that fails the protocol checker, or a price this cohort's table does not cover).
<cohort-dir> defaults to this file's own directory; an explicit argument lets a test point it at
synthetic records elsewhere, while this file's own location (never the data directory) is what its
sibling import of protocol-v2's check/verdict modules resolves against.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'protocol-v2'))
import check  # noqa: E402
import verdict  # noqa: E402

NA = 'n/a'
VARIANTS = ('s65-migration-replay', 's66-notice-replay')
BASELINE_ARM = 'method'
CANDIDATE_ARM = 'method:candidate'
# The floor applies per held-out variant, never as a summed total across the two variants: each variant
# needs at least this many valid episodes, for both arms, before any pooled figure is computed.
NMIN = 2
SEAL_CLAUSE = re.compile(r'decision\.py sha256=([0-9a-f]{64}); price-table sha256=([0-9a-f]{64})')
DATED_MODEL = re.compile(r'^(.+)-(\d{8})$')


class Refusal(Exception):
    """Exit 1: nothing that follows can be trusted."""


def sha_file(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as problem:
        raise Refusal('unreadable %s (%s)' % (path, problem.__class__.__name__))


def verify_seal(manifest):
    """Refuse unless the manifest's own decision_rule clause names this exact source and price table."""
    match = SEAL_CLAUSE.search(manifest.get('decision_rule') or '')
    if not match:
        raise Refusal("manifest decision_rule carries no 'decision.py sha256=...; price-table sha256=...' clause")
    decision_hash, price_hash = match.group(1), match.group(2)
    actual_decision = sha_file(Path(__file__).resolve())
    actual_price = sha_file(HERE / 'price-table.json')
    if decision_hash != actual_decision:
        raise Refusal('decision.py sha256 %s does not match the sealed %s' % (actual_decision, decision_hash))
    if price_hash != actual_price:
        raise Refusal('price-table.json sha256 %s does not match the sealed %s' % (actual_price, price_hash))


def base_model_id(model):
    """A served model id with one trailing 8-digit date suffix stripped (a snapshot id such as
    <id>-YYYYMMDD); a bare id is returned unchanged."""
    match = DATED_MODEL.match(model or '')
    return match.group(1) if match else model


def price_of(model, prices):
    """The {input, output} USD-per-million-token prices for a served model id. A model missing from the
    table even after stripping a date suffix refuses -- never guesses a price."""
    if model in prices:
        return prices[model]
    base = base_model_id(model)
    if base in prices:
        return prices[base]
    raise Refusal('no price for model %r' % model)


def episode_dollars(record, prices):
    """The whole episode's dollar cost: per-role when roles[] is populated, else the episode's own
    top-level executor/cost (a plain single-session arm -- every episode in this cohort is one session,
    so roles[] is always empty and this always falls back to the top-level fields). None when a token
    count is unknown ('n/a')."""
    roles = record.get('roles') or []
    parts = roles if roles else [{'model': record['executor']['model'], 'tokens_in': record['cost']['tokens_in'],
                                  'tokens_out': record['cost']['tokens_out']}]
    total = 0.0
    for part in parts:
        tokens_in, tokens_out = part['tokens_in'], part['tokens_out']
        if tokens_in == NA or tokens_out == NA:
            return None
        rates = price_of(part['model'], prices)
        total += tokens_in * rates['input'] / 1e6 + tokens_out * rates['output'] / 1e6
    return total


def median(values):
    values = sorted(values)
    count = len(values)
    middle = count // 2
    return values[middle] if count % 2 else (values[middle - 1] + values[middle]) / 2


def median_or_na(values):
    values = list(values)
    return NA if any(v == NA for v in values) else median(values)


def arm_records(records, scenario_id, arm):
    return [r for r in records if r['scenario_id'] == scenario_id and r['variant_id'] == 'h1' and r['arm'] == arm]


def valid(records):
    return [r for r in records if r['outcome'] in ('fell', 'avoided')]


def variant_counts(records, scenario_id, arm):
    """(fall_count, valid_count) for one held-out variant/arm pair, over its own valid episodes only."""
    v = valid(arm_records(records, scenario_id, arm))
    return sum(r['outcome'] == 'fell' for r in v), len(v)


def variant_arm_counts(records, baseline_arm, candidate_arm):
    """{(variant, arm): (fall_count, valid_count)} over both held-out variants and both arms."""
    return {(variant, arm): variant_counts(records, variant, arm)
           for variant in VARIANTS for arm in (baseline_arm, candidate_arm)}


def completeness(counts):
    """(ok, text): ok is True only when every (variant, arm) pair in `counts` clears NMIN valid episodes
    -- the per-variant floor, never summed (a 3-plus-1 split across the two variants must not silently
    pass just because the total clears an old, single combined threshold). `text` always states which
    case holds, naming exactly what is short when it is not, so the reason is never left implicit."""
    shortfalls = ['%s %s: %d valid (need %d)' % (variant, arm, n, NMIN)
                 for (variant, arm), (_, n) in sorted(counts.items()) if n < NMIN]
    if not shortfalls:
        return True, 'complete (every held-out variant has at least %d valid episodes for both arms)' % NMIN
    return False, 'incomplete (%s)' % '; '.join(shortfalls)


def pooled_fall_rate_difference(counts, baseline_arm, candidate_arm):
    """(point, lower, upper): the fall-rate difference pooled equally over both held-out variants, via
    the same bootstrap resampling and seed `verdict.pooled` always uses. Sign convention: each variant's
    own difference is baseline_fall_rate minus candidate_fall_rate (the same convention
    eval/protocol-v2/check.py's own compare() uses), so a POSITIVE pooled figure means the candidate arm
    (method:candidate) fell less often than the baseline (method); a NEGATIVE figure means the candidate
    arm fell more often. Call this only once `completeness` has confirmed both arms clear the floor in
    both variants; the caller enforces that, this function does not check it again."""
    differences = []
    for variant in VARIANTS:
        k_b, n_b = counts[(variant, baseline_arm)]
        k_c, n_c = counts[(variant, candidate_arm)]
        differences.append(k_b / n_b - k_c / n_c)
    return verdict.pooled(differences)


def resume_pair_records(records, arm):
    return [r for variant in VARIANTS for r in valid(arm_records(records, variant, arm))]


def dollar_median(records, arm, prices):
    """The median per-episode dollar cost over both held-out variants' own valid episodes for one arm,
    or 'n/a' when there are none or a token count is unknown."""
    episodes = resume_pair_records(records, arm)
    if not episodes:
        return NA
    values = [episode_dollars(r, prices) for r in episodes]
    return NA if any(v is None for v in values) else median(values)


def resume_summary(records, prices):
    """The `resume` comparison's own report-only line content (the caller prepends the fixed
    'resume: report-only: ' prefix): baseline_arm 'method', candidate_arm 'method:candidate', pooled over
    both held-out variants together -- neither is pre-registered out of the pool. Never PASS/FAIL or
    RULE/RECOMMENDATION-shaped. States, in order: the pooled fall-rate difference and its bootstrap
    interval (or that it is not computed), each arm's raw fall count per variant, the completeness
    statement, and each arm's median per-episode dollar cost."""
    counts = variant_arm_counts(records, BASELINE_ARM, CANDIDATE_ARM)
    ok, completeness_line = completeness(counts)
    if ok:
        point, lower, upper = pooled_fall_rate_difference(counts, BASELINE_ARM, CANDIDATE_ARM)
        pooled_text = 'pooled fall-rate difference %s [%s,%s]' % (
            verdict.fmt(point), verdict.fmt(lower), verdict.fmt(upper))
    else:
        pooled_text = 'pooled fall-rate difference not computed'
    parts = []
    for variant in VARIANTS:
        k_b, n_b = counts[(variant, BASELINE_ARM)]
        k_c, n_c = counts[(variant, CANDIDATE_ARM)]
        parts.append('%s %s=%d/%d %s=%d/%d' % (variant, BASELINE_ARM, k_b, n_b, CANDIDATE_ARM, k_c, n_c))
    counts_text = 'raw falls ' + '; '.join(parts)
    baseline_dollars = dollar_median(records, BASELINE_ARM, prices)
    candidate_dollars = dollar_median(records, CANDIDATE_ARM, prices)
    dollars_text = 'median episode cost %s=%s %s=%s' % (
        BASELINE_ARM, NA if baseline_dollars == NA else '$%.4f' % baseline_dollars,
        CANDIDATE_ARM, NA if candidate_dollars == NA else '$%.4f' % candidate_dollars)
    return '%s; %s; %s; %s' % (pooled_text, counts_text, completeness_line, dollars_text)


def evaluate(directory):
    """(summary, records, prices): `summary` is the report-only line's content (without the
    'resume: report-only: ' prefix). Raises Refusal when the seal does not match or the records fail the
    protocol checker."""
    manifest = load(directory / 'manifest.json')
    verify_seal(manifest)
    prices = load(HERE / 'price-table.json')['prices']
    report = check.Report()
    context = check.read_manifest(directory, report)
    records = check.read_episodes(directory, context, report) if context is not None else []
    if report.errors or context is None:
        raise Refusal('%s fails the protocol checker (%d error(s))' % (directory, len(report.errors)))
    summary = resume_summary(records, prices)
    return summary, records, prices


def main(argv):
    if len(argv) > 1:
        print('usage: decision.py [<cohort-dir>]', file=sys.stderr)
        return 2
    directory = Path(argv[0]).resolve() if argv else HERE
    try:
        summary, _, _ = evaluate(directory)
    except Refusal as problem:
        print('decision: refused: %s' % problem, file=sys.stderr)
        return 1
    print('resume: report-only: %s' % summary)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
