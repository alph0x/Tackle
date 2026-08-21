# Retro — learning loop

## Profile candidates (learning loop)

…

### Opt-out anytime

The user can stop evolution at any moment, per scope, with any phrasing. Two modes:

- **Pause**: flip the header to `Evolution: disabled (YYYY-MM-DD)`. Counters are kept; re-enabling resumes them.
- **Purge**: delete the profile file entirely. The next learning opportunity may re-ask for opt-in.

Both take effect immediately.

**The two modes are not interchangeable.** "Stop evolving" names the goal, not the mode: pause is reversible and keeps the learned state; purge is destructive and irreversible. When the phrasing does not name a mode, ask (batch the pause/purge choice with a recommendation — pause is the safe default), and never delete the profile file on an ambiguous request. Any write to the profile is batch-confirmed by the user before it lands — nothing here is ever written silently.
