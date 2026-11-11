"""Rebuild structured-cmc-review.html from ../fhir/resources and ../source extract."""
import json, glob, os
here = os.path.dirname(os.path.abspath(__file__))
res = []
for f in sorted(glob.glob(os.path.join(here, "..", "fhir", "resources", "*.json"))):
    r = json.load(open(f))
    if r["resourceType"] != "Composition":
        r.pop("text", None)
    res.append(r)
d = json.load(open(os.path.join(here, "..", "source", "sakura-bloom-r2-extract.json")))
from collections import Counter
titles = Counter(p["path"].split(" / ")[-1].strip() for p in d["pages"])
src = {}
for p in d["pages"]:
    parts = [x.strip() for x in p["path"].split(" / ")]
    t = parts[-1]
    if titles[t] > 1:
        t += " (" + ("HDPE bottle" if "Bottle" in parts[-2] else "blister" if "Blister" in parts[-2] else parts[-2][:40]) + ")"
    src["https://ichm4q.notion.site/" + p["id"].replace("-", "")] = t
t = open(os.path.join(here, "template.html")).read()
t = t.replace("__DATA__", json.dumps(res, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"))
t = t.replace("__SOURCES__", json.dumps(src, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"))
t = t.replace("__LOGIC__", open(os.path.join(here, "logic.js")).read())
t = t.replace("__POSTNOC__", open(os.path.join(here, "postnoc.js")).read())
open(os.path.join(here, "structured-cmc-review.html"), "w").write(t)
print("written", len(t))
