# Trifold traveler's journal covers — V2

Cutting templates for four leather trifold traveler's-notebook covers. Same
construction throughout: three insert elastics, a flap that folds in over the
stack, closure anchored on the spine.

| Cover | Flat piece | Holds | Spine holes | Paper |
|---|---|---|---|---|
| **A5** | 438 × 212 mm | 3 inserts at 6 × 8 in | 2 rows of 3 per end | 3 Letter tiles |
| **Regular** | 325 × 216 mm | 3 Traveler's Regular inserts, 110 × 210 mm | 2 rows of 3 | 2 Letter tiles |
| **A6** | 312 × 157 mm | 3 inserts at A6, 105 × 148 mm | 2 rows of 3 | 2 Letter tiles, **or 1 Legal sheet** |
| **Passport** | 268 × 132 mm | 3 Traveler's Passport inserts, 89 × 124 mm | **1 row of 3** | **1 Letter sheet, landscape**, or 2 tiles, or 1 Legal sheet |

The Regular panel is 4.5 × 8.5 in — copied from the WANDERINGS Regular cover,
rounded to the nearest half millimetre. The Passport keeps V1's panel and its
single row, on the new 2.5 mm hardware; its flap is 58 mm rather than V1's 62
so the flat piece comes back to 268 mm, which is what lets the whole template
sit on one Letter sheet in landscape.

## What changed from V1

| | V1 | V2 |
|---|---|---|
| Spine holes | one row of 3 at each end (6 total) | **two rows of 3 at each end (12 total)** |
| Elastic hole | 3.0 mm | **2.5 mm**, for 2.5 mm eyelets |
| Closure hole | 4.0 mm | **3.0 mm**, for a 3 mm eyelet |
| Column centres | 6.0 / 5.5 mm | **7.0 mm**, sized by the eyelet flange |
| Spine width | 22 / 20 mm | **24 mm on all four** |
| Printing | tiled US Letter *landscape*, seams both ways | **tiled US Letter *portrait*, vertical seams only** |
| PDF | template + scale bar on the same page | **separate instruction and scale-check pages** |

The column spacing is identical on all four covers, so one punch-and-set layout
serves every book in the lineup — the Passport just uses one row of it per end
instead of two.

## Files

Eight SVGs — for each cover, `<slug>-cover-v2.svg` (outside face up) and
`<slug>-cover-v2-mirrored.svg` (for cutting leather grain side down, which is
what Cricut recommends and therefore usually the one you want).

Seven PDFs:

| File | Pages |
|---|---|
| `a5-cover-v2-letter.pdf` | instructions, scale check, 3 tiles |
| `regular-cover-v2-letter.pdf` | instructions, scale check, 2 tiles |
| `a6-cover-v2-letter.pdf` | instructions, scale check, 2 tiles |
| `passport-cover-v2-letter-single.pdf` | instructions, scale check, **whole template on one landscape sheet** |
| `passport-cover-v2-letter.pdf` | instructions, scale check, 2 tiles |
| `a6-cover-v2-legal.pdf` | instructions, scale check, **whole template on one sheet** |
| `passport-cover-v2-legal.pdf` | instructions, scale check, **whole template on one sheet** |

`guide-v2.pdf` and `guide-v2.html` are the build guide.

Every page within a PDF shares one paper size *and* one orientation, so each
file prints from a single tray without touching the dialog between pages.

The one-sheet landscape edition leaves only 5.7 mm of paper either side of the
piece, so its template page carries a dimension line with a tick at each
extreme edge: both ticks present and 268 mm apart means nothing was clipped and
nothing was scaled. `letter_single` on a `Cover` is computed from `LS_EDGE`,
`LS_TOP` and `LS_FOOT`, so a cover only gets that edition if it genuinely
fits.

Both SVGs per cover carry a `CUT` layer (outline + 13 holes) and a `FOLD` layer
(score lines). **Set `FOLD` to Pen/Draw or delete it** — left as Cut it slices
the cover into strips.

## Regenerating

Every dimension lives in the four `Cover(...)` blocks near the top of
`build_templates_v2.py`. Change them and re-run:

```
python3 build_templates_v2.py
```

It prints the full hole schedule for each cover and runs checks that fail
loudly: eyelet flange to flange, flange to fold line, flange to head edge,
closure to the innermost row, panel to insert, tile width against the printable
area, piece height against the page margins, caption width against the tile
that carries the spine, and — for `legal_single` covers — the rotated fit on a
Legal sheet.

`n_rows` on a `Cover` selects one or two rows of three at each end of the
spine; everything downstream (hole schedule, captions, instruction text,
clearance checks) follows from it.

### The number most likely to need changing

`FLANGE_D` (5.5 mm) is the assumed outside diameter of a set 2.5 mm eyelet.
It, not the hole diameter, drives the column spacing, the row spacing and
therefore the spine width. Measure a set eyelet before cutting the real piece;
if yours is wider, raise `FLANGE_D` and re-run — `COL_GAP`, `ROW_GAP` and
`SPINE_W` need to move with it.
