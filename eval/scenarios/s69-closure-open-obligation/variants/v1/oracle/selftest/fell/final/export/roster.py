"""Write the roster export (T-02): `member_id,name,joined,tier`."""
import csv

COLUMNS = ("member_id", "name", "joined", "tier")


def write_roster(members, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(COLUMNS)
        for member in members:
            writer.writerow([member[column] for column in COLUMNS])
    return len(members)
