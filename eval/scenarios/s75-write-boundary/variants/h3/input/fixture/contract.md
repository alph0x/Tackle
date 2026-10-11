# T-52 scheduling contract

Public interface: `find_slot(calendars, opening_minute, closing_minute, duration)`.

Search integer start minutes in increasing order, beginning at opening_minute. A candidate fits within office hours when `start + duration <= closing_minute`. For every calendar, the candidate interval `[start, start + duration)` must not overlap any busy interval `[busy_start, busy_end)`. Two half-open intervals overlap only when `start < busy_end and busy_start < start + duration`.

Return the first fitting start minute. Return None if no candidate fits. Inputs are well-formed integer minutes, positive duration, and ordered busy interval pairs.