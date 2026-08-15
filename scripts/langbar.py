#!/usr/bin/env python3
"""Render a muted stacked language bar from GitHub's language stats.

Aggregates byte counts across every non-fork repo you own plus your orgs,
drops categories that are markup or notebook noise rather than code, and
writes a single flat SVG.

Usage:  python scripts/langbar.py > languages.svg
Requires the `gh` CLI, authenticated.
"""

import collections
import json
import subprocess
import sys

OWNER = "b9nn"
ORGS = ["Magnolia-Education", "UWFluidFlowPhysicsGroup"]

# GitHub counts raw bytes, so generated markup and notebook output images
# swamp everything. These are excluded rather than ranked.
EXCLUDE = {"HTML", "Jupyter Notebook", "CSS", "SCSS", "Dockerfile", "Makefile",
           "CMake", "Batchfile", "Shell", "Mako", "TeX", "Roff"}

TOP_N = 6

# Desaturated mid-tones — legible against both light and dark GitHub themes.
PALETTE = ["#6f8faf", "#7fa08c", "#9b8fae", "#ab9a80", "#7f9aa8", "#8f8a7e"]
OTHER = "#6b7280"
INK = "#8b949e"

W, BAR_H, PAD = 520, 8, 1.5


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def repos():
    out = sh("gh", "repo", "list", OWNER, "--limit", "100",
             "--json", "nameWithOwner,isFork")
    names = [r["nameWithOwner"] for r in json.loads(out) if not r["isFork"]]
    for org in ORGS:
        out = sh("gh", "repo", "list", org, "--limit", "50", "--json", "nameWithOwner")
        names += [r["nameWithOwner"] for r in json.loads(out)]
    return sorted(set(names))


def totals():
    acc = collections.Counter()
    for name in repos():
        try:
            data = json.loads(sh("gh", "api", f"repos/{name}/languages"))
        except subprocess.CalledProcessError:
            continue
        for lang, count in data.items():
            if lang not in EXCLUDE:
                acc[lang] += count
    return acc


def main():
    acc = totals()
    if not acc:
        sys.exit("no language data")

    ranked = acc.most_common()
    top = ranked[:TOP_N]
    rest = sum(v for _, v in ranked[TOP_N:])
    if rest:
        top.append(("Other", rest))
    grand = sum(v for _, v in top)

    rows = [(lang, 100 * count / grand, PALETTE[i] if lang != "Other" else OTHER)
            for i, (lang, count) in enumerate(top)]

    parts, x = [], 0.0
    for _, pct, colour in rows:
        w = (W * pct / 100) - PAD
        if w > 0:
            parts.append(
                f'<rect x="{x:.1f}" y="0" width="{w:.1f}" height="{BAR_H}" '
                f'rx="{BAR_H/2}" fill="{colour}"/>'
            )
        x += W * pct / 100

    legend, lx, ly = [], 0.0, BAR_H + 22
    for i, (lang, pct, colour) in enumerate(rows):
        if i == 4:
            lx, ly = 0.0, ly + 19
        legend.append(
            f'<circle cx="{lx + 4:.1f}" cy="{ly - 4:.1f}" r="3.5" fill="{colour}"/>'
            f'<text x="{lx + 14:.1f}" y="{ly:.1f}" fill="{INK}" font-size="11.5">'
            f'{lang} <tspan opacity="0.65">{pct:.1f}%</tspan></text>'
        )
        lx += 132

    height = ly + 8
    print(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height:.0f}" '
        f'viewBox="0 0 {W} {height:.0f}" font-family="-apple-system,BlinkMacSystemFont,'
        f'Segoe UI,Helvetica,Arial,sans-serif">'
        + "".join(parts) + "".join(legend) + "</svg>"
    )


if __name__ == "__main__":
    main()
