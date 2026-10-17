"""Original layout helpers; no copied third-party implementation or GIS analysis.

Map content is rendered by the caller using a verified GIS toolchain.
"""
from pathlib import Path
import math
import matplotlib as mpl
from matplotlib import pyplot as plt, font_manager
from matplotlib.offsetbox import TextArea, HPacker, AnnotationBbox


# Chinese runs use the first installed family of the zh chain, Latin runs the en chain.
STRICT_FONT_CHAINS = {"zh": ("SimHei",), "en": ("Arial",)}

# SimHei and Arial are proprietary, so a Linux or macOS install may genuinely
# not have them. GIS_FIGURE_FONT_ZH / GIS_FIGURE_FONT_EN let that machine declare
# the substitution order once instead of hiding it in a fallback: the value is a
# comma-separated preference list, the first installed name wins, and a chain
# that resolves to nothing still fails loudly.
_FONT_CHAIN_ENV = {"zh": "GIS_FIGURE_FONT_ZH", "en": "GIS_FIGURE_FONT_EN"}


def _declared_chains():
    import os
    declared = {}
    for key, name in _FONT_CHAIN_ENV.items():
        raw = os.environ.get(name, "").strip()
        if raw:
            declared[key] = [part.strip() for part in raw.split(",") if part.strip()]
    return declared or None


def resolve_fonts(preferred=None):
    """Resolve each font chain to the first family that is really installed.

    A chain is an explicitly declared preference order such as
    {"zh": ["SimHei", "Noto Sans CJK SC"], "en": ["Arial", "Helvetica"]}.
    Working through a declared chain is still the configurer's own choice, so it
    is allowed; what is never allowed is a substitution nobody asked for. A chain
    where nothing is installed raises instead of falling back silently.
    """
    chains = dict(STRICT_FONT_CHAINS)
    chains.update(_declared_chains() or {})
    if preferred:
        if not isinstance(preferred, dict):
            raise ValueError("fonts must map zh and en to font name lists")
        for key in ("zh", "en"):
            values = preferred.get(key)
            if values is None:
                continue
            names = [str(values)] if isinstance(values, str) else [str(v) for v in values]
            if not names or any(not name.strip() for name in names):
                raise ValueError("Font chains must be non-empty font names")
            chains[key] = tuple(names)
    resolved, paths = {}, {}
    for key, names in chains.items():
        for name in names:
            try:
                paths[key] = font_manager.findfont(name, fallback_to_default=False)
            except (ValueError, KeyError):
                continue
            resolved[key] = name
            break
        if key not in resolved:
            raise ValueError(
                f"No font from the {key} chain {list(names)} is installed; install one or "
                "declare another explicitly (fonts are never substituted silently)")
    return resolved, paths


def configure_fonts(preferred=None):
    """Fail explicitly if required fonts are missing; never silently substitute."""
    resolved, paths = resolve_fonts(preferred)
    mpl.rcParams.update({"font.family": resolved["en"], "font.size": 8.5,
                         "axes.unicode_minus": True, "pdf.fonttype": 42,
                         "ps.fonttype": 42, "svg.fonttype": "none"})
    return paths


def font_families(preferred=None):
    """Resolved zh/en family names, for callers that set per-artist text properties."""
    return resolve_fonts(preferred)[0]


def canvas(width_mm=180, height_mm=120):
    """Physical canvas, independent of geographic extent."""
    if not all(math.isfinite(v) and v > 0 for v in (width_mm, height_mm)):
        raise ValueError("Canvas dimensions must be positive finite millimetres")
    return plt.figure(figsize=(width_mm / 25.4, height_mm / 25.4),
                      layout=None, facecolor="white")


def panel(fig, rect_mm, projection=None, frame_pt=0.5):
    """rect_mm is left, bottom, width, height. No map extent is inferred."""
    x, y, w, h = rect_mm
    fw, fh = fig.get_size_inches() * 25.4
    if (not all(math.isfinite(v) for v in rect_mm) or min(x, y) < 0
            or min(w, h) <= 0 or x + w > fw + 1e-8 or y + h > fh + 1e-8):
        raise ValueError("Panel must fit inside the canvas")
    ax = fig.add_axes([x / fw, y / fh, w / fw, h / fh], projection=projection)
    for spine in ax.spines.values():
        spine.set_linewidth(frame_pt)
    return ax


def grid(fig, rows=2, cols=2, margin_mm=5, gap_mm=5, footer_mm=12,
         projection=None):
    """Top-to-bottom reading order, with a reserved footer for a legend.

    The caller controls axes aspect/CRS; equal containers do not imply equal scale.
    """
    if (not isinstance(rows, int) or not isinstance(cols, int)
            or min(rows, cols) < 1):
        raise ValueError("rows and cols must be positive integers")
    if not all(math.isfinite(v) and v >= 0 for v in (margin_mm, gap_mm, footer_mm)):
        raise ValueError("Spacing must be finite and nonnegative")
    fw, fh = fig.get_size_inches() * 25.4
    w = (fw - 2 * margin_mm - (cols - 1) * gap_mm) / cols
    h = (fh - 2 * margin_mm - footer_mm - (rows - 1) * gap_mm) / rows
    axes = []
    for row in range(rows):
        for col in range(cols):
            axes.append(panel(fig, (margin_mm + col * (w + gap_mm),
                                    fh - margin_mm - (row + 1) * h - row * gap_mm,
                                    w, h), projection))
    return axes


def mixed_label(ax, xy, runs, size=8.5, bold=False, families=None):
    """Explicit font runs, for example [('Study area ', 'en'), ('2021', 'en')].

    A Chinese run such as ('\u7814\u7a76\u533a ', 'zh') selects the zh family, by default SimHei;
    the helper never guesses which language a run is. `families` carries resolved
    names from font_families() when the figure declares its own font chains.
    xy uses axes fractions, and the helper does not rewrite existing map labels.
    """
    resolved = dict(STRICT_FONT_CHAINS)
    resolved.update({key: (value,) for key, value in (families or {}).items()})
    boxes = []
    for value, language in runs:
        if language not in ("zh", "en"):
            raise ValueError("Font run language must be zh or en")
        boxes.append(TextArea(value, textprops={
            "fontfamily": resolved[language][0],
            "fontsize": size, "fontweight": "bold" if bold else "normal"}))
    if not boxes:
        raise ValueError("At least one text run is required")
    packed = HPacker(children=boxes, align="baseline", pad=0, sep=0)
    artist = AnnotationBbox(packed, xy, xycoords="axes fraction", frameon=False,
                           box_alignment=(0, 1), pad=0)
    ax.add_artist(artist)
    return artist


def export(fig, output_stem, formats=("png", "pdf"), dpi=300, svg_outline=False):
    """Preserve physical canvas size; no tight crop. Refuse existing outputs.

    svg_outline additionally writes '<stem>.outlined.svg' with glyphs converted
    to paths, for viewers that cannot resolve SimHei or Arial. The plain SVG
    keeps live, editable text; the outlined copy is the delivery fallback and
    is never a substitute for checking the font on the target system.
    """
    if not math.isfinite(dpi) or dpi <= 0:
        raise ValueError("DPI must be positive and finite")
    if not formats or any(ext not in ("png", "pdf", "svg", "tiff") for ext in formats):
        raise ValueError("Supported formats: png, pdf, svg, tiff")
    if svg_outline and "svg" not in formats:
        raise ValueError("An outlined SVG requires svg in formats")
    stem = Path(output_stem)
    paths = [Path(str(stem) + "." + ext) for ext in formats]
    outlined = Path(str(stem) + ".outlined.svg") if svg_outline else None
    if any(path.exists() for path in paths) or (outlined is not None and outlined.exists()):
        raise FileExistsError("Use a new output stem to preserve earlier figures")
    stem.parent.mkdir(parents=True, exist_ok=True)
    with mpl.rc_context({"savefig.bbox": None}):
        for path in paths:
            fig.savefig(path, dpi=dpi, bbox_inches=None, facecolor="white")
        if outlined is not None:
            with mpl.rc_context({"svg.fonttype": "path"}):
                fig.savefig(outlined, dpi=dpi, bbox_inches=None, facecolor="white")
    return paths + ([outlined] if outlined is not None else [])
