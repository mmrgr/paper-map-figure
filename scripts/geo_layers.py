"""Read-only raster/vector rendering. No classification fitting or analysis."""
from pathlib import Path
import hashlib
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds
from pyproj import CRS
from map_styles import map_values, category_rgba
from geo_elements import projected


def missing_mask(series):
    """Rows that render as NoData: absent values and non-finite numbers.

    map_values() and bivariate_rgba() both paint a masked or non-finite value
    with the NoData colour rather than dropping the feature, so a count that
    gates the NoData legend has to follow exactly the same rule. Counting only
    the declared `column` misses bivariate layers and misses +/-inf, which is
    how grey NoData areas used to reach print without a legend.
    """
    mask = np.asarray(series.isna().to_numpy(), dtype=bool)
    try:
        values = np.asarray(series, dtype=float)
    except (TypeError, ValueError):
        return mask
    return mask | ~np.isfinite(values)


def source_record(path):
    path = Path(path).resolve()
    # Shapefile is a bundle; include every same-stem companion in provenance.
    files = sorted(path.parent.glob(path.stem + ".*")) if path.suffix.lower()==".shp" else [path]
    records = []
    for file in files:
        digest = hashlib.sha256()
        with file.open("rb") as stream:
            for block in iter(lambda: stream.read(1024*1024), b""):
                digest.update(block)
        records.append({"path":str(file), "sha256":digest.hexdigest()})
    return records


def raster(ax, path, display_crs, mapping=None, categories=None, band=1,
           extent=None, max_pixels=4000000):
    """Affine pixel corners preserve rotation/shear. No reprojection/resampling.

    extent may limit reading for north-up rasters only; geographic positions remain.
    """
    target = projected(display_crs)
    with rasterio.open(path) as src:
        if src.crs is None or not CRS(src.crs).equals(target):
            raise ValueError("Raster CRS must match projected panel CRS; provide aligned result")
        if src.gcps[0] or src.rpcs:
            raise ValueError("GCP/RPC geolocation requires an upstream georeferenced display raster")
        if not 1 <= band <= src.count: raise ValueError("Invalid raster band")
        if src.scales[band-1] != 1 or src.offsets[band-1] != 0:
            raise ValueError("Raster has scale/offset metadata; supply confirmed physical-value result")
        window = None
        if extent is not None and src.transform.b == 0 and src.transform.d == 0 and src.transform.e < 0:
            try:
                raw = from_bounds(*extent, transform=src.transform)
                left,top=np.floor(raw.col_off),np.floor(raw.row_off)
                right,bottom=np.ceil(raw.col_off+raw.width),np.ceil(raw.row_off+raw.height)
                window=rasterio.windows.Window(left,top,right-left,bottom-top)
                window = window.intersection(rasterio.windows.Window(0,0,src.width,src.height))
            except rasterio.errors.WindowError:
                raise ValueError("Raster does not intersect panel")
        rows = src.height if window is None else int(window.height)
        cols = src.width if window is None else int(window.width)
        if rows*cols > max_pixels:
            raise ValueError("Visible raster exceeds pixel budget; provide prepared display raster, no silent downsampling")
        data = src.read(band, window=window, masked=True)
        transform = src.transform if window is None else src.window_transform(window)
        mask = np.ma.getmaskarray(data) | ~np.isfinite(data.data)
        if categories is not None:
            rgba = category_rgba(data.data, categories, mask)
        elif mapping is not None:
            rgba = map_values(np.ma.array(data.data, mask=mask), mapping)
        else:
            raise ValueError("Raster needs explicit mapping or categories")
        rr, cc = np.meshgrid(np.arange(data.shape[0]+1), np.arange(data.shape[1]+1), indexing="ij")
        xx = transform.a*cc + transform.b*rr + transform.c
        yy = transform.d*cc + transform.e*rr + transform.f
        artist = ax.pcolormesh(xx, yy, rgba, shading="flat", antialiased=False,
                              rasterized=True, zorder=1)
        valid = np.ma.array(data.data,mask=mask).compressed()
        info = {"type":"raster", "band":band, "crs":str(src.crs),
                "shape":list(data.shape), "nodata_count":int(mask.sum()),
                "min":float(valid.min()) if valid.size else None,
                "max":float(valid.max()) if valid.size else None,
                "affine":list(transform)[:6], "resampled":False}
    return artist, info


def vector(ax, path, display_crs, column=None, mapping=None, categories=None,
           color="#E8E8E8", edgecolor="#555555", linewidth=.5,
           markersize=16, layer=None, proportional=None, bivariate=None):
    gdf = gpd.read_file(path, **({"layer":layer} if layer else {}))
    if gdf.crs is None: raise ValueError("Vector CRS missing")
    if gdf.empty or gdf.geometry.isna().any() or gdf.geometry.is_empty.any() or not gdf.is_valid.all():
        raise ValueError("Vector contains empty/invalid geometries; correct upstream")
    original_crs = gdf.crs
    drawn = gdf.to_crs(projected(display_crs))
    colors = color
    if column is not None:
        values = gdf[column].to_numpy()
        if categories is not None:
            colors = category_rgba(values, categories, gdf[column].isna().to_numpy())
        elif mapping is not None:
            colors = map_values(values, mapping)
        else: raise ValueError("Thematic column requires explicit mapping")
    if proportional:
        if not drawn.geom_type.isin(["Point","MultiPoint"]).all():
            raise ValueError("Proportional symbols require existing point locations")
        values = gdf[proportional["column"]].to_numpy(dtype=float)
        reference = float(proportional["reference_value"])
        area = float(proportional["reference_area_pt2"])
        if not np.isfinite([reference,area]).all() or reference <= 0 or area <= 0 or not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("Invalid proportional symbol values/reference")
        markersize = values / reference * area
    if bivariate:
        if column is not None: raise ValueError("Choose one colour mapping per layer")
        from map_styles import bivariate_rgba
        colors = bivariate_rgba(gdf[bivariate["x_column"]],gdf[bivariate["y_column"]],
                                bivariate["x_breaks"],bivariate["y_breaks"],bivariate["colors"])
    drawn.plot(ax=ax, color=colors, edgecolor=edgecolor, linewidth=linewidth,
               markersize=markersize, aspect="equal", zorder=3)
    # Every column that decides a colour can paint NoData, and a bivariate layer
    # sets none of `column`, so all of them have to be counted together.
    painted = []
    if column is not None: painted.append(column)
    if proportional: painted.append(proportional["column"])
    if bivariate: painted += [bivariate["x_column"], bivariate["y_column"]]
    nodata = np.zeros(len(gdf), dtype=bool)
    for name in painted:
        nodata |= missing_mask(gdf[name])
    return {"type":"vector", "features":len(gdf), "source_crs":str(original_crs),
            "display_crs":str(drawn.crs), "column":column, "geometry_modified":False,
            "display_transformed":not CRS(original_crs).equals(CRS(drawn.crs)),
            "nodata_count":int(nodata.sum())}


def flow(ax, path, display_crs, column, reference_value, reference_width_pt=1,
         color="#547A9C", layer=None, direction_from_vertex_order=False):
    """Existing line geometry only. No OD routing, bundling or aggregation."""
    gdf = gpd.read_file(path, **({"layer":layer} if layer else {}))
    if gdf.crs is None or gdf.empty or gdf.geometry.isna().any() or gdf.geometry.is_empty.any() or not gdf.is_valid.all(): raise ValueError("Invalid flow layer")
    if not gdf.geom_type.isin(["LineString","MultiLineString"]).all(): raise ValueError("Flows require existing lines")
    vals = gdf[column].to_numpy(dtype=float)
    if not np.isfinite(vals).all() or not np.isfinite([reference_value,reference_width_pt]).all() or (vals<0).any() or reference_value<=0 or reference_width_pt<=0:
        raise ValueError("Flow widths require nonnegative values and positive reference")
    drawn=gdf.to_crs(projected(display_crs))
    drawn.plot(ax=ax, color=color,
             linewidth=vals/reference_value*reference_width_pt, aspect="equal", zorder=4)
    if direction_from_vertex_order:
        for geom,value in zip(drawn.geometry,vals):
            if value==0: continue
            parts=geom.geoms if geom.geom_type=="MultiLineString" else [geom]
            for part in parts:
                if part.length<=0: raise ValueError("Cannot orient zero-length flow line")
                start,end=part.interpolate(.48,normalized=True),part.interpolate(.52,normalized=True)
                ax.annotate("",xy=(end.x,end.y),xytext=(start.x,start.y),
                            arrowprops={"arrowstyle":"-|>","color":color,"lw":value/reference_value*reference_width_pt,
                                        "mutation_scale":8},zorder=5)
    return {"type":"flow", "features":len(gdf), "column":column,
            "direction":"user-confirmed vertex order" if direction_from_vertex_order else "not inferred; lines only", "aggregation":False}
