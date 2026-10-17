"""Histogram with existing breaks, not a classification fitting tool.

python color_diagnostics.py data.tif output --breaks 0 10 20 --band 1
For vector: --column FIELD. No source mutation or spatial statistics.
"""
import argparse
import numpy as np
import geopandas as gpd
import rasterio
from figure_layout import configure_fonts,canvas,panel,export


def histogram(path, output, breaks, band=1, column=None, bins=30):
    configure_fonts()
    edges=np.asarray(breaks,dtype=float)
    if len(edges)<2 or not np.isfinite(edges).all() or np.any(np.diff(edges)<=0):
        raise ValueError("Supply existing increasing breakpoints")
    if column:
        values=gpd.read_file(path)[column].to_numpy(dtype=float)
    else:
        with rasterio.open(path) as src:
            if src.width*src.height>4000000: raise ValueError("Use prepared values for large diagnostic rasters")
            if src.scales[band-1]!=1 or src.offsets[band-1]!=0: raise ValueError("Resolve physical-value encoding upstream")
            values=src.read(band,masked=True).compressed()
    values=values[np.isfinite(values)]
    if not len(values): raise ValueError("No valid diagnostic values")
    fig=canvas(150,90);ax=panel(fig,[18,17,124,62])
    ax.hist(values,bins=bins,color="#A8BACB",edgecolor="white")
    for number in edges: ax.axvline(number,color="#AE413A",lw=.8)
    ax.set_xlabel("Source value (existing breaks in red)",fontfamily="Arial")
    ax.set_ylabel("Count",fontfamily="Arial")
    return export(fig,output)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("path");p.add_argument("output")
    p.add_argument("--breaks",type=float,nargs="+",required=True);p.add_argument("--band",type=int,default=1);p.add_argument("--column")
    a=p.parse_args();print(histogram(a.path,a.output,a.breaks,a.band,a.column))
