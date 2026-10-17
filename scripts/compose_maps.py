"""Compose existing complete map images with preserved aspect ratio.

Usage: python compose_maps.py config.json
Config paths are relative to the config file. No geospatial reconstruction, no
colour remapping and no redrawing of existing text or symbols.

Optional per panel:
  source_width_mm      physical width of the original figure, for shrinkage
  source_font_pt       one size or a list of sizes used in the original figure
  source_linewidth_pt  stroke width used in the original figure
Given those, the report converts them to the size they will actually have in
the composed figure, which is the only way to judge print legibility when an
existing map is scaled down.
"""
import argparse
import json
import math
from pathlib import Path
from PIL import Image
from figure_layout import configure_fonts, canvas, panel, export

MIN_FONT_PT = 7.0
MIN_LINEWIDTH_PT = 0.4


def _sizes(value):
    if isinstance(value, (int, float)):
        return [float(value)]
    if not value:
        raise ValueError("source_font_pt must be a number or a non-empty list")
    return [float(item) for item in value]


def scale_report(item, placed_mm, findings, min_font_pt=MIN_FONT_PT):
    """Convert original text/stroke sizes to their size after placement."""
    result = {}
    source_width = item.get("source_width_mm")
    if source_width is None:
        result["shrink_ratio"] = "unknown; provide source_width_mm to convert text sizes"
        return result
    if not math.isfinite(source_width) or source_width <= 0:
        raise ValueError("source_width_mm must be positive and finite")
    ratio = placed_mm / source_width
    result["shrink_ratio"] = round(ratio, 3)
    if item.get("source_font_pt") is not None:
        effective = [round(size * ratio, 2) for size in _sizes(item["source_font_pt"])]
        result["effective_font_pt"] = effective
        result["below_min_font_pt"] = [size for size in effective if size < min_font_pt]
        if result["below_min_font_pt"]:
            findings.append({"image": item["image"],
                             "kind": "text_below_print_size",
                             "effective_font_pt": result["below_min_font_pt"],
                             "limit_pt": min_font_pt,
                             "note": "Enlarge the panel, drop a column or split the figure; "
                                     "raising DPI does not fix this"})
    if item.get("source_linewidth_pt") is not None:
        width = round(float(item["source_linewidth_pt"]) * ratio, 2)
        result["effective_linewidth_pt"] = width
        if width < MIN_LINEWIDTH_PT:
            findings.append({"image": item["image"], "kind": "stroke_below_print_size",
                             "effective_linewidth_pt": width, "limit_pt": MIN_LINEWIDTH_PT})
    return result


def compose(config_path, min_font_pt=None):
    source = Path(config_path).resolve()
    cfg = json.loads(source.read_text(encoding="utf-8"))
    unknown = set(cfg) - {"width_mm", "height_mm", "output_stem", "formats", "dpi",
                          "panels", "min_font_pt", "svg_outline"}
    if unknown:
        raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
    # An explicit --min-font-pt on the command line wins over the configuration,
    # which wins over the built-in limit. A non-positive limit would call every
    # size legible, so it is refused rather than silently disabling the check.
    limit = float(cfg.get("min_font_pt", MIN_FONT_PT) if min_font_pt is None else min_font_pt)
    if not math.isfinite(limit) or limit <= 0:
        raise ValueError("min_font_pt must be a positive finite point size")
    if cfg.get("svg_outline") and "svg" not in tuple(cfg.get("formats", ["png", "pdf"])):
        raise ValueError("svg_outline requires svg in formats")
    configure_fonts()
    fig = canvas(cfg["width_mm"], cfg["height_mm"])
    boxes = []
    report = []
    findings = []
    for item in cfg["panels"]:
        x, y, w, h = item["rect_mm"]
        for px, py, pw, ph in boxes:
            if x < px + pw and x + w > px and y < py + ph and y + h > py:
                raise ValueError("Image containers overlap; use a separate inset area")
        boxes.append((x, y, w, h))
        path = (source.parent / item["image"]).resolve()
        with Image.open(path) as image:
            image = image.convert("RGBA")
            iw, ih = image.size
            scale = min(w / iw, h / ih)
            actual_w, actual_h = iw * scale, ih * scale
            ax = panel(fig, (x + (w - actual_w) / 2, y + (h - actual_h) / 2,
                             actual_w, actual_h))
            ax.imshow(image, interpolation="nearest", aspect="equal")
            ax.set_axis_off()
        entry = {"image": str(path), "placed_mm": [actual_w, actual_h],
                 "effective_source_dpi": round(25.4 / scale, 2),
                 "note": "Existing text/fonts/scale bars retained; inspect at final size"}
        entry.update(scale_report({**item, "image": str(path)}, actual_w, findings, limit))
        report.append(entry)
    stem = source.parent / cfg["output_stem"]
    formats = tuple(cfg.get("formats", ["png", "pdf"]))
    report_path = Path(str(stem) + ".layout.json")
    # Every artifact this call would create is checked before any work, so a
    # rejected run has not modified the output directory.
    intended = [Path(str(stem) + "." + ext) for ext in formats] + [report_path]
    if cfg.get("svg_outline"):
        intended.append(Path(str(stem) + ".outlined.svg"))
    if any(path.exists() for path in intended):
        raise FileExistsError("Choose a new output_stem to preserve earlier figures")
    outputs = export(fig, stem, formats, cfg.get("dpi", 300),
                     svg_outline=bool(cfg.get("svg_outline", False)))
    result = {"panels": report, "findings": findings, "outputs": [str(p) for p in outputs],
              "limit_pt": limit,
              "limits": "Placement and size arithmetic only; composition does not verify the "
                        "geographic content of the source images"}
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config")
    parser.add_argument("--min-font-pt", type=float, default=None,
                        help="override the min_font_pt of the configuration")
    args = parser.parse_args()
    print(json.dumps(compose(args.config, args.min_font_pt), ensure_ascii=False, indent=2))
