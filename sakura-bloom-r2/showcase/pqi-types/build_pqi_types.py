#!/usr/bin/env python3
"""Build the data files for the PQI Type 1-4 showcases.

Reads   sakura-bloom-r2/fhir/pqi-types/type{1..4}/*.json   (the PQI Type 1-4 examples)
        sakura-bloom-r2/fhir/dossier/sakura-bloom-r2-dossier-collection.json
                                                    (base resource set, used only to resolve
                                                     canonical references the type bundles
                                                     point to but do not carry)
Writes  showcases/pqi-types/data/*.js   one data file per type, shared resources, stats, logic.js
        showcases/pqi-types/img/*.png   figures, de-duplicated by content

Deterministic: running it twice gives the same output.
Usage:  python3 sakura-bloom-r2/showcase/pqi-types/build_pqi_types.py
"""
import base64
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SB = os.path.normpath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(SB, "fhir", "pqi-types")
BASE = os.path.join(SB, "fhir", "dossier", "sakura-bloom-r2-dossier-collection.json")
OUT = os.path.normpath(os.path.join(SB, "..", "showcases", "pqi-types"))
DATA = os.path.join(OUT, "data")
IMG = os.path.join(OUT, "img")
FHIR_BASE = "http://example.org/sakura-bloom-r2/fhir/"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def docs_for(t):
    """The 20 document Bundles of one type: Module 2.3 first, then the 19 Module 3.2 documents."""
    d = os.path.join(SRC, "type%d" % t)
    m23 = load(os.path.join(d, "bundle-document-type%d-pq-sakura-bloom-m23.json" % t))
    coll = load(os.path.join(d, "bundle-document-collection-pq-sakura-bloom-m32-type%d.json" % t))
    return m23, coll, [m23] + [e["resource"] for e in coll["entry"]]


def key(r):
    return r["resourceType"] + "/" + r["id"]


def walk_sections(sections, out=None):
    out = [] if out is None else out
    for s in sections or []:
        out.append(s)
        walk_sections(s.get("section"), out)
    return out


def sec_code(s):
    c = s.get("code") or {}
    cod = (c.get("coding") or [{}])[0]
    return cod.get("code") or c.get("text") or s.get("title") or ""


def text_len(div):
    return len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", div or "")).strip())


def js(name, obj):
    return "window.PQIDATA = window.PQIDATA || {};\nPQIDATA.%s = %s;\n" % (
        name, json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


images = {}      # "Binary/img-x" -> "img/<hash>.png"
written = set()


def take_binaries(bundle):
    for e in bundle["entry"]:
        r = e["resource"]
        if r["resourceType"] != "Binary":
            continue
        raw = base64.b64decode(r["data"])
        h = hashlib.sha1(raw).hexdigest()[:12]
        ext = {"image/png": "png", "image/jpeg": "jpg", "image/svg+xml": "svg"}.get(r.get("contentType"), "bin")
        fn = "%s.%s" % (h, ext)
        if fn not in written:
            os.makedirs(IMG, exist_ok=True)
            with open(os.path.join(IMG, fn), "wb") as f:
                f.write(raw)
            written.add(fn)
        images[key(r)] = "img/" + fn


def doc_meta(b):
    comp = b["entry"][0]["resource"]
    counts = {}
    for e in b["entry"]:
        t = e["resource"]["resourceType"]
        counts[t] = counts.get(t, 0) + 1
    return {
        "bundleId": b["id"],
        "bundleType": b.get("type"),
        "bundleProfile": (b.get("meta", {}).get("profile") or [""])[0],
        "identifier": (b.get("identifier") or {}).get("value"),
        "timestamp": b.get("timestamp"),
        "firstEntry": comp["resourceType"],
        "entryCount": len(b["entry"]),
        "counts": counts,
        "fullUrls": sum(1 for e in b["entry"] if e.get("fullUrl")),
    }


def strip_text(r):
    r = dict(r)
    r.pop("text", None)
    return r


def stats_for(t, docs):
    out = []
    for b in docs:
        comp = b["entry"][0]["resource"]
        secs = walk_sections(comp.get("section"))
        authored = gen = links = entries = 0
        gen_secs = 0
        for s in secs:
            tx = s.get("text") or {}
            if tx.get("status") == "generated":
                gen += text_len(tx.get("div"))
                gen_secs += 1
            elif tx.get("div"):
                authored += text_len(tx.get("div"))
            for en in s.get("entry") or []:
                entries += 1
                if any(x.get("url") == "http://hl7.org/fhir/StructureDefinition/textLink" for x in en.get("extension") or []):
                    links += 1
        res = sum(1 for e in b["entry"] if e["resource"]["resourceType"] not in ("Composition", "Binary", "DocumentReference"))
        out.append({
            "code": doc_code(comp), "title": short_title(comp["title"]), "type": t,
            "sections": len(secs), "authoredChars": authored, "generatedChars": gen, "generatedSections": gen_secs,
            "entries": entries, "links": links, "resources": res,
            "figures": sum(1 for e in b["entry"] if e["resource"]["resourceType"] == "Binary"),
            "bytes": len(json.dumps(b, separators=(",", ":"))),
        })
    return out


def doc_code(comp):
    top = [s for s in comp.get("section", []) if sec_code(s) != "pqi-product-data"]
    return sec_code(top[0]) if top else comp["id"]


def short_title(t):
    return re.sub(r"\s*-\s*Sakura Bloom.*$", "", t)


def main():
    base = {key(e["resource"]): e["resource"] for e in load(BASE)["entry"]}
    base_by_url = {r["url"]: r for r in base.values() if r.get("url")}
    stats = {}
    per_type = {}
    for t in (1, 2, 3, 4):
        m23, coll, docs = docs_for(t)
        for b in docs:
            take_binaries(b)
        per_type[t] = (m23, coll, docs)
        stats[t] = stats_for(t, docs)

    collection = {t: {"id": per_type[t][1]["id"], "type": per_type[t][1]["type"],
                      "profile": (per_type[t][1].get("meta", {}).get("profile") or [""])[0],
                      "entries": len(per_type[t][1]["entry"])} for t in per_type}

    # ---------- Type 1: full documents (narrative + figure DocumentReferences) ----------
    m23, coll, docs = per_type[1]
    t1 = {"collection": collection[1], "docs": [], "figures": {}, "images": images}
    for b in docs:
        meta = doc_meta(b)
        meta["composition"] = b["entry"][0]["resource"]
        meta["binaries"] = [key(e["resource"]) for e in b["entry"] if e["resource"]["resourceType"] == "Binary"]
        meta["contained"] = sum(len(e["resource"].get("contained") or []) for e in b["entry"])
        t1["docs"].append(meta)
        for e in b["entry"]:
            r = e["resource"]
            if r["resourceType"] == "DocumentReference":
                t1["figures"][key(r)] = r
    write(os.path.join(DATA, "t1.js"), js("t1", t1))

    # ---------- Type 2: structure + product data (CTD narrative is unchanged from Type 1) ----------
    m23, coll, docs = per_type[2]
    t2 = {"collection": collection[2], "docs": [], "resources": {}, "t1Mentions": {}, "copies": {}}
    t1_intro = next(s for s in walk_sections(t1["docs"][0]["composition"]["section"]) if sec_code(s) == "2.3.INTRO")
    t2["t1Intro"] = re.sub(r"<p>Figure 1[^<]*</p><p><img[^>]*/></p>", "", t1_intro["text"]["div"])
    hashes = {}
    for b in docs:
        meta = doc_meta(b)
        comp = json.loads(json.dumps(b["entry"][0]["resource"]))
        for s in walk_sections(comp.get("section")):
            tx = s.get("text")
            if tx and sec_code(s) != "pqi-product-data":
                s["text"] = {"status": tx.get("status"), "chars": text_len(tx.get("div"))}
        meta["composition"] = comp
        meta["carries"] = sorted(key(e["resource"]) for e in b["entry"]
                                 if e["resource"]["resourceType"] not in ("Composition", "Binary", "DocumentReference"))
        t2["docs"].append(meta)
        for e in b["entry"]:
            r = e["resource"]
            if r["resourceType"] not in ("Composition", "Binary", "DocumentReference"):
                t2["resources"][key(r)] = strip_text(r)
                hashes.setdefault(key(r), set()).add(hashlib.sha1(json.dumps(r, sort_keys=True).encode()).hexdigest())
    for k, hs in hashes.items():
        t2["copies"][k] = {"docs": sum(1 for d in t2["docs"] if k in d["carries"]), "identical": len(hs) == 1}
    # how often key master-data values are written out in the Type 1 narrative
    t1_text = [(d["composition"]["id"], sec_code(s), (s.get("text") or {}).get("div", ""))
               for d in t1["docs"] for s in walk_sections(d["composition"].get("section"))]
    probes = {}
    for k, r in t2["resources"].items():
        if r["resourceType"] == "Organization":
            probes[k] = [r["name"]]
        elif r["resourceType"] == "MedicinalProductDefinition":
            probes[k] = [r["name"][0]["productName"], "Sakura Bloom"]
        elif r["resourceType"] == "SubstanceDefinition" and r["id"] == "sakuramil":
            probes[k] = ["Sakuramil"]
    for k, names in probes.items():
        hits = []
        for doc_id, code, div in t1_text:
            plain = re.sub(r"<[^>]+>", " ", div)
            n = sum(plain.count(nm) for nm in names[-1:])
            if n:
                hits.append([doc_id, code, n])
        t2["t1Mentions"][k] = {"term": names[-1], "hits": hits, "total": sum(h[2] for h in hits)}
    write(os.path.join(DATA, "t2.js"), js("t2", t2))

    # ---------- Shared resource set for Types 3 and 4 ----------
    shared = {}
    for t in (3, 4):
        for b in per_type[t][2]:
            for e in b["entry"]:
                r = e["resource"]
                if r["resourceType"] in ("Composition", "Binary"):
                    continue
                shared[key(r)] = strip_text(r)
    urls = {r.get("url") for r in shared.values() if r.get("url")}
    blob = json.dumps(list(shared.values()))
    cans = sorted(set(re.findall(r'"(' + re.escape(FHIR_BASE) + r'[A-Za-z]+/[^"]+)"', blob)))
    registry = {}
    for c in cans:
        if c in urls or c[len(FHIR_BASE):] in shared:
            continue
        r = base_by_url.get(c) or base.get(c[len(FHIR_BASE):])
        if r:
            registry[key(r)] = strip_text(r)
    write(os.path.join(DATA, "resources.js"), js("resources", {
        "bundle": sorted(shared.values(), key=key),
        "registry": sorted(registry.values(), key=key),
        "note": "registry = resources referenced by canonical URL from the Type 3/4 bundles but not carried in them; "
                "taken from the base Sakura Bloom R2 resource set (same canonical base)."}))

    # ---------- Type 3: linked documents ----------
    for t in (3, 4):
        m23, coll, docs = per_type[t]
        out = {"collection": collection[t], "docs": []}
        for b in docs:
            meta = doc_meta(b)
            meta["composition"] = b["entry"][0]["resource"]
            meta["carries"] = sorted(key(e["resource"]) for e in b["entry"]
                                     if e["resource"]["resourceType"] not in ("Composition", "Binary"))
            out["docs"].append(meta)
        if t == 4:
            # the Type 3 version of every section that Type 4 replaced, for side-by-side comparison
            t3docs = {doc_code(b["entry"][0]["resource"]): b["entry"][0]["resource"] for b in per_type[3][2]}
            out["t3"] = {}
            for b in docs:
                comp = b["entry"][0]["resource"]
                c3 = t3docs.get(doc_code(comp))
                if not c3:
                    continue
                s3 = {sec_code(s): s for s in walk_sections(c3.get("section"))}
                for s in walk_sections(comp.get("section")):
                    c = sec_code(s)
                    if c == "pqi-product-data":
                        continue
                    a = (s3.get(c) or {}).get("text") or {}
                    bb = s.get("text") or {}
                    if a.get("status") != bb.get("status") or a.get("div") != bb.get("div"):
                        out["t3"][c] = {"text": a, "entry": (s3.get(c) or {}).get("entry", [])}
        if t == 4:
            replaced = sum(1 for b in docs for sec in walk_sections(b["entry"][0]["resource"].get("section"))
                           if sec_code(sec) in out["t3"] and (sec.get("text") or {}).get("status") == "generated")
        write(os.path.join(DATA, "t%d.js" % t), js("t%d" % t, out))

    write(os.path.join(DATA, "stats.js"), js("stats", {
        "types": stats, "collections": collection,
        "sourceBytes": {t: os.path.getsize(os.path.join(SRC, "type%d" % t, "bundle-document-type%d-pq-sakura-bloom-m23.json" % t))
                        + os.path.getsize(os.path.join(SRC, "type%d" % t, "bundle-document-collection-pq-sakura-bloom-m32-type%d.json" % t))
                        for t in per_type},
        "images": {"ids": len(images), "unique": len(written)},
        "registry": len(registry),
        "replaced": replaced,
        "uniqueResources": {t: len({key(e["resource"]) for b in per_type[t][2] for e in b["entry"]
                                    if e["resource"]["resourceType"] not in ("Composition", "Binary")
                                    and not (e["resource"]["resourceType"] == "DocumentReference"
                                             and (e["resource"].get("type") or {}).get("text") == "Figure")})
                            for t in per_type}}))

    # drop images no Binary uses any more
    for fn in sorted(os.listdir(IMG)):
        if fn not in written:
            os.remove(os.path.join(IMG, fn))

    # the shared PQI logic module of the structured CMC review (spec/result evaluation, stability series)
    with open(os.path.join(SB, "showcase", "logic.js"), encoding="utf-8") as f:
        write(os.path.join(DATA, "logic.js"), f.read())

    for f in sorted(os.listdir(DATA)):
        print("  %-16s %9d bytes" % (f, os.path.getsize(os.path.join(DATA, f))))
    print("  img/             %d files (%d Binary ids)" % (len(written), len(images)))
    print("  registry fill-ins: %d" % len(registry))


if __name__ == "__main__":
    main()
