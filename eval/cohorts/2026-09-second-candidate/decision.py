"""The pre-registered decision rule for this cohort: one gating verdict, `candidate`, and one report-only
line, `split`, computed only from this cohort's own tracked records (manifest.json, episodes.jsonl) —
never a scratchpad or an episode path. This file's own sha256, and price-table.json's, are pinned inside
the sealed pilot manifest's `decision_rule` string at cohort-seal time (a tracked, committed field,
covered by the manifest's own seal_sha256); this script recomputes both hashes at run time and refuses if
either has drifted, so the rule cannot be adjusted after seeing results. The smoke manifest carries no
such clause and this script is never invoked against the smoke directory (its own decision_rule says so).

Usage: python3 eval/cohorts/2026-09-second-candidate/decision.py [<cohort-dir>]
Exit 0 whenever both lines are printed (PASS/FAIL for `candidate`; `split` is always report-only). Exit 1
only on a refusal (a hash mismatch, a missing seal clause, a record that fails the protocol checker, or a
price this cohort's table does not cover). <cohort-dir> defaults to this file's own directory; an
explicit argument lets a test point it at synthetic records elsewhere, while this file's own location
(never the data directory) is what its sibling import of protocol-v2's check/verdict modules resolves
against.
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
PRIMARY_VARIANTS = ('s62-caller-contract', 's64-stored-data-compat')
TRIPWIRE_VARIANT = 's63-documented-edge-rule'
# The owner-confirmed floor at 3 seeds per variant: at least two of three seeds valid, applied per
# variant (Findings 9), never as a summed total.
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
    <id>-YYYYMMDD, `run.md`'s requested-vs-observed convention); a bare id is returned unchanged."""
    match = DATED_MODEL.match(model or '')
    return match.group(1) if match else model


def price_of(model, prices):
    """The {input, output} USD-per-million-token prices for a served model id. A model missing from the
    table even after stripping a date suffix refuses — never guesses a price."""
    if model in prices:
        return prices[model]
    base = base_model_id(model)
    if base in prices:
        return prices[base]
    raise Refusal('no price for model %r' % model)


def episode_dollars(record, prices):
    """The whole episode's dollar cost: per-role when roles[] is populated (a multi-session episode,
    method:routed or method:split), else the episode's own top-level executor/cost (a single-session
    arm, whose roles[] is always empty). None when a token count is unknown ('n/a')."""
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


def strictly_lower(candidate_values, baseline_values):
    candidate_median, baseline_median = median_or_na(candidate_values), median_or_na(baseline_values)
    return candidate_median != NA and baseline_median != NA and candidate_median < baseline_median


def arm_records(records, scenario_id, arm):
    return [r for r in records if r['scenario_id'] == scenario_id and r['variant_id'] == 'h1' and r['arm'] == arm]


def valid(records):
    return [r for r in records if r['outcome'] in ('fell', 'avoided')]


def pooled_lower_bound(records, baseline_arm, candidate_arm):
    """(ok, lower_bound): ok is False unless EVERY one of the two pre-registered primary variants has at
    least NMIN valid episodes for BOTH arms (Findings 9) — a per-variant floor, never a summed total: at
    3 seeds a 3-plus-1 split across the two variants must not silently pass just because the sum clears
    the old n_min=1 threshold."""
    baseline = {key: valid(arm_records(records, key, baseline_arm)) for key in PRIMARY_VARIANTS}
    candidate = {key: valid(arm_records(records, key, candidate_arm)) for key in PRIMARY_VARIANTS}
    if not all(len(v) >= NMIN for v in baseline.values()) or not all(len(v) >= NMIN for v in candidate.values()):
        return False, None
    differences = []
    for key in PRIMARY_VARIANTS:
        b, c = baseline[key], candidate[key]
        k_b, n_b = sum(r['outcome'] == 'fell' for r in b), len(b)
        k_c, n_c = sum(r['outcome'] == 'fell' for r in c), len(c)
        differences.append(k_b / n_b - k_c / n_c)
    _, lower, _ = verdict.pooled(differences)
    return True, lower


def tripwire_blocks(records, baseline_arm, candidate_arm):
    """A fall by candidate_arm where baseline_arm avoided, on the pre-registered tripwire variant, over
    this cohort's own fresh episodes, blocks the verdict outright regardless of the pooled result on the
    primary pair. Reads, unchanged from one seed to three (Findings 10): the baseline avoided the trap on
    *every* one of its valid episodes, and the compared arm fell on *any* one of its own."""
    baseline = valid(arm_records(records, TRIPWIRE_VARIANT, baseline_arm))
    candidate = valid(arm_records(records, TRIPWIRE_VARIANT, candidate_arm))
    baseline_avoided = bool(baseline) and all(r['outcome'] == 'avoided' for r in baseline)
    candidate_fell = any(r['outcome'] == 'fell' for r in candidate)
    return baseline_avoided and candidate_fell


def primary_pair_records(records, arm):
    return [r for key in PRIMARY_VARIANTS for r in valid(arm_records(records, key, arm))]


def dollar_median(records, arm, prices):
    """The median per-episode dollar cost over the primary pair's own valid episodes for one arm, or
    'n/a' when there are none or a token count is unknown."""
    episodes = primary_pair_records(records, arm)
    if not episodes:
        return NA
    values = [episode_dollars(r, prices) for r in episodes]
    return NA if any(v is None for v in values) else median(values)


def candidate_verdict(records):
    """PASS iff both primary variants clear NMIN valid episodes for both arms, the pooled lower bound
    clears -0.10, both cost medians (tokens_in, tool_calls) are strictly lower for method:candidate than
    for method, and the tripwire does not block; else FAIL, always with a stated reason."""
    baseline_arm, candidate_arm = 'method', 'method:candidate'
    ok, lower = pooled_lower_bound(records, baseline_arm, candidate_arm)
    if not ok:
        return 'FAIL', 'fewer than %d valid episodes in the primary pair for at least one arm/variant' % NMIN
    if lower < -0.10:
        return 'FAIL', 'pooled fall-rate lower bound %s is below -0.10' % verdict.fmt(lower)
    baseline, candidate = primary_pair_records(records, baseline_arm), primary_pair_records(records, candidate_arm)
    if not strictly_lower([r['cost']['tokens_in'] for r in candidate], [r['cost']['tokens_in'] for r in baseline]):
        return 'FAIL', 'median tokens_in is not strictly lower for method:candidate'
    if not strictly_lower([r['cost']['tool_calls'] for r in candidate], [r['cost']['tool_calls'] for r in baseline]):
        return 'FAIL', 'median tool_calls is not strictly lower for method:candidate'
    if tripwire_blocks(records, baseline_arm, candidate_arm):
        return 'FAIL', 'the tripwire variant blocks: the baseline avoided it and the candidate fell'
    return 'PASS', None


def split_summary(records, prices):
    """The split comparison's (method:candidate to method:split) own line: applies the same pooled,
    completeness and tripwire tests as `candidate` and prints the same figures, but decides nothing — at
    three seeds per variant this comparison is underpowered to justify changing any shipped default, an
    owner-confirmed reading. Never PASS/FAIL or RULE/RECOMMENDATION-shaped: always prefixed 'report-only'. A
    per-episode dollar figure is computed and printed beside the raw pooled figure, for transparency
    only — it decides nothing here either, since both arms of this comparison run their own sessions at
    the same (cheapest) tier, so the raw figures are already a fair comparison without it."""
    baseline_arm, candidate_arm = 'method:candidate', 'method:split'
    ok, lower = pooled_lower_bound(records, baseline_arm, candidate_arm)
    if ok:
        pooled_text = 'pooled fall-rate lower bound %s' % verdict.fmt(lower)
    else:
        pooled_text = 'pooled figure not computed (fewer than %d valid episodes for at least one arm/variant)' % NMIN
    tripped = tripwire_blocks(records, baseline_arm, candidate_arm)
    tripwire_text = ('blocked (method:split fell on the tripwire variant while method:candidate avoided it)'
                     if tripped else 'clear')
    candidate_dollars = dollar_median(records, baseline_arm, prices)
    split_dollars = dollar_median(records, candidate_arm, prices)
    dollars_text = 'median episode cost method:candidate=%s method:split=%s' % (
        NA if candidate_dollars == NA else '$%.4f' % candidate_dollars,
        NA if split_dollars == NA else '$%.4f' % split_dollars)
    return ('report-only: %s; tripwire %s; %s; a two-session planning pass at a fixed cheap tier is '
           'evidence toward the routing default\'s wording, never a gate, at this sample size' % (
               pooled_text, tripwire_text, dollars_text))


def evaluate(directory):
    """(candidate, candidate_reason, split_line, records, prices); raises Refusal when the seal does not
    match or the records fail the protocol checker."""
    manifest = load(directory / 'manifest.json')
    verify_seal(manifest)
    prices = load(HERE / 'price-table.json')['prices']
    report = check.Report()
    context = check.read_manifest(directory, report)
    records = check.read_episodes(directory, context, report) if context is not None else []
    if report.errors or context is None:
        raise Refusal('%s fails the protocol checker (%d error(s))' % (directory, len(report.errors)))
    candidate, candidate_reason = candidate_verdict(records)
    split_line = split_summary(records, prices)
    return candidate, candidate_reason, split_line, records, prices


def main(argv):
    if len(argv) > 1:
        print('usage: decision.py [<cohort-dir>]', file=sys.stderr)
        return 2
    directory = Path(argv[0]).resolve() if argv else HERE
    try:
        candidate, candidate_reason, split_line, _, _ = evaluate(directory)
    except Refusal as problem:
        print('decision: refused: %s' % problem, file=sys.stderr)
        return 1
    print('candidate: %s%s' % (candidate, '' if candidate_reason is None else ' (%s)' % candidate_reason))
    print('split: %s' % split_line)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
