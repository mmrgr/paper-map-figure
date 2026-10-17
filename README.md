# paper-map-figure

A skill for turning **existing** GIS and remote-sensing results into final, publication-ready paper
figures: typesetting, beautification and export, plus visual review of maps you already have.

It owns the canvas, map viewport, frame, fonts, colour, legends, scale bars, north arrows and the
layout of single maps, multi-panel figures and main-map-plus-inset figures. It does **not** run
remote-sensing retrieval, classification training, SDM, interpolation, buffering, overlay statistics or
any other analysis, and it never recomputes results, thresholds or class breaks to look better.

## What it protects

Every mode preserves the real geographic objects, the real raster values and attributes, the confirmed
numeric-to-colour mapping, and the true distance, direction and inset relationships. Generative
redrawing, smoothing or repairing of the map body is forbidden: AI may only propose style and layout
parameters, and the real map is always rendered by a deterministic GIS or plotting tool.

## Three modes

| Mode | When | Deliverable |
|---|---|---|
| Code | Accurate output, batch consistency, or an existing project | Figures plus reproducible code/config |
| AI Review | An assessment is wanted, or only a screenshot exists | An actionable fix list, no redraw |
| Hybrid | A figure is wanted and then iterated, with redrawable material | Deterministic render, visual review, style edits, re-render |

## Install

This repository is the skill directory itself: `SKILL.md` sits at the root, next to `scripts/`,
`references/` and `assets/`.

```bash
git clone https://github.com/mmrgr/paper-map-figure.git
cp -r paper-map-figure ~/.workbuddy/skills/paper-map-figure
```

Keep the folder name `paper-map-figure` so the skill name in `SKILL.md` stays consistent.

Dependencies are recorded, not installed, in [scripts/requirements.txt](scripts/requirements.txt):

```
matplotlib==3.10.9  numpy==2.2.6  Pillow==12.2.0
geopandas==1.1.4  rasterio==1.4.4  pyproj==3.7.1  shapely==2.1.2
PyMuPDF==1.27.2.3   # optional: PDF size and font-embedding verification
```

PyMuPDF and affine are optional. Without PyMuPDF the PDF checks report `not_checked` rather than passing
silently. SimHei and Arial must be installed; the code reports them missing rather than substituting
another font.

```bash
python scripts/check_environment.py
```

## Quick start

```bash
# 1. Copy the synthetic examples to a work directory and render one
cp -r assets/examples /tmp/figure-work
cd /tmp/figure-work
python /path/to/scripts/render_map.py single.json

# 2. Or compose existing map images without any geospatial reconstruction
python /path/to/scripts/compose_maps.py compose.json

# 3. Check colour-vision behaviour of a palette or a whole configuration
python /path/to/scripts/cvd_check.py --config single.json
python /path/to/scripts/cvd_check.py --colors "#287A45,#A6C96A,#E6C65B" --labels forest,grass,crop

# 4. Standalone export checks
python /path/to/scripts/figure_qa.py rendered/single.png --width-mm 180 --height-mm 140 --pdf rendered/single.pdf
```

Each render writes, next to the figure:

- `<stem>.png`, `.pdf` (and `.svg`, `.tiff` if requested)
- `<stem>.qa.json` — findings, layer records, source SHA-256 values, versions, the colour-vision report
- `<stem>.config.json` — the resolved configuration, replayable as-is
- `<stem>.caption.md` — a fill-in caption covering every field the figure must declare
- `<stem>.review/` — page preview, grayscale copy and the visual-review prompt

Set `svg_outline: true` to also write `<stem>.outlined.svg` with glyphs as paths (it needs `svg` in
`formats`), and `cvd_strict: true` to fail the render when a colour pair breaches the colour-vision
threshold.

Outputs are staged and only committed once every check passes, so a failed render leaves no
half-written figure to block the next attempt:

```bash
# Replay a saved configuration somewhere else, without editing the JSON
python /path/to/scripts/render_map.py single.config.json --output-stem copy
```

SimHei and Arial must be installed; the code reports them missing rather than substituting another
font. On a machine that has neither, declare the substitution explicitly instead of inheriting one —
`"fonts": {"zh": ["Noto Sans CJK SC"], "en": ["Liberation Sans"]}` in the configuration, or the
environment variables `GIS_FIGURE_FONT_ZH` / `GIS_FIGURE_FONT_EN`. The first installed name wins, a
chain where nothing is installed still fails, and the font actually used is recorded in `.qa.json`.

## Layout

```
SKILL.md                     the skill: scope, three modes, and every production rule
scripts/
  check_environment.py       read-only environment and font check
  render_map.py              JSON-driven figure rendering
  batch_render.py            render several configurations
  figure_layout.py           millimetre canvas, panels, mixed SimHei/Arial runs, export
  map_styles.py              continuous, diverging, classified, categorical, bivariate mappings
  geo_layers.py              read-only GeoTIFF, vector, flow and proportional-symbol layers
  geo_elements.py            scale bars, true north, extent links, graticule
  figure_qa.py               export checks and the caption template
  cvd_check.py               colour-vision simulation and CIEDE2000 findings
  color_diagnostics.py       histogram of existing breaks
  compose_maps.py            compose existing images, with effective text size
  page_preview.py            paper-size placement preview
  demo_gallery.py            synthetic fixtures and runnable configs
  test_rendering.py          regression tests
references/
  code-resources.md          configuration reference and upstream implementations read
  color-guide.md             colour decisions and palettes
  professional-color-resources.md   index of six professional colour sources
  validation.md              what was executed, and what it does not prove
assets/examples/             six runnable SYNTHETIC configurations and their data
```

## Verified

35 regression checks pass and all six synthetic configurations render. See
[references/validation.md](references/validation.md) for exactly what was executed and, equally
importantly, what it does not establish. The examples are technical fixtures, marked SYNTHETIC TEST, and
are not real geography or a paper design template.

`.github/workflows/test.yml` runs the suite on every push and pull request.

## Scope boundaries

The backend requires the raster CRS to match the panel CRS and never reprojects, resamples or converts
source values behind the scenes. Date-line-crossing global data, unusual polar projections, NetCDF,
multi-band true colour and display reprojection of existing rasters belong in a dedicated GIS tool
first. Scale bars are local by nature where the projection distorts distance.

## License

MIT. See [LICENSE](LICENSE).

Third-party projects read while designing this one, and the design ideas taken from each, are credited in
[references/code-resources.md](references/code-resources.md). No upstream source is bundled.
