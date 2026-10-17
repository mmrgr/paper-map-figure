"""Report dependencies and fonts without installing or modifying anything.

python check_environment.py

Required packages gate the main rendering path. Optional packages enable the
PDF font/geometry verification and affine-based regression checks; when they
are missing those checks report "not_checked" instead of passing silently.
"""
import json
from importlib import import_module
from importlib.metadata import version, PackageNotFoundError

REQUIRED = {"matplotlib": "matplotlib", "numpy": "numpy", "Pillow": "PIL",
            "geopandas": "geopandas", "rasterio": "rasterio",
            "pyproj": "pyproj", "shapely": "shapely"}
OPTIONAL = {"PyMuPDF": ("fitz", "PDF page size and embedded-font verification"),
            "affine": ("affine", "regression checks on rotated raster corners")}


def _versions(mapping):
    found = {}
    for package, module in mapping.items():
        try:
            import_module(module)
        except ImportError as error:
            found[package] = {"available": False, "reason": str(error)}
            continue
        try:
            found[package] = {"available": True, "version": version(package)}
        except PackageNotFoundError:
            found[package] = {"available": True, "version": "unknown"}
    return found


def check():
    result = {"dependencies": _versions(REQUIRED), "optional": _versions(
        {name: module for name, (module, _) in OPTIONAL.items()}), "fonts": {},
        "ready": True, "notes": []}
    for package, record in result["optional"].items():
        if not record["available"]:
            result["notes"].append(
                f"{package} is missing: {OPTIONAL[package][1]} will report not_checked")
    if any(not record["available"] for record in result["dependencies"].values()):
        result["ready"] = False
    try:
        from figure_layout import configure_fonts
        result["fonts"] = configure_fonts()
    except (ImportError, ValueError) as error:
        result["fonts"] = {"error": str(error)}
        result["ready"] = False
    return result


if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False, indent=2))
