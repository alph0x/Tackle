RoomBooking tracks meeting-room reservations as `Booking(room, start, end)` objects, where `start` and
`end` are `datetime.date` values. For a monthly usage report, add `occupied_days_in_window(booking: Booking,
window_start: date, window_end: date) -> int` to `roombooking/booking.py`. It should return how many
of the booking's occupied days fall within the reporting window `[window_start, window_end]`: if the
booking starts before the window or ends after it, only the days inside the window count. A booking
that does not overlap the window at all should count as 0 occupied days.
