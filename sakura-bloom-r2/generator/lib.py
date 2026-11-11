"""Helpers for building the Sakura Bloom R2 FHIR PQI dataset (FHIR R5)."""
import json, re, html, hashlib
from collections import OrderedDict

BASE = "http://example.org/sakura-bloom-r2/fhir"
PQ = "http://hl7.org/fhir/uv/pharm-quality"
SD = PQ + "/StructureDefinition/"
UCUM = "http://unitsofmeasure.org"
EDQM = "http://standardterms.edqm.eu"
CS_LOCAL = PQ + "/CodeSystem/cs-local-codes-drug-pq-example"
CS_PLAN = "http://terminology.hl7.org/CodeSystem/pharmaceutical-plan-type"
CS_ORGTYPE = "http://terminology.hl7.org/CodeSystem/pharmaceutical-organization-type"
CS_REPORT = "http://terminology.hl7.org/CodeSystem/pharmaceutical-report-type"
CS_MFGSTEP = "http://terminology.hl7.org/CodeSystem/manufacturing-step"
CS_PARTROLE = "http://terminology.hl7.org/CodeSystem/manufacturing-participant-role"
CS_IMPTYPE = "http://terminology.hl7.org/CodeSystem/impurity-type"
CS_IMPORIGIN = "http://terminology.hl7.org/CodeSystem/impurity-origin"
CS_SITEUTIL = "http://terminology.hl7.org/CodeSystem/product-site-utilization-type"
CS_CRIT = "http://terminology.hl7.org/CodeSystem/observation-qualified-value-criticality"
CS_SCALE = "http://terminology.hl7.org/CodeSystem/manufacturing-step-scale"
CS_PKGPROP = "http://terminology.hl7.org/CodeSystem/package-property"
NOTION = "https://ichm4q.notion.site/"

PROFILES = {
    "Organization": SD + "Organization-drug-pq",
    "SubstanceDefinition": SD + "SubstanceDefinition-component-substance-drug-pq",
    "Substance": SD + "Substance-drug-pq",
    "MedicinalProductDefinition": SD + "MedicinalProductDefinition-drug-product-pq",
    "ManufacturedItemDefinition": SD + "ManufacturedItemDefinition-drug-pq",
    "PackagedProductDefinition": SD + "PackagedProductDefinition-drug-pq",
    "Ingredient": SD + "Ingredient-drug-pq",
    "PlanDefinition": SD + "PlanDefinition-drug-pq",
    "ObservationDefinition": SD + "ObservationDefinition-test-method-drug-pq",
    "ActivityDefinition": SD + "ActivityDefinition-test-drug-pq",
    "Observation": SD + "Observation-test-result-drug-pq",
    "DiagnosticReport": SD + "DiagnosticReport-analysis-drug-pq",
    "Medication": SD + "Medication-batch-information-drug-pq",
    "SpecimenDefinition": SD + "SpecimenDefinition-drug-pq",
    "Specimen": SD + "Specimen-drug-pq",
    "DeviceDefinition": SD + "DeviceDefinition-drug-pq",
    "DocumentReference": SD + "DocumentReference-drug-pq",
    "Composition": SD + "Composition-drug-pq",
    "Procedure": SD + "Procedure-drug-pq",
}

CANONICAL_TYPES = {"PlanDefinition", "ObservationDefinition", "ActivityDefinition", "SpecimenDefinition"}

R = OrderedDict()          # id -> resource
GROUPS = {}                # bundle name -> list of (type,id)
ISSUES = []                # source data issues / modelling notes


def slug(s, maxlen=60):
    s = s.lower().replace("µ", "u").replace("°", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > maxlen:
        h = hashlib.md5(s.encode()).hexdigest()[:6]
        s = s[:maxlen - 7].rstrip("-") + "-" + h
    return s


def key(rtype, rid):
    return f"{rtype}/{rid}"


def add(rtype, rid, body, groups=(), source=None):
    assert re.match(r"^[A-Za-z0-9\-\.]{1,64}$", rid), rid
    k = key(rtype, rid)
    if k in R:
        raise ValueError("duplicate " + k)
    res = OrderedDict()
    res["resourceType"] = rtype
    res["id"] = rid
    meta = {"profile": [PROFILES[rtype]]} if rtype in PROFILES else {}
    if source:
        meta["source"] = source
    if meta:
        res["meta"] = meta
    if rtype in CANONICAL_TYPES:
        res["url"] = f"{BASE}/{rtype}/{rid}"
    res.update(body)
    R[k] = res
    for g in groups:
        tag(g, rtype, rid)
    return res


def tag(group, rtype, rid):
    GROUPS.setdefault(group, [])
    if (rtype, rid) not in GROUPS[group]:
        GROUPS[group].append((rtype, rid))


def ref(rtype, rid, display=None):
    k = key(rtype, rid)
    r = {"reference": k}
    if display:
        r["display"] = display
    return r


def canon(rtype, rid):
    return f"{BASE}/{rtype}/{rid}"


def cc(text=None, system=None, code=None, display=None):
    c = {}
    if system and code:
        cd = {"system": system, "code": code}
        if display:
            cd["display"] = display
        c["coding"] = [cd]
    if text:
        c["text"] = text
    return c


UNIT_MAP = {
    "%": ("%", "%"), "ppm": ("[ppm]", "ppm"), "mg": ("mg", "mg"), "kg": ("kg", "kg"), "g": ("g", "g"),
    "nm": ("nm", "nm"), "µm": ("um", "µm"), "um": ("um", "µm"), "min": ("min", "min"), "kn": ("kN", "kN"),
    "kp": ("kgf", "kp"), "°c": ("Cel", "°C"), "c": ("Cel", "°C"), "cfu/g": ("{CFU}/g", "CFU/g"),
    "mo": ("mo", "months"), "months": ("mo", "months"), "l": ("L", "L"), "ml": ("mL", "mL"),
    "m³/min": ("m3/min", "m³/min"), "g/min": ("g/min", "g/min"), "rpm": ("/min", "rpm"),
    "°c/min": ("Cel/min", "°C/min"), "µg/g": ("ug/g", "µg/g"), "mg/ml": ("mg/mL", "mg/mL"),
    "tablets": ("{tablets}", "tablets"), "g/mol": ("g/mol", "g/mol"), "cc": ("cm3", "cc"), "mm": ("mm", "mm"),
}


def q(value, unit=None, comparator=None):
    out = OrderedDict()
    if comparator:
        out["comparator"] = comparator
    out["value"] = value
    if unit:
        code, disp = UNIT_MAP.get(unit.lower(), (None, unit))
        out["unit"] = disp
        if code:
            out["system"] = UCUM
            out["code"] = code
    return out


NUM = r"(\d+(?:[.,]\d+)?)"
UNIT_RX = r"(%|ppm|mg|kg|nm|µm|um|CFU/g|kN|kp|°C|min|g)?"


def fnum(s):
    s = s.replace(",", ".")
    v = float(s)
    return int(v) if v.is_integer() and "." not in s else v


def parse_criterion(text):
    """Parse an acceptance criterion into a Range (low/high quantities) where possible."""
    t = text.replace("–", "-").replace("—", "-").replace("‑", "-").strip()
    t2 = re.sub(r"\s+", " ", t)
    m = re.search(r"(?:NMT|not more than|≤|<=|max\.?)\s*" + NUM + r"\s*" + UNIT_RX, t2, re.I)
    if m:
        return {"high": q(fnum(m.group(1)), m.group(2))}
    m = re.search(r"(?:NLT|not less than|≥|>=)\s*" + NUM + r"\s*" + UNIT_RX, t2, re.I)
    if m:
        return {"low": q(fnum(m.group(1)), m.group(2))}
    m = re.search(NUM + r"\s*" + UNIT_RX + r"\s*(?:-|to)\s*" + NUM + r"\s*" + UNIT_RX, t2)
    if m:
        u = m.group(4) or m.group(2)
        return {"low": q(fnum(m.group(1)), u), "high": q(fnum(m.group(3)), u)}
    return None


def parse_result(text):
    """Parse a reported result -> (value[x] key, value)."""
    t = re.sub(r"\s+", " ", text.replace("–", "-")).strip()
    if not t or t in {"-", "—"}:
        return None
    m = re.match(r"^(<|>|≤|≥)\s*" + NUM + r"\s*" + UNIT_RX + r"\s*$", t)
    if m:
        comp = {"≤": "<=", "≥": ">="}.get(m.group(1), m.group(1))
        return ("valueQuantity", q(fnum(m.group(2)), m.group(3) or None, comp))
    m = re.match(r"^" + NUM + r"\s*" + UNIT_RX + r"$", t)
    if m:
        return ("valueQuantity", q(fnum(m.group(1)), m.group(2) or None))
    if re.match(r"^<\s*LOQ$", t, re.I):
        return ("valueString", "< LOQ")
    return ("valueString", t)


def ext(url, **kw):
    e = OrderedDict([("url", url)])
    e.update(kw)
    return e


def qv_text(s):
    return ext(SD + "Extension-qualified-value-text-pq", valueString=s)


# ---------------------------------------------------------------- source access
class Source:
    def __init__(self, path):
        d = json.load(open(path))
        self.pages = d["pages"]
        self.collections = d["collections"]
        for p in self.pages:
            p["short"] = p["path"].replace("ICH M4Q(R2) Final Mock-ups / SakuraBloom R2  / ", "")
            p["url"] = NOTION + p["id"].replace("-", "")

    def page(self, pat, last=True):
        hits = [p for p in self.pages if (p["short"].split(" / ")[-1] if last else p["short"]).strip().startswith(pat)]
        if not hits:
            hits = [p for p in self.pages if pat in p["short"]]
        if not hits:
            raise KeyError(pat)
        return hits[0]

    @staticmethod
    def tables(text):
        """Return list of (caption, rows) for pipe tables in rendered text."""
        out, cur, cap, prev = [], None, None, ""
        for line in text.split("\n"):
            s = line.strip()
            if s.startswith("|") and s.endswith("|"):
                cells = [c.strip() for c in s[1:-1].split(" | ")]
                if cur is None:
                    cur = []
                    cap = prev
                cur.append(cells)
            else:
                if cur is not None:
                    out.append((cap, cur))
                    cur = None
                if s:
                    prev = s.lstrip("#").strip()
        if cur is not None:
            out.append((cap, cur))
        return out


# ---------------------------------------------------------------- narrative
def md_to_xhtml(text, maxlen=None):
    """Convert the extract's lightweight markup into FHIR-safe XHTML."""
    lines = text.split("\n")
    out, tbl = [], []

    def flush():
        if tbl:
            rows = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in tbl)
            out.append(f"<table border=\"1\">{rows}</table>")
            tbl.clear()

    for ln in lines:
        s = ln.strip()
        if s.startswith("|") and s.endswith("|") and len(s) > 1:
            tbl.append([c.strip() for c in s[1:-1].split(" | ")])
            continue
        flush()
        if not s:
            continue
        if s.startswith("#"):
            lvl = min(len(s) - len(s.lstrip("#")) + 2, 6)
            out.append(f"<h{lvl}>{html.escape(s.lstrip('#').strip())}</h{lvl}>")
        elif s.startswith("- ") or s.startswith("1. "):
            out.append(f"<p>• {html.escape(s.split(' ',1)[1])}</p>")
        elif s.startswith("→ [PAGE:"):
            continue
        else:
            out.append(f"<p>{html.escape(s)}</p>")
    flush()
    body = "".join(out) or "<p>(no content)</p>"
    return {"status": "generated", "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{body}</div>"}


def bundle(bid, profile_id, entries, btype="collection", ts="2026-11-08T00:00:00Z", title=None):
    b = OrderedDict()
    b["resourceType"] = "Bundle"
    b["id"] = bid
    if profile_id:
        b["meta"] = {"profile": [SD + profile_id]}
    b["identifier"] = {"system": BASE + "/bundle-id", "value": bid}
    b["type"] = btype
    b["timestamp"] = ts
    b["entry"] = []
    for rtype, rid in entries:
        e = OrderedDict()
        e["fullUrl"] = f"{BASE}/{rtype}/{rid}"
        e["resource"] = R[key(rtype, rid)]
        if btype == "transaction":
            e["request"] = {"method": "PUT", "url": f"{rtype}/{rid}"}
        b["entry"].append(e)
    return b


def finalize():
    """Post-process: R5 cardinality fixes and minimal generated narrative."""
    def fix_actions(acts):
        for a in acts or []:
            if isinstance(a.get("code"), list):
                a["code"] = a["code"][0] if a["code"] else None
                if a["code"] is None:
                    del a["code"]
            fix_actions(a.get("action"))
    for k, r in R.items():
        if r["resourceType"] == "PlanDefinition":
            fix_actions(r.get("action"))
        if "text" not in r and r["resourceType"] != "Composition":
            label = (r.get("title") or r.get("name") if isinstance(r.get("name"), str) else None) or \
                    (r.get("name", [{}])[0].get("name") if isinstance(r.get("name"), list) and r["name"] and isinstance(r["name"][0], dict) and "name" in r["name"][0] else None) or \
                    (r.get("name", [{}])[0].get("productName") if r["resourceType"] == "MedicinalProductDefinition" else None) or \
                    (r.get("code", {}).get("text") if isinstance(r.get("code"), dict) else None) or \
                    (r.get("deviceName", [{}])[0].get("name") if r["resourceType"] == "DeviceDefinition" else None) or \
                    r.get("description") or r["id"]
            extra = ""
            if r["resourceType"] == "Observation":
                v = r.get("valueQuantity") or r.get("valueString")
                if isinstance(v, dict):
                    v = f"{v.get('comparator','')}{v.get('value')} {v.get('unit','')}"
                subj = r.get("subject", {}).get("reference", "")
                extra = f": {v} ({subj})"
            elif r["resourceType"] == "ObservationDefinition":
                extra = ": " + "; ".join((qv.get("context", {}).get("text", "") + " " + qv["extension"][0]["valueString"]).strip() for qv in r.get("qualifiedValue", []))
            elif r["resourceType"] in ("Substance", "Medication"):
                lot = (r.get("batch", {}) or {}).get("lotNumber") or (r.get("identifier", [{}])[0].get("value"))
                extra = f" - lot {lot}"
            r["text"] = {"status": "generated", "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\"><p><b>{html.escape(r['resourceType'])}</b> {html.escape(str(label))}{html.escape(extra)}</p></div>"}
            # keep text right after meta/url for readability
            items = list(r.items())
            r.clear()
            for kk, vv in items:
                if kk == "text":
                    continue
                r[kk] = vv
                if kk == ("url" if "url" in dict(items) else ("meta" if "meta" in dict(items) else "id")):
                    r["text"] = dict(items)["text"]
