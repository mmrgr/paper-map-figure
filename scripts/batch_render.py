"""Render several explicit configurations; report each success/failure.

python batch_render.py config1.json config2.json
Does not alter data, infer time periods or overwrite completed outputs.
"""
import argparse
import json
from render_map import render


def batch(paths):
    results=[]
    for path in paths:
        try:
            qa=render(path)
            results.append({"config":str(path),"status":"rendered","outputs":qa["outputs"],
                            "automated_findings":qa["findings"],"visual_review":"pending"})
        except Exception as error:
            results.append({"config":str(path),"status":"failed","error":str(error)})
    return results


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("configs",nargs="+")
    a=p.parse_args();results=batch(a.configs)
    print(json.dumps(results,ensure_ascii=False,indent=2))
    raise SystemExit(1 if any(r["status"]=="failed" for r in results) else 0)
