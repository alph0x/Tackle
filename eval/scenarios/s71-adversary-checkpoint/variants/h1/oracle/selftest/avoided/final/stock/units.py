"""Convert journal quantities to single units."""


def to_units(qty, uom, pack):
    """qty as journalled; uom is 'case' or 'each'; pack is units per case for the item."""
    if uom == 'case':
        return int(qty) * pack
    if uom == 'each':
        return int(qty)
    raise ValueError('unknown unit of measure: %s' % uom)
