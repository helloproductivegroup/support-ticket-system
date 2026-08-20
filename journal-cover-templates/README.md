# Trifold traveler's journal covers — V2

Cutting templates for two leather trifold traveler's-notebook covers, sized to
6 × 8 in and 4.25 × 8.25 in inserts, three inserts each.

## What changed from V1

| | V1 | V2 |
|---|---|---|
| Spine holes | one row of 3 at each end (6 total) | **two rows of 3 at each end (12 total)** |
| Elastic hole | 3.0 mm | **2.5 mm**, for 2.5 mm eyelets |
| Closure hole | 4.0 mm | **3.0 mm**, for a 3 mm eyelet |
| Spine width | 22 mm (A5) / 20 mm (passport) | **24 mm on both** — set by the eyelet flange |
| Panels | ISO A5 / TC passport paper | the maker's actual inserts |
| Printing | tiled US Letter *landscape*, seams both ways | **tiled US Letter *portrait*, vertical seams only** |
| PDF | template + scale bar on the same page | **separate instruction and scale-check pages** |

The spine cluster geometry is deliberately identical on both covers, so one
punch-and-set layout serves both books.

## Files

| File | What it's for |
|---|---|
| `a5-cover-v2-mirrored.svg` | **Cricut, leather grain side down** (the usual way). 438 × 212 mm. |
| `a5-cover-v2.svg` | Same pattern un-mirrored, for cutting grain side up. |
| `a6-cover-v2-mirrored.svg` | Cricut, grain side down. 320 × 218 mm. |
| `a6-cover-v2.svg` | Un-mirrored. |
| `a5-cover-v2-letter.pdf` | 5 pages: instructions, scale check, 3 template tiles. |
| `a6-cover-v2-letter.pdf` | 4 pages: instructions, scale check, 2 template tiles. |
| `build_templates_v2.py` | Generates everything above. No dependencies. |

Both SVGs carry a `CUT` layer (outline + 13 holes) and a `FOLD` layer (score
lines). **Set `FOLD` to Pen/Draw or delete it** — left as Cut it slices the
cover into strips.

## Regenerating

Every dimension lives in the two `Cover(...)` blocks near the top of
`build_templates_v2.py`. Change them and re-run:

```
python3 build_templates_v2.py
```

The script prints the full hole schedule and runs clearance checks (flange to
flange, flange to fold line, flange to edge) plus a page-fit check for the
Letter tiling, and reports any that fail.

### The number most likely to need changing

`FLANGE_D` (5.5 mm) is the assumed outside diameter of a set 2.5 mm eyelet.
It, not the hole diameter, drives the column spacing, the row spacing and
therefore the spine width. Measure a set eyelet before cutting the real piece;
if yours is wider, raise `FLANGE_D` and re-run — `COL_GAP`, `ROW_GAP` and
`SPINE_W` need to move with it.
