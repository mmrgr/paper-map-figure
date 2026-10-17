"""Generate explicitly SYNTHETIC fixtures and runnable map configurations.

python demo_gallery.py output_directory
This is a software test/demo, never a research result or real geography.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
import geopandas as gpd
from shapely.geometry import Point, LineString, box
from pyproj import Transformer
from render_map import render


def create_fixtures(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    crs="EPSG:32649";extent=[450000,3800000,498000,3832000]
    yy,xx=np.mgrid[0:32,0:48]
    values=(18+20*(xx/47)*(.4+.6*(1-yy/31))).astype("float32")
    values[0:4,0:5]=-9999
    classes=(1+(xx//16)).astype("uint8");classes[:4,:5]=0
    for name,data,nodata in [("temperature",values,-9999),("classes",classes,0)]:
        with rasterio.open(root/(name+".tif"),"w",driver="GTiff",width=48,height=32,count=1,
                           dtype=data.dtype,crs=crs,transform=from_origin(450000,3832000,1000,1000),nodata=nodata) as dst:
            dst.write(data,1)
    gpd.GeoDataFrame({"name":["synthetic extent"]},geometry=[box(*extent)],crs=crs).to_file(root/"boundary.gpkg")
    gpd.GeoDataFrame({"count":[1.,4.,9.],"x":[.2,.5,.8],"y":[.8,.5,.2]},
                    geometry=[Point(462000,3810000),Point(475000,3820000),Point(486000,3814000)],crs=crs).to_file(root/"points.gpkg")
    gpd.GeoDataFrame({"flow":[5.,10.]},geometry=[LineString([(455000,3810000),(480000,3825000)]),
                     LineString([(460000,3828000),(490000,3805000)])],crs=crs).to_file(root/"flows.gpkg")
    return extent,crs


def configs(root):
    extent,crs=create_fixtures(root)
    root=Path(root)
    mapping={"temperature":{"type":"continuous","variable":"synthetic temperature","unit":"degC","vmin":18,"vmax":38,"cmap":"YlOrRd"}}
    layer={"type":"raster","path":"temperature.tif","mapping":"temperature"}
    def p(key,rect):
        return {"id":key,"rect_mm":rect,"crs":crs,"extent":extent,"label":key,
                "layers":[dict(layer)],"scale_bar":{"length_m":10000,"location":[.08,.12]},
                "north_arrow":{"location":[.90,.73],"size_mm":7}}
    single={"width_mm":180,"height_mm":140,"output_stem":"single","mappings":mapping,
            "panels":[p("a",[8,28,164,105])],"legends":[{"mapping":"temperature","rect_mm":[48,13,90,3],"ticks":[18,23,28,33,38]}],
            "nodata_legend":{"rect_mm":[144,12,30,5]},
            "note":{"rect_mm":[8,2,165,5],"text":"SYNTHETIC TEST — temperature (°C); no real geography"},"caption":"Synthetic fixture only"}
    series={"width_mm":180,"height_mm":150,"output_stem":"series","mappings":mapping,"comparison_groups":[["a","b","c","d"]],
            "panels":[p(k,r) for k,r in zip("abcd",[[7,85,80,56],[93,85,80,56],[7,25,80,56],[93,25,80,56]])],
            "legends":[{"mapping":"temperature","rect_mm":[48,13,90,3],"ticks":[18,23,28,33,38]}],
            "nodata_legend":{"rect_mm":[144,12,30,5]},
            "note":{"rect_mm":[7,2,166,5],"text":"SYNTHETIC TEST — shared temperature scale (°C)"}}
    for panel in series["panels"]:
        panel["north_arrow"]["size_mm"]=5;panel["scale_bar"]["length_m"]=5000
    trans=Transformer.from_crs(crs,3857,always_xy=True)
    x0,y0=trans.transform(extent[0],extent[1]);x1,y1=trans.transform(extent[2],extent[3])
    inset={"width_mm":180,"height_mm":140,"output_stem":"inset","mappings":mapping,
           "panels":[p("main",[7,25,122,105]),
                     {"id":"locator","rect_mm":[136,78,37,43],"crs":"EPSG:3857",
                      "extent":[x0-80000,y0-80000,x1+80000,y1+80000],"label":"b",
                      "layers":[{"type":"vector","path":"boundary.gpkg","color":"#EEEEEE"}]}],
           "links":[{"detail":"main","context":"locator","connect":False}],
           "legends":[{"mapping":"temperature","rect_mm":[30,13,80,3]}],
           "nodata_legend":{"rect_mm":[139,12,33,5]},
           "note":{"rect_mm":[7,2,166,5],"text":"SYNTHETIC TEST — locator; temperature (°C)"}}
    for name,cfg in [("single",single),("series",series),("inset",inset)]:
        (root/(name+".json")).write_text(json.dumps(cfg,indent=2),encoding="utf-8")
    return root


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("output_directory")
    args=parser.parse_args();root=configs(args.output_directory)
    for name in ("single","series","inset"):
        qa=render(root/(name+".json"));print(name,len(qa["findings"]),"automated findings")
