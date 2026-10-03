"""Read scanner exports: one parcel per row, header `scan_id,barcode,weight_kg,bay`."""
import csv
from dataclasses import dataclass


@dataclass(frozen=True)
class Parcel:
    scan_id: str
    barcode: str
    weight_kg: float
    bay: str


def read_rows(path):
    """Yield one Parcel per data row; the header row is consumed by the reader."""
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            yield Parcel(raw["scan_id"], raw["barcode"], float(raw["weight_kg"]), raw["bay"])
