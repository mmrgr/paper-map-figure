"""Render read-only GIS results from explicit JSON: python render_map.py config.json.

No network, classification fitting, raster reprojection or data modification.
"""
import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from figure_layout import (configure_fonts, font_families, canvas, panel, mixed_label,
                           export)
from map_styles import continuous, classified, colorbar, category_handles
from geo_layers import raster, vector, flow, source_record
from geo_elements import projected, scale_bar, north_arrow, extent_link, graticule
from figure_qa import (inspect_figure, verify_png, verify_pdf, versions, review_packet,
                       caption_template)
import cvd_check


def text_runs(value):
    """Automatic Han/fullwidth vs Latin runs for ordinary text (not TeX math)."""
    runs=[]
    for char in str(value):
        code=ord(char)
        lang="zh" if (0x2E80<=code<=0x9FFF or 0xF900<=code<=0xFAFF or 0xFF00<=code<=0xFFEF) else "en"
        if runs and runs[-1][1]==lang: runs[-1]=(runs[-1][0]+char,lang)
        else: runs.append((char,lang))
    return runs


def mapping_from(spec):
    if not spec.get("variable") or not spec.get("unit"):
        raise ValueError("Every mapping requires variable and unit (use '1' for dimensionless)")
    kind=spec["type"]
    if kind=="continuous": return continuous(spec["vmin"],spec["vmax"],spec.get("cmap","viridis"),spec.get("center"))
    if kind=="classified": return classified(spec["breaks"],spec.get("cmap","YlOrRd"))
    if kind=="categorical":
        entries=spec["entries"]
        codes=[e["code"] for e in entries]
        if not entries or len(set(codes))!=len(codes): raise ValueError("Category codes must be unique")
        return {e["code"]:e["color"] for e in entries}
    raise ValueError("Unknown mapping type")


def render(config_path, output_stem=None):
    config_path=Path(config_path).resolve()
    cfg=json.loads(config_path.read_text(encoding="utf-8"))
    unknown=set(cfg)-{"width_mm","height_mm","output_stem","formats","dpi","review","mappings","panels","links","legends","nodata_legend","note","caption","comparison_groups","svg_outline","cvd_threshold","cvd_strict","fonts"}
    if unknown: raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
    if not cfg.get("panels") or any(not spec.get("layers") for spec in cfg["panels"]):
        raise ValueError("At least one nonempty map panel is required")
    base=config_path.parent
    # An explicit override replays a saved configuration somewhere else without
    # editing it; the snapshot stays a record of what was asked for.
    stem=(base/(output_stem if output_stem is not None else cfg["output_stem"])).resolve()
    # Fail before rendering if any intended artifact already exists.
    formats=tuple(cfg.get("formats",["png","pdf"]))
    targets=[Path(str(stem)+"."+ext) for ext in formats]+[Path(str(stem)+".qa.json"),Path(str(stem)+".config.json"),Path(str(stem)+".caption.md")]
    if cfg.get("svg_outline"): targets.append(Path(str(stem)+".outlined.svg"))
    if cfg.get("review",True): targets.append(Path(str(stem)+".review"))
    if any(p.exists() for p in targets): raise FileExistsError("Choose a new output_stem")
    if "png" not in formats: raise ValueError("PNG required for export verification and visual review")
    if cfg.get("svg_outline") and "svg" not in formats:
        raise ValueError("svg_outline requires svg in formats")
    if cfg.get("review",True) and (cfg["width_mm"]>180 or cfg["height_mm"]>237):
        raise ValueError("Default A4 review only fits width <=180 and height <=237 mm; set review=false and use actual journal page")
    fonts=configure_fonts(cfg.get("fonts"))
    families=font_families(cfg.get("fonts"))
    latin=families["en"]
    fig=canvas(cfg["width_mm"],cfg["height_mm"])
    mappings={key:mapping_from(spec) for key,spec in cfg.get("mappings",{}).items()}
    axes={}; specs={}; layer_info=[]; sources={}; elements=[]; used={}; rectangles=[]; advanced=[]
    try:
        for spec in cfg["panels"]:
            key=spec["id"]
            if key in axes: raise ValueError("Panel ids must be unique")
            crs=projected(spec["crs"])
            rect=spec["rect_mm"]
            x,y,w,h=rect
            for px,py,pw,ph in rectangles:
                if x<px+pw and x+w>px and y<py+ph and y+h>py:
                    raise ValueError("Panels overlap; use a side inset or existing GIS layout")
            rectangles.append(rect)
            ax=panel(fig,rect)
            axes[key]=ax;specs[key]=spec
            extent=spec["extent"]
            if len(extent)!=4 or not np.isfinite(extent).all() or extent[0]>=extent[2] or extent[1]>=extent[3]:
                raise ValueError("Extent must be xmin,ymin,xmax,ymax")
            for layer in spec["layers"]:
                path=(base/layer["path"]).resolve()
                if str(path) not in sources: sources[str(path)]=source_record(path)
                mid=layer.get("mapping")
                mapping=mappings[mid] if mid else None
                used.setdefault(mid,set()).add(key)
                cat=mapping if isinstance(mapping,dict) else None
                scalar=None if cat is not None else mapping
                kind=layer["type"]
                if kind=="raster":
                    _,info=raster(ax,path,crs,scalar,cat,layer.get("band",1),extent)
                elif kind=="vector":
                    info=vector(ax,path,crs,column=layer.get("column"),mapping=scalar,categories=cat,
                                color=layer.get("color","#E8E8E8"),edgecolor=layer.get("edgecolor","#555555"),
                                linewidth=layer.get("linewidth",.5),markersize=layer.get("markersize",16),
                                layer=layer.get("layer"),proportional=layer.get("proportional"),bivariate=layer.get("bivariate"))
                elif kind=="flow":
                    info=flow(ax,path,crs,layer["column"],layer["reference_value"],
                              layer.get("reference_width_pt",1),layer.get("color","#547A9C"),layer.get("layer"),
                              layer.get("direction_from_vertex_order",False))
                else: raise ValueError("Layer type must be raster, vector or flow")
                if layer.get("proportional") or layer.get("bivariate") or kind=="flow":
                    if not layer.get("legend"): raise ValueError("Symbol, flow and bivariate layers require their own legend")
                    advanced.append(layer)
                layer_info.append({"panel":key,"path":str(path),"mapping":mid,**info})
            ax.set_xlim(extent[0],extent[2]);ax.set_ylim(extent[1],extent[3])
            ax.set_aspect("equal",adjustable="box");ax.set_autoscale_on(False)
            if not spec.get("coordinates",False): ax.set_xticks([]);ax.set_yticks([])
            else:
                ax.tick_params(labelsize=8);ax.ticklabel_format(style="plain",useOffset=False)
            if spec.get("graticule"):
                graticule(ax,crs,**spec["graticule"])
            if spec.get("label"):
                mixed_label(ax,(.02,.98),text_runs(spec["label"]),size=10,bold=True,families=families)
            for label in spec.get("labels",[]):
                # Label positions are supplied in real data coordinates, never moved features.
                fraction=ax.transAxes.inverted().transform(ax.transData.transform(label["xy"]))
                mixed_label(ax,fraction,text_runs(label["text"]),size=label.get("size",8),families=families)
        fig.canvas.draw()
        for group in cfg.get("comparison_groups",[]):
            first=specs[group[0]]
            for key in group[1:]:
                current=specs[key]
                if not projected(first["crs"]).equals(projected(current["crs"])) or first["extent"]!=current["extent"]:
                    raise ValueError("Same-region comparison group requires identical CRS and extent")
                if [l.get("mapping") for l in first["layers"]]!=[l.get("mapping") for l in current["layers"]]:
                    raise ValueError("Comparison group requires matching layer mappings")
        for key,ax in axes.items():
            spec=specs[key]
            if spec.get("scale_bar"):
                elements.append({"panel":key,"scale_bar":scale_bar(ax,spec["crs"],fontfamily=latin,**spec["scale_bar"])})
            if spec.get("north_arrow"):
                options={} if spec["north_arrow"] is True else spec["north_arrow"]
                elements.append({"panel":key,"north_arrow":north_arrow(ax,spec["crs"],fontfamily=latin,**options)})
        for link in cfg.get("links",[]):
            a,b=link["detail"],link["context"]
            elements.append({"link":[a,b],"extent":extent_link(fig,axes[a],specs[a]["crs"],axes[b],specs[b]["crs"],
                                                               connect=link.get("connect",True))})
        for legend in cfg.get("legends",[]):
            mid=legend["mapping"]
            if mid not in mappings: raise ValueError(f"Legend references unknown mapping: {mid}")
            if mid not in used: raise ValueError("Legend mapping is not used by any panel")
            mapping=mappings[mid];spec=cfg["mappings"][mid]
            cax=panel(fig,legend["rect_mm"])
            if isinstance(mapping,dict):
                cax.set_axis_off()
                # Explicit text runs guarantee Chinese/Latin font choice.
                from matplotlib.patches import Rectangle
                entries=spec["entries"]; step=1/len(entries)
                for i,e in enumerate(entries):
                    yy=1-(i+1)*step
                    cax.add_patch(Rectangle((0,yy+.15*step),.12,.65*step,facecolor=e["color"],transform=cax.transAxes))
                    mixed_label(cax,(.18,yy+.85*step),text_runs(e["label"]),size=8,families=families)
            else:
                bar=colorbar(fig,cax,mapping,legend.get("orientation","horizontal"),legend.get("ticks"))
                bar.ax.tick_params(labelsize=8)
            if legend.get("label"):
                mixed_label(cax,(0,legend.get("label_y",2.8)),text_runs(legend["label"]),size=8,families=families)
        shown={legend["mapping"] for legend in cfg.get("legends",[])}
        if set(used)-{None}-shown:
            raise ValueError("Every used thematic mapping needs a matching legend")
        from map_styles import bivariate_legend,size_legend
        for layer in advanced:
            spec=layer["legend"];lax=panel(fig,spec["rect_mm"])
            if layer.get("bivariate"):
                bi=layer["bivariate"]
                bivariate_legend(lax,bi["colors"],bi.get("x_label",""),bi.get("y_label",""),fontfamily=latin)
                for axis,edges in [(lax.xaxis,bi["x_breaks"]),(lax.yaxis,bi["y_breaks"])]:
                    axis.set_ticks(range(len(edges)-1))
                    axis.set_ticklabels([f"[{a:g},{b:g}{']' if i==len(edges)-2 else ')'}" for i,(a,b) in enumerate(zip(edges[:-1],edges[1:]))],fontsize=7)
                if spec.get("label"): mixed_label(lax,(0,1.22),text_runs(spec["label"]),size=8,families=families)
            else:
                prop=layer.get("proportional")
                value=prop["reference_value"] if prop else layer["reference_value"]
                size=prop["reference_area_pt2"] if prop else layer.get("reference_width_pt",1)
                yy=size_legend(lax,spec["values"],value,size,"points" if prop else "lines",layer.get("color","#547A9C"),
                               layer.get("edgecolor","#555555"),layer.get("linewidth",.5))
                for number,y in zip(spec["values"],yy): mixed_label(lax,(.4,y+.07),text_runs(f"{number:g} {spec['unit']}"),size=8,families=families)
                if spec.get("label"): mixed_label(lax,(0,1.22),text_runs(spec["label"]),size=8,families=families)
        if any(info.get("nodata_count",0) for info in layer_info) and not cfg.get("nodata_legend"):
            raise ValueError("Visible NoData requires a nodata_legend rectangle")
        if cfg.get("nodata_legend"):
            from matplotlib.patches import Rectangle
            item=cfg["nodata_legend"];nax=panel(fig,item["rect_mm"]);nax.set_axis_off()
            nax.add_patch(Rectangle((0,.2),.16,.6,facecolor="#D9D9D9",transform=nax.transAxes))
            mixed_label(nax,(.23,.9),text_runs(item.get("label","NoData")),size=8,families=families)
        if cfg.get("note"):
            note=cfg["note"]; ax=panel(fig,note["rect_mm"]);ax.set_axis_off()
            mixed_label(ax,(0,1),text_runs(note["text"]),size=note.get("size",8),families=families)
        qa=inspect_figure(fig)
        for path,record in sources.items():
            if source_record(path)!=record: raise RuntimeError("Source data changed during rendering")
        # The colour check reads the configuration only, so it runs before a
        # single byte is written: a strict failure then costs no artifact, and a
        # later run is not blocked by the refusal to overwrite.
        nodata_panels={info["panel"] for info in layer_info if info.get("nodata_count",0)}
        cvd=cvd_check.report(cvd_check.entries_from_config(config_path),
                             nodata="#D9D9D9" if (nodata_panels or cfg.get("nodata_legend")) else None,
                             threshold=float(cfg.get("cvd_threshold",10.0)),
                             nodata_panels=nodata_panels or None)
        if cfg.get("cvd_strict") and cvd["findings"]:
            raise ValueError("Colour pairs fail the colour-vision check; revise the confirmed "
                             "mapping or set cvd_strict to false")
        # Everything below writes files, so it is staged first and only moved
        # into place once every check has passed. A failure at any point leaves
        # the output directory exactly as it was found.
        staging=Path(tempfile.mkdtemp(prefix="."+stem.name+".staging-",dir=stem.parent))
        try:
            stage=staging/stem.name
            outputs=export(fig,stage,formats,cfg.get("dpi",300),svg_outline=bool(cfg.get("svg_outline",False)))
            # Report the paths the figure ends up at, not the staged ones.
            final=[Path(str(stem)+str(p)[len(str(stage)):]) for p in outputs]
            qa.update({"layers":layer_info,"elements":elements,"sources":sources,"versions":versions(),
                       "font_paths":fonts,"mappings":cfg.get("mappings",{}),
                       "outputs":[str(p) for p in final],
                       "png":verify_png(str(stage)+".png",cfg["width_mm"],cfg["height_mm"],cfg.get("dpi",300)),
                       "cvd":cvd,
                       "ai_visual_review":"pending; automated QA is not AI review"})
            if "pdf" in formats:
                qa["pdf"]=verify_pdf(str(stage)+".pdf",cfg["width_mm"],cfg["height_mm"])
            if cfg.get("review",True):
                review_packet(str(stage)+".png",str(stage)+".review",cfg["width_mm"],cfg["height_mm"],cfg.get("caption",""))
                qa["review_packet"]=str(stem)+".review"
            Path(str(stage)+".caption.md").write_text(
                caption_template(cfg,sources,elements),encoding="utf-8")
            import copy
            # Relative paths and an explicit root keep the snapshot replayable
            # next to the data instead of pinned to one machine.
            snapshot=copy.deepcopy(cfg)
            snapshot["config_root"]=str(base)
            snapshot["output_stem"]=str(stem)
            if output_stem is None:
                snapshot["output_stem"]=cfg["output_stem"]
            qa["configuration_source"]=str(config_path)
            Path(str(stage)+".config.json").write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding="utf-8")
            Path(str(stage)+".qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding="utf-8")
            # Commit: nothing was created yet, so refusing to overwrite is already
            # guaranteed by the pre-flight check above.
            for produced in sorted(staging.iterdir()):
                os.replace(produced,Path(str(stem)+produced.name[len(stem.name):]))
            return qa
        finally:
            shutil.rmtree(staging,ignore_errors=True)
    finally:
        plt.close(fig)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("config")
    parser.add_argument("--output-stem",help="write the figure somewhere else than the "
                        "configuration says, without editing the snapshot")
    args=parser.parse_args();result=render(args.config,args.output_stem)
    print(json.dumps({"outputs":result["outputs"],"findings":result["findings"],
                      "cvd_findings":result["cvd"]["findings"]},ensure_ascii=False,indent=2))
