# Code validation record

Date: 2026-09-10. The subject is this skill's Python plotting code. It does not constitute acceptance
against a user's real data or against every GIS projection.

## Executed

- 35 regression checks pass: explicit breaks and the final upper bound, source values unchanged, valid
  zero, unknown classes and out-of-range rejection, bivariate bins, single map, multi-panel, inset,
  classified and continuous rasters, break histogram, proportional and flow legends, source checksums,
  no overwrite of existing outputs, ellipsoidal distance, true north, rotated rasters, proportional
  symbol area, flow width, cross-CRS extent, SVG and TIFF export, raster edge cells and graticule lines,
  plus outlined SVG export, colour-vision simulation and pair findings, composed-figure effective text
  size, the environment report, and the caption template.
- Added for the reliability fixes: a figure with no colour pair is reported as not applicable instead
  of failing after export, fixed vector and flow colours are covered by the colour-vision check with
  the NoData comparison scoped to the panels that paint it, a bivariate layer with a missing value
  counts it and demands a NoData legend, a strict colour-vision failure leaves no artifact in the
  output directory, `compose_maps.py` honours `min_font_pt` and `svg_outline` from the configuration,
  and a saved configuration replays at a new output stem with relative paths intact.
- Six synthetic configurations were rendered to PNG and PDF: single, series, inset, categorical,
  classified, advanced. No preview images are shipped; re-render them from `assets/examples/` when
  needed.
- The automated checks on the final six reported no small text, missing glyphs, off-canvas text or text
  overlap candidates. PDF physical sizes match the configuration, and the Arial, Arial Bold and SimHei
  fonts found were embedded.
- The single map, multi-panel, locator, categorical and advanced-symbol examples were inspected. The
  first round found crowded labels on a small scale bar, which led to middle-label avoidance; the
  locator example was changed to an extent marker only so a connector line no longer crossed the panel
  text.
- Source SHA-256 values are unchanged before and after rendering; rotated rasters are drawn from their
  real affine corners and windowed reads keep every intersecting edge cell.

## Added after the first validation round

- `cvd_check.py` simulates protan, deutan and tritan deficiency using the Machado, Oliveira and
  Fernandes (2009) severity matrices in linear RGB, measures CIEDE2000 distances between the colours a
  figure actually uses, and reports lightness reversals along continuous ramps. Verified values include
  the severity-0 identity case, a zero distance for identical colours, the expected red-green collapse
  under protanopia, a flagged grass/crop pair (3.23) and forest/built-up pair (5.75), and a deliberately
  non-monotonic greyscale ramp whose reversal is detected at the expected position.
- `export()` gained `svg_outline`, which writes an extra `<stem>.outlined.svg` with glyphs converted to
  paths while the plain SVG keeps live text. Verified that the outlined file contains no `<text>` run and
  that requesting it without `svg` in `formats` is rejected.
- `compose_maps.py` now reports the shrinkage ratio, the effective font and stroke size and the effective
  source DPI of a scaled existing figure, and flags sizes below the legibility limit. Verified with a
  180 mm figure placed 60 mm wide: ratio 1/3, effective fonts 3.0 and 2.67 pt, effective source DPI 900,
  and both a text and a stroke finding.
- `render_map.py` records a `cvd` block in `.qa.json`, writes a fill-in `<stem>.caption.md`, and supports
  `svg_outline`, `cvd_threshold` and `cvd_strict`.
- `check_environment.py` reports required and optional packages separately, so a missing PyMuPDF is
  visible rather than silently downgrading the PDF font-embedding check to `not_checked`.
- `figure_qa.py` gained a command-line entry point for standalone size, PDF and review-packet checks, and
  `caption_template()`.

## Reproduce

With dependencies and fonts present, run `python scripts/test_rendering.py NEW_WORK_DIRECTORY`. It writes
synthetic data, configurations, figures, review packets and `test-results.json`. The directory must be
new so earlier results are never overwritten.

Runnable configurations and their synthetic output are in `assets/examples/`; copy the whole examples
folder into the current task work directory, then run any JSON in it. Configurations write into a
`rendered` subdirectory underneath. Every example is technical validation, not a paper design template
and not a real study area.

## What this does not establish

- No final acceptance has been performed with a user's real data.
- The colour-vision check is a simulation with this skill's working threshold, not a formal
  accessibility audit and not a print proof. No physical proof has been printed.
- Automated layout QA does not judge aesthetic quality and cannot prove that real geographic facts are
  correct.
- Date-line-crossing global data, unusual polar regions and unsupported input formats still need a
  dedicated GIS tool.
- The default A4 review preview assumes a page that is not any particular journal's template.
