def reading_order(regions):
    """Approximate rows by top-edge proximity, then read each row right to left.

    This is intentionally not a panel-layout model. Tall boxes cannot bridge rows.
    """
    rows = []
    for region in sorted(regions, key=lambda r: (r["bbox"][1], -r["bbox"][0])):
        x, y, w, h = region["bbox"]
        row = next((row for row in rows
                    if abs(y - row[0]["bbox"][1]) <=
                    0.35 * min(h, row[0]["bbox"][3])), None)
        if row is None:
            rows.append([region])
        else:
            row.append(region)
    return [r for row in rows for r in sorted(row, key=lambda r: -r["bbox"][0])]
