"""Explicit, data-preserving colour mappings and matching legends."""
import numpy as np
from matplotlib import colormaps
from matplotlib.colors import Normalize, TwoSlopeNorm, BoundaryNorm, ListedColormap
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Patch


def continuous(vmin, vmax, cmap="viridis", center=None, nodata="#D9D9D9"):
    if not np.isfinite([vmin, vmax]).all() or vmin >= vmax:
        raise ValueError("Provide confirmed finite vmin < vmax")
    if center is not None and not (np.isfinite(center) and vmin < center < vmax):
        raise ValueError("Confirmed center must be strictly inside limits")
    norm = Normalize(vmin, vmax, clip=False) if center is None else TwoSlopeNorm(center, vmin, vmax)
    colors = colormaps[cmap].copy()
    colors.set_bad(nodata)
    return ScalarMappable(norm=norm, cmap=colors)


def classified(breaks, cmap="YlOrRd", nodata="#D9D9D9"):
    """Explicit intervals [a,b); final upper bound included by map_values().

    Out-of-range values are rejected, never clipped into endpoint classes.
    """
    edges = np.asarray(breaks, dtype=float)
    if edges.ndim != 1 or len(edges) < 2 or not np.isfinite(edges).all() or np.any(np.diff(edges) <= 0):
        raise ValueError("Provide finite strictly increasing confirmed breaks")
    colors = colormaps[cmap].resampled(len(edges) - 1)
    colors.set_bad(nodata)
    return ScalarMappable(norm=BoundaryNorm(edges, colors.N, clip=False), cmap=colors)


def map_values(values, mapping):
    """Return RGBA without mutating values; reject unrepresented finite extremes."""
    data = np.ma.masked_invalid(np.ma.asarray(values, dtype=float)).copy()
    valid = data.compressed()
    if valid.size and (valid.min() < mapping.norm.vmin or valid.max() > mapping.norm.vmax):
        raise ValueError("Values exceed confirmed map range; resolve explicitly")
    if isinstance(mapping.norm, BoundaryNorm):
        maximum = mapping.norm.boundaries[-1]
        data[data == maximum] = np.nextafter(maximum, -np.inf)
    return mapping.to_rgba(data)


def category_rgba(values, colors, nodata_mask=None, nodata="#D9D9D9"):
    """colors maps source class codes to colours; never invent unknown classes."""
    from matplotlib.colors import to_rgba
    values = np.asarray(values)
    mask = np.zeros(values.shape, dtype=bool) if nodata_mask is None else np.asarray(nodata_mask, dtype=bool)
    if mask.shape != values.shape:
        raise ValueError("NoData mask must match values")
    result = np.empty(values.shape + (4,), dtype=float)
    result[...] = to_rgba(nodata)
    assigned = mask.copy()
    for code, color in colors.items():
        selected = (values == code) & ~mask
        result[selected] = to_rgba(color)
        assigned |= selected
    if not assigned.all():
        raise ValueError("Unknown category: provide its confirmed colour or NoData mask")
    return result


def colorbar(fig, cax, mapping, orientation="horizontal", ticks=None):
    """Use exactly the map's ScalarMappable; labels/units supplied by caller."""
    return fig.colorbar(mapping, cax=cax, orientation=orientation, ticks=ticks)


def category_handles(entries):
    """entries: [(confirmed label, colour), ...] in the desired legend order."""
    return [Patch(facecolor=color, edgecolor="none", label=label) for label, color in entries]


def bivariate_rgba(x, y, x_breaks, y_breaks, colors, nodata="#D9D9D9"):
    """Fixed <=3x3 bins; rows low-to-high y, columns low-to-high x."""
    from matplotlib.colors import to_rgba
    x, y = np.asarray(x,dtype=float), np.asarray(y,dtype=float)
    if x.shape != y.shape: raise ValueError("Bivariate values must have same shape")
    xe, ye = np.asarray(x_breaks,dtype=float), np.asarray(y_breaks,dtype=float)
    for edges in (xe,ye):
        if edges.ndim!=1 or not 2<=len(edges)<=4 or not np.isfinite(edges).all() or np.any(np.diff(edges)<=0):
            raise ValueError("Bivariate breaks require 1..3 increasing intervals")
    palette = np.array([[to_rgba(c) for c in row] for row in colors])
    if palette.shape != (len(ye)-1,len(xe)-1,4): raise ValueError("Colour matrix does not match breaks")
    valid = np.isfinite(x)&np.isfinite(y)
    if ((x[valid]<xe[0])|(x[valid]>xe[-1])|(y[valid]<ye[0])|(y[valid]>ye[-1])).any():
        raise ValueError("Bivariate values outside fixed breaks")
    xi = np.minimum(np.searchsorted(xe,x,side="right")-1,len(xe)-2)
    yi = np.minimum(np.searchsorted(ye,y,side="right")-1,len(ye)-2)
    result=np.empty(x.shape+(4,));result[...]=to_rgba(nodata)
    result[valid]=palette[yi[valid],xi[valid]]
    return result


def bivariate_legend(ax, colors, x_label, y_label, fontfamily=None):
    from matplotlib.colors import to_rgba
    palette=np.array([[to_rgba(c) for c in row] for row in colors])
    ax.imshow(palette,origin="lower",interpolation="nearest",aspect="equal")
    ax.set_xticks([]);ax.set_yticks([])
    ax.set_xlabel(x_label,fontfamily=fontfamily or "Arial",fontsize=8)
    ax.set_ylabel(y_label,fontfamily=fontfamily or "Arial",fontsize=8)
    return ax


def size_legend(ax, values, reference_value, reference_size, kind="points", color="#547A9C",edgecolor="#555555",linewidth=.5):
    """Reference symbols only; labels may be added with mixed_label by the caller."""
    values=np.asarray(values,dtype=float)
    if not len(values) or not np.isfinite(values).all() or (values<0).any() or reference_value<=0 or reference_size<=0:
        raise ValueError("Invalid size legend references")
    ax.set_xlim(0,1);ax.set_ylim(0,1);ax.set_axis_off()
    y=1-(np.arange(len(values))+.5)/len(values)
    if kind=="points":
        ax.scatter(np.full(len(values),.15),y,s=values/reference_value*reference_size,color=color,
                   edgecolor=edgecolor,linewidth=linewidth,clip_on=False)
    elif kind=="lines":
        for value,yy in zip(values,y): ax.plot([0,.3],[yy,yy],color=color,lw=value/reference_value*reference_size)
    else: raise ValueError("Legend kind must be points or lines")
    return y.tolist()
