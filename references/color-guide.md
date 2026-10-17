# Colour decisions and palettes

Professional sources are indexed in
[professional colour resources](professional-color-resources.md), which covers six resources:
ColorBrewer, Scientific Colour Maps, NASA, cmocean, ESA WorldCover and Esri. Pick the matching resource
when fixing a scheme; never treat the custom palettes below as an industry standard.

## 1. Separate "standard" from "default proposal"

No single palette is standard for every GIS or remote-sensing paper. The order of precedence is: an
explicit requirement from the user or the target rules, then the official legend and version of the data
product used, then a confirmed project-wide mapping, then the defaults below. Official class colours are
never replaced automatically because another set looks better; when a custom colour is used, say so and
never call it official.

The HEX values below are adjustable design starting points proposed by this skill and are not declared
to have passed every colour-vision and print test. Check the actual panels, adjacencies and final size
before adopting them. Colour depends on data semantics, so a file name containing "heatmap" does not by
itself call for temperature colours.

## 2. Temperature: absolute temperature and temperature change are different

| Variable | Recommended expression | Constraint |
|---|---|---|
| Absolute temperature or LST, no special baseline | Prefer a sequential ramp; consider cmocean `thermal` or ColorBrewer `YlOrRd`, the latter light yellow at the low end and orange to deep red at the high end | Not limited to one cold-warm combination; do not render an ordinary mid temperature as a white with special meaning; state units and the shared range |
| User explicitly wants cold colours low and warm high | Use a checked cold-to-warm scheme, cool low and orange-red high | This is a semantic preference, not a standard; a typical diverging ramp requires a definite reference midpoint and never defaults to the mid value of the range or the sample mean |
| Temperature anomaly or a difference between two periods | Blue negative, light neutral near zero, orange-red positive; consider `RdBu_r` | Fix the midpoint at the confirmed zero or baseline; state the difference unit and never share a colour scale between absolute temperature and a difference |
| Deviation from a threshold | Cool below, neutral near, warm above | The threshold must come from the research definition; 0 °C has special meaning only in freezing-related questions |

Suggested ordered temperature palette (low to high, five classes): `#FFFFB2`, `#FECC5C`, `#FD8D3C`,
`#F03B20`, `#BD0026`. This is the five-class `YlOrRd` scheme; use it directly only when five breaks
already exist, otherwise take the version of the ramp with the right class count and never change the
breaks to fit the colours.

An example five-colour design for a temperature change (negative end to midpoint to positive end):
`#2166AC`, `#92C5DE`, `#F7F7F7`, `#F4A582`, `#B2182B`. The number of colours does not define the
intervals; whether the neutral colour represents a class depends on the confirmed classification, and a
non-zero value near zero is never labelled "no change".

Do not default to jet or a rainbow scheme for temperature: repeated hue reversal easily creates
unnecessary visual banding. Multi-date temperature maps keep the same ramp direction, range and units,
and are never stretched independently and then compared by colour. Difference maps are not forced to
symmetric limits; keep the confirmed range, check the midpoint normalisation and state any necessary
difference in scale between the two sides.

## 3. Common land cover: semantics and distinctness come first

The following is a **custom paper-colour proposal**, not the official legend of ESA, any national
standard or any product. Use it only when no fixed colours exist, and never treat identically named
classes from different datasets as automatically the same class.

| Class | Suggested colour | HEX starting point | Note |
|---|---|---|---|
| Forest | Deep green | `#287A45` | Keep a clear lightness difference from grassland |
| Grassland | Light green | `#A6C96A` | Not so pale that it disappears on white |
| Shrub | Olive green | `#788A3F` | Adjust hue or add texture if it is hard to separate from forest and grass |
| Cropland | Soft golden yellow | `#E6C65B` | Keep it apart from bare-ground brown |
| Built-up or impervious | Brick red | `#C85A54` | Carries a red-green discrimination risk, so check it; switch to grey-purple or add an outline when needed |
| Water | Blue | `#3C8DCC` | Classified water does not imply depth through blue shading that was never supplied |
| Wetland | Teal | `#58AFA5` | Check carefully when water and grassland appear together |
| Bare ground or sand | Sand brown | `#C5A880` | If the data separates the two, colour them separately rather than merging |
| Snow and ice | Very pale blue | `#E5F2F8` | Pair with a thin outline so it is not confused with the background or NoData |
| NoData | Neutral grey | `#D9D9D9` | Give it its own legend entry; if it conflicts with a valid class, use an explicit missing-value texture |

Land-cover classes are unordered, so forest, grassland and cropland must not be arranged along one
light-to-dark ramp as if they were ranked. With many classes, do not rely on tiny colour differences
alone: improve legend grouping, outlines and auxiliary textures first, and suggest faceting if that is
still not enough. Never merge classes on your own initiative.

Auxiliary features on a thematic map should recede: thin grey lines for roads, low-saturation blue for
watercourses, thin dark grey for administrative boundaries and a slightly stronger line for the study
area outline. Their colours follow the contrast of the main ramp, and an auxiliary boundary must never
be more prominent than the research result.

## 4. Continuous, discrete, banded: choose the mapping before the colour

**Continuous and discrete describe the mapping; sequential, diverging and qualitative describe colour
semantics. They are different dimensions.** A continuous temperature field may use a sequential
gradient; classified temperature should still use ordered colours, while unordered land-cover classes
use qualitative colours.

| Expression | Colour rule | Legend and implementation |
|---|---|---|
| Continuous single direction | Sequential ramp; `viridis` or `cividis` as options, `YlOrRd` for temperature | Continuous colour bar keeping the existing limits and normalisation; no invented breaks |
| Ordered discrete classes | Take colours from a sequential ramp by class | Swatches map to explicit numeric intervals; apply existing breaks only and never blur class limits with a smooth gradient |
| Continuous change with a centre | Diverging ramp, ordered on each side | The midpoint matches the research baseline; an asymmetric range is not changed by default |
| Discrete change with a centre | Colour from a diverging ramp using the existing negative, neutral and positive intervals | Show the exact intervals; never add a "normal class" that does not exist |
| Unordered land cover | Qualitative or semantically meaningful class colours | One swatch per class, with no interpolation between classes |
| Elevation bands | The conventional light green low, yellow-brown middle, brown high may be used; ordered ramps are preferable for quantitative comparison | Label the elevation unit and the existing band limits; terrain colour does not imply vegetation type |

Elevation must not default to white at the highest band: white reads as snow and ice, so use it only
when the legend says so. Water depth needs its own blue sequence with an explicit direction; a combined
land-and-sea ramp is not an ordinary temperature ramp. A hillshade is optional context only, and a
strong overlay changes how readers perceive the thematic colours, so weaken or remove it; never compute
or fabricate new terrain.

Raster classification maps use a display that preserves classes, so bilinear colour mixing cannot
produce classes that do not exist; a continuous map is likewise never smoothed for appearance. Rendering
sampling follows the existing result and is recorded, and display processing is never written back to
the data.

## 5. Into the visual review

The image review judges, in order:

1. Whether low and high, negative and positive are easy to understand, and whether a midpoint was
   invented.
2. Whether forest and grass, crop and bare ground, water and wetland remain distinguishable at the
   actual size.
3. Whether a continuous ramp shows false boundaries and whether discrete swatches clearly match their
   intervals.
4. Whether the subject, auxiliary features, NoData and page background conflict.
5. Whether the same colour means the same value or class across panels.

Report "I personally dislike this colour" separately from "this colour makes readers misread". A
colour-only change still requires updating the map and the legend together; values, thresholds, classes
and spatial facts stay unchanged.

Run [cvd_check.py](../scripts/cvd_check.py) before adopting a red-green diverging ramp, or whenever a
figure mixes several class colours. It simulates protan, deutan and tritan deficiencies at two
severities, reports the CIEDE2000 distance for the pairs that must stay apart, and checks a continuous
ramp for lightness reversals. Report its findings and its limits: it is not a print proof and not a
formal accessibility audit.

## Sources

- [ColorBrewer scheme types](https://colorbrewer2.org/learnmore/schemes.html): the semantic distinction
  between sequential, diverging and qualitative.
- [ColorBrewer tool](https://colorbrewer2.org/): named ramps and their discrete-class versions.
- [Scientific colour maps](https://zenodo.org/record/1287763): a reference for scientific palettes and
  perceptual uniformity.

Accessed 2026-09-09. The temperature and land-cover defaults are this skill's design proposals; when a
product's official colours are used, verify the product and version separately.
