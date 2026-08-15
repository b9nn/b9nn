#!/usr/bin/env python3
"""Render a muted stacked bar of contribution activity by type.

Pulls GitHub's own contributionsCollection totals for every year since the
account was created and renders the split across commits, pull requests,
code review and issues.

Usage:  python scripts/activitybar.py > activity.svg
Requires the `gh` CLI, authenticated.
"""

import datetime as dt
import json
import subprocess
import sys

USER = "b9nn"

# Matches scripts/langbar.py — desaturated mid-tones, legible on either theme.
PALETTE = ["#6f8faf", "#7fa08c", "#9b8fae", "#ab9a80"]
INK = "#8b949e"

W, BAR_H, PAD = 520, 8, 1.5

FIELDS = [
    ("commits", "totalCommitContributions"),
    ("pull requests", "totalPullRequestContributions"),
    ("code review", "totalPullRequestReviewContributions"),
    ("issues", "totalIssueContributions"),
]


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def created_year():
    out = sh("gh", "api", f"users/{USER}", "--jq", ".created_at")
    return int(out.strip()[:4])


def totals():
    """Sum contribution counts year by year — the API caps each query at 1 year."""
    acc = {name: 0 for name, _ in FIELDS}
    private = 0
    this_year = dt.date.today().year
    for year in range(created_year(), this_year + 1):
        start = f"{year}-01-01T00:00:00Z"
        end = f"{year}-12-31T23:59:59Z"
        query = f"""
        {{ user(login: "{USER}") {{
             contributionsCollection(from: "{start}", to: "{end}") {{
               totalCommitContributions
               totalPullRequestContributions
               totalPullRequestReviewContributions
               totalIssueContributions
               restrictedContributionsCount
             }} }} }}"""
        data = json.loads(sh("gh", "api", "graphql", "-f", f"query={query}"))
        block = data["data"]["user"]["contributionsCollection"]
        for name, key in FIELDS:
            acc[name] += block[key]
        private += block["restrictedContributionsCount"]
    return acc, private


def main():
    acc, private = totals()
    grand = sum(acc.values())
    if not grand:
        sys.exit("no contribution data")

    rows = [(name, 100 * acc[name] / grand, PALETTE[i])
            for i, (name, _) in enumerate(FIELDS) if acc[name]]

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
    for i, (name, pct, colour) in enumerate(rows):
        if i == 3:
            lx, ly = 0.0, ly + 19
        legend.append(
            f'<circle cx="{lx + 4:.1f}" cy="{ly - 4:.1f}" r="3.5" fill="{colour}"/>'
            f'<text x="{lx + 14:.1f}" y="{ly:.1f}" fill="{INK}" font-size="11.5">'
            f'{name} <tspan opacity="0.65">{pct:.1f}%</tspan></text>'
        )
        lx += 132

    if private:
        ly += 19
        legend.append(
            f'<text x="0" y="{ly:.1f}" fill="{INK}" font-size="11" opacity="0.65">'
            f'+{private:,} contributions in private repositories</text>'
        )

    height = ly + 8
    print(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height:.0f}" '
        f'viewBox="0 0 {W} {height:.0f}" font-family="-apple-system,BlinkMacSystemFont,'
        f'Segoe UI,Helvetica,Arial,sans-serif">'
        + "".join(parts) + "".join(legend) + "</svg>"
    )


if __name__ == "__main__":
    main()
