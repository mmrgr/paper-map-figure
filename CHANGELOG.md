# Changelog

## Unreleased - maintenance

Reliability fixes on the rendering path. No new map type and no change to what the
skill refuses to do.

### Fixed

- **A legal figure could fail at the last step.** `check_entries()` raised on an
  empty colour list, so a configuration carrying only fixed-colour vector or flow
  layers — no `mappings`, no bivariate matrix — raised after the map had already
  been exported. An empty list now reports `applicable: false` instead.
- **A strict colour-vision failure left half a figure behind.** The check ran
  after `export()`, so PNG and PDF existed with no `.qa.json`, `.config.json` or
  `.caption.md`, and the refusal to overwrite then blocked the next attempt. The
  check now runs before anything is written, and every artifact is staged in a
  temporary directory and only moved into place once all checks pass, so a failed
  render leaves the output directory exactly as it was found.
- **Bivariate maps under-reported NoData.** `nodata_count` only looked at the
  plain `column`, which a bivariate layer never sets, so missing values were
  painted with the NoData grey without the required NoData legend. Non-finite
  values are now counted for every column that drives colour — `column`,
  `proportional`, and both bivariate axes — and `+/-inf` counts alongside `NaN`.
- **`compose_maps.py` ignored two keys it accepted.** `svg_outline` was read but
  rejected as an unknown key, and `min_font_pt` was accepted and silently ignored
  in favour of the command-line value. Both now work, the command line still wins
  over the configuration when given, and a non-positive limit is refused instead
  of quietly disabling the legibility check.

### Added

- Fixed vector and flow colours are included in the colour-vision check instead
  of being skipped, and each entry records the panels it is drawn in so the
  NoData grey is only compared with colours in panels that actually paint it. A
  near-grey locator fill is no longer reported as confusable with missing data in
  the main map.
- Declared font chains. SimHei and Arial stay the default and a missing font
  still fails loudly, but `fonts` in the configuration or `GIS_FIGURE_FONT_ZH` /
  `GIS_FIGURE_FONT_EN` can declare an explicit preference order such as
  `Noto Sans CJK SC` or `Liberation Sans`. Every substitution is declared and
  recorded, never inferred.
- `<stem>.config.json` keeps relative layer paths and records `config_root`, and
  `render_map.py config.json --output-stem other/name` moves the output without
  editing the JSON, so a saved configuration replays instead of being pinned to
  one machine.
- `svg_outline` without `svg` in `formats` is refused before rendering instead of
  during export, and a legend naming an unknown mapping now reports it.
- A GitHub Actions workflow running `test_rendering.py` on push and pull request.

### Changed

- `cvd_check.report()` gained `applicable` and `checked_colors` so "nothing to
  simulate" is distinguishable from "no finding". `check_entries([])` returns two
  empty lists instead of raising; the threshold argument is still validated.

## 1.0.0 - 2026-09-10

First public release. English edition of the skill, with the gaps found in the internal audit closed.

### Added

- `scripts/cvd_check.py`: colour-vision simulation using the Machado, Oliveira and Fernandes (2009)
  severity matrices in linear RGB, converted to CIELAB and measured with CIEDE2000. Compares every
  combination of unordered classes, neighbouring classified bins and bivariate neighbours, compares
  NoData against every data colour, and checks continuous ramps for lightness reversals. Usable on an
  explicit palette or on a whole `render_map.py` configuration, with an optional side-by-side swatch
  image.
- `svg_outline` in `export()` and in the render configuration: writes an additional
  `<stem>.outlined.svg` with glyphs converted to paths, for viewers that cannot resolve SimHei or Arial,
  while the plain SVG keeps live editable text.
- A caption specification (SKILL.md section 5.6) plus `<stem>.caption.md` and
  `figure_qa.caption_template()`, which turn the recording requirements scattered through the document
  into a fill-in table.
- `compose_maps.py` now reports the shrinkage ratio, effective font size, effective stroke width and
  effective source DPI of a scaled existing figure, and flags anything below the legibility limit.
- Print colour guidance (CMYK risks, out-of-gamut clipping, proofing) and a per-item acceptance check
  table in SKILL.md section 9.
- `render_map.py` configuration keys `svg_outline`, `cvd_threshold` and `cvd_strict`; the colour-vision
  report is recorded under `cvd` in `.qa.json`.
- A command-line entry point for `figure_qa.py`, so size, PDF and review-packet checks can run on any
  exported figure.
- `check_environment.py` reports required and optional packages separately and lists which checks a
  missing optional package disables.
- `README.md`, `CHANGELOG.md`, `LICENSE`, `.gitignore`, `.gitattributes`, and `version`, `author`,
  `license` and `metadata` in the skill frontmatter.

### Changed

- Documentation and all in-script messages translated from the Chinese first draft to English.
- Example class labels changed to English (`Forest`, `Crop`, `Water`).
- The automated layout `findings` list stays limited to layout and export problems; colour-vision
  results are reported separately under `cvd`, so existing automation keeps its meaning.

### Verified

- 30 regression checks pass (previously 24): the new ones cover outlined SVG export, colour-vision
  simulation and pair findings, the CVD report shape, composed-figure effective text and stroke size, the
  environment report and the caption template.
- The six synthetic configurations all render to PNG and PDF with no automated findings.
