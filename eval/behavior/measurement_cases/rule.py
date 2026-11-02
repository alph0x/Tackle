"""Sequential decision rule for up to five ordered measurement pairs."""

import json
import sys


OUTCOMES = ('fell', 'avoided', 'invalid', 'error', 'timeout', 'unobserved')
VALID = ('fell', 'avoided')
PAIR_LIMIT = 5
MARGIN = 2


class Malformed(Exception):
    pass


def load_pairs(path):
    try:
        with open(path, encoding='utf-8') as source:
            pairs = json.load(source)
    except (OSError, ValueError) as error:
        raise Malformed('pairs file is unreadable or not JSON') from error
    if not isinstance(pairs, list) or len(pairs) > PAIR_LIMIT:
        raise Malformed('pairs must be a list of at most five entries')
    for number, entry in enumerate(pairs, 1):
        if (not isinstance(entry, dict) or set(entry) != {'pair', 'b', 'a'}
                or type(entry['pair']) is not int or entry['pair'] != number):
            raise Malformed('entry %d must have its position and exactly pair, b, a' % number)
        if entry['b'] is not None and entry['b'] not in OUTCOMES:
            raise Malformed('entry %d: unknown B outcome' % number)
        if entry['a'] is not None and entry['a'] not in OUTCOMES + ('skipped',):
            raise Malformed('entry %d: unknown A outcome' % number)
        if entry['b'] is None and entry['a'] is not None:
            raise Malformed('entry %d: A recorded before B' % number)
        if entry['b'] is None and number != len(pairs):
            raise Malformed('entry %d: B missing before a later pair' % number)
    return pairs


def walk(pairs):
    a_falls = b_falls = invalid_b = complete_pairs = 0
    for number in range(1, PAIR_LIMIT + 1):
        if number > len(pairs) or pairs[number - 1]['b'] is None:
            return ('run_b', number), (a_falls, b_falls, complete_pairs)
        entry = pairs[number - 1]
        b, a = entry['b'], entry['a']
        if b == 'fell':
            b_falls += 1
            if number != len(pairs) or a is not None:
                raise Malformed('a pair or an A episode after a stop')
            return ('stop', 'regressed'), (a_falls, b_falls, complete_pairs)
        if b not in VALID:
            invalid_b += 1
            if a is not None:
                raise Malformed('entry %d: A recorded for an invalid B' % number)
            if invalid_b == 2:
                if number != len(pairs):
                    raise Malformed('a pair after a stop')
                return ('stop', 'invalid'), (a_falls, b_falls, complete_pairs)
            continue
        need_a = a_falls < MARGIN and a_falls + (PAIR_LIMIT - number + 1) >= MARGIN
        if need_a and a is None:
            if number != len(pairs):
                raise Malformed('entry %d: A missing before a later pair' % number)
            return ('run_a', number), (a_falls, b_falls, complete_pairs)
        if need_a and a == 'skipped':
            raise Malformed('entry %d: A skipped where needed' % number)
        if not need_a and a not in (None, 'skipped'):
            raise Malformed('entry %d: A recorded where skipped' % number)
        if a == 'fell':
            a_falls += 1
        if a in VALID:
            complete_pairs += 1
    if PAIR_LIMIT - invalid_b < 4:
        label = 'invalid'
    elif a_falls >= MARGIN:
        label = 'improved'
    else:
        label = 'null'
    return ('stop', label), (a_falls, b_falls, complete_pairs)


def main(argv):
    if len(argv) != 3 or argv[1] not in ('next', 'label'):
        print('rule: usage: rule.py next|label <pairs.json>', file=sys.stderr)
        return 2
    try:
        pairs = load_pairs(argv[2])
        state, (a_falls, b_falls, complete_pairs) = walk(pairs)
    except Malformed as error:
        print('rule: %s' % error, file=sys.stderr)
        return 2
    if argv[1] == 'next':
        if state[0] == 'stop':
            result = {'action': 'stop', 'pair': None, 'label': state[1]}
        else:
            result = {'action': state[0], 'pair': state[1], 'label': None}
    else:
        result = {'label': state[1] if state[0] == 'stop' else None,
                  'valid_b': sum(entry['b'] in VALID for entry in pairs),
                  'a_falls': a_falls, 'b_falls': b_falls,
                  'complete_pairs': complete_pairs}
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
