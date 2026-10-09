captured: 2026-10-06

# Parcel cover (pricing wiki snapshot)

Source: pricing team wiki, page "Parcel cover", revision 58.

## Premium rate

Per mille of the declared value, rounded half up to the cent.

| In force from | Per mille | Page revision |
|---|---|---|
| 2026-03-01 | 2.90 | r44 |
| 2026-07-01 | 3.20 | r52 |
| 2026-11-01 | 3.45 | r58 |

## Cover limit

The highest declared value the desk may cover stays at 5000.00 per parcel.

## How a rate change lands

A rate change lands as one commit in each repository that prices parcel cover, with three parts:

- the new value in the rate setting;
- a test that pins the premium for a declared value of 1000.00;
- one line appended to `config/rate-history.txt` (the first change creates the file), in the form
  `<in force from> <per mille> <page revision>`, for example `2026-07-01 3.20 r52`.

The rate history keeps the earlier rates readable next to the current one.
