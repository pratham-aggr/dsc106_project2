"""
reproduce_analysis.py
=====================
Computes every number used in viz1_disparity_ratio.html and viz2_decade_trend.html
directly from the raw ProPublica CCRB dataset.

Usage
-----
  python reproduce_analysis.py

Input
-----
  allegations_202007271729.csv  (place in same directory, or edit CSV_PATH below)

Output
------
  Prints all numbers to stdout.
  Writes viz1_data.json and viz2_data.json for reference.

Dependencies
------------
  pip install pandas
"""

import json
import pandas as pd

CSV_PATH = "allegations_202007271729.csv"

# ── NYC population shares (ACS 2015 5-year estimates, NYC Dept. of City Planning)
NYC_POP = {
    "Black":    24.3,
    "Hispanic": 28.9,
    "White":    32.1,
    "Asian":    13.9,
}

KNOWN_GROUPS = ["Black", "Hispanic", "White", "Asian"]

# ─────────────────────────────────────────────────────────────────────────────
# Load
# ─────────────────────────────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df):,} rows × {len(df.columns)} columns")
print(f"Years: {df['year_received'].min()} – {df['year_received'].max()}")
print(f"Null complainant_ethnicity: {df['complainant_ethnicity'].isna().sum():,}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 1 — Disparity Ratio
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("VIZ 1: DISPARITY RATIO BY RACE")
print("=" * 60)

# Keep only rows with a recognised complainant ethnicity
valid_eth = ["Black", "Hispanic", "White", "Asian", "American Indian", "Other Race"]
v1 = df[df["complainant_ethnicity"].isin(valid_eth)].copy()
print(f"Rows with known ethnicity: {len(v1):,}  (excluded {len(df)-len(v1):,} Unknown/Refused/null)")

complaint_shares = v1["complainant_ethnicity"].value_counts(normalize=True) * 100
print("\nComplaint shares (all known groups):")
print(complaint_shares.round(2).to_string())

viz1_data = []
print("\nDisparity ratios (KNOWN groups only, matched to NYC pop):")
for grp in KNOWN_GROUPS:
    c = round(complaint_shares.get(grp, 0), 1)
    p = NYC_POP[grp]
    r = round(c / p, 2)
    print(f"  {grp:<12} complaint={c:5.1f}%  pop={p:4.1f}%  ratio={r:.2f}x")
    viz1_data.append({"group": grp, "complaint_pct": c, "pop_pct": p, "ratio": r})

with open("viz1_data.json", "w") as f:
    json.dump(viz1_data, f, indent=2)
print("\nWrote viz1_data.json")

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 2 — 5-Period Trend (2001–2019)
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("VIZ 2: COMPLAINT SHARE TREND 2001–2019")
print("=" * 60)

# Pre-1996: ethnicity is entirely null → drop.
# 1996-2000: sparse (< 300/yr with ethnicity data) → drop.
# 2020: only 4 rows → drop.
v2 = df[
    df["complainant_ethnicity"].isin(KNOWN_GROUPS) &
    (df["year_received"] >= 2001) &
    (df["year_received"] <= 2019)
].copy()

print(f"Rows used: {len(v2):,}  (2001–2019, known ethnicity, 4 main groups)")

bins   = [2000, 2004, 2008, 2012, 2016, 2019]
labels = ["2001–04", "2005–08", "2009–12", "2013–16", "2017–19"]
v2["period"] = pd.cut(v2["year_received"], bins=bins, labels=labels)

pivot = (
    v2.groupby(["period", "complainant_ethnicity"], observed=True)
    .size()
    .unstack(fill_value=0)
)
pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

print("\nPeriod complaint share (%):")
print(pct[KNOWN_GROUPS].round(1).to_string())
print("\nPeriod totals (n):")
print(pivot.sum(axis=1).to_string())

viz2_data = {
    "periods": labels,
    "series": {}
}
for grp in KNOWN_GROUPS:
    viz2_data["series"][grp] = [round(float(pct.loc[p, grp]), 1) for p in labels]

with open("viz2_data.json", "w") as f:
    json.dump(viz2_data, f, indent=2)
print("\nWrote viz2_data.json")

# ─────────────────────────────────────────────────────────────────────────────
# Sanity checks
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("SANITY CHECKS")
print("=" * 60)
print(f"VIZ 1 complaint shares sum: {sum(d['complaint_pct'] for d in viz1_data):.1f}%  (excludes Other/AmerIndian)")
for p in labels:
    row_sum = sum(viz2_data["series"][g][labels.index(p)] for g in KNOWN_GROUPS)
    print(f"VIZ 2 period {p} shares sum: {row_sum:.1f}%  (excludes Other/AmerIndian)")
