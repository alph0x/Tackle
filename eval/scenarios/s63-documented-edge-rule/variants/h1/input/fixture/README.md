# RoomBooking

Meeting-room booking utilities.

## Layout

- `roombooking/booking.py` — `Booking(room, start, end)`, `days_occupied(booking)`, and
  `overlaps(a, b)`.
- `roombooking/rooms.py` — a small `Room` registry.

## Running the tests

```sh
python3 -m unittest discover -s tests -v
```

## Date ranges are inclusive

A booking's date range is inclusive on both ends: a booking from 2026-01-10 to 2026-01-12 occupies
the 10th, 11th and 12th — three days, not two. A booking from 2026-01-10 to 2026-01-10 occupies just
that one day, not zero. `days_occupied()` in `roombooking/booking.py` is the reference implementation
of this rule.
