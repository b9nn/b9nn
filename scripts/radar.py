#!/usr/bin/env python3
"""Render GitHub's four-axis "Activity overview" radar as a standalone SVG.

Same data GitHub puts on the profile page — the split across commits, code
review, issues and pull requests — drawn to match the muted palette used by
the other cards.

Usage:  python scripts/radar.py > radar.svg
Requires the `gh` CLI, authenticated.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from activitybar import totals  # noqa: E402

ACCENT = "#6f8faf"
AXIS = "#8b949e"
INK = "#8b949e"

R = 74                      # axis half-length
CX, CY = 210, 118           # centre
W, H = 420, 236

# (label, key, unit-vector) — matches GitHub's own axis order.
AXES = [
    ("code review", "code review", (0, -1)),
    ("issues", "issues", (1, 0)),
    ("pull requests", "pull requests", (0, 1)),
    ("commits", "commits", (-1, 0)),
]


def main():
    acc, _ = totals()
    grand = sum(acc.values())
    if not grand:
        sys.exit("no contribution data")

    pct = {k: 100 * v / grand for k, v in acc.items()}
    peak = max(pct.values()) or 1

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="-apple-system,BlinkMacSystemFont,'
        f'Segoe UI,Helvetica,Arial,sans-serif">'
    ]

    # axis spokes
    for _, _, (dx, dy) in AXES:
        out.append(
            f'<line x1="{CX}" y1="{CY}" x2="{CX + dx * R}" y2="{CY + dy * R}" '
            f'stroke="{AXIS}" stroke-width="1" opacity="0.35"/>'
        )

    # the kite
    pts = []
    for _, key, (dx, dy) in AXES:
        r = R * (pct[key] / peak)
        pts.append((CX + dx * r, CY + dy * r))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    out.append(
        f'<polygon points="{poly}" fill="{ACCENT}" fill-opacity="0.28" '
        f'stroke="{ACCENT}" stroke-width="1.5" stroke-linejoin="round"/>'
    )
    for x, y in pts:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{ACCENT}"/>')

    # labels, pushed clear of each axis end
    for label, key, (dx, dy) in AXES:
        lx, ly = CX + dx * (R + 16), CY + dy * (R + 16)
        anchor = "middle" if dx == 0 else ("start" if dx > 0 else "end")
        base = ly + (4 if dy == 0 else (-6 if dy < 0 else 14))
        out.append(
            f'<text x="{lx:.0f}" y="{base - 13:.0f}" text-anchor="{anchor}" '
            f'fill="{INK}" font-size="12">{pct[key]:.0f}%</text>'
            f'<text x="{lx:.0f}" y="{base:.0f}" text-anchor="{anchor}" '
            f'fill="{INK}" font-size="11.5" opacity="0.7">{label}</text>'
        )

    out.append("</svg>")
    print("".join(out))


if __name__ == "__main__":
    main()
