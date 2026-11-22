#!/usr/bin/env python3
"""Fix three issues in the PQI Type 1-4 examples (and the base Sakura Bloom data where they apply).

1. Missing references (Types 3 and 4): every ObservationDefinition, ActivityDefinition or other resource that a
   carried resource references by canonical URL (and whatever those reference in turn, by canonical or plain
   reference) is added to the document Bundle.
   The resources come from fhir/dossier/sakura-bloom-r2-dossier-collection.json (same canonical base).
2. Uncoded operation: MedicinalProductDefinition.operation for Aparna Pharmaceutical (drug product manufacture)
   had an empty type in Type 2. It now carries type.concept "Drug product manufacture" in every copy of the
   resource (Types 2-4 and the base data); Types 3/4 and the base keep the reference to the DP process.
3. Placeholders: each labelled placeholder figure gets the image, title and provenance from figures/manifest.json
   (built by figures/make_figures.py). The Binary bytes, the DocumentReference and the <img alt> are updated.

Idempotent: running it again changes nothing. Stdlib only.
Usage:  python3 sakura-bloom-r2/fhir/pqi-types/fix_pqi_types.py
"""
import base64
import glob
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FHIR = os.path.normpath(os.path.join(HERE, ".."))
BASE_URL = "http://example.org/sakura-bloom-r2/fhir/"
OP_TEXT = "Drug product manufacture"
stats = {"figures": 0, "binaries": 0, "alts": 0, "operations": 0, "added": 0, "files": 0}


def key(r):
    return r["resourceType"] + "/" + r["id"]


def load(path):
    raw = open(path, encoding="utf-8").read()
    obj = json.loads(raw)
    fmt = None
    for indent in (2, 1, None, 4):
        for ea in (False, True):
            for sep in ((", ", ": "), (",", ":"), (",", ": ")):
                if json.dumps(obj, indent=indent, ensure_ascii=ea, separators=sep if indent is None else (",", ": ")) in (raw, raw.rstrip("\n")):
                    fmt = (indent, ea, sep)
                    break
            if fmt: break
        if fmt: break
    return obj, raw, fmt or (2, False, (",", ": "))


def dump(obj, raw, fmt, path):
    indent, ea, sep = fmt
    out = json.dumps(obj, indent=indent, ensure_ascii=ea, separators=sep if indent is None else (",", ": "))
    if raw.endswith("\n"):
        out += "\n"
    if out != raw:
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        stats["files"] += 1


def fix_operation(r):
    if r.get("resourceType") != "MedicinalProductDefinition":
        return
    for op in r.get("operation", []):
        orgs = [o.get("reference") for o in op.get("organization", [])]
        t = op.setdefault("type", {})
        if "Organization/aparna-pharm" in orgs and "concept" not in t and (not t or "dp-manufacturing-process" in json.dumps(t)):
            new = {"concept": {"text": OP_TEXT}}
            new.update(t)
            op["type"] = new
            stats["operations"] += 1


def walk_resources(o):
    """Yield every resource dict inside a Bundle or a single resource (nested Bundles included)."""
    if isinstance(o, dict):
        if "resourceType" in o:
            yield o
        for v in o.values():
            yield from walk_resources(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk_resources(v)


def fix_figures(bundle, manifest, figdir):
    res = {key(e["resource"]): e["resource"] for e in bundle.get("entry", [])}
    titles = {}
    for k, r in res.items():
        if r["resourceType"] != "DocumentReference" or r["id"] not in manifest:
            continue
        m = manifest[r["id"]]
        at = r["content"][0]["attachment"]
        data = open(os.path.join(figdir, m["file"]), "rb").read()
        if r.get("description") != m["description"] or at.get("title") != m["title"]:
            r["description"] = m["description"]
            at["title"] = m["title"]
            at["contentType"] = "image/png"
            stats["figures"] += 1
        if "size" in at:
            at["size"] = len(data)
        if "hash" in at:
            at["hash"] = base64.b64encode(hashlib.sha1(data).digest()).decode()
        b = res.get(at.get("url"))
        if b and b["resourceType"] == "Binary":
            enc = base64.b64encode(data).decode()
            if b.get("data") != enc:
                b["data"] = enc
                b["contentType"] = "image/png"
                stats["binaries"] += 1
        titles[at.get("url")] = m["title"]
    if not titles:
        return
    comp = bundle["entry"][0]["resource"]
    def esc(s): return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    def visit(secs):
        for s in secs or []:
            tx = s.get("text")
            if tx and tx.get("div"):
                def rep(mo):
                    src = mo.group(1)
                    if src in titles:
                        new = f'<img src="{src}" alt="{esc(titles[src])}" />'
                        if new != mo.group(0):
                            stats["alts"] += 1
                        return new
                    return mo.group(0)
                tx["div"] = re.sub(r'<img src="([^"]+)" alt="[^"]*"\s*/>', rep, tx["div"])
            visit(s.get("section"))
    visit(comp.get("section"))


def fill_references(bundle, base, base_by_url):
    carried = {key(e["resource"]) for e in bundle["entry"]}
    queue = [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] not in ("Binary",)]
    added = []
    while queue:
        r = queue.pop()
        txt = json.dumps(r)
        targets = re.findall(r'"(' + re.escape(BASE_URL) + r'[A-Za-z]+/[^"]+)"', txt)
        targets += [BASE_URL + x for x in re.findall(r'"reference": "([A-Z][A-Za-z]+/[A-Za-z0-9\-.]+)"', txt)]
        for u in targets:
            t = base_by_url.get(u) or base.get(u[len(BASE_URL):])
            if not t or key(t) in carried:
                continue
            carried.add(key(t))
            added.append(t)
            queue.append(t)
    for t in sorted(added, key=key):
        bundle["entry"].append({"fullUrl": BASE_URL + key(t), "resource": json.loads(json.dumps(t))})
    stats["added"] += len(added)


def document_bundles(obj):
    if obj.get("type") == "document":
        return [obj]
    return [e["resource"] for e in obj.get("entry", []) if e["resource"].get("resourceType") == "Bundle" and e["resource"].get("type") == "document"]


def main():
    figdir = os.path.join(HERE, "figures")
    manifest = json.load(open(os.path.join(figdir, "manifest.json"), encoding="utf-8"))
    base_obj = json.load(open(os.path.join(FHIR, "dossier", "sakura-bloom-r2-dossier-collection.json"), encoding="utf-8"))
    base = {key(e["resource"]): e["resource"] for e in base_obj["entry"]}
    for r in base.values():
        fix_operation(r)
    base_by_url = {r["url"]: r for r in base.values() if r.get("url")}

    # 1-3: the PQI type examples
    for path in sorted(glob.glob(os.path.join(HERE, "type*", "*.json"))):
        t = int(re.search(r"type(\d)", os.path.basename(os.path.dirname(path))).group(1))
        obj, raw, fmt = load(path)
        for b in document_bundles(obj):
            fix_figures(b, manifest, figdir)
            for r in walk_resources(b):
                fix_operation(r)
            if t in (3, 4):
                fill_references(b, base, base_by_url)
        dump(obj, raw, fmt, path)

    # 2: the same operation fix in the base data (resources, domain bundles, dossier)
    for path in sorted(glob.glob(os.path.join(FHIR, "resources", "MedicinalProductDefinition-*.json")) +
                       glob.glob(os.path.join(FHIR, "bundles", "*.json")) + glob.glob(os.path.join(FHIR, "dossier", "*.json"))):
        obj, raw, fmt = load(path)
        if "MedicinalProductDefinition" not in raw:
            continue
        for r in walk_resources(obj):
            fix_operation(r)
        dump(obj, raw, fmt, path)

    # report what is left
    left = 0
    for path in sorted(glob.glob(os.path.join(HERE, "type*", "*.json"))):
        left += open(path, encoding="utf-8").read().count("Labelled placeholder")
    print(json.dumps(stats), "| placeholders left:", left)


if __name__ == "__main__":
    main()
