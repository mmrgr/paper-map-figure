"""Simulate colour-vision deficiencies on the colours a figure actually uses.

python cvd_check.py --config config.json
python cvd_check.py --colors "#287A45,#C85A54" --labels forest,built-up

Applies the Machado, Oliveira & Fernandes (2009) severity matrices in linear
RGB, converts the result to CIELAB and reports CIEDE2000 distances for the
pairs that must stay apart on the printed map. Reports only; never rewrites a
confirmed colour mapping.
"""
import argparse
import json
from math import atan2, degrees, exp, hypot, sin, cos, radians, sqrt
from pathlib import Path
import numpy as np
from matplotlib.colors import to_hex, to_rgb

KINDS = ("protan", "deutan", "tritan")

# Machado et al. 2009, severity 1.0, linear RGB, row-major.
MATRICES = {
    "protan": [[0.152286, 1.052583, -0.204868],
               [0.114503, 0.786281, 0.099216],
               [-0.003882, -0.048116, 1.051998]],
    "deutan": [[0.367322, 0.860646, -0.227968],
               [0.280085, 0.672501, 0.047413],
               [-0.011820, 0.042940, 0.968881]],
    "tritan": [[1.255528, -0.076749, -0.178779],
               [-0.078411, 0.930809, 0.147602],
               [0.004733, 0.691367, 0.303900]],
}
# CIE standard D65 white point and the sRGB-to-XYZ matrix.
D65 = np.array([0.95047, 1.00000, 1.08883])
SRGB_TO_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375],
                        [0.2126729, 0.7151522, 0.0721750],
                        [0.0193339, 0.1191920, 0.9503041]])


def srgb_to_linear(rgb):
    rgb = np.asarray(rgb, dtype=float)
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(rgb):
    rgb = np.clip(np.asarray(rgb, dtype=float), 0.0, 1.0)
    return np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * rgb ** (1 / 2.4) - 0.055)


def to_lab(rgb):
    """sRGB 0..1 to CIELAB under D65."""
    linear = srgb_to_linear(rgb)
    xyz = SRGB_TO_XYZ @ linear / D65
    delta = 6 / 29
    f = np.where(xyz > delta ** 3, np.cbrt(xyz), xyz / (3 * delta ** 2) + 4 / 29)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def simulate(rgb, kind, severity=1.0):
    """Linear-RGB severity matrix; severity<1 interpolates towards identity."""
    if kind not in MATRICES:
        raise ValueError(f"Unknown deficiency kind: {kind}")
    if not 0.0 <= severity <= 1.0:
        raise ValueError("Severity must be within 0..1")
    full = np.asarray(MATRICES[kind], dtype=float)
    matrix = (1 - severity) * np.eye(3) + severity * full
    return linear_to_srgb(matrix @ srgb_to_linear(rgb))


def simulate_hex(color, kind, severity=1.0):
    from matplotlib.colors import to_hex
    return to_hex(simulate(to_rgb(color), kind, severity))


def delta_e_2000(lab1, lab2):
    """CIEDE2000 with kL=kC=kH=1."""
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2
    c1, c2 = hypot(a1, b1), hypot(a2, b2)
    c_bar = (c1 + c2) / 2
    g = 0.5 * (1 - sqrt(c_bar ** 7 / (c_bar ** 7 + 25 ** 7)))
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = hypot(a1p, b1), hypot(a2p, b2)
    h1p = degrees(atan2(b1, a1p)) % 360 if c1p else 0.0
    h2p = degrees(atan2(b2, a2p)) % 360 if c2p else 0.0
    d_lp = l2 - l1
    d_cp = c2p - c1p
    if c1p * c2p == 0:
        d_hp, h_bar = 0.0, h1p + h2p
    else:
        raw = h2p - h1p
        d_hp = raw - 360 if raw > 180 else (raw + 360 if raw < -180 else raw)
        if abs(h1p - h2p) <= 180:
            h_bar = (h1p + h2p) / 2
        elif h1p + h2p < 360:
            h_bar = (h1p + h2p + 360) / 2
        else:
            h_bar = (h1p + h2p - 360) / 2
    d_h = 2 * sqrt(c1p * c2p) * sin(radians(d_hp / 2))
    l_bar = (l1 + l2) / 2
    c_bar_p = (c1p + c2p) / 2
    t = (1 - 0.17 * cos(radians(h_bar - 30)) + 0.24 * cos(radians(2 * h_bar))
         + 0.32 * cos(radians(3 * h_bar + 6)) - 0.20 * cos(radians(4 * h_bar - 63)))
    d_theta = 30 * exp(-(((h_bar - 275) / 25) ** 2))
    r_c = 2 * sqrt(c_bar_p ** 7 / (c_bar_p ** 7 + 25 ** 7))
    s_l = 1 + (0.015 * (l_bar - 50) ** 2) / sqrt(20 + (l_bar - 50) ** 2)
    s_c, s_h = 1 + 0.045 * c_bar_p, 1 + 0.015 * c_bar_p * t
    r_t = -sin(radians(2 * d_theta)) * r_c
    return sqrt((d_lp / s_l) ** 2 + (d_cp / s_c) ** 2 + (d_h / s_h) ** 2
                + r_t * (d_cp / s_c) * (d_h / s_h))


def mapping_colors(mapping, count=None):
    """Colours a mapping actually paints, in ascending value/legend order.

    Discrete class colours are sampled at bin midpoints so the result matches
    the legend swatches exactly; a sampled ramp includes both endpoints.
    """
    if isinstance(mapping, dict):
        return [color for _, color in sorted(mapping.items())]
    cmap = mapping.cmap
    if count is None:
        count = getattr(cmap, "N", None)
        if not count:
            raise ValueError("Provide the number of levels to sample")
        positions = (np.arange(count) + 0.5) / count
    else:
        if count < 2:
            raise ValueError("Sample at least two levels of a ramp")
        positions = np.linspace(0, 1, count)
    return [to_hex(rgba) for rgba in cmap(positions)]


def pairs_within(group, adjacent_only):
    """Adjacent levels only when a ramp carries an order; all pairs otherwise."""
    if adjacent_only:
        return [(group[i], group[i + 1]) for i in range(len(group) - 1)]
    return [(group[i], group[j]) for i in range(len(group))
            for j in range(i + 1, len(group))]


def worst_case(first, second, kinds=KINDS, severities=(1.0, 0.6)):
    """Smallest CIEDE2000 distance across every simulated deficiency."""
    worst = None
    for kind in kinds:
        for severity in severities:
            simulated = [simulate(to_rgb(first), kind, severity),
                         simulate(to_rgb(second), kind, severity)]
            distance = delta_e_2000(to_lab(simulated[0]), to_lab(simulated[1]))
            if worst is None or distance < worst["delta_e"]:
                worst = {"kind": kind, "severity": severity, "delta_e": round(distance, 2),
                         "simulated": [to_hex(simulated[0]), to_hex(simulated[1])]}
    return worst


def ramp_lightness(colors, kind, severity, tolerance=0.5):
    """CIELAB lightness along a ramp, plus positions where it reverses.

    A continuous ramp is read through lightness, not through adjacent colour
    distance, so a reversal is the defect worth reporting: it invents a
    boundary that the data does not contain.
    """
    series = [round(to_lab(simulate(to_rgb(color), kind, severity))[0], 2) for color in colors]
    direction = 1 if series[-1] >= series[0] else -1
    reversals = [index for index in range(len(series) - 1)
                 if direction * (series[index + 1] - series[index]) < -tolerance]
    return {"direction": "increasing" if direction > 0 else "decreasing",
            "lightness_range": round(max(series) - min(series), 2),
            "reversal_positions": reversals, "lightness": series}


def check_entries(entries, nodata=None, threshold=10.0,
                  severities=(1.0, 0.6), kinds=KINDS, adjacent_only=None,
                  nodata_panels=None):
    """entries: [{"group","label","color","mode"}]. Returns findings, worst first.

    Unordered categories are compared in every combination, because any two
    legend classes may end up adjacent. Classified bins are compared with their
    neighbours. Continuous ramps are checked for lightness reversals instead;
    neighbouring colours are supposed to be close there. Continuous ramps also
    appear in ramp_checks() as evidence, whether or not they fail.

    An empty entry list is a legal figure, not a defective one: a map carrying
    only one fixed-colour polygon or flow layer has no thematic mapping to
    simulate. The caller reads that situation from the returned counts, never
    from an exception.

    nodata_panels=None keeps the historical behaviour of comparing the NoData
    grey with every entry. A concrete set of panel ids restricts the comparison
    to colours actually drawn in those panels, so a near-grey fill in an
    unrelated locator panel is not reported as confusable with missing data.
    """
    entries = list(entries)
    if threshold <= 0:
        raise ValueError("Threshold must be positive")
    groups = {}
    for item in entries:
        groups.setdefault(item["group"], []).append(item)
    findings = []
    ramps = []
    for name, items in groups.items():
        mode = items[0].get("mode", "categorical")
        if mode == "continuous" and adjacent_only is None:
            reversals = {}
            for kind in kinds:
                for severity in severities:
                    case = f"{kind} at severity {severity:g}"
                    analysis = ramp_lightness([item["color"] for item in items], kind, severity)
                    ramps.append({"group": name, "case": case, **analysis})
                    for index in analysis["reversal_positions"]:
                        reversals.setdefault(index, []).append(case)
            if reversals:
                positions = sorted(reversals)
                findings.append({"group": name, "kind": "lightness_reversal",
                                 "positions": positions,
                                 "between": [f"{items[index]['label']} to "
                                             f"{items[index + 1]['label']}" for index in positions],
                                 "affected_cases": sorted({case for cases in reversals.values()
                                                           for case in cases}),
                                 "lightness": ramps[0]["lightness"],
                                 "note": "A ramp that stops getting lighter introduces a boundary "
                                         "the data does not contain; use a perceptually uniform "
                                         "ramp or an ordered discrete scheme"})
            continue
        ordered = adjacent_only if adjacent_only is not None else mode != "categorical"
        for first, second in pairs_within(items, bool(ordered)):
            worst = worst_case(first["color"], second["color"], kinds, severities)
            if worst["delta_e"] >= threshold:
                continue
            findings.append({"group": name, "kind": "pair_distance",
                             "pair": [first["label"], second["label"]],
                             "colors": [first["color"], second["color"]],
                             "simulated": worst["simulated"],
                             "worst_case": f"{worst['kind']} at severity {worst['severity']:g}",
                             "delta_e": worst["delta_e"], "threshold": threshold})
    if nodata:
        scoped = entries if nodata_panels is None else [
            item for item in entries
            if not item.get("panel") or set(item["panel"]) & set(nodata_panels)]
        for item in scoped:
            worst = worst_case(nodata, item["color"], kinds, severities)
            if worst["delta_e"] >= threshold:
                continue
            findings.append({"group": item["group"], "kind": "nodata_distance",
                             "pair": [f"NoData {nodata}", item["label"]],
                             "colors": [nodata, item["color"]], "simulated": worst["simulated"],
                             "worst_case": f"{worst['kind']} at severity {worst['severity']:g}",
                             "delta_e": worst["delta_e"], "threshold": threshold})
    findings.sort(key=lambda item: (item.get("delta_e", 0), item["group"],
                                    item.get("pair", [])))
    return findings, ramps


def entries_from_config(config_path):
    """Read the colours a render_map configuration paints; never infer values.

    Thematic mappings, bivariate matrices and the fixed colours of vector and
    flow layers are all collected, so the check covers what the figure really
    paints instead of only what carries a legend. Each entry records the panels
    it is drawn in, which lets a NoData grey be compared only with colours that
    can sit next to it in the same panel.

    Outline colours are left out on purpose: a hairline stroke is not a data
    class and comparing it with the fill it borders reports nothing a reader
    would act on. Fills and flow strokes are included even when they fall back
    to the layer default, because the default is still painted.
    """
    import map_styles
    source = Path(config_path).resolve()
    cfg = json.loads(source.read_text(encoding="utf-8"))
    specs = cfg.get("mappings", {})
    panels = cfg.get("panels", [])
    # A mapping that no layer references paints nothing and is not checked.
    used = {layer.get("mapping") for panel in panels
            for layer in panel.get("layers", []) if layer.get("mapping")}
    mappings = {}
    for key, spec in specs.items():
        kind = spec["type"]
        if kind == "categorical":
            mappings[key] = {"mode": "categorical", "labels": [e["label"] for e in spec["entries"]],
                             "colors": [e["color"] for e in spec["entries"]]}
        elif kind == "classified":
            mapping = map_styles.classified(spec["breaks"], spec.get("cmap", "YlOrRd"))
            breaks = spec["breaks"]
            mappings[key] = {"mode": "classified", "colors": mapping_colors(mapping),
                             "labels": [f"[{a:g},{b:g})" for a, b in zip(breaks[:-2], breaks[1:-1])]
                                       + [f"[{breaks[-2]:g},{breaks[-1]:g}]"]}
        elif kind == "continuous":
            mapping = map_styles.continuous(spec["vmin"], spec["vmax"], spec.get("cmap", "viridis"),
                                            spec.get("center"))
            spans = np.linspace(spec["vmin"], spec["vmax"], 9)
            mappings[key] = {"mode": "continuous", "colors": mapping_colors(mapping, 9),
                             "labels": [f"{value:g}" for value in spans]}
        else:
            raise ValueError(f"Unsupported mapping type in configuration: {kind}")
    entries = []
    # A shared mapping paints the same colours wherever it is used, so the
    # panels are recorded as an explicit list rather than by splitting groups.
    for key, spec in mappings.items():
        if key not in used:
            continue
        where = {panel.get("id") for panel in panels
                 for layer in panel.get("layers", []) if layer.get("mapping") == key}
        for label, color in zip(spec["labels"], spec["colors"]):
            entries.append({"group": key, "label": f"{key} {label}", "color": color,
                            "mode": spec["mode"], "panel": sorted(where)})
    for panel in panels:
        key = panel.get("id")
        for layer in panel.get("layers", []):
            spec = layer.get("bivariate")
            if not spec:
                continue
            matrix = spec["colors"]
            # Rows and columns are each an ordered run, so neighbours are enough.
            for row, colors in enumerate(matrix):
                entries.extend({"group": f"bivariate {key} row {row}", "mode": "bivariate",
                                "label": f"row {row} column {column}", "color": color,
                                "panel": [key]}
                               for column, color in enumerate(colors))
            for column in range(len(matrix[0])):
                entries.extend({"group": f"bivariate {key} column {column}", "mode": "bivariate",
                                "label": f"column {column} row {row}",
                                "color": row_colors[column], "panel": [key]}
                               for row, row_colors in enumerate(matrix))
    # Fixed colours: classification carried by the existing drawing, so they are
    # only checked for distinctness, never for ramp order.
    for panel in panels:
        key = panel.get("id")
        fixed = []
        for index, layer in enumerate(panel.get("layers", [])):
            if layer.get("bivariate"):
                continue
            kind = layer.get("type")
            if kind == "vector":
                fixed.append((f"{key} layer {index} fill", layer.get("color", "#E8E8E8")))
            elif kind == "flow":
                fixed.append((f"{key} layer {index} flow", layer.get("color", "#547A9C")))
        if not fixed:
            continue
        entries.extend({"group": f"fixed colours {key}", "mode": "categorical",
                        "label": label, "color": color, "panel": [key]}
                       for label, color in fixed)
    return entries


def swatch(entries, output, threshold=10.0):
    """Side-by-side original/simulated swatches; a visual aid, not evidence."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.patches import Rectangle
    entries = list(entries)
    rows = [(entry, kind, severity) for entry in entries
            for kind in KINDS for severity in (1.0, 0.6)]
    height = 0.34 * len(rows) + 1.0
    fig = plt.figure(figsize=(6.6, height), facecolor="white")
    ax = fig.add_axes([0.28, 1.0 / height, 0.68, 1 - 1.6 / height])
    ax.set_xlim(0, 3)
    ax.set_ylim(0, len(rows))
    ax.set_axis_off()
    for index, (entry, kind, severity) in enumerate(rows):
        y = len(rows) - index - 1
        for column, color in enumerate((entry["color"],
                                        simulate_hex(entry["color"], kind, severity))):
            ax.add_patch(Rectangle((column * 1.05, y + .12), .5, .76, facecolor=color,
                                   edgecolor="#555555", linewidth=.5, transform=ax.transData))
        ax.text(2.2, y + .5, f"{kind} {severity:g}", fontsize=7, va="center", color="#333333")
    fig.savefig(output, dpi=300, facecolor="white")
    plt.close(fig)
    return str(output)


def report(entries, nodata=None, threshold=10.0, nodata_panels=None):
    entries = list(entries)
    findings, ramps = check_entries(entries, nodata=nodata, threshold=threshold,
                                   nodata_panels=nodata_panels)
    result = {"checked_colors": len(entries), "threshold": threshold, "findings": findings,
              "ramp_checks": ramps,
              "limitations": ["Simulated with Machado 2009 severity matrices in linear RGB; "
                              "intermediate severities interpolate towards identity",
                              "Threshold is this skill's working value for adjacent classes, "
                              "not an accessibility standard",
                              "Not a substitute for printing a proof or for a formal audit",
                              "This check never changes a confirmed colour mapping"]}
    if not entries:
        # A figure of one fixed-colour layer is legal and simply has nothing to
        # simulate. Reporting that plainly is required; failing the render is not.
        result["applicable"] = False
        result["note"] = ("No colours to simulate: the figure declares no thematic mapping "
                          "and no fixed layer colour. Check an explicit palette with "
                          "cvd_check.py --colors instead.")
    elif len(entries) < 2 and not nodata:
        # One colour on its own cannot be confused with anything either.
        result["applicable"] = False
        result["note"] = ("A single colour cannot be confused with another; add a second "
                          "class, a fixed layer colour or the NoData grey to compare it with.")
    else:
        result["applicable"] = True
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="render_map.py configuration to read colours from")
    parser.add_argument("--colors", help="comma-separated colours instead of a configuration")
    parser.add_argument("--labels", help="comma-separated labels for --colors")
    parser.add_argument("--nodata", default="#D9D9D9")
    parser.add_argument("--threshold", type=float, default=10.0)
    parser.add_argument("--adjacent-only", action="store_true",
                        help="compare only neighbouring colours in the order given")
    parser.add_argument("--swatch", help="optional PNG comparing original and simulated colours")
    parser.add_argument("--json", help="optional JSON report destination")
    args = parser.parse_args()
    if bool(args.config) == bool(args.colors):
        raise SystemExit("Provide exactly one of --config or --colors")
    if args.colors:
        colors = [c.strip() for c in args.colors.split(",") if c.strip()]
        labels = [l.strip() for l in (args.labels or "").split(",") if l.strip()]
        if labels and len(labels) != len(colors):
            raise SystemExit("--labels must match --colors in length")
        entries = [{"group": "provided", "label": label or color, "color": color,
                    "mode": "classified" if args.adjacent_only else "categorical"}
                   for label, color in zip(labels or colors, colors)]
    else:
        entries = entries_from_config(args.config)
    output = report(entries, args.nodata, args.threshold)
    if args.swatch:
        output["swatch"] = swatch(entries, args.swatch, args.threshold)
    if args.json:
        Path(args.json).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
