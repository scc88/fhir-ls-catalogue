#!/usr/bin/env python3
"""Build the synthetic ePI Type 1-4 examples for the ePI showcases.

    python3 showcases/epi-types/build/build_epi_types.py

Product data (product, tablet, ingredients, substances, sites) is reused from the Sakura Bloom
PQI dataset in sakura-bloom-r2/fhir/resources, so the ePI and PQI showcases describe the same
fictitious product. Pack sizes, GTINs, the marketing authorisation and every clinical statement
are invented here (see content.py). Output is deterministic.

Writes
  showcases/epi-types/fhir/Bundle-epi-t{1..4}-{smpc-en|pil-en|ifu-en}.json   FHIR R5 document bundles
  showcases/epi-types/data/epi-data.js                                    the same bundles for the pages
"""
import base64, copy, json, re, sys, uuid
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import content as C  # noqa: E402

ROOT = HERE.parents[2]
PQI = ROOT / "sakura-bloom-r2" / "fhir" / "resources"
OUT = HERE.parent
BASE = "http://example.org/fhir-gra/epi"
NS = uuid.UUID("6f1c3a52-0b7e-4c1e-9a55-5a4b0e1d2c01")
DATE = "2026-11-02"
TS = "2026-11-02T09:00:00Z"

EPI = "http://hl7.org/fhir/uv/emedicinal-product-info"
SPOR = "https://spor.ema.europa.eu/rmswi"
SCT = "http://snomed.info/sct"
ATC = "http://www.whocc.no/atc"
EDQM = "http://standardterms.edqm.eu"
UCUM = "http://unitsofmeasure.org"
LOCAL = "http://example.org/fhir-gra/CodeSystem/synthetic-concept"
PILCS = "http://example.org/fhir-gra/CodeSystem/pil-section"
IFUCS = "http://example.org/fhir-gra/CodeSystem/ifu-section"
TYPECS = "http://example.org/fhir-gra/CodeSystem/epi-type"
FREQCS = "http://example.org/fhir-gra/CodeSystem/frequency"
TEXTLINK = "http://hl7.org/fhir/StructureDefinition/textLink"
TRANSL = "http://hl7.org/fhir/StructureDefinition/translation"
HTEST = {"system": "http://terminology.hl7.org/CodeSystem/v3-ActReason", "code": "HTEST", "display": "test health data"}
XHTML = "http://www.w3.org/1999/xhtml"

ABBR = {"CUD": "ClinicalUseDefinition", "ING": "Ingredient", "PPD": "PackagedProductDefinition", "MPD": "MedicinalProductDefinition",
        "MID": "ManufacturedItemDefinition", "APD": "AdministrableProductDefinition", "ORG": "Organization",
        "RA": "RegulatedAuthorization", "GRP": "Group", "SD": "SubstanceDefinition"}
LEVEL3 = {"ClinicalUseDefinition", "Group"}  # everything else is product data (Type 2)
TYPE_NAMES = {1: "Digital label", 2: "Product identification", 3: "Clinical information", 4: "Dynamic digital label"}


def cc(system, code, display, text=None):
    return {"coding": [{"system": system, "code": code, "display": display}], "text": text or display}


def tx(text):
    return {"text": text}


def q(v, unit, code=None):
    return {"value": v, "unit": unit, "system": UCUM, "code": code or unit}


def uid(name):
    return "urn:uuid:" + str(uuid.uuid5(NS, name))


def gtin(base13):
    digits = [int(c) for c in base13]
    s = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(digits)))
    return base13 + str((10 - s % 10) % 10)


def load(name):
    return json.loads((PQI / f"{name}.json").read_text(encoding="utf-8"))


def mark(r, note=None):
    r = copy.deepcopy(r)
    m = r.setdefault("meta", {})
    m["security"] = [HTEST]
    if note:
        m.setdefault("tag", []).append({"system": "http://example.org/fhir-gra/CodeSystem/provenance", "code": "reused-from-pqi", "display": note})
    return r


# ====================================================================== resources
def product_resources():
    R = {}
    mpd = load("MedicinalProductDefinition-sakura-bloom-20mg")
    mpd.pop("operation", None)
    mpd.pop("text", None)
    mpd["characteristic"] = [c for c in mpd.get("characteristic", []) if c["type"]["text"] in ("Maximum daily dose", "Method of administration")]
    mpd["legalStatusOfSupply"] = tx("Medicinal product subject to medical prescription")
    R["MedicinalProductDefinition/sakura-bloom-20mg"] = mark(mpd, "Same resource as the Sakura Bloom PQI dataset (manufacturing operations removed)")

    mid = load("ManufacturedItemDefinition-sakura-bloom-20mg-tablet")
    mid.pop("text", None)
    mid["property"] = mid.get("property", []) + [{"type": cc(f"{EPI}/CodeSystem/epi-ig", "image", "Image"),
                                                  "valueAttachment": {"contentType": "image/svg+xml", "url": "#tablet-image", "title": "Tablet image"}}]
    R["ManufacturedItemDefinition/sakura-bloom-20mg-tablet"] = mark(mid, "Same resource as the Sakura Bloom PQI dataset")

    for f in sorted(PQI.glob("Ingredient-*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        r.pop("text", None)
        R[f"Ingredient/{r['id']}"] = mark(r, "Same resource as the Sakura Bloom PQI dataset")

    sds = ["sakuramil", "lactose-monohydrate", "microcrystalline-cellulose", "croscarmellose-sodium", "hydroxypropyl-cellulose",
           "magnesium-stearate", "hypromellose", "macrogol-6000", "titanium-dioxide", "iron-oxide-red", "coating-premix-red", "purified-water"]
    for s in sds:
        r = load(f"SubstanceDefinition-{s}")
        r.pop("text", None)
        for k in ("manufacturer", "supplier", "relationship", "characterization", "property"):
            r.pop(k, None)
        R[f"SubstanceDefinition/{s}"] = mark(r, "Same resource as the Sakura Bloom PQI dataset (CMC detail removed)")

    for o in ["sakura-pharma", "aparna-pharm", "pack-alpha", "cocopharma"]:
        r = load(f"Organization-{o}")
        r.pop("text", None)
        R[f"Organization/{o}"] = mark(r, "Same resource as the Sakura Bloom PQI dataset")

    R["Organization/sakura-pharma-eu"] = mark({
        "resourceType": "Organization", "id": "sakura-pharma-eu",
        "identifier": [{"system": "http://example.org/fhir-gra/organization-id", "value": "SAKURA-EU-0001"}],
        "active": True, "type": [cc(f"{EPI}/CodeSystem/epi-ig", "marketing-authorization-holder", "Marketing authorization holder")],
        "name": "Sakura Pharmaceuticals Europe B.V.",
        "contact": [{"address": {"use": "work", "type": "physical", "line": ["Bloesemlaan 1"], "city": "Amsterdam", "postalCode": "1000 AA", "country": "NL"}}],
        "partOf": {"reference": "Organization/sakura-pharma"}})

    R["AdministrableProductDefinition/apd-sakura-bloom-20mg"] = mark({
        "resourceType": "AdministrableProductDefinition", "id": "apd-sakura-bloom-20mg", "status": "active",
        "formOf": [{"reference": "MedicinalProductDefinition/sakura-bloom-20mg"}],
        "administrableDoseForm": cc(EDQM, "10221000", "Film-coated tablet"),
        "unitOfPresentation": cc(EDQM, "15054000", "Tablet"),
        "producedFrom": [{"reference": "ManufacturedItemDefinition/sakura-bloom-20mg-tablet"}],
        "routeOfAdministration": [{"code": cc(EDQM, "20053000", "Oral use")}]})

    packs = [("ppd-blister-28", "pack-pa-al-pvc-blister", "28 tablets (4 blisters of 7)", 28, "0200000102802"[:13], 4, 7, "blister",
              "PA/Al/PVC cold-form blisters of 7 film-coated tablets, 4 blisters in a carton."),
             ("ppd-bottle-30", "pack-hdpe-bottle", "30 tablets (bottle)", 30, "0200000103002"[:13], 1, 30, "bottle",
              "White HDPE bottle with child-resistant polypropylene closure and induction seal, 30 film-coated tablets, in a carton.")]
    for pid, src, label, n, base, inner_n, per, kind, desc in packs:
        p = load(f"PackagedProductDefinition-{src}")
        p.pop("text", None)
        p["id"] = pid
        p["name"] = f"Sakura Bloom 20 mg film-coated tablets - {label}"
        p["identifier"] = [{"system": "https://www.gs1.org/gtin", "value": gtin(base)}]
        p["containedItemQuantity"] = [q(n, "tablet", "{tablet}")]
        p["description"] = desc + f" Derived from the PQI PackagedProductDefinition/{src}; pack size and GTIN invented for this example."
        p["legalStatusOfSupply"] = [{"code": tx("Medicinal product subject to medical prescription")}]
        outer = p["packaging"]
        outer["quantity"] = 1
        inner = outer["packaging"][0]
        inner["quantity"] = inner_n
        inner["containedItem"] = [{"item": {"reference": {"reference": "ManufacturedItemDefinition/sakura-bloom-20mg-tablet"}}, "amount": q(per, "tablet", "{tablet}")}]
        R[f"PackagedProductDefinition/{pid}"] = mark(p, f"Packaging reused from PQI PackagedProductDefinition/{src}")

    for n, (pid, label) in enumerate([("ppd-blister-28", "28 tablets, blister"), ("ppd-bottle-30", "30 tablets, bottle")], 1):
        R[f"RegulatedAuthorization/ra-sakura-bloom-00{n}"] = mark({
            "resourceType": "RegulatedAuthorization", "id": f"ra-sakura-bloom-00{n}",
            "identifier": [{"system": "http://example.org/fhir-gra/marketing-authorisation-number", "value": f"EU/1/00/0000/00{n}"}],
            "subject": [{"reference": f"PackagedProductDefinition/{pid}"}, {"reference": "MedicinalProductDefinition/sakura-bloom-20mg"}],
            "type": tx("Marketing authorisation"), "description": f"Synthetic marketing authorisation ({label}).",
            "region": [tx("European Union (synthetic)")],
            "status": cc("http://hl7.org/fhir/publication-status", "active", "Active"), "statusDate": "2026-03-02",
            "validityPeriod": {"start": "2026-03-02"},
            "holder": {"reference": "Organization/sakura-pharma-eu"}})
    return R


def group(gid, name, code, display, rng):
    return mark({"resourceType": "Group", "id": gid, "name": name, "type": "person", "membership": "definitional",
                 "characteristic": [{"code": cc(LOCAL, code, display), "valueRange": rng, "exclude": False}]})


def cud(cid, kind, body, population=None):
    r = {"resourceType": "ClinicalUseDefinition", "id": cid, "type": kind,
         "category": [cc(f"{EPI}/CodeSystem/epi-ig", kind if kind != "undesirable-effect" else "undesirable-effect",
                         {"indication": "Indication", "contraindication": "Contraindication", "interaction": "Interaction",
                          "undesirable-effect": "Undesirable effect", "warning": "Warning"}[kind])],
         "subject": [{"reference": "MedicinalProductDefinition/sakura-bloom-20mg"}],
         "status": cc("http://hl7.org/fhir/publication-status", "active", "Active")}
    key = {"undesirable-effect": "undesirableEffect"}.get(kind, kind)
    r[key] = body
    if population:
        r["population"] = [{"reference": f"Group/{p}"} for p in population]
    return mark(r)


def cr(system, code, display, text=None):
    return {"concept": cc(system, code, display, text)}


def drug(code, name):
    return cc(ATC, code, name)


# undesirable effects: id, system, code, medical term, SOC, frequency, patient term
UE = [
    ("ue-headache", SCT, "25064002", "Headache", "Nervous system disorders", "common", "headache"),
    ("ue-nausea", SCT, "422587007", "Nausea", "Gastrointestinal disorders", "common", "feeling sick (nausea)"),
    ("ue-myalgia", SCT, "68962001", "Myalgia", "Musculoskeletal and connective tissue disorders", "common", "muscle pain"),
    ("ue-dizziness", SCT, "404640003", "Dizziness", "Nervous system disorders", "uncommon", "dizziness"),
    ("ue-hypertension", SCT, "38341003", "Hypertension", "Vascular disorders", "uncommon", "high blood pressure"),
    ("ue-alt-increased", LOCAL, "alt-increased", "Alanine aminotransferase increased", "Investigations", "uncommon",
     "raised liver enzymes in blood tests"),
    ("ue-rash", SCT, "271807003", "Rash", "Skin and subcutaneous tissue disorders", "rare", "skin rash"),
    ("ue-angioedema", SCT, "41291007", "Angioedema", "Skin and subcutaneous tissue disorders", "rare",
     "swelling of the face, lips, tongue or throat (angioedema)"),
]
# not in the bundles: offered by the Type 4 "one change, every document" showcase
UE_CANDIDATE = ("ue-insomnia", SCT, "193462001", "Insomnia", "Psychiatric disorders", "uncommon", "difficulty sleeping (insomnia)")


def ue_resource(row):
    cid, system, code, term, soc, freq, en = row
    concept = cc(system, code, term, en)
    return cud(cid, "undesirable-effect", {
        "symptomConditionEffect": {"concept": concept},
        "classification": tx(soc),
        "frequencyOfOccurrence": cc(FREQCS, freq, C.FREQ[freq]["en"])})


def clinical_resources():
    R = {}
    R["Group/grp-adults"] = group("grp-adults", "Adults (18 years and over)", "age", "Age", {"low": q(18, "years", "a")})
    R["Group/grp-severe-renal"] = group("grp-severe-renal", "Severe renal impairment (eGFR below 30 mL/min/1.73 m2)", "egfr",
                                        "Estimated glomerular filtration rate", {"high": q(30, "mL/min/1.73 m2", "mL/min/{1.73_m2}")})
    ind = cud("ind-hypercholesterolaemia", "indication", {
        "diseaseSymptomProcedure": cr(SCT, "13644009", "Hypercholesterolaemia", "Primary hypercholesterolaemia"),
        "intendedEffect": {"concept": tx("Reduction of LDL-cholesterol, as an adjunct to diet")}}, ["grp-adults"])
    ind["extension"] = [{"url": f"{EPI}/StructureDefinition/ext-epi-dosing-guideline", "valueDosage": {
        "text": "20 mg once daily; may be increased to 40 mg once daily after at least 4 weeks. Maximum 40 mg a day.",
        "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
        "route": cc(EDQM, "20053000", "Oral use"),
        "doseAndRate": [{"doseQuantity": q(20, "mg")}],
        "maxDosePerPeriod": [{"numerator": q(40, "mg"), "denominator": q(1, "day", "d")}]}}]
    R["ClinicalUseDefinition/ind-hypercholesterolaemia"] = ind

    R["ClinicalUseDefinition/ci-hypersensitivity"] = cud("ci-hypersensitivity", "contraindication", {
        "diseaseSymptomProcedure": cr(SCT, "421961002", "Hypersensitivity reaction", "Hypersensitivity to Sakuramil or to any of the excipients")})
    R["ClinicalUseDefinition/ci-liver"] = cud("ci-liver", "contraindication", {
        "diseaseSymptomProcedure": cr(SCT, "235856003", "Disorder of liver", "Active liver disease or unexplained persistent elevation of serum transaminases")})
    R["ClinicalUseDefinition/ci-strong-cyp3a4"] = cud("ci-strong-cyp3a4", "contraindication", {
        "diseaseSymptomProcedure": {"concept": tx("Concomitant treatment with a strong CYP3A4 inhibitor")},
        "otherTherapy": [{"relationshipType": cc("http://hl7.org/fhir/therapy-relationship-type", "contraindicated-only-with", "Contraindicated only with"),
                          "treatment": {"concept": d}} for d in (drug("J02AB02", "ketoconazole"), drug("J02AC02", "itraconazole"), drug("J01FA09", "clarithromycin"))]})
    R["ClinicalUseDefinition/ci-pregnancy"] = cud("ci-pregnancy", "contraindication", {"diseaseSymptomProcedure": cr(SCT, "77386006", "Pregnancy", "Pregnancy")})
    R["ClinicalUseDefinition/ci-breastfeeding"] = cud("ci-breastfeeding", "contraindication", {"diseaseSymptomProcedure": cr(LOCAL, "breastfeeding", "Breast-feeding")})

    R["ClinicalUseDefinition/warn-liver-enzymes"] = cud("warn-liver-enzymes", "warning", {
        "description": "Perform liver function tests before treatment, at 12 weeks and periodically thereafter. Stop treatment if transaminases rise persistently above 3 x ULN.",
        "code": cc(LOCAL, "liver-function-monitoring", "Liver function monitoring")})
    R["ClinicalUseDefinition/warn-blood-pressure"] = cud("warn-blood-pressure", "warning", {
        "description": "Check blood pressure before treatment and at each follow-up visit, particularly in patients with hypertension.",
        "code": cc(SCT, "38341003", "Hypertension")})
    R["ClinicalUseDefinition/warn-lactose"] = cud("warn-lactose", "warning", {
        "description": "Contains lactose. Patients with hereditary galactose intolerance, total lactase deficiency or glucose-galactose malabsorption should not take this medicine.",
        "code": cc(LOCAL, "galactose-intolerance", "Hereditary galactose intolerance, lactase deficiency or glucose-galactose malabsorption")})
    R["ClinicalUseDefinition/warn-renal-severe"] = cud("warn-renal-severe", "warning", {
        "description": "Severe renal impairment (eGFR below 30 mL/min/1.73 m2): do not exceed 20 mg once daily.",
        "code": cc(SCT, "709044004", "Chronic kidney disease")}, ["grp-severe-renal"])

    def inter(cid, drugs, itype, effect, management):
        return cud(cid, "interaction", {
            "interactant": [{"itemCodeableConcept": d} for d in drugs],
            "type": cc("http://hl7.org/fhir/interaction-type", itype, {"drug-drug": "Drug-drug interaction", "drug-food": "Drug-food interaction"}[itype]),
            "effect": {"concept": tx(effect)}, "management": [tx(management)]})
    R["ClinicalUseDefinition/int-cyp3a4-strong"] = inter("int-cyp3a4-strong",
        [drug("J02AB02", "ketoconazole"), drug("J02AC02", "itraconazole"), drug("J01FA09", "clarithromycin")], "drug-drug",
        "Sakuramil exposure (AUC) increased about 4-fold", "Contraindicated (see section 4.3)")
    R["ClinicalUseDefinition/int-cyp3a4-moderate"] = inter("int-cyp3a4-moderate",
        [drug("C08DB01", "diltiazem"), drug("C08DA01", "verapamil")], "drug-drug",
        "Sakuramil exposure increased about 2-fold", "Do not exceed 20 mg once daily")
    R["ClinicalUseDefinition/int-rifampicin"] = inter("int-rifampicin", [drug("J04AB02", "rifampicin")], "drug-drug",
        "Sakuramil exposure reduced by about 70%", "Avoid concomitant use")
    R["ClinicalUseDefinition/int-warfarin"] = inter("int-warfarin", [drug("B01AA03", "warfarin")], "drug-drug",
        "Small increase in INR", "Monitor INR when Sakura Bloom is started, stopped or its dose changed")
    R["ClinicalUseDefinition/int-grapefruit"] = inter("int-grapefruit", [cc(LOCAL, "grapefruit-juice", "Grapefruit juice")], "drug-food",
        "Increased Sakuramil exposure with large quantities", "Avoid more than 1 litre a day")
    for row in UE:
        R[f"ClinicalUseDefinition/{row[0]}"] = ue_resource(row)
    return R


# ====================================================================== generated blocks
def ues(R):
    out = []
    for k, r in R.items():
        if k.startswith("ClinicalUseDefinition/") and r["type"] == "undesirable-effect":
            u = r["undesirableEffect"]
            c = u["symptomConditionEffect"]["concept"]
            out.append({"id": r["id"], "term": c["coding"][0]["display"], "en": c["text"],
                        "soc": u["classification"]["text"], "freq": u["frequencyOfOccurrence"]["coding"][0]["code"]})
    return out


def ue_table(items):
    """Must stay identical to EP.ueTable in epi-types.js."""
    rows = []
    for soc in C.SOC_ORDER:
        for f in sorted(C.FREQ, key=lambda k: C.FREQ[k]["rank"]):
            hits = sorted((i for i in items if i["soc"] == soc and i["freq"] == f), key=lambda i: i["id"])
            if hits:
                rows.append(f"<tr><td>{soc}</td><td>{C.FREQ[f]['en']}</td><td>" +
                            ", ".join(f"{{{{CUD/{i['id']}|{i['term']}}}}}" for i in hits) + "</td></tr>")
    return ('<div id="gen-ue-table"><table><tr><th>System organ class</th><th>Frequency</th><th>Adverse reaction</th></tr>'
            + "".join(rows) + "</table></div>")


def pil_se(items, lang):
    """Must stay identical to EP.pilSideEffects in epi-types.js."""
    parts = []
    for f in sorted(C.FREQ, key=lambda k: C.FREQ[k]["rank"]):
        hits = [i for i in items if i["freq"] == f]
        hits.sort(key=lambda i: (C.SOC_ORDER.index(i["soc"]), i["id"]))
        if hits:
            parts.append(f"<p><b>{C.FREQ[f][lang + '_pil']}</b></p><ul>" +
                         "".join(f"<li>{{{{CUD/{i['id']}|{i[lang]}}}}}</li>" for i in hits) + "</ul>")
    return '<div id="gen-pil-se">' + "".join(parts) + "</div>"


# ====================================================================== documents
LINK_RE = re.compile(r"\{\{([A-Za-z]+)/([A-Za-z0-9\-.]+)\|(.+?)\}\}", re.S)


def expand(html, t, state):
    def rep(m):
        rt = ABBR.get(m.group(1), m.group(1))
        ref = f"{rt}/{m.group(2)}"
        text = m.group(3)
        if t < (3 if rt in LEVEL3 else 2):
            return text
        state["entries"].append(ref)
        state["all"].add(ref)
        if t < 4:
            return text
        state["n"] += 1
        hid = f"{m.group(2)}-{state['n']}"
        state["links"].append((hid, ref))
        return f'<span id="{hid}">{text}</span>'
    return LINK_RE.sub(rep, html)


def build_section(node, t, codesys, state, gen, idp):
    code, display, title, html, children = node
    for k, v in gen.items():
        html = html.replace(k, v)
    state["entries"], state["links"] = [], []
    body = expand(html, t, state)
    div = f'<div xmlns="{XHTML}">{body}</div>'
    ET.fromstring(div)  # well-formed XHTML or fail the build
    s = {"id": f"{idp}{code}", "title": title, "code": cc(codesys, code, display), "text": {"status": "additional", "div": div}}
    if state["links"]:
        s["text"]["extension"] = [{"url": TEXTLINK, "extension": [{"url": "htmlid", "valueString": h}, {"url": "data", "valueUri": r}]} for h, r in state["links"]]
    seen = []
    for r in state["entries"]:
        if r not in seen:
            seen.append(r)
    if seen:
        s["entry"] = [{"reference": r} for r in seen]
    kids = [build_section(ch, t, codesys, state, gen, idp) for ch in children]
    if kids:
        s["section"] = kids
    return s


TABLET_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 120" width="240" height="120"><title>Sakura Bloom 20 mg tablet, both faces</title>
<defs><radialGradient id="g" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#f6c9c4"/><stop offset="1" stop-color="#d98f88"/></radialGradient></defs>
<circle cx="60" cy="60" r="48" fill="url(#g)" stroke="#b86d66" stroke-width="2"/><text x="60" y="70" font-family="Arial,Helvetica,sans-serif" font-size="30" font-weight="700" text-anchor="middle" fill="#a85d57">SB</text>
<circle cx="180" cy="60" r="48" fill="url(#g)" stroke="#b86d66" stroke-width="2"/><text x="180" y="70" font-family="Arial,Helvetica,sans-serif" font-size="30" font-weight="700" text-anchor="middle" fill="#a85d57">20</text></svg>"""

DOCS = [  # key, kind, lang, content, type coding, code system for sections, title
    ("smpc-en", "smpc", "en", C.SMPC, (SPOR, "100000155532", "Summary of Product Characteristics"), SPOR,
     "Sakura Bloom 20 mg film-coated tablets - Summary of Product Characteristics"),
    ("pil-en", "pil", "en", C.PIL["en"], (SPOR, "100000155538", "Package Leaflet"), PILCS,
     "Sakura Bloom 20 mg film-coated tablets - Package leaflet"),
    ("ifu-en", "ifu", "en", C.IFU, (f"{EPI}/CodeSystem/epi-document-type-example", "instructions-for-use", "Instructions for use"), IFUCS,
     "Sakura Bloom 20 mg film-coated tablets - Instructions for use"),
]


def resolve_check(bundle):
    have = {f"{e['resource']['resourceType']}/{e['resource']['id']}" for e in bundle["entry"]}
    bad = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "reference" and isinstance(v, str) and not v.startswith("#") and v not in have:
                    bad.append(f"{path}: {v}")
                walk(v, path)
        elif isinstance(o, list):
            for v in o:
                walk(v, path)
    for e in bundle["entry"]:
        r = e["resource"]
        walk(r, f"{r['resourceType']}/{r['id']}")
        if r["resourceType"] == "Composition":
            for x in json.dumps(r).split('"valueUri": "')[1:]:
                ref = x.split('"')[0]
                if ref not in have:
                    bad.append(f"textLink: {ref}")
    if bad:
        raise SystemExit(f"Unresolved references in {bundle['id']}:\n  " + "\n  ".join(sorted(set(bad))))


def build():
    PR = product_resources()
    CR = clinical_resources()
    items = ues(CR)
    minimal_mpd = mark({"resourceType": "MedicinalProductDefinition", "id": "sakura-bloom-20mg",
                        "identifier": PR["MedicinalProductDefinition/sakura-bloom-20mg"]["identifier"],
                        "name": [{"productName": "Sakura Bloom 20 mg film-coated tablets"}]})
    minimal_org = copy.deepcopy(PR["Organization/sakura-pharma-eu"])
    minimal_org.pop("partOf", None)
    binary = {"resourceType": "Binary", "id": "tablet-image", "meta": {"profile": [f"{EPI}/StructureDefinition/binary-epi"]},
              "contentType": "image/svg+xml", "data": base64.b64encode(TABLET_SVG.encode()).decode()}

    out_docs, files = [], []
    (OUT / "fhir").mkdir(parents=True, exist_ok=True)
    (OUT / "data").mkdir(parents=True, exist_ok=True)
    for t in (1, 2, 3, 4):
        if t == 1:
            res = {"MedicinalProductDefinition/sakura-bloom-20mg": minimal_mpd, "Organization/sakura-pharma-eu": minimal_org}
        elif t == 2:
            res = dict(PR)
        else:
            res = {**PR, **CR}
        for key, kind, lang, node, typ, codesys, title in DOCS:
            gen = {"[[UE_TABLE]]": ue_table(items), "[[PIL_SE]]": pil_se(items, lang)}
            gen.update({f"[[PICTO:{n}]]": f'<p><img src="#picto-{n}" alt="Step {n} pictogram"/></p>' for n in C.PICTOS})
            state = {"n": 0, "all": set(), "entries": [], "links": []}
            root = build_section(node, t, codesys, state, gen, {"smpc": "s-", "pil": "p-", "ifu": "i-"}[kind])
            contained = [binary] + ([{"resourceType": "Binary", "id": f"picto-{n}", "meta": {"profile": [f"{EPI}/StructureDefinition/binary-epi"]},
                                      "contentType": "image/svg+xml", "data": base64.b64encode(svg.encode()).decode()} for n, svg in C.PICTOS.items()] if kind == "ifu" else [])
            name = f"epi-t{t}-{key}"
            comp = {"resourceType": "Composition", "id": f"comp-{key}-t{t}",
                    "meta": {"profile": [f"{EPI}/StructureDefinition/Composition-uv-epi"], "security": [HTEST]},
                    "contained": contained,
                    "text": {"status": "generated", "div": f'<div xmlns="{XHTML}"><p>{title}. ePI Type {t} ({TYPE_NAMES[t]}). Synthetic example.</p></div>'},
                    "identifier": [{"system": "urn:ietf:rfc:3986", "value": uid(name + "/composition")}],
                    "version": "1", "status": "final", "type": cc(*typ), "language": lang,
                    "subject": [{"reference": "MedicinalProductDefinition/sakura-bloom-20mg"}],
                    "date": DATE, "author": [{"reference": "Organization/sakura-pharma-eu"}], "title": title,
                    "section": [root]}
            entries = [{"fullUrl": f"{BASE}/Composition/{comp['id']}", "resource": comp}]
            for k in sorted(res):
                r = res[k]
                entries.append({"fullUrl": f"{BASE}/{r['resourceType']}/{r['id']}", "resource": r})
            prof = [f"{EPI}/StructureDefinition/Bundle-uv-epi"] + ([f"{EPI}/StructureDefinition/bundle-epi-type3"] if t >= 3 else [])
            bundle = {"resourceType": "Bundle", "id": name,
                      "meta": {"profile": prof, "security": [HTEST],
                               "tag": [{"system": TYPECS, "code": f"type-{t}", "display": f"ePI Type {t}: {TYPE_NAMES[t]}"}]},
                      "identifier": {"system": "urn:ietf:rfc:3986", "value": uid(name)},
                      "type": "document", "timestamp": TS, "entry": entries}
            resolve_check(bundle)
            fn = f"Bundle-{name}.json"
            (OUT / "fhir" / fn).write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            files.append(fn)
            out_docs.append({"type": t, "key": key, "kind": kind, "lang": lang, "file": f"fhir/{fn}", "bundle": bundle})
            print(f"  {fn}: {len(entries)} entries, {sum(1 for _ in re.finditer(TEXTLINK, json.dumps(comp)))} textLinks")

    data = {"generated": TS, "docs": out_docs, "freq": C.FREQ, "soc": C.SOC_ORDER,
            "candidate": ue_resource(UE_CANDIDATE)}
    js = "/* Generated by showcases/epi-types/build/build_epi_types.py. Do not edit by hand. Synthetic data. */\nwindow.EPIDATA = " + \
         json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (OUT / "data" / "epi-data.js").write_text(js, encoding="utf-8")
    print(f"  data/epi-data.js: {len(js) / 1024:.0f} KB")


if __name__ == "__main__":
    build()
