"""Create a labelled A4 placement preview, not a submission page template.

Usage: python page_preview.py map.png preview --width-mm 180
"""
import argparse
from pathlib import Path
from PIL import Image
from figure_layout import configure_fonts, canvas, panel, mixed_label, export


def preview(image_path, output_stem, width_mm=180):
    configure_fonts()
    fig = canvas(210, 297)
    with Image.open(image_path) as image:
        image = image.convert("RGBA")
        iw, ih = image.size
        height_mm = width_mm * ih / iw
        if width_mm <= 0 or width_mm > 180 or height_mm > 237:
            raise ValueError("Figure does not fit this A4 preview; revise width or layout")
        ax = panel(fig, ((210 - width_mm) / 2, 267 - height_mm, width_mm, height_mm))
        ax.imshow(image, interpolation="nearest", aspect="equal")
        ax.set_axis_off()
    header = panel(fig, (15, 278, 180, 10))
    header.set_axis_off()
    mixed_label(header, (0, 1), [("Paper-size preview / ", "en"),
                               (f"A4 assumption; figure {width_mm:g} mm", "en")])
    return export(fig, output_stem)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("output_stem")
    parser.add_argument("--width-mm", type=float, default=180)
    args = parser.parse_args()
    print(preview(args.image, args.output_stem, args.width_mm))
