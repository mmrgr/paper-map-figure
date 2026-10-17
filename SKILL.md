---
name: paper-map-figure
description: Turn existing GIS or remote-sensing results into final, publication-ready paper figures — typeset, beautify and export maps, or review the visual quality of maps you already have. Covers figure frames and margins, physical size, colour, legends, scale bars, north arrows, single maps, multi-panel layouts and main-map-plus-inset. Supports Code, AI Review and Hybrid modes. Only produces the final figure; it does not run remote-sensing analysis, SDM modelling or spatial analysis.
version: 1.0.0
author: YuTong Chen
license: MIT
metadata:
  version: "1.0.0"
  tags: [gis, remote-sensing, cartography, publication-figure, colour-vision, qgis, matplotlib]
  requires:
    python: ["matplotlib", "numpy", "Pillow", "geopandas", "rasterio", "pyproj", "shapely"]
  optional:
    python: ["PyMuPDF", "affine"]
---

# Publication figures for GIS and remote sensing

Turn **existing, already-confirmed geographic results** into clear, coherent and reproducible
paper figures. Beautification should improve reading; it must not change the research conclusion
or the spatial facts.

## 1. Scope and what must not change

This skill owns the canvas, the map viewport, the figure frame, fonts, colour, legends, scale bars
and north arrows, and the layout and export of single maps, multi-panel figures and main-map-plus-
inset figures.

It does not perform remote-sensing retrieval, classification training, SDM, interpolation,
buffering, overlay statistics, spatial tests or any other analysis, and it never recomputes
indicators, class breaks or results to look better. When an upstream problem is found, name the
missing input, then continue with the parts of the layout work that stand on their own.

**Every mode must preserve:**

- The real geographic objects, their true positions, shapes and topology; real raster values,
  sample points, attributes, units, time steps and category meanings.
- The confirmed numeric-to-colour mapping: ranges, class breaks, midpoints, transforms and the
  meaning of NoData. Changing a colour ramp is not a licence to change any of these.
- The distance relationship of the scale bar, the directional meaning of the north arrow, and the
  true correspondence between an inset and the main map.

Generative redrawing, repairing, smoothing or moving the map body to remove "clutter" is forbidden;
so is deleting anomalous high or low values, moving sample points, editing boundaries, inventing
water bodies or roads, or altering legend values. AI may only suggest or adjust **style and layout
parameters**; the real map must be rendered by GIS or deterministic plotting tools.

The coordinate-to-canvas transforms, layer display, viewport clipping and scale-bar calibration that
cartography requires are rendering, not spatial analysis. Clip the display viewport only; never
modify source data and never crop away a region the conclusion depends on. Keep the confirmed CRS;
never silently guess a CRS or reproject analysis data. When a display reprojection is needed, use an
explicit source and target CRS and record it; if it cannot be handled reliably, ask for a
georeferenced map or project instead.

## 2. Inputs and default decisions

Prefer the user's existing data, map project, plotting code or exported figure, plus the required
dimensions and journal rules. Ask only about gaps that affect correctness; when the available
information is sufficient, produce a first version.

Record before drawing:

| Input | Purpose | If missing |
|---|---|---|
| Existing results, variable or classes, units, period | Determines what the map expresses | Never guess what values mean; review the layout instead |
| CRS, map extent, orientation information | Verifies the scale bar, orientation and placement | Do not add a scale bar or north arrow that cannot be verified |
| Colour limits, classes, NoData | Preserves semantics and cross-panel comparability | Read from a trusted project or code; otherwise list the value mapping as unconfirmed |
| Final physical size and file format | Determines legibility after reduction | Use the draft sizes below and state that they are provisional |
| Panel meaning and reading order | Chooses the layout and shared legends | Follow the user's order; never reorder research results |

With only flat images such as PNG or JPEG, AI Review and whole-figure layout work that does not
change map content are possible; the true CRS, distances and complete values cannot be recovered
from a screenshot. To recolour a thematic map, rebuild a numeric legend or change map elements, ask
for the source project or data first. Never pass generative image editing off as a reproducible
redraw.

## 3. The three modes

| Mode | When it applies | Work and deliverables |
|---|---|---|
| Code | Accurate output, batch consistency, or an existing project or code base | Implement style parameters in GIS or code; deliver figures, code or project, and configuration |
| AI Review | The user wants an assessment, or only a screenshot exists | Visual review with an actionable fix list; no automatic redraw, no claim of verified geographic accuracy |
| Hybrid | The user wants a figure made and then iterated, and redrawable material exists | Deterministic render, AI visual review, edit the style configuration, render and verify again |

Follow the user's chosen mode. If none is given: with redrawable material and a request to beautify,
default to Hybrid; for a direct batch of usable output use Code; with only images use AI Review.

### Code

Run [check_environment.py](scripts/check_environment.py) first to check dependencies and fonts. With
ready projected raster or vector results, use [render_map.py](scripts/render_map.py) to draw the real
layers, colour legends, scale bar, true north, main map and inset from an explicit configuration, and
[batch_render.py](scripts/batch_render.py) for several configurations. Supported options and the
upstream sources that were read are in [plotting code](references/code-resources.md).

An existing plotting project may reuse [figure_layout.py](scripts/figure_layout.py),
[geo_layers.py](scripts/geo_layers.py), [geo_elements.py](scripts/geo_elements.py) and
[map_styles.py](scripts/map_styles.py) as needed; migration is never forced. With only flat images,
use [compose_maps.py](scripts/compose_maps.py), and do not infer real values or re-map thematic
colours.

After export, use [figure_qa.py](scripts/figure_qa.py) to record verifiable problems and provenance,
and [page_preview.py](scripts/page_preview.py) to generate a preview at the real physical size, then
run the section 8 AI image review. [color_diagnostics.py](scripts/color_diagnostics.py) draws a
histogram of existing breaks; [cvd_check.py](scripts/cvd_check.py) simulates colour-vision
deficiencies on the colours the figure actually uses. [demo_gallery.py](scripts/demo_gallery.py) and
[test_rendering.py](scripts/test_rendering.py) only generate synthetic test data and are never
delivered as real maps.

Each render writes, next to the figure, a `.qa.json` record, a replayable `.config.json`, a fill-in
`.caption.md` (section 5.6) and, unless `review` is false, a `.review` folder holding the page
preview, a grayscale copy and the review prompt. Set `svg_outline: true` to also write
`<stem>.outlined.svg`, in which glyphs are converted to paths; it needs `svg` in `formats`. Set
`cvd_strict: true` to fail the render when a colour pair breaches the colour-vision threshold, and
`cvd_threshold` to change that threshold.

Outputs are staged and only committed once every check has passed, so a failed render leaves no
half-written figure behind to block the next attempt. `--output-stem` moves the output without editing
the configuration, and the saved `<stem>.config.json` keeps relative layer paths plus `config_root`, so
a configuration replays next to the data instead of being pinned to one machine.

The scripts require the raster CRS and the display CRS to match and never reproject, resample or
convert source values behind the scenes; inputs such as date-line-crossing global data, unusual polar
projections and NetCDF are out of scope and belong in the existing professional GIS toolchain.
Geographic elements are calibrated once the final viewport is fixed, and any viewport change requires
a redraw. Passing the automated checks is not a visual review and not acceptance of the real data.

`assets/examples/` holds six runnable synthetic configurations and their data; copy them into a task
work directory first and never treat them as real results. Executed checks and known boundaries are in
[validation record](references/validation.md).

Reuse the existing toolchain and reuse code or GIS layouts where possible; never migrate a whole
project just to beautify a figure. Keep style separate from data, and record at least size, panel
positions, map extent and CRS, colour ramp, value mapping, fonts, line widths and export settings in
the configuration. Scale bars and north arrows come from cartographic tools, never from an image
model.

### AI Review

Look at the overall visual hierarchy first, then check text and strokes at the final printed size,
and finally zoom in on clipping, overlap and export artefacts. Deliver a table:
`panel or element | observed problem | concrete fix | priority | verifiable from the image alone`.

Where image understanding is available, follow the section 8 visual review; the current assistant
reading images satisfies that condition and no external model call is needed. Without image
understanding, run the size and configuration checks that are possible and state plainly that no
visual review was performed.

Suggestions must be actionable, for example "move the legend to a separate right-hand column and
align it with the top edge of the main map", not "make it more premium". Separate visible layout
problems from problems that need source-data verification, and never use an aesthetic score as proof
of scientific correctness.

### Hybrid

Render a baseline and save its configuration, then review it as in AI Review. Implement the accepted
suggestions as style parameters in code or the project, render again and re-check what must not
change. One revision round is the default; if clear occlusion or illegibility remains, revise those
specific problems instead of looping without a target. Unresolved source-data problems travel with
the delivery notes.

If the user explicitly wants an AI style sketch, generate only a placeholder layout or decorative
reference that contains no real map, values or orientation information; it can never serve as a final
paper map. The real figure still has to be produced in deterministic tools, and generated imagery
must never be pasted over the map body or quantitative elements.

## 4. Size, frame and margins

Fix the final physical size first, then fonts and line widths. Journal or user rules take precedence;
the following are **draft starting points for this skill, not a universal submission standard**:

| Item | Adjustable starting point |
|---|---|
| Single-column / double-column width | 85 mm / 180 mm; height follows the shape of the study area and the number of panels |
| Outer margin / panel gap | 3-5 mm / 3-5 mm, plus dedicated room for legends and coordinate labels |
| Body text / panel letters | About 8-9 pt / 10-11 pt at final size |
| Figure frame stroke | About 0.4-0.6 pt, adjusted for the background and output size |

Distinguish three objects: the **canvas** is the whole paper figure, the **map viewport** is the
geographic display extent, and the **panel frame** is a layout container. Resizing a panel must never
be done by stretching the map horizontally or vertically.

- Choose landscape or portrait from the shape of the study area; the map keeps the aspect ratio its
  projection requires. Remove wasted margin before enlarging the subject, and do not force it to fill
  the canvas.
- The map extent covers the complete study object with a little context; when the extent is widened
  to make room for a legend, confirm the subject is still clear. Whitespace may carry auxiliary
  elements but must not hide information.
- A simple single map may have no frame; use a light frame to organise the extent when there are
  coordinate axes, several map viewports or an inset. Avoid triple emphasis from an outer frame, a
  coordinate frame and administrative boundaries together.
- Panels at the same level share frame weight and spacing. An inset frame may be lighter but its
  separate extent must be visible.
- If panels become unreadable when reduced, drop a column, switch to a double-column figure or split
  the figure; do not shrink the fonts indefinitely. Whitespace serves grouping and reading rhythm,
  not a fixed fill ratio.
- Check the real size after export; automatic tight cropping can change the physical canvas size, so
  export parameters alone are not sufficient evidence.

### Fonts: SimHei plus Arial

- **Chinese text uses SimHei; English text and digits use Arial.** This applies to map labels,
  coordinates, legends, colour bars, scale-bar text, panel titles and every other piece of text inside
  the figure; keep one set consistent across the whole figure.
- In mixed text, assign the font per run: SimHei for Chinese, Arial for Latin, digits and their units.
  Setting a fallback list and assuming correct assignment is not enough; check the rendered result.
- Panel letters a, b, c use bold Arial; other text is normally regular. Build hierarchy through size
  and position rather than bolding everything.
- Font sizes follow the final physical size starting points in this section; unifying fonts does not
  mean fixing every element at one size.
- Check that SimHei and Arial are available before rendering. If they are missing, report it plainly
  and never silently substitute SimSun, Microsoft YaHei, Source Han Sans or another font, and never
  call a substituted preview a compliant final figure.
- A machine that genuinely has neither font — common on Linux and macOS — declares the substitution
  instead of inheriting one: `fonts:{"zh":[...],"en":[...]}` in the configuration, or the environment
  variables `GIS_FIGURE_FONT_ZH` / `GIS_FIGURE_FONT_EN`, each an explicit preference order such as
  `Noto Sans CJK SC` or `Liberation Sans`. The first installed name wins, a chain where nothing is
  installed still fails, and the font actually used is recorded in `.qa.json`. A declared substitution
  belongs in the delivery notes, because it is a real difference from this default.
- Check that the minus sign (-), degree sign, super- and subscripts, Greek letters and mathematical
  symbols render correctly. Where a special symbol genuinely needs another font, use a documented
  compatibility substitution for that symbol alone and state the exception.
- For PDF export, check font embedding and the actual fonts; for SVG, check how it displays in the
  target environment and, where needed, provide an additional copy with text converted to paths
  (`svg_outline` in Code mode) while keeping the editable source. Never declare that fonts match
  elsewhere just because the local preview looked right.
- When the user specifies fonts or provides submission rules that must be followed, that explicit
  request wins, and record the difference from this default.

## 5. Thematic map type, classification, colour and legends

### 5.1 Choosing the thematic map type

Choose the expression from the semantics of the existing result; never reanalyse the data just to fit
a map type. When the user already has a definite type, check its suitability first and raise the risk
of misleading instead of silently changing it.

| Existing data or result | Preferred map type | Constraint |
|---|---|---|
| Ratios or rates over polygon units | Choropleth | Confirm denominator, units and statistical definition; do not compute normalised indicators here |
| Counts or magnitudes at points | Proportional or graduated symbols | Symbol area corresponds to value, never radius proportional; state the range of each graduated class |
| Two related rates | Bivariate choropleth | Default to no more than a 3x3 combination; both dimensions need explicit classes and a 2-D legend |
| Existing point density or KDE output | Dot density or kernel density surface | KDE must record the upstream bandwidth and its units in the caption or metadata; a dot density map states what each dot represents and whether locations are schematic, and schematic dots are never presented as measured positions; do not generate densities or place random points here |
| Continuous field (raster) | Classified or stretched continuous rendering | Keep the confirmed mapping; for terrain, an existing hillshade may serve as background but is not added by default and no terrain result is computed here |
| Migration or OD flows | Flow map | Line width maps to flow with an explicit ratio and direction is clear. When crowded, ask upstream for an aggregated result; this skill does not aggregate, delete flow lines or change flows |
| Results changing over time | Small multiples or a map series | Static small multiples are preferred for papers; animation suits separately produced communication material and is not a default deliverable here |

### 5.2 Classification: checking whether the expression changed the conclusion

Classification is not purely decorative. The following explains and reviews existing schemes; it
does not authorise recomputing breaks for a nicer look.

| Scheme | Reasoning | What to check |
|---|---|---|
| Natural breaks (Jenks) | Uses the internal clustering of the data and suits some skewed distributions | Not the default answer for every skewed dataset; independently computed breaks differ between time steps, so identical colours cannot be compared across them by value |
| Quantiles | Gives classes of similar unit counts | Does not guarantee equal coloured area on the map; can split near-equal values or group very different values, and repeated values also affect grouping |
| Equal interval | Organises the legend with equal value spans | Cross-map comparability also requires a shared range and shared breaks; skewed data may concentrate in a few classes, which is not simply "failure" |
| Fixed or custom breaks | Domain thresholds, or a fixed comparison scale for a map series | Every map uses the same confirmed breaks; breaks may come from a domain standard or a previously agreed scheme and are not required to be produced by hand |

- A univariate classified map can consider **5 plus or minus 2 classes** for legibility; this is an
  empirical starting point only. A confirmed domain classification takes precedence, and thresholds
  must not be changed to round out the class count. Bivariate maps are handled separately by the
  combination limit above.
- The key principle is a **shared numeric mapping across comparative panels**, not one particular
  algorithm; shared breaks, even those originally produced by an algorithm, can be fixed and reused
  for a map series.
- Where source values exist, the classification review should be accompanied by a histogram marking
  the existing breaks, as an internal QA aid for empty classes, over-concentration and the
  distribution near boundaries. Reading existing values to draw a diagnostic histogram changes
  nothing and runs no spatial statistics; with only a screenshot, state clearly that this is
  impossible.
- Record the classification method, breaks, units, interval-endpoint convention and whether the
  mapping is shared across maps in the caption or metadata.
- When the user asks to compare schemes, or two schemes already exist, review their visual impact
  side by side; any alternative must come with explicit breaks and must not be silently computed. If
  a "hotspot" or difference narrative changes markedly between schemes, tell the reader that the
  expression is sensitive to classification and never pick the single map that best supports the
  expected conclusion. A layout-only change does not require inventing a second scheme.

### 5.3 Colour

Start from **ColorBrewer, cmcrameri or the viridis family** where they match the variable, then check
the actual ramp at the final size; coming from those libraries does not make a ramp automatically
acceptable.

| Ramp type | Use | Selection rule |
|---|---|---|
| Sequential | Ordered quantities such as temperature, density, suitability | Lightness change must support ordered reading; avoid a mid-ramp jump that invents a boundary |
| Diverging | Quantities with a meaningful midpoint | Zero, the mean or a threshold serves as the midpoint only when the research semantics support it; keep the confirmed midpoint and never move it for colour symmetry |
| Qualitative | Unordered classes such as land cover | Default to no more than about 8 classes for distinctness; with more existing classes use auxiliary symbols or grouped legends and never merge classes |

- Colour-vision-deficiency friendliness is the default goal. Before adopting a red-green diverging
  ramp, a CVD simulation **must** be run; run [cvd_check.py](scripts/cvd_check.py) and report its
  findings. If no simulation was run, say so and never claim a pass. A figure with no thematic
  mapping and only one fixed colour has nothing to simulate; report `applicable: false` rather than
  passing, and never treat it as a verdict on the palette.
- **NoData is not zero.** Use a neutral grey or another style clearly separated from valid values and
  describe it separately in the legend; it must not occupy the bottom of the ramp. If a valid class
  is also grey, change the NoData style rather than the class.
- The basemap should be low-contrast and low-saturation so it serves orientation. Consider an existing
  light basemap or a CartoDB Positron style; downloading or adding a basemap is never mandatory, and
  any external basemap keeps its required attribution.

Identify the semantics of the variable before changing its appearance. Continuous quantities use an
ordered-lightness ramp; a diverging ramp only when a centre has a definite meaning; categorical
quantities use distinguishable class colours. Prioritise separation between subject and background,
and never let basemap texture overpower the thematic information.

- Keep existing class assignments and value mappings; never manufacture a sharper contrast by
  changing ranges, applying a log transform or reclassifying. If a change is needed, state that it
  goes beyond beautification and wait for the user to fix the expression rules.
- Comparative panels of the same variable share the confirmed mapping and units; different variables
  do not share a colour scale merely because the colours match. When the original panels used
  different mappings, point out that they are not comparable instead of quietly fixing them.
- NoData, valid zero and out-of-range areas must be distinguishable. Check recognisability under
  colour-vision deficiency and use symbols or line styles to support classification when needed.
- When a ramp changes, re-render the map and legend together; never recover values by replacing pixel
  colours in a flat image.

### 5.4 A short colour convention: use it directly, look things up only when unsure

First check whether the user specified colours, a product's official legend or a confirmed project
palette; if so, keep it. Otherwise choose directly from the table below without reading `references`
first. **This is this skill's default convention, not an industry standard**; it fixes colour style
only and changes no existing range, break, midpoint or class.

| Data or situation | Default | Notes |
|---|---|---|
| Absolute temperature or LST | `YlOrRd`: light yellow low, orange middle, deep red high | Sequential when there is no special midpoint; consider `thermal` when a cold-warm scientific ramp is wanted, and consult the references when unsure |
| Temperature difference or anomaly | `RdBu_r`: blue negative, light near the reference, red positive | Centre on the confirmed zero or reference value; do not treat an ordinary mid value as a special baseline |
| General continuous quantities such as density or suitability | `viridis`: deep purple low, blue-green middle, yellow high | Use the full ordered ramp and state the direction of low and high in the legend; do not default every quantity to "blue low, red high" |
| Ordered discrete classes | Pick as many swatches from the matching sequential ramp as there are confirmed classes | Low to high has a visual order and swatches match the original breaks; never reclassify to fit the colours |
| Unordered land-cover classes | Use the class colours below as a starting point | Do not imply order with light-to-dark shading, and never merge classes |
| Elevation bands | Light green low, yellow-brown middle, brown high | Label elevation and band limits and do not imply vegetation; do not default the highest band to white, which reads as snow and ice |
| NoData or supporting basemap | Neutral grey for NoData; low-saturation, low-contrast basemap | NoData gets its own legend entry, distinct from zero, valid classes and the page background |

Without an established palette, common land-cover classes start from: **forest deep green `#287A45`,
grassland light green `#A6C96A`, cropland golden yellow `#E6C65B`, built-up brick red `#C85A54`,
water blue `#3C8DCC`, wetland teal `#58AFA5`, bare ground sand brown `#C5A880`, snow and ice pale blue
`#E5F2F8`, NoData grey `#D9D9D9`**. This custom set still needs its forest-grassland, red-green and
water-wetland combinations checked; never claim it has passed colour-vision testing.

Continuous data takes a continuous colour bar, classified data a discrete legend matching its
intervals, and land-cover classes separate swatches; never interpolate colours between unordered
classes. Map and legend update together, and comparative maps of one variable keep a single mapping.
Review checks semantics, coherence and legibility after reduction.

**Consult `references` only when:**

- The common rules are not enough to fix a ramp, land-cover colours conflict, there are many classes,
  the cold-warm semantics are unclear, or the variable is unusual: read the relevant part of
  [colour decisions and palettes](references/color-guide.md).
- A product's official palette, an exact version, professional justification or a better scientific
  ramp is needed: read the [professional colour resources index](references/professional-color-resources.md)
  and then the corresponding official source, rather than loading all six resources at once.
- What is missing is a unit, class meaning, break or baseline: that is a missing source fact and
  cannot be guessed from a colour document. State the gap and continue with the layout work that does
  not depend on it.

### 5.5 Legends

Continuous mappings normally use a colour bar; categorical or classified mappings use a legend that
matches them; the legend comes from the same rendering configuration. Units, tick precision and class
names must match the source, and rounding must not hide a threshold difference.

Legend dimensions follow label length and available space: a narrow right-hand column suits a vertical
colour bar and a wide canvas suits a horizontal bar. Prefer a dedicated legend area; when placing one
in empty map space, check for occlusion. Reduce decorative borders and keep swatches aligned with their
text; long labels may wrap but must not lose meaning. When out-of-range values exist, show the
extension end according to the actual rule and never truncate visually without explanation.

### 5.6 The caption

The caption is part of the deliverable, not an afterthought: it is where the recording requirements
scattered through this document actually land. Every render writes a fill-in `<stem>.caption.md`; fill
it in and delete the rows that do not apply.

A complete caption states, in this order:

| Field | Required content |
|---|---|
| Figure number and subject | One sentence naming the variable, the region and the period, in the order the reader meets them |
| Variable, unit, period | Variable name, unit, and the time step or period; never inherit a period from a neighbouring figure |
| Spatial coverage and CRS | The study area and the CRS or projection actually used for display |
| Data source and version | Dataset name, product version and access date; keep "unconfirmed" rather than inventing one |
| Classification and mapping | Method, breaks, interval-endpoint convention, and whether panels share one mapping |
| NoData | What missing, masked or excluded means, and how it is drawn |
| Scale bar | Which panels carry one, and that the scale is local where the projection distorts it |
| North arrow | Which panels carry one, and whether it shows true north or grid north |
| Abbreviations, symbols, inset | Every abbreviation expanded, and what the inset or extent marker refers to |
| Statistics or significance | Only if the figure shows them; state the test and the convention used |

Rules:

- Record only what the source supports. An unknown period, datum or product version stays
  "unconfirmed"; never fill a gap with a plausible guess.
- The caption must not contradict the legend or the value mapping; when either changes, update the
  caption in the same revision.
- Do not repeat the caption as an in-figure title (section 7). The figure carries only what the
  reader needs while reading the map.

## 6. Scale bars and north arrows

**Scale bar: style may change, ground distance must be verified.** Generate it from the trusted CRS,
the final map viewport and the tool's ground-distance capability; a projected coordinate unit in
metres does not by itself guarantee a locally accurate ground scale. A latitude-longitude map cannot
treat degrees as a fixed distance.

- Choose readable round values; changing the displayed total length requires recomputing the drawn
  length. Never edit the number to match an existing line.
- Recalibrate after changing the map extent, projection or panel size. Scaling the map and the scale
  bar together preserves the relationship; scaling either alone breaks it.
- For large extents or obvious projection distortion, state where the scale applies or omit it in
  favour of a graticule, and never imply that the scale is constant across the map.
- Decide per panel and per inset whether a scale bar is needed; never copy the main map's scale bar
  into an inset.

**North arrow: shape, weight and position may be improved; decorative rotation is forbidden.** State
clearly whether it shows true north or grid north, and derive direction from the projection, the
rotation and the location rather than assuming screen-up is true north. Where direction varies
markedly with position, avoid a single arrow that misleads.

Omit the arrow when north is obvious and needs no indication. When kept, use a simple, small symbol
that sits below the scale bar in the auxiliary hierarchy and does not hide thematic content. With
insufficient input, never estimate or add quantitative or directional information from an image.

## 7. Three layouts

### Single map

The main map occupies the reading centre; legends and auxiliary elements go in reserved space or
reliable empty areas. Add an in-figure title only when genuinely needed, to avoid duplicating the
caption. If coordinate labels are kept, format them consistently and prevent collisions at the
corners.

### Multiple panels

Order panels by the comparison logic of variable, time or scenario, and place the a, b, c labels
consistently. Comparisons over one study area preferably share extent, scale, mapping and legend;
different study areas may share outer panel dimensions but the different map scales must be stated,
and a map is never stretched to fill a frame.

A shared legend is only for panels with the same semantics, units and mapping. Reserve a full row or
column for it before allocating map space. Check the subject size, labels and auxiliary elements of
every panel, not just whether the outer frames line up.

### Main map plus inset

Decide the inset's purpose first: a **locator** answers where the study area is, a **detail inset**
answers where the detail is. Do not mix the two logics.

- Start at about 20-30% of the main map width and adjust for legibility; this is a layout starting
  point, not a fixed ratio. The main map stays visually dominant.
- Prefer a corner that does not cover data, or a separate side column. If no reliable empty space
  exists, place the inset outside the main map.
- Locator boundaries, extent boxes, location points and connector anchors come from real coordinates
  and are produced by the tool; under a different CRS they need a correct display transform, not
  hand-drawn "roughly there" positions.
- The extent marker of a detail inset must match the actual viewport; a locator shown only as a point
  is expressed differently from an extent box. Never pass off a fictitious rectangle as the study
  area boundary.
- Decide an inset's orientation, scale and legend needs independently. For the same variable, keep
  the main map's value mapping by default; where a different mapping is genuinely used, label it
  clearly so colours do not invite a wrong comparison.

## 8. AI image review: is it clear and coherent once in the paper?

This section serves AI Review mode and is the visual check after each Hybrid render. The goal is the
**reading experience at the actual paper size**, not whether a zoomed-in image looks polished. The
vision model only reports judgements and fixes; any change happens back in the code or GIS project.

### 8.1 Material to give the vision model

- The actual exported figure, plus the final width and height in mm, the single- or double-column
  layout, and the final font size of in-figure text. Provide panel meanings so a deliberate
  comparison layout is not misread as untidy.
- If the user provides a paper page or template, place the figure in the page preview at its actual
  footprint; otherwise generate a page sketch with the assumption stated, by default checking a
  85 mm single-column or 180 mm double-column width, and never call it a universal journal standard.
- Provide both the full-page preview and the full-resolution figure: the page shows placement,
  whitespace and the relationship to body text, the original shows local occlusion and detail. The
  page sketch is for review only and never changes the final map file.
- Without paper dimensions, use the provisional width above and state the assumption in the
  conclusion; screen size alone cannot judge print legibility. If an original is scaled into the
  paper, convert final font size and stroke width by the same factor.

### 8.2 Four things to judge

| Direction | What the vision model checks | Where the fix lands |
|---|---|---|
| Is the layout sound | Whether the main map dominates; whether map and canvas proportions are coherent; whether margins are unbalanced; whether panel alignment, spacing and reading order are clear; whether the legend and inset squeeze or occlude the subject | Name the panel and the side, and the suggested alignment, position or size |
| Are the colours attractive and legible | Whether colours are coherent; whether light and dark levels read clearly; whether the basemap competes; whether adjacent classes are hard to tell apart; whether colours are too vivid or too washed out; whether several maps share one visual style | Specify ramp, background or boundary colour changes while keeping the existing value mapping; separate aesthetic preference from an actual legibility problem |
| Are the scale bar and north arrow well placed | Whether they cover data, touch the frame or squeeze the legend; whether they dominate; whether they coordinate with other auxiliary elements; whether their panel assignment is clear; whether they are confused with the inset | Suggest a specific empty area or a separate auxiliary block, and note that moving or resizing them requires a re-render and a re-check of distance and direction |
| Does it work at paper size | Whether fonts, ticks and symbols are too small; whether strokes are too thin; whether the map body is hard to make out; whether the colour bar and long labels are crowded; whether the page footprint is coherent; whether panel differences survive reduction | Suggest a larger final font, a different panel arrangement, a wider column or splitting the figure; never only "raise the DPI" |

### 8.3 Method and limits

1. **Full page and whole figure first**: judge whether the first visual focus lands on the research
   content, whether the whole is balanced, and whether the reader can find the panel-to-legend
   correspondence naturally.
2. **Then check at final size**: judge legibility from the given millimetres, font sizes and stroke
   widths, and do not let zoomed detail hide a reduction problem. The model or viewer may scale the
   image automatically, so a size judgement must combine the configuration and never claim that a
   screen preview is the physical size.
3. **Then look locally**: locate label collisions, frame clipping, crowded colour-bar ticks and
   auxiliary elements covering content. Use an extra view for local magnification and never replace
   the whole-figure review with a local crop.

A visual review cannot prove that scale-bar values, true north, geographic boundaries or raster values
are correct; those are verified from source information and deterministic tools as in section 9. A
clean visual review does not mean the CVD simulation, font embedding or geographic accuracy checks
passed; report only the checks actually performed.

### 8.4 Review output format

Start with one clear verdict: **visually acceptable / minor fixes / needs re-layout / insufficient
material**, stating the paper width and height or the page assumption used. That verdict covers visual
review only.

Then, per direction, write what is acceptable plus any concrete problem. Use the table below when
there are problems; where a direction has none, one short sentence is enough, and never invent fixes
to fill the table.

| Panel or element | Observed problem and reading impact | Actionable fix | Priority | How to verify |
|---|---|---|---|---|
| e.g. the vertical colour bar in panel b | Tick labels crowd together after reduction and are hard to match to values | Widen the reserved colour-bar column and increase label spacing; if ticks are reduced, keep the key thresholds and the complete mapping | Must fix | Re-render at the final width and check again |

Priorities are **must fix** (occlusion, clipping, illegibility or a confused correspondence),
**worth improving** (visual hierarchy, position or colour affecting reading) and **optional
preference** (an aesthetic choice that does not affect understanding). Never replace problem
statements with a single "beauty score".

Close with the top three changes worth making first, and state which judgements still lack material.
AI Review mode delivers the review; Hybrid mode implements the authorised style changes, checks again
at the same paper size and reports whether the problems are resolved. Never change geographic content
or the value mapping to earn a better aesthetic score.

## 9. Export and acceptance

Follow the journal's specified format first. When none is given, provide a PNG for review plus
reproducible code or the project; for formal delivery provide PDF, SVG or TIFF as appropriate. A
raster map inside a vector container is still limited by the original resolution, and raising the DPI
does not create real detail.

Drafts may use 300 dpi; line art or hybrid figures follow the target journal. Pixel dimensions follow
`millimetres / 25.4 * dpi`. Check for missing glyphs, font embedding or substitution, transparent
backgrounds, and whether colours and strokes survive in the target format.

Acceptance has two parts:

1. **Facts and mapping**: source data unchanged; extent, CRS, variables, units, thresholds and NoData
   consistent; spot-check the rendering mapping at representative locations or classes and at boundary
   values; scale bar, orientation and inset relationship reliable. With only an image, state clearly
   what cannot be verified.
2. **Layout and output**: the actual physical size is correct; text is legible at printed size; frames,
   map, legends and panel labels show no overlap or clipping; auxiliary elements do not compete with
   the subject; comparison relationships are clear across maps; and the exported file was actually
   opened and checked.

Never substitute "looks right" for geographic or numeric verification, and never call an unverified
draft a submission-ready final figure.

**Print colour.** When a journal requires CMYK, state the conversion path and its risks: hues and
saturation shift, out-of-gamut colours are clipped, and an RGB preview does not represent the printed
result. Record which elements are most at risk (saturated reds, greens and blues, and thin coloured
lines) and ask for a proof where the print outcome matters. A raster TIFF may also need a specific bit
depth and compression; follow the journal. Never present an RGB export as a CMYK deliverable.

**Acceptance checks per item.** Report only what was actually executed, and keep the record beside the
figure:

| Check | How |
|---|---|
| Physical size | `figure_qa.py --width-mm --height-mm` against the exported PNG and PDF |
| Font embedding | `figure_qa.py --pdf` (needs PyMuPDF; reports `not_checked` when absent) |
| Target-environment fonts | Outlined SVG copy where text cannot be assumed present |
| Colour vision | `cvd_check.py` findings and ramp checks recorded in `.qa.json` |
| Omission of required elements | Caption rows filled from `<stem>.caption.md` |

Delivery per mode: the figure or review list, brief revision notes, the reproducible
configuration or project when a redraw happened, and the specific items still unverified. When the
user only asked for a review, do not start redrawing.

## 10. Typical requests

- "Use paper-map-figure in Hybrid mode to lay out four existing LST time steps as a double-column 2x2
  figure, keep the shared colour scale, and improve the margins and the shared legend."
- "AI Review: only check the font size, frames and visual hierarchy of this main-map-plus-locator
  figure. Do not change the figure."
- "Code: keep the existing project, export a 180 mm-wide paper figure, recalibrate the scale bar, and
  preserve all geographic content and value mappings."

## 11. Design references

When a colour choice needs professional justification, read the
[professional colour resources index](references/professional-color-resources.md) and pick the
relevant source for the data type among the six resources; there is no need to load them all.

This skill follows the honesty-about-expression, legend-consistency and delivery-verification ideas of
[cartography-geoviz](https://github.com/muend/geoai-skills/blob/main/skills/cartography-geoviz/SKILL.md)
(accessed 2026-09-09). It is an independent English work aimed at final figure production: the size
starting points, layout details and three-mode workflow are designed here, and it does not take on the
analysis, classification computation or interactive map responsibilities of that reference project.
