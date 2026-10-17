"""CRS-aware furniture for ordinary projected Matplotlib axes.

Independent implementation; see references/code-resources.md for reviewed designs.
Call after final limits/aspect are set; rerender after changing map extent.
"""
import numpy as np
from pyproj import CRS, Transformer
from matplotlib.patches import Rectangle, ConnectionPatch


def projected(crs):
    crs = CRS.from_user_input(crs)
    if not crs.is_projected:
        raise ValueError("This backend requires an explicit projected display CRS")
    return crs


def converters(crs):
    crs = projected(crs)
    return (Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True),
            Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True), crs.get_geod())


def xy_at(ax, fraction):
    if len(fraction) != 2 or not np.isfinite(fraction).all() or not all(0 < v < 1 for v in fraction):
        raise ValueError("Furniture location must be inside axes (0,1)")
    return ax.transData.inverted().transform(ax.transAxes.transform(fraction))


def horizontal_distance(crs, x0, x1, y):
    """Ellipsoidal length sampled along a horizontal projected map segment."""
    inverse, _, geod = converters(crs)
    xs = np.linspace(x0, x1, 65)
    lon, lat = inverse.transform(xs, np.full_like(xs, y), errcheck=True)
    if not np.isfinite([lon, lat]).all():
        raise ValueError("Scale bar falls outside projection domain")
    distance = abs(geod.line_length(lon, lat))
    if not np.isfinite(distance) or distance <= 0:
        raise ValueError("Unable to calibrate scale")
    return float(distance)


def scale_bar(ax, crs, length_m, location=(0.08, 0.10), segments=2,
              style="boxes", fontsize=8, height_mm=1.0, max_variation=0.05,
              fontfamily=None):
    """Locally calibrated ground-distance bar; explicit length in metres.

    Reports map-wide sampled scale variation. Does not assert uniform global scale.
    """
    if not np.isfinite(length_m) or length_m <= 0:
        raise ValueError("Scale length must be finite and positive")
    if not isinstance(segments, int) or not 1 <= segments <= 8:
        raise ValueError("Use 1..8 scale segments")
    if style not in ("boxes", "ticks") or height_mm <= 0:
        raise ValueError("Invalid scale style or height")
    ax.figure.canvas.draw()
    x0, y = xy_at(ax, location)
    right = ax.get_xlim()[1]
    if ax.get_xlim()[0] >= right or ax.get_ylim()[0] >= ax.get_ylim()[1]:
        raise ValueError("Inverted map axes are unsupported")
    maximum = x0 + (right - x0) * 0.85
    if horizontal_distance(crs, x0, maximum, y) < length_m:
        raise ValueError("Requested scale bar does not fit; choose a shorter distance")
    lo, hi = x0, maximum
    for _ in range(60):
        mid = (lo + hi) / 2
        if horizontal_distance(crs, x0, mid, y) < length_m:
            lo = mid
        else:
            hi = mid
    x1 = (lo + hi) / 2
    # Equal ground-distance subdivisions; they need not have identical pixel width.
    edges = [x0]
    for n in range(1, segments):
        lo, hi = x0, x1
        for _ in range(50):
            mid = (lo + hi) / 2
            if horizontal_distance(crs, x0, mid, y) < length_m * n / segments:
                lo = mid
            else:
                hi = mid
        edges.append((lo + hi) / 2)
    edges.append(x1)
    ymin, ymax = ax.get_ylim()
    ax_height_mm = ax.get_window_extent().height / ax.figure.dpi * 25.4
    dh = height_mm / ax_height_mm * (ymax - ymin)
    unit, divisor = ("km", 1000) if length_m >= 1000 else ("m", 1)
    for i in range(segments):
        if style == "boxes":
            ax.add_patch(Rectangle((edges[i], y), edges[i+1]-edges[i], dh,
                                  facecolor="black" if i % 2 == 0 else "white",
                                  edgecolor="black", linewidth=.5, zorder=30))
        else:
            ax.plot(edges[i:i+2], [y, y], color="black", linewidth=.7, zorder=30)
    labels=[]
    for i, x in enumerate(edges):
        if style == "ticks":
            ax.plot([x, x], [y, y+dh], color="black", linewidth=.7, zorder=30)
        label = f"{length_m*i/segments/divisor:g}"
        if i == segments:
            label += " " + unit
        labels.append(ax.annotate(label, (x, y), xytext=(0, -3), textcoords="offset points",
                    ha="center", va="top", fontfamily=fontfamily or "Arial", fontsize=fontsize,
                    zorder=31))
    ax.figure.canvas.draw()
    renderer=ax.figure.canvas.get_renderer()
    bounds=[text.get_window_extent(renderer) for text in labels]
    labels_reduced=False
    if any(bounds[i].x1+2>bounds[i+1].x0 for i in range(len(bounds)-1)):
        for label in labels[1:-1]: label.set_visible(False)
        labels_reduced=True
        if bounds[0].x1+2>bounds[-1].x0:
            raise ValueError("Scale labels cannot fit at final size; choose a longer bar or larger panel")
    measured = horizontal_distance(crs, x0, x1, y)
    span = ax.get_xlim()[1] - ax.get_xlim()[0]
    sampled = []
    for fx in (.15, .5, .85):
        for fy in (.15, .5, .85):
            px, py = xy_at(ax, (fx, fy))
            sampled.append(horizontal_distance(crs, px, px+span*.001, py)/(span*.001))
    local = length_m/(x1-x0)
    variation = float(max(abs(np.array(sampled)/local - 1)))
    return {"length_m": length_m, "measured_m": measured,
            "endpoints_xy": [[float(x0), float(y)], [float(x1), float(y)]],
            "reference": "local horizontal projected path, ellipsoidal distance",
            "sampled_scale_variation": variation, "intermediate_labels_hidden":labels_reduced,
            "warning": "Scale varies across map; label as local or omit" if variation > max_variation else None}


def north_arrow(ax, crs, location=(.90, .82), size_mm=9, fontsize=9, fontfamily=None):
    """True north at the arrow anchor, computed on the CRS ellipsoid."""
    if not np.isfinite(size_mm) or size_mm <= 0:
        raise ValueError("North arrow size must be positive")
    ax.figure.canvas.draw()
    inverse, forward, geod = converters(crs)
    x, y = xy_at(ax, location)
    lon, lat = inverse.transform(x, y, errcheck=True)
    if abs(lat) > 89.5:
        raise ValueError("Near-pole north direction requires specialist treatment")
    nl, nt, _ = geod.fwd(lon, lat, 0, 100)
    nx, ny = forward.transform(nl, nt, errcheck=True)
    origin = ax.transData.transform((x, y))
    direction = ax.transData.transform((nx, ny)) - origin
    if not np.isfinite(direction).all() or np.linalg.norm(direction) < 1e-10:
        raise ValueError("Cannot determine true north; no fallback arrow")
    direction /= np.linalg.norm(direction)
    end = origin + direction * size_mm / 25.4 * ax.figure.dpi
    end_fraction = ax.transAxes.inverted().transform(end)
    if not all(.03 < v < .97 for v in end_fraction):
        raise ValueError("North arrow would extend beyond map frame")
    ax.annotate("", xy=end_fraction, xytext=location, xycoords="axes fraction",
                arrowprops={"arrowstyle": "-|>", "color": "black", "lw": .9,
                            "mutation_scale": 12}, zorder=30)
    ax.annotate("N", xy=end_fraction, xycoords="axes fraction", xytext=(0, 3),
                textcoords="offset points", ha="center", va="bottom",
                fontfamily=fontfamily or "Arial", fontsize=fontsize, fontweight="bold", zorder=31)
    return {"anchor_lonlat": [float(lon), float(lat)], "north": "true at anchor",
            "screen_angle_from_up_deg": float(np.degrees(np.arctan2(direction[0], direction[1])))}


def extent_link(fig, detail_ax, detail_crs, context_ax, context_crs,
                color="#303030", connect=True, linewidth=.7):
    """Densify the actual detail viewport perimeter into context CRS."""
    x0, x1 = detail_ax.get_xlim(); y0, y1 = detail_ax.get_ylim()
    n = 65
    xs = np.r_[np.linspace(x0,x1,n), np.full(n,x1), np.linspace(x1,x0,n), np.full(n,x0)]
    ys = np.r_[np.full(n,y0), np.linspace(y0,y1,n), np.full(n,y1), np.linspace(y1,y0,n)]
    transform = Transformer.from_crs(projected(detail_crs), projected(context_crs), always_xy=True)
    xx, yy = transform.transform(xs, ys, errcheck=True)
    if not np.isfinite([xx, yy]).all():
        raise ValueError("Inset extent crosses invalid projection coordinates")
    context_ax.plot(xx, yy, color=color, linewidth=linewidth, zorder=25)
    if connect:
        # Right edge of detail to the corresponding transformed points in context.
        for point in [(x1,y0), (x1,y1)]:
            target = transform.transform(*point, errcheck=True)
            fig.add_artist(ConnectionPatch(xyA=point, xyB=target,
                           coordsA=detail_ax.transData, coordsB=context_ax.transData,
                           color=color, linewidth=linewidth, zorder=24))
    return {"detail_extent": [x0,y0,x1,y1], "perimeter_vertices": len(xx),
            "context_bounds": [float(min(xx)),float(min(yy)),float(max(xx)),float(max(yy))]}


def graticule(ax, crs, longitudes, latitudes, lonlat_bounds, color="#AAAAAA"):
    """Draw explicitly specified geographic lines, no automatic extent inference."""
    west, south, east, north = lonlat_bounds
    if not (-180 <= west < east <= 180 and -89.5 < south < north < 89.5):
        raise ValueError("Use non-dateline-crossing lon/lat bounds away from poles")
    transform = Transformer.from_crs(4326, projected(crs), always_xy=True)
    for lon in longitudes:
        if not west <= lon <= east: raise ValueError("Longitude outside graticule bounds")
        xx, yy = transform.transform(np.full(361,lon), np.linspace(south,north,361), errcheck=True)
        ax.plot(xx, yy, color=color, lw=.35, ls=":", zorder=8)
    for lat in latitudes:
        if not south <= lat <= north: raise ValueError("Latitude outside graticule bounds")
        xx, yy = transform.transform(np.linspace(west,east,361), np.full(361,lat), errcheck=True)
        ax.plot(xx, yy, color=color, lw=.35, ls=":", zorder=8)
