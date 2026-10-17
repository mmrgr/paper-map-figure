"""Regression checks using isolated synthetic data. No external downloads.

python test_rendering.py NEW_WORK_DIRECTORY
"""
import argparse
import json
from pathlib import Path
import numpy as np
import rasterio
from affine import Affine
from pyproj import Transformer
from matplotlib import pyplot as plt
from demo_gallery import configs
from render_map import render
from map_styles import classified,continuous,map_values,category_rgba,bivariate_rgba
from geo_layers import source_record,raster,vector,flow
from geo_elements import horizontal_distance,scale_bar,north_arrow,extent_link
from figure_layout import canvas,panel,configure_fonts,export


def rejects(fn):
    try: fn()
    except (ValueError,FileExistsError): return
    raise AssertionError("Expected explicit rejection")


def run(root):
    root=configs(root);checks=[];configure_fonts()
    a=np.array([0.,1.,2.,np.nan]);before=a.copy();m=classified([0,1,2]);rgba=map_values(a,m)
    assert np.array_equal(a,before,equal_nan=True) and np.allclose(rgba[1],rgba[2])
    checks.append("fixed bins preserve inputs and include last upper endpoint")
    rejects(lambda:map_values([3],m));rejects(lambda:continuous(1,1));rejects(lambda:continuous(0,1,center=2))
    rejects(lambda:category_rgba([3],{1:"red"}));checks.append("invalid bounds and unknown classes rejected")
    cats=category_rgba([0,1],{0:"blue",1:"red"});assert not np.allclose(cats[0],cats[1])
    checks.append("valid zero category preserved")
    b=bivariate_rgba([0,1],[1,0],[0,.5,1],[0,.5,1],[["red","blue"],["green","yellow"]]);assert b.shape==(2,4)
    checks.append("bivariate explicit bins")
    source=source_record(root/"temperature.tif")
    for name in ("single","series","inset"):
        qa=render(root/(name+".json"))
        assert not qa["findings"],qa["findings"]
        assert qa["png"]["pixels"][0]>2000
        checks.append(name+" end-to-end PNG/PDF, fonts and review packet")
    assert source==source_record(root/"temperature.tif");checks.append("source checksums unchanged")
    qa=__import__('copy').deepcopy(json.loads((root/"single.json").read_text()))
    qa['output_stem']='categorical';qa['panels'][0]['layers'][0]['path']='classes.tif'
    qa['note']['text']='SYNTHETIC TEST — land-cover categories; no real geography'
    # Bilingual labels on purpose: this fixture is what proves the SimHei/Arial run splitting.
    qa['mappings']['temperature']={'type':'categorical','variable':'synthetic cover','unit':'class',
        'entries':[{'code':1,'color':'#287A45','label':'林地 Forest'},{'code':2,'color':'#E6C65B','label':'耕地 Crop'},{'code':3,'color':'#3C8DCC','label':'水体 Water'}]}
    qa['legends'][0]={'mapping':'temperature','rect_mm':[135,32,38,35]}
    qa['panels'][0]['rect_mm']=[8,28,120,105]
    (root/'categorical.json').write_text(json.dumps(qa,ensure_ascii=False),encoding='utf-8')
    render(root/'categorical.json');checks.append('categorical raster and bilingual legend end-to-end')
    qa['output_stem']='classified';qa['panels'][0]['layers'][0]['path']='temperature.tif'
    qa['note']['text']='SYNTHETIC TEST — classified temperature (°C)'
    qa['mappings']['temperature']={'type':'classified','variable':'synthetic temperature','unit':'degC','breaks':[18,23,28,33,38]}
    qa['legends'][0]={'mapping':'temperature','rect_mm':[30,13,90,3]}
    (root/'classified.json').write_text(json.dumps(qa),encoding='utf-8');render(root/'classified.json')
    checks.append('classified raster end-to-end')
    from color_diagnostics import histogram
    histogram(root/'temperature.tif',root/'histogram',[18,23,28,33,38]);checks.append('existing-break histogram export')
    advanced={'width_mm':180,'height_mm':155,'output_stem':'advanced','panels':[],
              'note':{'rect_mm':[6,2,168,5],'text':'SYNTHETIC TEST — points, flows and bivariate symbols'}}
    styles=[{'type':'vector','path':'points.gpkg','color':'#547A9C',
             'proportional':{'column':'count','reference_value':1,'reference_area_pt2':10},
             'legend':{'rect_mm':[9,18,40,32],'values':[1,4,9],'unit':'count'}},
            {'type':'flow','path':'flows.gpkg','column':'flow','reference_value':5,'reference_width_pt':1,
             'direction_from_vertex_order':True,'legend':{'rect_mm':[66,18,40,32],'values':[5,10],'unit':'units'}},
            {'type':'vector','path':'points.gpkg','bivariate':{'x_column':'x','y_column':'y','x_breaks':[0,.5,1],
              'y_breaks':[0,.5,1],'colors':[['#EEEEEE','#72A8C4'],['#C37A9B','#574A7B']]},
             'legend':{'rect_mm':[137,18,29,29],'label':'x / y'}}]
    for i,layer in enumerate(styles):
        advanced['panels'].append({'id':str(i),'label':chr(97+i),'crs':'EPSG:32649',
            'rect_mm':[6+i*57,70,51,70],'extent':[450000,3800000,498000,3832000],'layers':[layer]})
    (root/'advanced.json').write_text(json.dumps(advanced),encoding='utf-8');render(root/'advanced.json')
    checks.append('proportional, directed flow and bivariate legends end-to-end')
    rejects(lambda:render(root/"single.json"));checks.append("existing outputs not overwritten")
    # A bivariate layer with a missing value paints the NoData grey, so it has to
    # demand a legend exactly like a raster with masked cells.
    import geopandas as gpd
    from shapely.geometry import Point
    holes=gpd.GeoDataFrame({"x":[.2,float('nan'),.8],"y":[.8,.5,.2]},
                           geometry=[Point(462000,3810000),Point(475000,3820000),
                                     Point(486000,3814000)],crs="EPSG:32649")
    holes.to_file(root/"holes.gpkg")
    probe=canvas(80,60);probe_ax=panel(probe,[5,5,70,50])
    holes_info=vector(probe_ax,root/"holes.gpkg",32649,bivariate={"x_column":"x","y_column":"y",
        "x_breaks":[0,.5,1],"y_breaks":[0,.5,1],"colors":[["#EEEEEE","#72A8C4"],["#C37A9B","#574A7B"]]})
    plt.close(probe)
    assert holes_info["nodata_count"]==1,holes_info
    checks.append("bivariate missing values count as visible NoData")
    # A strict colour-vision failure used to be raised after PNG and PDF were
    # written, leaving artifacts that then blocked the next attempt.
    strict=json.loads((root/"categorical.json").read_text(encoding='utf-8'))
    strict['output_stem']='strict';strict['cvd_strict']=True
    strict['mappings']['temperature']['entries'][0]['color']='#A6C96A'
    (root/'strict.json').write_text(json.dumps(strict),encoding='utf-8')
    rejects(lambda:render(root/'strict.json'))
    assert not (root/'strict.png').exists() and not (root/'strict.pdf').exists()
    checks.append("strict colour-vision failure leaves no artifacts behind")
    # The saved configuration stays replayable: relative paths, an explicit root,
    # and an output-stem override to move the figure without editing the JSON.
    snapshot=json.loads((root/'single.config.json').read_text(encoding='utf-8'))
    assert snapshot['output_stem']=='single' and 'config_root' in snapshot
    assert all(not Path(layer['path']).is_absolute()
               for spec in snapshot['panels'] for layer in spec['layers'])
    render(root/'single.config.json',output_stem='replayed')
    assert (root/'replayed.png').exists()
    checks.append("saved configuration replays at a new output stem")
    fig=canvas();ax=panel(fig,[10,15,160,95]);ax.set_xlim(400000,500000);ax.set_ylim(3750000,3850000);ax.set_aspect("equal")
    bar=scale_bar(ax,32649,10000);assert abs(bar["measured_m"]-10000)<.001
    # Independent endpoint geodesic (short straight local segment should match).
    tr=Transformer.from_crs(32649,4326,always_xy=True)
    from pyproj import Geod
    p0,p1=bar["endpoints_xy"];lon0,lat0=tr.transform(*p0);lon1,lat1=tr.transform(*p1)
    assert abs(Geod(ellps="WGS84").inv(lon0,lat0,lon1,lat1)[2]-10000)<.1
    checks.append("scale bar independently matches ellipsoidal ground distance")
    ar=north_arrow(ax,32649,location=(.5,.7));assert abs(ar["screen_angle_from_up_deg"])<1
    rejects(lambda:scale_bar(ax,4326,1000));rejects(lambda:scale_bar(ax,32649,1e8))
    checks.append("true north and invalid/geographic scalebar handling")
    # Off central meridian north must not silently default to screen up.
    ar=north_arrow(ax,32649,location=(.05,.7));assert abs(ar["screen_angle_from_up_deg"])>.1
    checks.append("off-meridian true north rotation")
    # Rotated affine is rendered from actual pixel corners, not axis-aligned extent.
    rotated=root/"rotated.tif";aff=Affine(100,25,450000,20,-100,3830000)
    with rasterio.open(rotated,"w",driver="GTiff",width=3,height=2,count=1,dtype="float32",crs=32649,transform=aff) as dst:
        dst.write(np.ones((2,3),dtype="float32"),1)
    artist,info=raster(ax,rotated,32649,continuous(0,2))
    coord=artist.get_coordinates();assert np.allclose(coord[1,1],aff*(1,1))
    rejects(lambda:raster(ax,rotated,3857,continuous(0,2)))
    checks.append("rotated raster corners and mismatched CRS rejection")
    vector(ax,root/"points.gpkg",32649,proportional={"column":"count","reference_value":1,"reference_area_pt2":10})
    assert np.allclose(ax.collections[-1].get_sizes(),[10,40,90]);checks.append("symbol area proportional to value")
    flow(ax,root/"flows.gpkg",32649,"flow",5,1)
    assert np.allclose(ax.collections[-1].get_linewidths(),[1,2]);checks.append("flow widths proportional without aggregation")
    ctx=panel(fig,[140,100,30,15]);ctx.set_xlim(0,1);ctx.set_ylim(0,1)
    result=extent_link(fig,ax,32649,ctx,3857,connect=False)
    assert result["perimeter_vertices"]==260;checks.append("inset perimeter transformed/densified")
    export(fig,root/'formats',formats=('svg','tiff'))
    assert (root/'formats.svg').stat().st_size>1000 and (root/'formats.tiff').stat().st_size>1000
    checks.append('SVG and TIFF export')
    # Outlined SVG keeps the same drawing but must not rely on installed fonts.
    export(fig,root/'outlined',formats=('svg',),svg_outline=True)
    live=(root/'outlined.svg').read_text(encoding='utf-8')
    outlined=(root/'outlined.outlined.svg').read_text(encoding='utf-8')
    assert '<text' in live and live.count('<text')>outlined.count('<text')
    assert 'glyph' in outlined or '<use' in outlined
    rejects(lambda:export(fig,root/'bad',formats=('png',),svg_outline=True))
    checks.append('outlined SVG export differs from live-text SVG')
    from cvd_check import (simulate,simulate_hex,delta_e_2000,to_lab,check_entries,
                           entries_from_config,report as cvd_report)
    assert np.allclose(simulate([.2,.5,.8],'protan',0.0),[.2,.5,.8])
    assert delta_e_2000(to_lab([50,0,0]),to_lab([50,0,0]))==0
    red_green=[to_lab(simulate([1,0,0],'protan')),to_lab(simulate([0,0.6,0],'protan'))]
    original=[to_lab([1,0,0]),to_lab([0,0.6,0])]
    assert delta_e_2000(*red_green)<delta_e_2000(*original)
    flagged,ramps=check_entries([{'group':'cover','label':'grass','color':'#A6C96A'},
                                 {'group':'cover','label':'crop','color':'#E6C65B'}])
    assert flagged and flagged[0]['worst_case'].startswith('protan')
    assert not check_entries([{'group':'cover','label':'black','color':'#000000'},
                              {'group':'cover','label':'white','color':'#FFFFFF'}])[0]
    clean,profile=check_entries([{'group':'ramp','label':'low','color':'#FFFFB2',
                                  'mode':'continuous'},
                                 {'group':'ramp','label':'high','color':'#BD0026',
                                  'mode':'continuous'}])
    assert not clean and profile and profile[0]['lightness_range']>30
    broke,profile_of_broken=check_entries([{'group':'ramp','label':'a','color':'#404040','mode':'continuous'},
                                 {'group':'ramp','label':'b','color':'#909090','mode':'continuous'},
                                 {'group':'ramp','label':'c','color':'#606060','mode':'continuous'},
                                 {'group':'ramp','label':'d','color':'#E0E0E0','mode':'continuous'}])
    assert broke and broke[0]['kind']=='lightness_reversal' and broke[0]['positions']==[1]
    assert len(broke[0]['affected_cases'])==6 and len(profile_of_broken)==6
    rejects(lambda:check_entries([],threshold=0));rejects(lambda:simulate([0,0,0],'unknown'))
    assert len(entries_from_config(root/'categorical.json'))==3
    checks.append('CVD simulation and colour-pair findings')
    assert 'findings' in cvd_report([{'group':'g','label':'a','color':'#A6C96A'},
                                     {'group':'g','label':'b','color':'#E6C65B'}])
    checks.append('CVD report shape and limitations')
    # A figure with no thematic mapping once raised after the map was exported;
    # it now reports that there is nothing to simulate instead of failing.
    blank=cvd_report([])
    assert blank['applicable'] is False and blank['checked_colors']==0 and not blank['findings']
    assert check_entries([])==([],[])
    checks.append('CVD check tolerates a figure with no colour pair')
    # Fixed vector and flow colours are covered, not skipped, and the NoData grey
    # is only compared inside the panels that actually paint missing values.
    inset_entries=entries_from_config(root/'inset.json')
    locator=[entry for entry in inset_entries if entry['group'].startswith('fixed colours')]
    assert locator and all(entry['panel']==['locator'] for entry in locator)
    # The locator fill is a near-grey, so an unscoped comparison with the NoData
    # grey reports it; restricted to the panel that actually paints NoData it does not.
    unscoped=check_entries(inset_entries,nodata='#D9D9D9')[0]
    scoped=check_entries(inset_entries,nodata='#D9D9D9',nodata_panels={'main'})[0]
    assert any('locator' in str(finding.get('pair')) for finding in unscoped)
    assert not any('locator' in str(finding.get('pair')) for finding in scoped)
    checks.append('fixed layer colours are checked and NoData stays panel-scoped')
    # An existing figure scaled down must report the text size it will print at.
    from compose_maps import compose
    (root/'compose.json').write_text(json.dumps({'width_mm':120,'height_mm':80,'output_stem':'composed',
        'panels':[{'image':'single.png','rect_mm':[5,5,60,50],'source_width_mm':180,
                   'source_font_pt':[9,8],'source_linewidth_pt':0.5}]}),encoding='utf-8')
    composed=compose(root/'compose.json')
    panel_report=composed['panels'][0]
    assert abs(panel_report['shrink_ratio']-1/3)<1e-3
    assert panel_report['effective_font_pt']==[3.0,2.67]
    assert abs(panel_report['effective_source_dpi']-900)<5
    assert [finding['kind'] for finding in composed['findings']]==['text_below_print_size','stroke_below_print_size']
    checks.append('composed figure reports effective text and stroke size')
    # min_font_pt had to be given on the command line because the JSON key was
    # accepted and ignored; svg_outline was read but rejected as an unknown key.
    scaled=json.loads((root/'compose.json').read_text(encoding='utf-8'))
    scaled['output_stem']='composed-json';scaled['min_font_pt']=9.0
    (root/'compose-json.json').write_text(json.dumps(scaled),encoding='utf-8')
    assert compose(root/'compose-json.json')['limit_pt']==9.0
    assert compose(root/'compose-json.json',1.0)['limit_pt']==1.0
    outlined=json.loads((root/'compose.json').read_text(encoding='utf-8'))
    outlined['output_stem']='composed-svg';outlined['formats']=['png','svg'];outlined['svg_outline']=True
    (root/'compose-svg.json').write_text(json.dumps(outlined),encoding='utf-8')
    assert any(path.endswith('.outlined.svg')
               for path in compose(root/'compose-svg.json')['outputs'])
    checks.append('compose honours min_font_pt and svg_outline from the configuration')
    from check_environment import check as environment_check
    environment=environment_check()
    assert environment['ready'] and 'optional' in environment and 'PyMuPDF' in environment['optional']
    checks.append('environment report covers required and optional packages')
    from figure_qa import caption_template
    caption=caption_template(json.loads((root/'single.json').read_text(encoding='utf-8')))
    assert 'Figure caption template' in caption and 'unconfirmed' in caption
    checks.append('caption template lists the mandatory fields')
    _,window_info=raster(ax,root/'temperature.tif',32649,continuous(18,38),extent=[450500,3800500,452500,3802500])
    assert window_info['shape']==[3,3];checks.append('fractional viewport retains all intersecting raster cells')
    from geo_elements import graticule
    graticule(ax,32649,[110,111],[34,35],[109,33,112,36])
    checks.append('projected graticule rendering')
    scale_bar(ax,32649,10000,location=(.1,.2),style='ticks')
    checks.append('tick-style ground-distance scale')
    plt.close(fig)
    (root/"test-results.json").write_text(json.dumps({"passed":len(checks),"checks":checks},indent=2),encoding="utf-8")
    return checks


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("work_directory")
    args=parser.parse_args();checks=run(args.work_directory)
    print(json.dumps({"passed":len(checks),"checks":checks},ensure_ascii=False,indent=2))
