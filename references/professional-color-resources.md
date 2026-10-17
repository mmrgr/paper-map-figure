# Professional GIS colour resources index

Accessed 2026-09-09. This file indexes the official entry points and scope of six professional
resources; it stores links and summaries, not copies of the originals or local PDFs. Linked content may
change, so record the version when a specific palette is adopted.

## 1. ColorBrewer: thematic map colour

- [Scheme type explanation](https://colorbrewer2.org/learnmore/schemes.html)
- [Online colour tool](https://colorbrewer2.org/)
- Scope: choosing sequential, diverging and qualitative schemes, and their class counts.
- How this skill uses it: look up sequential schemes for ordered classes, diverging schemes when a
  definite reference midpoint exists, and qualitative schemes for unordered classes. The number of
  colours follows the existing breaks; breaks are never changed to fit a palette.

## 2. Scientific Colour Maps: continuous scientific data

- [Official site](https://www.fabiocrameri.ch/colourmaps/)
- [User guide PDF](https://www.fabiocrameri.ch/ws/media-library/ce2eb6eee7c345f999e61c02e2733962/readme_scientificcolourmaps.pdf)
- [Ramp categories](https://www.fabiocrameri.ch/colourpalettes/)
- Scope: perceptually uniform scientific ramps, colour-vision and greyscale reading, and sequential,
  diverging and cyclic types.
- How this skill uses it: pick candidates for continuous rasters and difference maps from the matching
  type, and record the ramp name and version actually used. Still check the whole figure background,
  transparent overlays and the final size; a reputable ramp is not a substitute for reviewing the
  figure.

## 3. NASA: Subtleties of Color

- [Part 1 of 6, with navigation](https://earthobservatory.nasa.gov/blogs/elegantfigures/2013/08/05/subtleties-of-color-part-1-of-6/)
- Scope: colour perception, the relationship between data and colour types, colour semantics and
  practical tools.
- How this skill uses it: as the reference for judging whether a colour misleads, especially lightness
  change, visual banding and the match between colour and variable meaning. It is a design guide, not a
  standard requiring fixed RGB values on every map.

## 4. cmocean: ramps organised by scientific variable

- [Official documentation](https://matplotlib.org/cmocean/)
- [Source repository](https://github.com/matplotlib/cmocean)
- [thermal diagnostic PDF](https://matplotlib.org/cmocean/colormaps_viscm-1_00.pdf)
- Scope: ramps for ocean-science variables, perceptual diagnostics and implementation.
- How this skill uses it: `thermal` may be considered for temperature and `topo` for combined land and
  sea elevation; check the semantics and mapping fit before moving it to a specific GIS or
  remote-sensing variable. It is not a mandatory standard for every LST product.
- Constraint: data clipping or other numeric processing in the example code is not authorised by this
  skill's beautification scope and is never copied onto real results.

## 5. ESA WorldCover: product-official land-cover symbology

- [Official data and symbology entry](https://esa-worldcover.org/en/data-access)
- [WorldCover 2021 Product User Manual V2.0 PDF](https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/docs/WorldCover_PUM_V2.0.pdf)
- Scope: product class definitions, colours and QGIS or ArcGIS symbol files.
- How this skill uses it: when mapping the corresponding WorldCover product, read the product palette or
  official style first and check class codes, names and version. Other land-cover products use their own
  official legends, and the WorldCover palette is never treated as a global standard.
- Note: the official entry offers more than one symbol scheme, so record which one was actually adopted
  rather than writing "the ESA palette".

## 6. Esri, *Cartography.*: cartographic expression reference

- [Official sample chapter PDF](https://www.esri.com/content/dam/esrisites/en-us/esri-press/pdfs/cartography-definitive-guide-making-maps-sample-chapter.pdf)
- [Esri colour ramp design note](https://www.esri.com/arcgis-blog/products/arcgis-online/mapping/new-color-ramps-in-map-viewer-beta)
- Scope: classified and continuous thematic maps, diverging expression, and the visual relationship
  between ramps and basemaps.
- How this skill uses it: check that the expression suits the comparison and that the subject colour
  separates clearly from the background. A sample chapter is not the whole book and is not a submission
  standard for any particular journal.

## Order of selection in this skill

1. An explicit user rule, an official data-product palette or a project mapping takes precedence.
2. Consult ColorBrewer for discrete classification, and Scientific Colour Maps and cmocean for
   continuous scientific variables.
3. Use the NASA and Esri principles to explain and review visual choices.
4. Use the custom values in [colour decisions and palettes](color-guide.md) only when nothing has been
   specified.

These resources justify colour choices; they do not authorise changing real values, geographic content,
class meanings, classification breaks or midpoints. Final figure production still follows the
truthfulness boundaries and the review workflow in SKILL.md.
