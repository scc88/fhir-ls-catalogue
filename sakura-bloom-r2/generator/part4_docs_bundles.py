"""Module 2.3 / 3.2 Compositions, PQI domain bundles, dossier and transaction bundles."""
import os
from lib import *
from part2_specs import ap_for

TS = "2026-11-08T00:00:00Z"


def section_entries(short):
    """Map a Notion page (path) to structured resources it is represented by."""
    t = short.split(" / ")[-1].strip()
    e = []
    has = lambda *ks: all(k in short for k in ks)
    if t.startswith("2.3.1"):
        e += ["MedicinalProductDefinition/sakura-bloom-20mg", "ManufacturedItemDefinition/sakura-bloom-20mg-tablet", "PackagedProductDefinition/pack-hdpe-bottle", "PackagedProductDefinition/pack-pa-al-pvc-blister"]
    if t.startswith("2.3.2"):
        e += ["PlanDefinition/spec-dp", "PlanDefinition/spec-ds-sakuramil", "PlanDefinition/dp-manufacturing-process", "PlanDefinition/ds-manufacturing-process"] + \
             [k for k in R if k.startswith("ObservationDefinition/cpp-")]
    if "DS.D Description" in t:
        e += ["SubstanceDefinition/sakuramil"]
    if "DS.M Manufactur" in t:
        e += ["PlanDefinition/ds-manufacturing-process", "DocumentReference/doc-ds-synthetic-scheme", "DocumentReference/doc-ds-block-flow-diagram"]
    if "DS.C Control" in t and t.startswith("2.3"):
        e += ["PlanDefinition/spec-ds-sakuramil", "SubstanceDefinition/cp-9-1", "SubstanceDefinition/cp-8", "SubstanceDefinition/cp-6"]
    if t.startswith("3.2.DS.C Control"):
        e += [k for k in R if k.startswith("DiagnosticReport/dr-ba-ds-")]
    if "Elemental risk" in t:
        e += [k for k in R if k.startswith("DiagnosticReport/dr-elemental-")] + ["PlanDefinition/study-elemental-impurities"]
    if "Residual solvents carry over" in t:
        e += [k for k in R if k.startswith("DiagnosticReport/dr-carryover-")]
    if "ICH M7" in t:
        e += ["DocumentReference/doc-ich-m7-risk-assessment", "SubstanceDefinition/cp-6", "SubstanceDefinition/cp-4"]
    if "Nitrosamine" in t:
        e += ["DocumentReference/doc-nitrosamine-risk-assessment"]
    if "DS.S Storage" in t:
        e += ["PlanDefinition/spec-cc-ds-ldpe-bag", "PlanDefinition/stability-protocol-ds-post-approval"]
        if t.startswith("3.2"):
            e += ["PlanDefinition/stability-protocol-ds-registration"] + [k for k in R if k.startswith("DiagnosticReport/dr-st-ds-")]
    for frag, sid in [("[CP-4]", "cp-4"), ("[CP-8]", "cp-8"), ("(CP-6)", "cp-6"), ("(CP-7)", "cp-7")]:
        if frag in t and (".SM." in t or ".SI." in t or "SM.D" in t or "SI.D" in t or "SM Manufacture" in t):
            e += [f"SubstanceDefinition/{sid}"]
            if ".C " in t or ".C Control" in t or "Control" in t:
                pid = f"PlanDefinition/spec-{'sm' if sid in ('cp-4', 'cp-8') else 'si'}-{sid}"
                if pid in R:
                    e.append(pid)
    m = re.search(r"RM\.C\.? Control \[(.*?)\]", t)
    if m:
        sid = "rm-" + slug(m.group(1).replace("Catalyst ", "").replace(" (Dichloromethane, DCM)", ""))
        e += [f"SubstanceDefinition/{sid}", f"PlanDefinition/spec-{sid}"]
    if "EX Compendial excipients" in t:
        e += [k for k in R if k.startswith("PlanDefinition/spec-ex-") and "premix" not in k]
    if "Non-compendial" in t or "Coating Premix Red KIRSCH" in t:
        e += ["SubstanceDefinition/coating-premix-red", "PlanDefinition/spec-ex-coating-premix-red"]
    if " RS" in t or "RS.C" in t or ".RS." in t:
        e += [k for k in R if k.startswith("Substance/rs-")]
        if "CP-9 working" in t or "Primary working" in t:
            e += ["DiagnosticReport/dr-char-cp-9-primary-working-standard"]
        if "identification standard" in t:
            e += ["PlanDefinition/spec-rs-cp-9-identification-standard", "DiagnosticReport/dr-char-cp-9-identification-standard"]
        if "CP-6 standard" in t:
            e += ["DiagnosticReport/dr-char-cp-6-standard"]
    if "DP.D Description" in t:
        e += ["MedicinalProductDefinition/sakura-bloom-20mg", "ManufacturedItemDefinition/sakura-bloom-20mg-tablet"] + [k for k in R if k.startswith("Ingredient/")]
    if "DP.M Manufacture" in t:
        e += ["PlanDefinition/dp-manufacturing-process", "Medication/dp-batch-formula-commercial", "DocumentReference/doc-dp-process-flow-diagram"] + [k for k in R if k.startswith("DeviceDefinition/eq-") and "ds-" not in k]
    if "DP.C Control" in t and t.startswith("2.3"):
        e += ["PlanDefinition/spec-dp"]
    if "3.2.DP.C.1 Batch Analysis" in t:
        e += [k for k in R if k.startswith("DiagnosticReport/dr-ba-dp-")] + [k for k in R if k.startswith("Medication/dp-") and k.count("-") == 1]
    if "DP.S" in t and "Bottle" in t:
        e += ["PackagedProductDefinition/pack-hdpe-bottle", "PlanDefinition/spec-cc-hdpe-bottle", "PlanDefinition/stability-protocol-dp-post-approval", "PlanDefinition/stability-protocol-dp-commitment"]
    if "DP.S" in t and "Blister" in t:
        e += ["PackagedProductDefinition/pack-pa-al-pvc-blister", "PlanDefinition/spec-cc-blister-foils", "PlanDefinition/stability-protocol-dp-post-approval", "PlanDefinition/stability-protocol-dp-commitment"]
    if "DP.S" in t and "Bulk" in t:
        e += ["PackagedProductDefinition/pack-bulk-alu-bag", "PlanDefinition/spec-cc-bulk-bag"]
    if "Registration stability report" in t:
        pk = "bottle" if "Bottle" in short else "blister"
        e += ["PlanDefinition/stability-protocol-dp-registration"] + [k for k in R if k.startswith("DiagnosticReport/dr-st-dp-") and f"-{pk}-" in k]
    if "FA Facilities" in t:
        e += [k for k in R if k.startswith("Organization/")]
    if "Analytical Procedures" in t and "(" in t:
        apid = ap_for(t.replace("3.2.AP", "2.3.3.AP").replace("Assay/ID SM1", "Assay SM1").replace("Assay/ID SM2", "Assay SM2").replace("Assay/ID IM1", "Assay IM1").replace("Deg. by HPLC", "Deg."))
        if apid:
            e.append(f"PlanDefinition/{apid}")
    if "PLCM" in t or "Post-approval Quality Commitments" in t:
        e += ["PlanDefinition/stability-protocol-dp-commitment", "PlanDefinition/stability-protocol-ds-post-approval"]
    return [x for x in dict.fromkeys(e) if x in R]


def composition(cid, module_prefix, title, S):
    pages = [p for p in S.pages if p["short"].startswith(module_prefix)]
    root = {"children": OrderedDict(), "page": None}
    for p in sorted(pages, key=lambda p: p["short"].count(" / ")):
        parts = p["short"].split(" / ")
        node = root
        for part in parts[1:]:
            node = node["children"].setdefault(part, {"children": OrderedDict(), "page": None})
        node["page"] = p
    top = [p for p in pages if p["short"] == module_prefix]

    def natkey(k):
        return [(0, int(x), "") if x.isdigit() else (1, 0, x) for x in re.split(r"(\d+)", k)]

    def mk(name, node):
        sec = OrderedDict()
        sec["title"] = name.strip()
        p = node["page"]
        if p:
            sec["code"] = cc(name.strip().split(" ")[0])
            sec["text"] = md_to_xhtml(p["text"])
            ent = section_entries(p["short"])
            if ent:
                sec["entry"] = [{"reference": k} for k in ent]
        kids = [mk(k, v) for k, v in sorted(node["children"].items(), key=lambda kv: natkey(kv[0]))]
        if kids:
            sec["section"] = kids
        if "text" not in sec and "entry" not in sec and not kids:
            sec["text"] = md_to_xhtml("(section not populated in source)")
        return sec

    sections = [mk(k, v) for k, v in sorted(root["children"].items(), key=lambda kv: natkey(kv[0]))]
    body = OrderedDict()
    body["identifier"] = [{"system": BASE + "/document-id", "value": cid}]
    body["status"] = "final"
    body["type"] = cc(title)
    body["category"] = [cc("ICH M4Q(R2) Common Technical Document - Quality")]
    body["subject"] = [ref("MedicinalProductDefinition", "sakura-bloom-20mg")]
    body["date"] = "2025-09-15"
    body["author"] = [ref("Organization", "sakura-pharma")]
    body["title"] = title + " - Sakura Bloom 20 mg film-coated tablets (SakuraBloom R2 mock-up)"
    if top:
        body["text"] = md_to_xhtml(top[0]["text"])
    body["section"] = sections
    add("Composition", cid, body, ["core", "dp"], source=(top[0]["url"] if top else None))


BUNDLES = [  # group, bundle id, PQI bundle profile, allowed PlanDefinitions (None = all)
    ("organizations", "bundle-organizations", "Bundle-organizations-pq", None),
    ("ds-general-properties", "bundle-ds-general-properties", "Bundle-drug-substance-general-properties-pq", None),
    ("ds-characterization", "bundle-ds-characterization", "Bundle-drug-substance-characterization-pq", ["char-protocol-reference-standards"]),
    ("impurities", "bundle-impurities", "Bundle-product-impurities-pq", None),
    ("ds-manufacturing", "bundle-ds-manufacturing", "Bundle-product-manufacturing-pq", ["ds-manufacturing-process"]),
    ("ds-specification", "bundle-ds-specification", "Bundle-drug-substance-specification-pq", ["spec-ds-sakuramil"]),
    ("materials-specifications", "bundle-materials-specifications", None, None),
    ("ds-batch-info", "bundle-ds-batch-info", "Bundle-drug-substance-batch-info-pq", None),
    ("ds-batch-analysis", "bundle-ds-batch-analysis", "Bundle-batch-analysis-pq", ["spec-ds-sakuramil"]),
    ("ds-stability", "bundle-ds-stability", "Bundle-drug-stability-pq", ["stability-protocol-ds-registration"]),
    ("reference-standards", "bundle-reference-standards", "Bundle-drug-reference-standards-pq", None),
    ("container-closure", "bundle-container-closure", "Bundle-container-closure-system-pq", None),
    ("dp", "bundle-dp", "Bundle-drug-product-pq", None),
    ("dp-composition", "bundle-dp-composition", "Bundle-drug-product-composition-pq", None),
    ("dp-excipients", "bundle-dp-excipients", "Bundle-drug-product-excipients-pq", None),
    ("batch-formula", "bundle-dp-batch-formula", "Bundle-batch-formula-pq", None),
    ("dp-manufacturing", "bundle-dp-manufacturing", "Bundle-product-manufacturing-pq", ["dp-manufacturing-process"]),
    ("dp-specification", "bundle-dp-specification", "Bundle-drug-product-specification-pq", ["spec-dp"]),
    ("dp-batch-info", "bundle-dp-batch-info", "Bundle-drug-product-batch-info-pq", None),
    ("dp-batch-analysis", "bundle-dp-batch-analysis", "Bundle-batch-analysis-pq", ["spec-dp"]),
    ("dp-microbiology", "bundle-dp-microbiology", "Bundle-drug-product-microbiological-attributes-pq", None),
    ("dp-stability", "bundle-dp-stability", "Bundle-drug-stability-pq", ["stability-protocol-dp-registration"]),
]


def build(S, outdir):
    composition("module-2-3-quality-overview", "Module 2.3 Quality Overview", "ICH M4Q(R2) Module 2.3 Quality Overview", S)
    composition("module-3-2-body-of-data", "Module 3.2 Body of Data", "ICH M4Q(R2) Module 3.2 Body of Data", S)
    tag("dp", "MedicinalProductDefinition", "sakura-bloom-20mg")
    tag("dp", "ManufacturedItemDefinition", "sakura-bloom-20mg-tablet")
    tag("dp", "Organization", "aparna-pharm")
    tag("dp", "Organization", "sakura-pharma")
    for k in R:
        if k.startswith("Organization/"):
            tag("organizations", *k.split("/"))
    tag("container-closure", "MedicinalProductDefinition", "sakura-bloom-20mg")
    # fill ObservationDefinitions referenced by protocols/test sets into stability bundles
    for g, ts in (("ds-stability", "ts-ds-stability-full"), ("dp-stability", "ts-dp-stability-full")):
        for c in R[f"ActivityDefinition/{ts}"]["observationRequirement"]:
            tag(g, "ObservationDefinition", c.rsplit("/", 1)[1])
    for g in ("ds-stability",):
        for k in R:
            if k.startswith("ActivityDefinition/ts-ds"):
                tag(g, *k.split("/"))
    for g in ("dp-microbiology",):
        for o in ("od-dp-met-tamc", "od-dp-met-tymc", "od-dp-met-e-coli"):
            tag(g, "ObservationDefinition", o)
    for g in ("ds-batch-info", "dp-batch-info"):
        tag(g, "PlanDefinition", "ds-manufacturing-process" if g.startswith("ds") else "dp-manufacturing-process")

    os.makedirs(f"{outdir}/bundles", exist_ok=True)
    os.makedirs(f"{outdir}/resources", exist_ok=True)
    summary = []
    for g, bid, prof, plans in BUNDLES:
        ents = [(t, i) for t, i in GROUPS.get(g, []) if not (t == "PlanDefinition" and plans is not None and i not in plans)]
        if g == "ds-stability" or g == "dp-stability":
            ents = [(t, i) for t, i in ents if not (t == "ActivityDefinition" and ((g == "ds-stability") != i.startswith("ts-ds")))]
        b = bundle(bid, prof, ents, ts=TS)
        json.dump(b, open(f"{outdir}/bundles/{bid}.json", "w"), ensure_ascii=False, indent=1)
        summary.append((bid, prof or "(none - plain collection)", len(ents)))
    # analytical procedure bundles (Protocol 1..1 => one per procedure)
    ap_ods = {}
    for k, r in R.items():
        if k.startswith("PlanDefinition/"):
            def walk(acts):
                for a in acts or []:
                    for d in a.get("documentation", []):
                        apid = d["resource"].rsplit("/", 1)[1]
                        if a.get("definitionCanonical"):
                            ap_ods.setdefault(apid, set()).add(a["definitionCanonical"].rsplit("/", 1)[1])
                    walk(a.get("action"))
            walk(r.get("action"))
    os.makedirs(f"{outdir}/bundles/analytical-procedures", exist_ok=True)
    for k, r in R.items():
        if k.startswith("PlanDefinition/ap-"):
            apid = r["id"]
            subj = r["subjectReference"]["reference"].split("/")
            ents = []
            if subj[0] == "MedicinalProductDefinition":
                ents.append(tuple(subj))
                ents.append(("SubstanceDefinition", "sakuramil"))
                ents.append(("SpecimenDefinition", "spd-test-sample-dp"))
            else:
                ents.append(tuple(subj))
                ents.append(("SpecimenDefinition", "spd-test-sample-ds"))
            ents.append(("PlanDefinition", apid))
            ents += [("ObservationDefinition", o) for o in sorted(ap_ods.get(apid, []))]
            for e in r.get("extension", []):
                if "valueReference" in e:
                    ents.append(tuple(e["valueReference"]["reference"].split("/")))
            b = bundle(f"bundle-{apid}", "Bundle-analytical-procedure-pq", ents, ts=TS)
            json.dump(b, open(f"{outdir}/bundles/analytical-procedures/bundle-{apid}.json", "w"), ensure_ascii=False, indent=1)
            summary.append((f"analytical-procedures/bundle-{apid}", "Bundle-analytical-procedure-pq", len(ents)))
    # dossier (all) collection + transaction
    allents = [tuple(k.split("/")) for k in R]
    os.makedirs(f"{outdir}/dossier", exist_ok=True)
    json.dump(bundle("sakura-bloom-r2-dossier", None, allents, ts=TS), open(f"{outdir}/dossier/sakura-bloom-r2-dossier-collection.json", "w"), ensure_ascii=False)
    json.dump(bundle("sakura-bloom-r2-transaction", None, allents, btype="transaction", ts=TS), open(f"{outdir}/dossier/sakura-bloom-r2-transaction.json", "w"), ensure_ascii=False)
    # document bundles (Composition first)
    for cid in ("module-2-3-quality-overview", "module-3-2-body-of-data"):
        refs = set()

        def collect(x):
            if isinstance(x, dict):
                if "reference" in x and isinstance(x["reference"], str) and "/" in x["reference"]:
                    refs.add(x["reference"])
                for v in x.values():
                    collect(v)
            elif isinstance(x, list):
                for v in x:
                    collect(v)
        frontier = [f"Composition/{cid}"]
        while frontier:
            k = frontier.pop()
            before = set(refs)
            collect(R[k])
            for nk in refs - before:
                if nk in R:
                    frontier.append(nk)
        ents = [("Composition", cid)] + [tuple(k.split("/")) for k in R if k in refs and k != f"Composition/{cid}"]
        json.dump(bundle(f"{cid}-document", None, ents, btype="document", ts=TS), open(f"{outdir}/dossier/{cid}-document.json", "w"), ensure_ascii=False)
    for k, r in R.items():
        t, i = k.split("/")
        json.dump(r, open(f"{outdir}/resources/{t}-{i}.json", "w"), ensure_ascii=False, indent=1)
    return summary
