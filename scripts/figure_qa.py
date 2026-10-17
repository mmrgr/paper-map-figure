"""Observable export checks and review packet, not an AI aesthetic verdict."""
import importlib.metadata
import json
from pathlib import Path
from PIL import Image, ImageOps
from matplotlib.text import Text
from matplotlib import font_manager
from matplotlib.ft2font import FT2Font


def inspect_figure(fig, min_font_pt=7):
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    frame=fig.bbox
    findings=[]; texts=[]; fonts={}
    for obj in fig.findobj(match=Text):
        if not obj.get_visible() or not obj.get_text().strip(): continue
        value=obj.get_text()
        bounds=obj.get_window_extent(renderer)
        # Skip undisplayed tick objects beyond the actual figure.
        if bounds.width==0 or bounds.height==0: continue
        if obj.get_fontsize()<min_font_pt:
            findings.append({"kind":"small_text","text":value,"size_pt":obj.get_fontsize()})
        if bounds.x0<frame.x0-.5 or bounds.y0<frame.y0-.5 or bounds.x1>frame.x1+.5 or bounds.y1>frame.y1+.5:
            findings.append({"kind":"outside_canvas","text":value})
        path=font_manager.findfont(obj.get_fontproperties(),fallback_to_default=False)
        if path not in fonts: fonts[path]=FT2Font(path).get_charmap()
        missing=[c for c in set(value) if not c.isspace() and ord(c) not in fonts[path]]
        if missing: findings.append({"kind":"missing_glyph","text":value,"characters":missing})
        texts.append((value,bounds))
    for i,(value,bb) in enumerate(texts):
        for other,ob in texts[i+1:]:
            # Candidate only: legitimate adjacent text runs can touch.
            overlap_x=min(bb.x1,ob.x1)-max(bb.x0,ob.x0)
            overlap_y=min(bb.y1,ob.y1)-max(bb.y0,ob.y0)
            if overlap_x>2 and overlap_y>2:
                findings.append({"kind":"possible_text_overlap","texts":[value,other]})
    return {"canvas_mm":(fig.get_size_inches()*25.4).tolist(),
            "findings":findings,"fonts":list(fonts),
            "limits":"Geographic correctness and aesthetics are not inferred by this check"}


def verify_png(path,width_mm,height_mm,dpi):
    with Image.open(path) as image:
        expected=[width_mm/25.4*dpi,height_mm/25.4*dpi]
        if any(abs(actual-target)>1.1 for actual,target in zip(image.size,expected)):
            raise ValueError("Exported PNG dimensions differ from intended physical size")
        return {"pixels":list(image.size),"dpi_metadata":image.info.get("dpi"),"expected_pixels":expected}


def versions():
    return {name:importlib.metadata.version(name) for name in
            ["matplotlib","numpy","Pillow","geopandas","rasterio","pyproj","shapely"]}


def verify_pdf(path,width_mm,height_mm):
    """Optional PyMuPDF inspection: page dimensions and embedded font streams."""
    try: import fitz
    except ImportError: return {"status":"not_checked","reason":"PyMuPDF not installed"}
    with fitz.open(path) as doc:
        if len(doc)!=1: raise ValueError("Expected single-page figure PDF")
        size=[doc[0].rect.width/72*25.4,doc[0].rect.height/72*25.4]
        if any(abs(a-b)>.1 for a,b in zip(size,[width_mm,height_mm])):
            raise ValueError("PDF physical size differs from configuration")
        fonts=[]
        for font in doc[0].get_fonts(full=True):
            xref=font[0]
            extracted=doc.extract_font(xref)
            fonts.append({"name":font[3],"embedded":bool(extracted[3])})
        return {"status":"checked","page_mm":size,"fonts":fonts}


def review_packet(png, output_dir, width_mm, height_mm, caption=""):
    """Keep packet separate from the official map. Never claim CVD simulation."""
    from page_preview import preview
    root=Path(output_dir);root.mkdir(parents=True,exist_ok=False)
    preview(png,root/"page",width_mm)
    with Image.open(png) as image:
        ImageOps.grayscale(image.convert("RGB")).save(root/"grayscale.png")
    prompt=f"""# Visual review input

Figure physical size: {width_mm:g} x {height_mm:g} mm. The page is an A4 placeholder, not a journal template.
Figure caption: {caption}

Inspect the original figure, page.png and grayscale.png together, and check
against section 8 of SKILL.md:
1. Layout of the main map, whitespace, panels, legend and inset.
2. Colour semantics, coherence and legibility.
3. Whether the scale bar and north arrow occlude content or dominate.
4. Whether text, strokes and the map body stay legible at the physical size above.

Report one verdict (visually acceptable / minor fixes / needs re-layout /
insufficient material) and, per direction, location, problem, fix and priority.

A grayscale image is not a colour-vision-deficiency simulation. Never claim
geographic accuracy from an image.
"""
    (root/"review.md").write_text(prompt,encoding="utf-8")
    return str(root)


def caption_template(cfg, sources=None, elements=None):
    """Fill-in caption skeleton gathering every field SKILL.md requires.

    Fields the configuration cannot know (period, product version, provenance)
    are left as explicit placeholders rather than guessed.
    """
    def row(name, value, confirm):
        return f"| {name} | {value} | {confirm} |"

    mappings = cfg.get("mappings", {})
    described = []
    for key, spec in mappings.items():
        unit = spec.get("unit", "unconfirmed")
        if spec.get("type") == "continuous":
            described.append(f"{spec.get('variable', key)} ({unit}), "
                             f"continuous {spec.get('vmin'):g}-{spec.get('vmax'):g}, "
                             f"colormap {spec.get('cmap', 'viridis')}")
        elif spec.get("type") == "classified":
            described.append(f"{spec.get('variable', key)} ({unit}), fixed breaks "
                             + ", ".join(f"{value:g}" for value in spec.get("breaks", []))
                             + f", colormap {spec.get('cmap', 'YlOrRd')}")
        else:
            labels = ", ".join(entry.get("label", str(entry.get("code")))
                               for entry in spec.get("entries", []))
            described.append(f"{spec.get('variable', key)} ({unit}), unordered classes: {labels}")
    panels = cfg.get("panels", [])
    geometry = "; ".join(
        f"{panel.get('id')} {panel.get('crs')} "
        f"[{', '.join(f'{value:g}' for value in panel.get('extent', []))}]" for panel in panels)
    shared = cfg.get("comparison_groups", [])
    bars = [panel.get("id") for panel in panels if panel.get("scale_bar")]
    arrows = [panel.get("id") for panel in panels if panel.get("north_arrow")]
    lines = ["# Figure caption template", "",
             "Figure <number>. <one sentence: variable, region and period, in the order the "
             "reader meets them>.", "",
             "Fill every row. Keep \"unconfirmed\" where the source is unknown; never invent a "
             "period, product version or datum.", "",
             "| Field | Value from this configuration | Confirm against the source |",
             "|---|---|---|",
             row("Variable, unit, period", "; ".join(described) or "unconfirmed",
                 "period and unit come from outside the configuration"),
             row("Spatial coverage and CRS", geometry or "unconfirmed",
                 "confirm the extent is the intended study area"),
             row("Data source and product version", "unconfirmed",
                 "name the dataset, version and access date"),
             row("Classification and mapping", "see the mappings row above",
                 "state whether panels share one mapping"),
             row("NoData meaning", cfg.get("nodata_legend", {}).get("label", "NoData"),
                 "say whether NoData means missing, masked or excluded"),
             row("Scale bar", ", ".join(bars) or "none",
                 "state that the scale is local where the projection distorts it"),
             row("North arrow", ", ".join(arrows) or "none",
                 "state whether it is true north or grid north"),
             row("Abbreviations", "unconfirmed", "expand every abbreviation used in the figure"),
             ]
    if shared:
        lines.append(row("Shared mapping across panels",
                         "; ".join(", ".join(group) for group in shared),
                         "confirm comparability and identical units"))
    if elements:
        lines.append(row("Auxiliary elements", json.dumps(elements, ensure_ascii=False)[:200],
                         "confirm the inset and the main map refer to the same feature"))
    if sources:
        lines += ["", "## Source files recorded at render time", ""]
        for path, record in sources.items():
            lines.append(f"- `{path}` - {record}")
    lines += ["", "Source checksums and versions are also recorded in the `.qa.json` companion file.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("png")
    parser.add_argument("--width-mm", type=float, help="required for size verification")
    parser.add_argument("--height-mm", type=float, help="required for size verification")
    parser.add_argument("--dpi", type=float, default=300)
    parser.add_argument("--pdf", help="optional PDF to verify size and embedded fonts")
    parser.add_argument("--review", help="optional new directory for a visual review packet")
    parser.add_argument("--caption", default="")
    parser.add_argument("--json", help="optional JSON report destination")
    args = parser.parse_args()
    output = {"png": {"path": args.png, "bytes": Path(args.png).stat().st_size},
              "limits": "Recorded observations only; aesthetics and geographic correctness are not inferred"}
    if args.width_mm and args.height_mm:
        output["png"].update(verify_png(args.png, args.width_mm, args.height_mm, args.dpi))
    elif args.width_mm or args.height_mm:
        raise SystemExit("Provide --width-mm and --height-mm together")
    else:
        output["png"]["size_check"] = "not_checked; provide --width-mm and --height-mm"
    if args.pdf:
        output["pdf"] = {"path": args.pdf}
        if args.width_mm and args.height_mm:
            output["pdf"].update(verify_pdf(args.pdf, args.width_mm, args.height_mm))
        else:
            output["pdf"]["status"] = "not_checked; provide --width-mm and --height-mm"
    if args.review:
        if not (args.width_mm and args.height_mm):
            raise SystemExit("A review packet needs --width-mm and --height-mm")
        output["review_packet"] = review_packet(args.png, args.review, args.width_mm,
                                                args.height_mm, args.caption)
    output["versions"] = versions()
    if args.json:
        Path(args.json).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
