"""Build the two CMC motion showcases from the Sakura Bloom FHIR resources.

Reads  sakura-bloom-r2/fhir/resources/*.json
       sakura-bloom-r2/showcase/pack-layers.template.html
       sakura-bloom-r2/showcase/manufacturing-film.template.html
Writes showcases/pqi-pack-layers.html
       showcases/pqi-manufacturing-film.html
Run from the repo root:  python3 sakura-bloom-r2/showcase/build_cmc_motion.py
"""
import glob, json, os

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(here, "..", ".."))
R = {}
for f in glob.glob(os.path.join(here, "..", "fhir", "resources", "*.json")):
    r = json.load(open(f, encoding="utf-8"))
    R[r["resourceType"] + "/" + r["id"]] = r

def get(ref):
    return R.get(ref) if ref else None
def cc(c):
    if not c: return ""
    if c.get("text"): return c["text"]
    return ((c.get("coding") or [{}])[0]).get("display", "")
def code(c):
    co = ((c or {}).get("coding") or [{}])[0]
    return co.get("code", ""), co.get("system", "")
def qty(q):
    if not q: return ""
    v = q.get("value"); v = int(v) if isinstance(v, float) and v.is_integer() else v
    return f"{v} {q.get('unit', '')}".strip()
def prop(p):
    k = cc(p.get("type"))
    if "valueQuantity" in p: v = qty(p["valueQuantity"])
    elif "valueCodeableConcept" in p: v = cc(p["valueCodeableConcept"])
    elif "valueRange" in p:
        lo, hi = p["valueRange"].get("low"), p["valueRange"].get("high")
        v = f"{qty(lo)} – {qty(hi)}"
    else: v = p.get("valueString", "")
    return [k, v]
def orgs(lst):
    return [get(x.get("reference")).get("name") for x in (lst or []) if get(x.get("reference"))]
def edqm(c):
    k, s = code(c)
    return k if "edqm" in s else ""

# ---------------- pack / product / ingredients ----------------
mpd = next(r for k, r in R.items() if k.startswith("MedicinalProductDefinition/"))
mid = next(r for k, r in R.items() if k.startswith("ManufacturedItemDefinition/"))

def substance(sd):
    if not sd: return None
    ids = []
    for i in sd.get("identifier", []):
        sysname = "CAS" if "cas" in i.get("system", "") else "UNII" if "unii" in i.get("system", "").lower() else "ID"
        ids.append([sysname, i.get("value")])
    names = sd.get("name", [])
    pref = next((n["name"] for n in names if n.get("preferred")), names[0]["name"] if names else sd["id"])
    return {
        "name": pref,
        "ids": ids,
        "classification": "; ".join(cc(c) for c in sd.get("classification", [])),
        "grade": ", ".join(cc(g) for g in sd.get("grade", [])),
        "formula": (sd.get("structure") or {}).get("molecularFormula", ""),
        "source": cc((sd.get("sourceMaterial") or {}).get("type")),
        "manufacturer": orgs(sd.get("manufacturer")),
        "ref": "SubstanceDefinition/" + sd["id"],
    }

ingredients = {}
for k, r in R.items():
    if not k.startswith("Ingredient/"): continue
    sd = get(((r.get("substance") or {}).get("code") or {}).get("reference", {}).get("reference"))
    st = (r.get("substance") or {}).get("strength", [])
    ingredients[r["id"]] = {
        "role": cc(r.get("role")),
        "function": ", ".join(cc(f) for f in r.get("function", [])),
        "perTablet": next((s.get("textPresentation") for s in st if "tablet" in (s.get("textPresentation") or "")), ""),
        "perBatch": next((s.get("textPresentation") for s in st if "batch" in (s.get("textPresentation") or "")), ""),
        "substance": substance(sd),
        "ref": k,
    }

def comp(c):
    out = {"type": cc(c.get("type")), "amount": qty((c.get("amount") or [None])[0]), "constituents": [], "components": []}
    for x in c.get("constituent", []):
        ing = (((x.get("hasIngredient") or [{}])[0]).get("reference") or {}).get("reference", "")
        out["constituents"].append({"ing": ing.split("/")[-1], "amount": qty((x.get("amount") or [None])[0]), "function": ", ".join(cc(f) for f in x.get("function", []))})
    out["components"] = [comp(s) for s in c.get("component", [])]
    return out

tablet = {
    "name": mid.get("name"),
    "doseForm": cc(mid.get("manufacturedDoseForm")), "doseFormCode": edqm(mid.get("manufacturedDoseForm")),
    "unit": cc(mid.get("unitOfPresentation")), "unitCode": edqm(mid.get("unitOfPresentation")),
    "properties": [prop(p) for p in mid.get("property", [])],
    "manufacturer": orgs(mid.get("manufacturer")),
    "components": [comp(c) for c in mid.get("component", [])],
    "ref": "ManufacturedItemDefinition/" + mid["id"],
}

def shelf(p):
    s = (p.get("shelfLifeStorage") or [None])[0]
    if not s: return ""
    pre = "; ".join(cc(x) for x in s.get("specialPrecautionsForStorage", []))
    return f"{qty(s.get('periodDuration'))}" + (f" · {pre}" if pre else "")

def level(p):
    return {
        "type": cc(p.get("type")), "edqm": edqm(p.get("type")),
        "materials": [cc(m) for m in p.get("material", [])],
        "properties": [prop(x) for x in p.get("property", [])],
        "shelf": shelf(p),
        "manufacturer": orgs(p.get("manufacturer")),
        "parts": [level(x) for x in p.get("packaging", []) if not x.get("containedItem")],
    }

packs = []
for k, r in sorted(R.items()):
    if not k.startswith("PackagedProductDefinition/") or "bulk" in k: continue
    box = r["packaging"]
    prim = next((x for x in box.get("packaging", [])), None)
    packs.append({"id": r["id"], "name": r.get("name"), "type": cc(r.get("type")), "description": r.get("description"),
                  "box": level({k2: v for k2, v in box.items() if k2 != "packaging"}),
                  "primary": level(prim) if prim else None, "ref": k})

product = {
    "name": mpd["name"][0]["productName"],
    "identifier": ((mpd.get("identifier") or [{}])[0]).get("value", ""),
    "doseForm": cc(mpd.get("combinedPharmaceuticalDoseForm")), "doseFormCode": edqm(mpd.get("combinedPharmaceuticalDoseForm")),
    "route": cc((mpd.get("route") or [None])[0]), "routeCode": edqm((mpd.get("route") or [None])[0]),
}
PACK = {"product": product, "packs": packs, "tablet": tablet, "ingredients": ingredients}

# ---------------- manufacturing process ----------------
def steps(pd_id):
    pd = R["PlanDefinition/" + pd_id]
    out = []
    for a in pd["action"][0].get("action", []):
        params, mats, devices = [], [], []
        for e in a.get("extension", []):
            if e.get("url", "").endswith("process-parameters-pq"):
                d = {x["url"]: x for x in e.get("extension", [])}
                name = cc(d.get("parameter", {}).get("valueCodeableConcept"))
                v = d.get("value") or d.get("valueText") or {}
                val = qty(v.get("valueQuantity")) if "valueQuantity" in v else v.get("valueString", "")
                if "valueRange" in v: val = f"{qty(v['valueRange'].get('low'))} – {qty(v['valueRange'].get('high'))}"
                params.append([name, val])
        for p in a.get("participant", []):
            tr = p.get("typeReference") or {}
            if p.get("type") == "device":
                dd = get(tr.get("reference"))
                if dd: devices.append(dd["deviceName"][0]["name"])
                continue
            ref = next((x.get("valueReference", {}).get("reference") for x in tr.get("extension", [])), None)
            mats.append({"name": tr.get("display") or ref, "role": cc(p.get("role")), "ref": ref})
        def kind(c):
            t = cc(c.get("code")).lower()
            return "CPP" if "critical process parameter" in t else "IPC" if "in-process control" in t else cc(c.get("code")) or "Control"
        checks = [{"title": c.get("title"), "kind": kind(c), "type": cc(c.get("code"))} for c in a.get("action", [])]
        out.append({"title": a.get("title"), "description": a.get("description", ""), "params": params, "materials": mats, "devices": devices, "checks": checks})
    return {"title": pd.get("title"), "steps": out, "ref": "PlanDefinition/" + pd_id}

def site(operation):
    for o in mpd.get("operation", []):
        if operation.lower() in cc((o.get("type") or {}).get("concept")).lower():
            return ", ".join(orgs(o.get("organization")))
    return ""

PROC = {"ds": dict(steps("ds-manufacturing-process"), site=site("Drug substance manufacture")), "dp": dict(steps("dp-manufacturing-process"), site=site("Drug product manufacture")), "product": product,
        "tablet": {"properties": tablet["properties"], "components": tablet["components"]}, "ingredients": ingredients,
        "packs": [{"type": p["type"], "box": p["box"]["type"], "primary": p["primary"]["type"] if p["primary"] else ""} for p in packs]}

def write(tpl, out, data):
    t = open(os.path.join(here, tpl), encoding="utf-8").read()
    t = t.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
    open(os.path.join(root, "showcases", out), "w", encoding="utf-8").write(t)
    print("written", out, len(t))

if __name__ == "__main__":
    import sys
    if "--dump" in sys.argv:
        print(json.dumps({"PACK": PACK, "PROC": PROC}, ensure_ascii=False, indent=1))
    else:
        write("pack-layers.template.html", "pqi-pack-layers.html", PACK)
        write("manufacturing-film.template.html", "pqi-manufacturing-film.html", PROC)
