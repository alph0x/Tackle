"""Flag each planned stop as on time, early or late against its customer's window."""
from dispatch.windows import parse_window


def on_time(arrival, window):
    """arrival: minutes after midnight. window: (start, end) in minutes."""
    start, end = window
    return start <= arrival < end


def flag_stops(stops):
    """stops: dicts with stop, arrival ('HH:MM') and window ('HH:MM-HH:MM').

    Returns (stop, flag) rows; flag is 'on time', 'early', 'late' or 'no window'."""
    rows = []
    for stop in stops:
        window = parse_window(stop['window'])
        if window is None:
            rows.append((stop['stop'], 'no window'))
            continue
        hours, _, minutes = stop['arrival'].partition(':')
        arrival = int(hours) * 60 + int(minutes)
        if on_time(arrival, window):
            rows.append((stop['stop'], 'on time'))
        elif arrival < window[0]:
            rows.append((stop['stop'], 'early'))
        else:
            rows.append((stop['stop'], 'late'))
    return rows
