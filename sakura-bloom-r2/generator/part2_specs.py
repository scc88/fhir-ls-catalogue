"""Specifications (ObservationDefinition + PlanDefinition) and analytical procedures."""
from lib import *

LOCAL_CODES = {"Assay": "ASSAY", "Description": "DESC", "Identification": "IDT", "Dissolution": "Dissolution",
               "Degradation Products": "DGP", "Drug Substance Related Organic impurities": "DGP-s", "Residual solvents": "SOL",
               "Elemental impurities": "ELE", "Mutagenic impurities": "MUT", "Enantiomeric purity": "enantiomeric-purity",
               "Particle size distribution": "particle-size-distribution", "TAMC": "TAMC", "Appearance": "Appearance",
               "Water content": "WaterContent", "Microbiological Quality": "Microbiological Quality", "Impurity": "IMP", "NMR-H": "NMR-H", "NMR-C": "NMR-C"}

CAT_ALIAS = {"Related substances": "DGP-s", "Potentially mutagenic impurities": "MUT"}

AP_KEYS = [  # (fragment in 2.3.3 AP page title, ap id, subject (type,id))
    ("(Assay/ID) [Assay/Identification][Sakuramil]", "ap-ds-assay-id", ("SubstanceDefinition", "sakuramil")),
    ("(Related Substances)[Purity][Sakuramil]", "ap-ds-related-substances", ("SubstanceDefinition", "sakuramil")),
    ("(Potentially mutagentic Impurities)", "ap-ds-mutagenic-impurities", ("SubstanceDefinition", "sakuramil")),
    ("(Particle size distribution)[Particle size][Sakuramil]", "ap-ds-particle-size", ("SubstanceDefinition", "sakuramil")),
    ("(Residual Solvents) [Residual Solvents][Sakuramil][CP-4]", "ap-residual-solvents", ("SubstanceDefinition", "sakuramil")),
    ("(Assay SM1) [Assay][CP-4]", "ap-cp-4-assay", ("SubstanceDefinition", "cp-4")),
    ("(Related Substances SM1)[Purity][CP-4]", "ap-cp-4-related-substances", ("SubstanceDefinition", "cp-4")),
    ("(Enantiomeric purity SM1)[Purity][CP-4]", "ap-cp-4-enantiomeric-purity", ("SubstanceDefinition", "cp-4")),
    ("(Assay SM2) [Assay][CP-8]", "ap-cp-8-assay", ("SubstanceDefinition", "cp-8")),
    ("(Related Substances SM2)[Purity][CP-8]", "ap-cp-8-related-substances", ("SubstanceDefinition", "cp-8")),
    ("(Assay IM1) [Assay][CP-6]", "ap-cp-6-assay", ("SubstanceDefinition", "cp-6")),
    ("(Related Substances IM1)[Purity][CP-6]", "ap-cp-6-related-substances", ("SubstanceDefinition", "cp-6")),
    ("(Related Substances IM2)[Purity][CP-7]", "ap-cp-7-related-substances", ("SubstanceDefinition", "cp-7")),
    ("(Description)[Appearance][Sakura Bloom 20 mg]", "ap-dp-description", ("MedicinalProductDefinition", "sakura-bloom-20mg")),
    ("(Identity/NIR)", "ap-dp-identity-nir", ("MedicinalProductDefinition", "sakura-bloom-20mg")),
    ("(Identity/HPLC)", "ap-dp-identity-hplc", ("MedicinalProductDefinition", "sakura-bloom-20mg")),
    ("(Identity/UV)", "ap-dp-identity-uv", ("MedicinalProductDefinition", "sakura-bloom-20mg")),
    ("(Uniformity of dosage units/NIR)", "ap-dp-udu-nir", ("MedicinalProductDefinition", "sakura-bloom-20mg")),
    ("(Uniformity of dosage units/HPLC)", "ap-dp-udu-hplc", ("MedicinalProductDefinition", "sakura-bloom-20mg")),
    ("(Dissolution/RTRT)", "ap-dp-dissolution-rtrt", ("MedicinalProductDefinition", "sakura-bloom-20mg")),
    ("(Dissolution/UV)", "ap-dp-dissolution-uv", ("MedicinalProductDefinition", "sakura-bloom-20mg")),
    ("(Assay/NIR)", "ap-dp-assay-nir", ("MedicinalProductDefinition", "sakura-bloom-20mg")),
    ("(Assay/Deg.)", "ap-dp-assay-degradation", ("MedicinalProductDefinition", "sakura-bloom-20mg")),
    ("(MET)[Purity]", "ap-dp-microbial-enumeration", ("MedicinalProductDefinition", "sakura-bloom-20mg")),
    ("(Visual examination) [Appearance][Basic Coating Premix Red]", "ap-premix-visual", ("SubstanceDefinition", "coating-premix-red")),
    ("(Identity by IR (ATR)) [Identification] [Basic Coating Premix Red]", "ap-premix-identity-ir", ("SubstanceDefinition", "coating-premix-red")),
    ("(Identity of colorants)", "ap-premix-identity-colorants", ("SubstanceDefinition", "coating-premix-red")),
    ("(Identity of iron)", "ap-premix-identity-iron", ("SubstanceDefinition", "coating-premix-red")),
]
AP_TITLES = {}


def ap_for(text):
    """Resolve an analytical-procedure link text to an AP PlanDefinition id."""
    if not text:
        return None
    t = text.replace("Potentially mutagenic Impurities)", "Potentially mutagentic Impurities)")
    for frag, apid, _ in AP_KEYS:
        if frag in t:
            return apid
    for frag, apid, _ in AP_KEYS:  # alternative wording
        alt = frag.replace("Assay SM1", "Assay/ID SM1").replace("Assay SM2", "Assay/ID SM2").replace("Assay IM1", "Assay/ID IM1")
        if alt in t:
            return apid
    return None


def make_od(oid, t, source=None, groups=()):
    name, cat = t["name"], t.get("cat") or t["name"]
    code_key = t.get("code") or LOCAL_CODES.get(cat) or CAT_ALIAS.get(cat)
    txt = f"{cat} - {name}" if cat != name else name
    code = cc(txt, CS_LOCAL, code_key, {v: k for k, v in LOCAL_CODES.items()}[code_key]) if code_key else cc(txt)
    crits = t.get("crits") or [(t.get("ctx"), t["crit"])]
    qvs, numeric = [], False
    for ctx, crit in crits:
        qv = OrderedDict()
        qv["extension"] = [qv_text(crit)]
        if t.get("critical"):
            qv["extension"].append(ext(SD + "Extension-qualified-value-criticality-pq", valueCodeableConcept=cc("Critical", CS_CRIT, "critical", "Critical")))
        if t.get("target") is not None:
            qv["extension"].append(ext(SD + "Extension-qualified-value-target-pq", valueQuantity=t["target"]))
        if ctx:
            qv["context"] = cc(ctx)
        rng = t.get("range") if t.get("range") is not None else parse_criterion(crit)
        if rng:
            qv["range"] = rng
            numeric = True
        qvs.append(qv)
    body = {"title": name, "status": "active", "category": [cc(cat)], "code": code,
            "permittedDataType": ["Quantity"] if numeric else ["string"]}
    if t.get("method"):
        body["method"] = cc(t["method"])
    if t.get("unit"):
        u = q(0, t["unit"])
        body["permittedUnit"] = [{k: u[k] for k in ("system", "code", "display") if k in u}] if "system" in u else []
        if body["permittedUnit"]:
            body["permittedUnit"][0]["display"] = u.get("unit")
        else:
            del body["permittedUnit"]
    if t.get("desc"):
        body["description"] = t["desc"]
    body["qualifiedValue"] = qvs
    return add("ObservationDefinition", oid, body, groups, source=source)


def make_spec(pid, title, subject, tests, groups, source=None, desc=None, ptype=("1244577", "Specification Protocol"), default_group="Release and re-test"):
    od_ids = []
    for t in tests:
        oid = t.get("id") or slug(f"od-{pid[5:]}-{t['name']}", 64)
        make_od(oid, t, source, groups)
        t["_id"] = oid
        od_ids.append(oid)
    ctxs = []
    for t in tests:
        for c, _ in (t.get("crits") or [(t.get("ctx") or default_group, None)]):
            c = c or default_group
            if c not in ctxs:
                ctxs.append(c)
    actions = []
    for c in ctxs:
        sub = []
        for t in tests:
            tc = [x or default_group for x, _ in (t.get("crits") or [(t.get("ctx"), None)])]
            if c in tc:
                a = OrderedDict([("title", t["name"]), ("code", [cc("Test")]), ("definitionCanonical", canon("ObservationDefinition", t["_id"]))])
                if t.get("ap"):
                    a["documentation"] = [{"type": "depends-on", "label": "Analytical procedure", "resource": canon("PlanDefinition", t["ap"])}]
                elif t.get("method"):
                    a["description"] = "Method: " + t["method"]
                sub.append(a)
        actions.append({"title": c, "code": [cc("Timing Group")], "action": sub})
    body = {"title": title, "type": cc(ptype[1], CS_PLAN, ptype[0], ptype[1]), "status": "active",
            "subjectReference": ref(*subject)}
    if desc:
        body["description"] = desc
    body["action"] = actions
    add("PlanDefinition", pid, body, groups, source=source)
    return od_ids


def parse_spec_table(rows, pcol=0, ccol=1, mcol=2, skip_header=True):
    tests, cat, last = [], None, None
    for r in rows[1 if skip_header else 0:]:
        r = r + [""] * (3 - len(r))
        p, c, m = r[pcol].strip(), r[ccol].strip(), (r[mcol].strip() if mcol is not None and mcol < len(r) else "")
        if p and not c and not m:
            cat = p
            continue
        if not p and c and last:
            tests.append({"name": f"{last['name0']} {c.split(' - ')[0]}", "cat": last["cat"], "crit": c, "method": last["method"], "ap": last["ap"], "name0": last["name0"]})
            continue
        method_txt = re.sub(r"\[\[.*?\]\]|🧪.*", "", m).strip()
        t = {"name": p, "name0": p, "cat": cat or p, "crit": c or "See analytical procedure", "method": method_txt or None, "ap": ap_for(m)}
        tests.append(t)
        last = t
    return [t for t in tests if not (t["crit"] == "See analytical procedure" and any(x["name0"] == t["name"] and x is not t for x in tests))]


def build(S):
    # ------------------------------------------------------------ analytical procedures
    specdef_dp = add("SpecimenDefinition", "spd-test-sample-dp", {"status": "active", "title": "Drug product test sample",
        "typeCollected": cc("Sakura Bloom 20 mg film-coated tablets (or uncoated tablet cores for RTRT)"),
        "typeTested": [{"preference": "preferred", "type": cc("Film-coated tablets"), "isDerived": False}]}, ["analytical-procedures"])
    specdef_ds = add("SpecimenDefinition", "spd-test-sample-ds", {"status": "active", "title": "Drug substance / material test sample",
        "typeCollected": cc("Drug substance, starting material, intermediate or excipient sample"),
        "typeTested": [{"preference": "preferred", "type": cc("Powder / crystalline solid"), "isDerived": False}]}, ["analytical-procedures"])
    ap_pages = [p for p in S.pages if re.search(r"/ 2\.3\.3\. ?AP Analytical Procedures ", p["short"]) or re.search(r"/ 2\.3\.3\.AP Analytical Procedures +\(", p["short"])]
    for p in ap_pages:
        title = p["short"].split(" / ")[-1].strip()
        apid = ap_for(title)
        if not apid:
            if not title.startswith("("):
                ISSUES.append("Unmapped AP page: " + title)
            continue
        subj = [s for f, a, s in AP_KEYS if a == apid][0]
        AP_TITLES[apid] = title.replace("2.3.3. AP ", "").replace("2.3.3.AP ", "")
        actions = []
        for cap, rows in Source.tables(p["text"]):
            two = all(len(r) == 2 for r in rows)
            if two:
                for a, b in rows:
                    if a in ("Method Attribute",) and b == "Conditions":
                        continue
                    if not a and not b:
                        continue
                    actions.append({"title": a or "(continued)", "description": b or "-"})
            else:
                hdr = rows[0]
                actions.append({"title": cap or "Table", "description": "; ".join(" | ".join(r) for r in rows)})
        # 3.2 detailed procedure + 2.3.4 justification as DocumentReferences
        frag = title.split("Procedures", 1)[1].strip()
        docs = []
        for prefix, label in (("3.2.AP", "Detailed analytical procedure (Module 3.2)"), ("2.3.4", "Analytical procedure development / validation summary (2.3.4 DSJ)")):
            cand = [x for x in S.pages if x["short"].split(" / ")[-1].strip().startswith(prefix) and frag.replace("mutagentic", "mutagenic")[:25] in x["short"].split(" / ")[-1]]
            if cand:
                did = slug(f"doc-{apid[3:]}-{prefix}", 64)
                if f"DocumentReference/{did}" not in R:
                    add("DocumentReference", did, {"status": "current", "type": cc(label),
                        "description": cand[0]["short"].split(" / ")[-1].strip(),
                        "content": [{"attachment": {"contentType": "text/html", "url": cand[0]["url"], "title": cand[0]["short"].split(" / ")[-1].strip()}}]},
                        ["analytical-procedures"], source=cand[0]["url"])
                docs.append(did)
        body = {"extension": [ext(SD + "Extension-plan-document-reference-pq", valueReference=ref("DocumentReference", d)) for d in docs],
                "title": AP_TITLES[apid], "type": cc("Analytical Procedure", CS_PLAN, "analytical-procedure", "Analytical Procedure"),
                "status": "active", "subjectReference": ref(*subj),
                "description": f"Core quality information (2.3.3.AP) for {AP_TITLES[apid]}.",
                "action": actions or [{"title": "See detailed procedure"}]}
        if not body["extension"]:
            del body["extension"]
        add("PlanDefinition", apid, body, ["analytical-procedures"], source=p["url"])
    missing = [a for _, a, _ in AP_KEYS if f"PlanDefinition/{a}" not in R]
    for a in missing:
        ISSUES.append("No 2.3.3 AP page found for " + a)

    # ------------------------------------------------------------ DS specification
    dsc = S.page("2.3.3.DS.C Control")
    rows = Source.tables(dsc["text"])[0][1]
    tests = [t for t in parse_spec_table(rows) if t["name"] != "Particle size distribution"]
    for t in tests:
        if t["name"].startswith("Particle size distribution d("):
            t["unit"] = "nm"
            t["_norange"] = True
            t["desc"] = "The specification lists a nominal value without a stated tolerance."
            ISSUES.append(f"DS specification '{t['name']}' gives a nominal value ('{t['crit']}') without tolerance; stored as text criterion only (no Range).")
        if t["cat"] in ("Related substances", "Assay") or t["name"] in ("Loss on drying", "Residue on ignition"):
            t["unit"] = "%"
        if t["cat"] in ("Potentially mutagenic impurities", "Residual solvents"):
            t["unit"] = "ppm"
        if t["name"] in ("Loss on drying", "Residue on ignition"):
            t["cat"] = t["name"]
        if t["name"] == "Sakuramil" and t["cat"] == "Assay":
            t["name"] = "Assay (Sakuramil, dried basis)"
        if "Sakuramil (IR)" in t["name"]:
            t["method"] = "IR USP <197A>"
    DS_TESTS = tests
    make_spec("spec-ds-sakuramil", "Drug substance release / re-test specification - Sakuramil (IROHA-corp.)", ("SubstanceDefinition", "sakuramil"),
              DS_TESTS, ["ds-specification", "ds-batch-analysis", "ds-stability", "core"], dsc["url"],
              desc="Table 1-1 Drug substance release/re-test specification of Sakuramil (2.3.3.DS.C). Re-test period 36 months, storage 15-30 °C.")
    for t in DS_TESTS:
        if t.get("_norange"):
            for qv in R["ObservationDefinition/" + t["_id"]]["qualifiedValue"]:
                qv.pop("range", None)
    tag("ds-specification", "SubstanceDefinition", "sakuramil")
    tag("ds-specification", "Organization", "iroha-corp")

    # ------------------------------------------------------------ DP specification (release and shelf-life)
    dpc = S.page("2.3.3.DP.C Control")
    P = "spec-dp"
    rel, sl = "Batch release", "Shelf-life"
    dp_tests = [
        dict(id="od-dp-description", name="Description (visual inspection)", cat="Description", method="Visual inspection", ap="ap-dp-description",
             crits=[(rel, "Pale red colored, round, biconvex film-coated tablet, debossed with ‘SB’ on one side and ‘20’ on the other side")]),
        dict(id="od-dp-identification-nir", name="Identification (NIR, RTRT, PLSR model)", cat="Identification", method="Near infrared absorption spectrometry (NIR method) (RTRT) (Model: PLSR)", ap="ap-dp-identity-nir",
             crits=[(rel, "Identified as Sakura Bloom 20 mg Film-coated tablet / Corresponds to reference")], desc="Performed at release only (RTRT)."),
        dict(id="od-dp-identification-hplc", name="Identification (HPLC)", cat="Identification", method="HPLC method", ap="ap-dp-identity-hplc",
             crits=[(rel, "The retention time of the main peak from the sample solution coincides with that of the standard solution."), (sl, "Identified as Sakura Bloom 20 mg Film-coated tablet / Corresponds to reference")]),
        dict(id="od-dp-identification-uv", name="Identification (UV-Vis)", cat="Identification", method="Ultraviolet-visible spectrophotometry", ap="ap-dp-identity-uv",
             crits=[(rel, "The shape of the ultraviolet absorption spectrum from the sample solution coincides with that of the standard solution / Corresponds to reference"),
                    (sl, "The shape of the ultraviolet absorption spectrum from the sample solution coincides with that of the standard solution / Corresponds to reference")]),
        dict(id="od-dp-udu-nir", name="Uniformity of dosage units (NIR, RTRT)", cat="Uniformity of dosage units", method="Near infrared absorption spectrometry (NIR method) (RTRT)", ap="ap-dp-udu-nir",
             crits=[(rel, "When 200 uncoated tablets, sampled to represent the whole batch during the tableting process, are tested for Assay, the number of tablets exceeding 85.0%-115.0% is 6 or less and exceeding 75.0%-125% is 1 or less.")], range=None, desc="Performed at release only (RTRT)."),
        dict(id="od-dp-udu-hplc", name="Uniformity of dosage units (content uniformity, HPLC)", cat="Uniformity of dosage units", method="Content Uniformity HPLC method", ap="ap-dp-udu-hplc",
             crits=[(rel, "It meets the criteria of the Content Uniformity Test of the Ph. Eur., USP and JP.")]),
        dict(id="od-dp-dissolution-rtrt", name="Dissolution (RTRT dissolution model)", cat="Dissolution", unit="%", ap="ap-dp-dissolution-rtrt",
             method="Calculation by the dissolution model; inputs: DS particle size (laser diffraction), granule particle size (FBRM), uncoated tablet hardness (RTRT)",
             crits=[(rel, "The dissolution rate calculated by the dissolution model at the time point of 30 minutes is 80% or higher.")], range={"low": q(80, "%")}),
        dict(id="od-dp-dissolution-uv", name="Dissolution (paddle, UV, Q in 30 min)", cat="Dissolution", unit="%", ap="ap-dp-dissolution-uv", method="Dissolution test (paddle method), UV-Vis spectrophotometry",
             crits=[(rel, "Not Less Than 80% (Q in 30 minutes) of the declared content according to acceptance table 1 of harmonized Ph. Eur., USP and JP"),
                    (sl, "Not Less Than 80% (Q in 30 minutes) of the declared content according to acceptance table 1 of harmonized Ph. Eur., USP and JP")]),
        dict(id="od-dp-assay-nir", name="Assay (NIR, RTRT)", cat="Assay", unit="%", ap="ap-dp-assay-nir", method="Near infrared absorption spectrometry (NIR method) (RTRT)",
             crits=[(rel, "The results of the uniformity of dosage units test (RTRT) show a mean of 95.0% to 105.0% of the labeled amount.")], range={"low": q(95.0, "%"), "high": q(105.0, "%")}),
        dict(id="od-dp-assay-hplc", name="Assay (HPLC)", cat="Assay", unit="%", ap="ap-dp-assay-degradation", method="HPLC method",
             crits=[(rel, "95.0% to 105.0% of the declared content"), (sl, "95.0% to 105.0% of the declared content")]),
        dict(id="od-dp-degradation-cp-9-1", name="Degradation products - specified CP-9-1", cat="Degradation Products", unit="%", ap="ap-dp-assay-degradation", method="HPLC",
             crits=[(rel, "Not more than 0.3%"), (sl, "Not more than 0.5%")], desc="Based on the declared content of Sakuramil drug substance."),
        dict(id="od-dp-degradation-unspecified", name="Degradation products - any unspecified", cat="Degradation Products", unit="%", ap="ap-dp-assay-degradation", method="HPLC",
             crits=[(rel, "Not more than 0.2%"), (sl, "Not more than 0.2%")]),
        dict(id="od-dp-degradation-total", name="Degradation products - total", cat="Degradation Products", unit="%", ap="ap-dp-assay-degradation", method="HPLC",
             crits=[(rel, "Not more than 1.0%"), (sl, "Not more than 1.0%")]),
        dict(id="od-dp-met-tamc", name="Microbial enumeration - TAMC", cat="Microbiological Quality", unit="CFU/g", ap="ap-dp-microbial-enumeration", method="Microbial enumeration tests (plate-count method)",
             crits=[(rel, "Not more than 1000 CFU/g"), (sl, "Not more than 1000 CFU/g")], desc="Lot-wise on five consecutive production batches; may be reduced to every tenth batch (at least one batch per calendar year)."),
        dict(id="od-dp-met-tymc", name="Microbial enumeration - TYMC", cat="Microbiological Quality", unit="CFU/g", ap="ap-dp-microbial-enumeration", method="Microbial enumeration tests (plate-count method)",
             crits=[(rel, "Not more than 100 CFU/g"), (sl, "Not more than 100 CFU/g")]),
        dict(id="od-dp-met-e-coli", name="Specified micro-organism - Escherichia coli", cat="Microbiological Quality", ap="ap-dp-microbial-enumeration", method="Test for specified micro-organisms",
             crits=[(rel, "Absence of Escherichia coli in 1 g"), (sl, "Absence of Escherichia coli in 1 g")], range=None),
    ]
    for t in dp_tests:
        if t["id"] in ("od-dp-udu-nir", "od-dp-met-e-coli"):
            t["range"] = None
            t["_norange"] = True
    make_spec("spec-dp", "Specifications and test methods for Sakura Bloom 20 mg film-coated tablet (release and shelf-life)", ("MedicinalProductDefinition", "sakura-bloom-20mg"),
              dp_tests, ["dp-specification", "dp-batch-analysis", "dp-stability", "core"], dpc["url"],
              desc="Table 1 of 2.3.3.DP.C. RTRT is employed for identification, uniformity of dosage units, dissolution and assay at release; conventional end-product tests are specified for stability (shelf-life).",
              default_group=rel)
    for t in dp_tests:
        if t.get("_norange"):
            for qv in R["ObservationDefinition/" + t["id"]]["qualifiedValue"]:
                qv.pop("range", None)
            R["ObservationDefinition/" + t["id"]]["permittedDataType"] = ["string"]
    tag("dp-specification", "Organization", "aparna-pharm")

    # ------------------------------------------------------------ starting materials / intermediates
    sm = [("spec-sm-cp-4", "Specification of starting material CP-4", "cp-4", "2.3.3.SM.C Control [CP-4]", [
            dict(name="Description", cat="Description", crit="White to pale yellow crystals or crystalline powder", method="Visual"),
            dict(name="Identity - IR", cat="Identification", crit="The IR spectrum of the sample is comparable to that of the reference standard (IR)", method="USP <197A>"),
            dict(name="CP-3", cat="Related substances", crit="NMT 0.3 %", method="HPLC In-house", ap="ap-cp-4-related-substances", unit="%"),
            dict(name="Individual unspecified impurity", cat="Related substances", crit="NMT 0.1 %", method="HPLC In-house", ap="ap-cp-4-related-substances", unit="%"),
            dict(name="Total impurities", cat="Related substances", crit="NMT 0.5 %", method="HPLC In-house", ap="ap-cp-4-related-substances", unit="%"),
            dict(name="Enantiomeric purity", cat="Enantiomeric purity", crit="NMT 1.5 %", method="HPLC In-house", ap="ap-cp-4-enantiomeric-purity", unit="%"),
            dict(name="Residual solvents - Toluene", cat="Residual solvents", crit="NMT 890 ppm", method="GC USP <467>", ap="ap-residual-solvents", unit="ppm"),
            dict(name="Palladium (Pd)", cat="Elemental impurities", crit="NMT 10 ppm", method="ICP-MS USP <233>", unit="ppm"),
            dict(name="Assay", cat="Assay", crit="98.0 - 102.0 %", method="HPLC In-house", ap="ap-cp-4-assay", unit="%")]),
          ("spec-sm-cp-8", "Specification of starting material CP-8", "cp-8", "2.3.3.SM.C Control [CP-8]", [
            dict(name="Description", cat="Description", crit="White to pale yellow crystal or crystalline powder (visual observation)", method="Visual"),
            dict(name="Identification - IR", cat="Identification", crit="The IR spectrum of the sample is comparable to that of the reference standard (IR)", method="USP <197A>"),
            dict(name="CP-8-25I", cat="Related substances", crit="NMT 0.05 %", method="HPLC In-house", ap="ap-cp-8-related-substances", unit="%"),
            dict(name="CP-8-24I", cat="Related substances", crit="NMT 0.05 %", method="HPLC In-house", ap="ap-cp-8-related-substances", unit="%"),
            dict(name="Individual unspecified impurities", cat="Related substances", crit="NMT 0.1 %", method="HPLC In-house", ap="ap-cp-8-related-substances", unit="%"),
            dict(name="Total impurities", cat="Related substances", crit="NMT 1.0 %", method="HPLC In-house", ap="ap-cp-8-related-substances", unit="%"),
            dict(name="Assay", cat="Assay", crit="≥ 97 %", method="HPLC In-house", ap="ap-cp-8-assay", unit="%")]),
          ("spec-si-cp-6", "Specification of intermediate CP-6 (Intermediate 1)", "cp-6", "2.3.3.SI.C Control (CP-6)", [
            dict(name="Description", cat="Description", crit="White to pale yellow crystals or crystalline powder", method="Visual"),
            dict(name="Identity - IR", cat="Identification", crit="The IR spectrum of the sample is comparable to that of the reference standard (IR)", method="USP <197A>"),
            dict(name="CP-4", cat="Related substances", crit="NMT 0.3 %", method="HPLC In-house", ap="ap-cp-6-related-substances", unit="%"),
            dict(name="Individual unspecified impurity", cat="Related substances", crit="NMT 0.1 %", method="HPLC In-house", ap="ap-cp-6-related-substances", unit="%"),
            dict(name="Total impurities", cat="Related substances", crit="NMT 0.5 %", method="HPLC In-house", ap="ap-cp-6-related-substances", unit="%"),
            dict(name="Palladium (Pd)", cat="Elemental impurities", crit="NMT 10 ppm", method="ICP-MS USP <233>", unit="ppm"),
            dict(name="Assay", cat="Assay", crit="98.0 - 102.0 %", method="HPLC In-house", ap="ap-cp-6-assay", unit="%")]),
          ("spec-si-cp-7", "Specification of intermediate CP-7 (Intermediate 2)", "cp-7", "2.3.3.SI.C Control (CP-7)", [
            dict(name="Description", cat="Description", crit="White to pale yellow crystals or crystalline powder", method="Visual"),
            dict(name="Identity - IR", cat="Identification", crit="The IR spectrum of the sample is comparable to that of the reference standard (IR)", method="USP <197A>"),
            dict(name="CP-7-1", cat="Related substances", crit="NMT 1.0 %", method="HPLC In-house", ap="ap-cp-7-related-substances", unit="%"),
            dict(name="Individual unspecified impurity", cat="Related substances", crit="NMT 1.0 %", method="HPLC In-house", ap="ap-cp-7-related-substances", unit="%"),
            dict(name="Total impurities", cat="Related substances", crit="NMT 5 %", method="HPLC In-house", ap="ap-cp-7-related-substances", unit="%")])]
    for pid, title, sid, page, tests in sm:
        make_spec(pid, title, ("SubstanceDefinition", sid), tests, ["materials-specifications", "core"], S.page(page)["url"])
        tag("materials-specifications", "SubstanceDefinition", sid)

    # ------------------------------------------------------------ raw materials (parsed)
    for p in S.pages:
        if "/ 2.3.3.RM.C" not in p["short"]:
            continue
        mname = re.search(r"\[(.*?)\]", p["short"].split(" / ")[-1]).group(1)
        sid = "rm-" + slug(mname.replace("Catalyst ", "").replace(" (Dichloromethane, DCM)", ""))
        tabs = Source.tables(p["text"])
        if not tabs:
            ISSUES.append("No specification table on " + p["short"])
            continue
        tests = []
        for r in tabs[0][1][1:]:
            r = r + ["", "", ""]
            n, c, m = r[0], r[1], r[2]
            if not n:
                continue
            cat = n.split(" (")[0]
            cat = {"Appearance": "Appearance", "Identification": "Identification", "Assay": "Assay"}.get(cat, cat)
            tests.append(dict(name=n, cat=cat, crit=c or "-", method=m or None))
        make_spec("spec-" + sid, f"Specification of raw material {mname.replace('Catalyst ', '')}", ("SubstanceDefinition", sid), tests, ["materials-specifications", "core"], p["url"])
        tag("materials-specifications", "SubstanceDefinition", sid)

    # ------------------------------------------------------------ excipients
    exs = S.page("2.3.3.EX Compendial excipients")
    comp = [("lactose-monohydrate", "Lactose monohydrate"), ("microcrystalline-cellulose", "Cellulose, microcrystalline"), ("croscarmellose-sodium", "Croscarmellose sodium"),
            ("hydroxypropyl-cellulose", "Hydroxypropyl cellulose"), ("magnesium-stearate", "Magnesium stearate"), ("purified-water", "Water, purified")]
    for sid, n in comp:
        make_spec(f"spec-ex-{sid}", f"Specification of compendial excipient {n}", ("SubstanceDefinition", sid),
                  [dict(id=f"od-ex-{sid}-monograph", name=f"{n} - compliance with monograph", cat="Compendial compliance", crit="Complies with Ph. Eur., USP/NF and JP monographs", method="Ph. Eur., USP/NF, JP")],
                  ["dp-excipients", "core"], exs["url"])
    pm = S.page("2.3.3.EX Non-compendial Excipients")
    make_spec("spec-ex-coating-premix-red", "Specification of non-compendial excipient Basic coating premix, red", ("SubstanceDefinition", "coating-premix-red"), [
        dict(name="Appearance by visual examination", cat="Description", crit="Red powder", ap="ap-premix-visual", method="Visual examination"),
        dict(name="Identity by IR (ATR)", cat="Identification", crit="Complies with a reference spectrum from a reference material provided by the manufacturer", ap="ap-premix-identity-ir", method="IR (ATR)"),
        dict(name="Identity of colourants", cat="Identification", crit="Complies favorably to reference material provided by the manufacturer", ap="ap-premix-identity-colorants", method="TLC / colourant identity"),
        dict(name="Identity of iron", cat="Identification", crit="Positive", ap="ap-premix-identity-iron", method="Chemical identity reaction"),
        dict(name="Total ash", cat="Purity", crit="47.05 – 56.15%", method="Ph. Eur.", unit="%")], ["dp-excipients", "core"], pm["url"])

    # ------------------------------------------------------------ reference standard (identification standard)
    rs = S.page("2.3.3.RS.C Controls")
    make_spec("spec-rs-cp-9-identification-standard", "Control of CP-9 identification standard (Sakuramil spiked with CP-9-1 and CP-8)", ("SubstanceDefinition", "sakuramil"), [
        dict(name="Appearance", cat="Description", crit="White solid", method="visual evaluation"),
        dict(name="Sakuramil (IR)", cat="Identification", crit="The IR spectrum of the sample is comparable to that of the reference standard", method="IR USP <197A>"),
        dict(name="CP-9-1", cat="Related substances", crit="≤ 1.0 %", ap="ap-ds-related-substances", method="HPLC In-house", unit="%"),
        dict(name="CP-8", cat="Related substances", crit="≤ 1.0 %", ap="ap-ds-related-substances", method="HPLC In-house", unit="%"),
        dict(name="Individual unspecified impurities", cat="Related substances", crit="≤ 0.10 %", ap="ap-ds-related-substances", method="HPLC In-house", unit="%"),
        dict(name="Sakuramil", cat="Assay", crit="98.0 – 102.0 % (dried basis)", ap="ap-ds-assay-id", method="HPLC In-house", unit="%")],
        ["reference-standards", "core"], rs["url"], ptype=("1244578", "Reference Standard Analysis"))

    # ------------------------------------------------------------ container closure specifications
    cc_specs = [
        ("spec-cc-ds-ldpe-bag", "Primary packaging specification - LDPE bag (drug substance)", "2.3.3.DS.S Storage", ("SubstanceDefinition", "sakuramil"), [
            dict(name="Appearance", cat="Description", crit="transparent clean bag, without foreign particles or greasy spots, without holes and other defects", method="Visual"),
            dict(name="Colour", cat="Description", crit="natural colour of resin", method="Visual"),
            dict(name="Identification of the plastic by IR", cat="Identification", crit="corresponding to the reference spectrum", method="IR"),
            dict(name="Leakage", cat="Physical testing", crit="corresponding", method="Leak test"),
            dict(name="Thickness", cat="Dimensions", crit="100 µm ± 13 %", method="Thickness gauge", range={"low": q(87, "µm"), "high": q(113, "µm")}, target=q(100, "µm"))]),
        ("spec-cc-hdpe-bottle", "Primary packaging specification - 90 cc HDPE bottle and 38 mm child-resistant closure", "2.3.3.DP.S. Storage - Bottle", ("MedicinalProductDefinition", "sakura-bloom-20mg"), [
            dict(name="90 cc HDPE bottle - Appearance", cat="Description", crit="Clean and undamaged", method="Visual examination"),
            dict(name="90 cc HDPE bottle - Light transmission", cat="Light transmission", crit="Not more than 10 %", method="UV Spectroscopy", unit="%"),
            dict(name="90 cc HDPE bottle - Material", cat="Material identification", crit="High density polyethylene", method="Thermal analysis"),
            dict(name="38 mm child resistant closure - Appearance", cat="Description", crit="Clean and undamaged", method="Visual examination"),
            dict(name="38 mm child resistant closure - Colour", cat="Description", crit="Screw cap: Outer: White, Inner: Colorless; Liner: Upper: white, Lower: silver", method="Visual examination"),
            dict(name="38 mm child resistant closure - Material identification", cat="Material identification", crit="Outer cap: Polypropylene; Inner cap: Polypropylene", method="Thermal analysis")]),
        ("spec-cc-blister-foils", "Primary packaging specification - PA/AL/PVC forming foil and aluminium lidding foil", "2.3.3.DP.S Storage - Blister", ("MedicinalProductDefinition", "sakura-bloom-20mg"), [
            dict(name="PA/AL/PVC foil - Cleanliness", cat="Description", crit="Free from dust, fibers and dirt", method="Visual examination"),
            dict(name="PA/AL/PVC foil - Appearance", cat="Description", crit="Clear, colourless", method="Visual examination"),
            dict(name="PA/AL/PVC foil - Thickness (total)", cat="Dimensions", crit="≥ 150 µm", method="Dimension testing with suitable measuring equipment", range={"low": q(150, "µm")}),
            dict(name="PA/AL/PVC foil - Identity IR (PA film)", cat="Identification", crit="Corresponds qualitatively to the reference spectrum", method="Spectroscopic testing"),
            dict(name="PA/AL/PVC foil - Identity IR (PVC film)", cat="Identification", crit="Corresponds qualitatively to the reference spectrum", method="Spectroscopic testing"),
            dict(name="Aluminium foil - Cleanliness", cat="Description", crit="Free from dust, fibers and dirt", method="Visual examination"),
            dict(name="Aluminium foil - Thickness (total)", cat="Dimensions", crit="≥ 20 µm", method="Dimension testing with suitable measuring equipment", range={"low": q(20, "µm")}),
            dict(name="Aluminium foil - Identity IR (heat seal lacquer)", cat="Identification", crit="Corresponds qualitatively to the reference spectrum", method="Spectroscopic testing")]),
        ("spec-cc-bulk-bag", "Packaging specification - aluminium composite bag (bulk)", "2.3.3.DP.S Storage - Bulk", ("MedicinalProductDefinition", "sakura-bloom-20mg"), [
            dict(name="Aspect control", cat="Description", crit="Clear and free from defects and mold flashing", method="Visual"),
            dict(name="Appearance colour", cat="Description", crit="Nature", method="Visual"),
            dict(name="Identity by IR - ATR", cat="Identification", crit="Corresponds qualitatively to the reference spectrum", method="IR-ATR")]),
    ]
    for pid, title, page, subj, tests in cc_specs:
        make_spec(pid, title, subj, tests, ["container-closure", "core"], S.page(page)["url"], ptype=("container-specification", "Container Specification"), default_group="Incoming inspection")
