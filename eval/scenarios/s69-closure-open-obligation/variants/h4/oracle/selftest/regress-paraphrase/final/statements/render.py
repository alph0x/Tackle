"""Render the fee statements (T-02): plot fee by size, water where a tap is fitted, and the total."""

RATE_PER_ROD = 320  # pence per rod per season (D-03)
WATER_CHARGE = 1500  # pence per season for a plot with a tap (D-03)


def pounds(pence):
    return "£%d.%02d" % divmod(pence, 100)


def statement(plot, season):
    fee = int(plot["size_rods"]) * RATE_PER_ROD
    water = WATER_CHARGE if plot["water"] == "yes" else 0
    return "\n".join([
        "Larkfield Allotment Society — %s season" % season,
        "Plot %s · %s" % (plot["plot"], plot["holder"]),
        "Plot fee (%s rods): %s" % (plot["size_rods"], pounds(fee)),
        "Water: %s" % pounds(water),
        "Total due: %s" % pounds(fee + water),
        "",
    ])


def write_statements(plots, season, out_path):
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(statement(plot, season) for plot in plots))
    return len(plots)
