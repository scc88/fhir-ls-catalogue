"""Manufacturing processes, batches, batch analyses, stability, reference standards, impurity studies."""
from lib import *
from part2_specs import make_od, make_spec

PP = SD + "Extension-process-parameters-pq"
CS_PROC = "http://terminology.hl7.org/CodeSystem/process-parameter"
CS_DIAG = "http://terminology.hl7.org/CodeSystem/diagram-type"
MFGB = "http://hl7.org/fhir/StructureDefinition/medication-manufacturingBatch"
TRIG = "http://hl7.org/fhir/StructureDefinition/workflow-triggeredBy"
OBS_N = [0]


def pparam(label, text=None, value=None, coding=None):
    e = [ext("parameter", valueCodeableConcept=cc(label, *(coding or (None, None, None))))]
    if value is not None:
        e.append(ext("value", valueQuantity=value))
    if text:
        e.append(ext("valueText", valueString=text))
    return ext(PP, extension=e)


def participant(sid, role, display):
    rc = {"StartingMaterial": "Starting Material", "ProcessingMaterial": "Processing Material", "IntermediateMaterial": "Intermediate Material", "ResultingMaterial": "Resulting Material"}
    return {"typeReference": {"extension": [ext(SD + "Extension-manufacturing-participant-pq", valueReference=ref("SubstanceDefinition", sid))], "display": display},
            "role": cc(rc[role], CS_PARTROLE, role, rc[role])}


def docref(did, title, url, groups, dtype=True):
    return add("DocumentReference", did, {"status": "current",
        "type": cc("Process Flow Diagram", CS_DIAG, "ProcessFlowDiagram", "Process Flow Diagram") if dtype else cc(title),
        "description": title, "content": [{"attachment": {"contentType": "text/html", "url": url, "title": title}}]}, groups, source=url)


def obs(oid, od_id, subject, raw, performer=None, specimen=None, groups=(), effective=None, note=None, triggered=None):
    od = R["ObservationDefinition/" + od_id]
    body = OrderedDict()
    if triggered:
        body["extension"] = [ext(TRIG, valueReference=triggered)]
    body["status"] = "final"
    body["instantiatesCanonical"] = canon("ObservationDefinition", od_id)
    body["category"] = od.get("category", [])
    body["code"] = od["code"]
    body["subject"] = subject
    if effective:
        body["effectiveDateTime"] = effective
    if performer:
        body["performer"] = [performer]
    raw = re.sub(r"\s+", " ", raw).strip()
    comps = []
    m = re.match(r"^(?:Mean:\s*)?(\d+(?:\.\d+)?)\s*%?\s*\((\d+(?:\.\d+)?)\s*%?\s*[-–]\s*(\d+(?:\.\d+)?)\s*%?\)\s*(?:AV:\s*(\d+(?:\.\d+)?)\s*%)?\s*(?:n\s*=\s*(\d+))?\s*(Complies)?", raw)
    m2 = re.match(r"^(\d+(?:\.\d+)?)\s*\((\d+)\)\s*\[(\d+(?:\.\d+)?)\s*[-,]\s*(\d+(?:\.\d+)?)\]?", raw)
    if m:
        body["valueQuantity"] = q(fnum(m.group(1)), "%")
        comps = [("Minimum", q(fnum(m.group(2)), "%")), ("Maximum", q(fnum(m.group(3)), "%"))]
        if m.group(4):
            comps.append(("Acceptance value (AV)", q(fnum(m.group(4)), "%")))
        if m.group(5):
            comps.append(("Number of units tested (n)", {"value": int(m.group(5))}))
        if m.group(6):
            body["interpretation"] = [cc("Complies")]
    elif m2:
        body["valueQuantity"] = q(fnum(m2.group(1)), "%")
        comps = [("Number of units tested (n)", {"value": int(m2.group(2))}), ("Minimum", q(fnum(m2.group(3)), "%")), ("Maximum", q(fnum(m2.group(4)), "%"))]
    else:
        pr = parse_result(raw)
        if pr is None:
            return None
        k, v = pr
        if k == "valueQuantity" and "unit" not in v:
            u = (od.get("permittedUnit") or [{}])[0]
            if u.get("code"):
                v.update({"unit": u.get("display"), "system": UCUM, "code": u["code"]})
        body[k] = v
        if raw.lower() in ("complies", "complies¹", "no change", "absent"):
            body["interpretation"] = [cc("Complies" if raw.lower() != "absent" else "Absent")]
    if comps:
        body["component"] = [{"code": cc(c), "valueQuantity": v} for c, v in comps]
    if specimen:
        body["specimen"] = specimen[0] if isinstance(specimen, list) else specimen
    if note:
        body["note"] = [{"text": note}]
    if "Complies" in raw and "valueQuantity" in body and not body.get("interpretation"):
        body["interpretation"] = [cc("Complies")]
    add("Observation", oid, body, groups)
    return oid


def report(rid, code, subject, results, performer, groups, triggered=None, conclusion=None, category=None, specimen=None, effective=None, source=None, display=None):
    body = OrderedDict()
    if triggered:
        body["extension"] = [ext(TRIG, valueReference=triggered)]
    body["identifier"] = [{"system": BASE + "/report-id", "value": rid}]
    body["status"] = "final"
    if category:
        body["category"] = [cc(category)]
    body["code"] = cc(code, CS_REPORT, code, code)
    body["subject"] = subject
    if effective:
        body["effectiveDateTime"] = effective
    body["performer"] = [performer]
    if specimen:
        body["specimen"] = specimen
    body["result"] = [ref("Observation", o) for o in results if o]
    if conclusion:
        body["conclusion"] = conclusion
    add("DiagnosticReport", rid, body, groups, source=source)


# ------------------------------------------------------------------ mapping of table rows to ODs
def ds_od(cat, param, crit):
    p = param.lower()
    if "appearance" in p: return "od-ds-sakuramil-appearance"
    if "(ir)" in p: return "od-ds-sakuramil-sakuramil-ir"
    if "(hplc)" in p: return "od-ds-sakuramil-sakuramil-hplc"
    if p.strip() == "sakuramil" or (cat or "").lower() == "assay": return "od-ds-sakuramil-assay-sakuramil-dried-basis"
    if "cp-9-1" in p: return "od-ds-sakuramil-cp-9-1"
    if p.strip() == "cp-8": return "od-ds-sakuramil-cp-8"
    if "unspecified" in p: return "od-ds-sakuramil-individual-unspecified-impurities"
    if "total" in p: return "od-ds-sakuramil-total-impurities"
    if "cp-6" in p: return "od-ds-sakuramil-cp-6"
    if "dichloromethane" in p or "methylene" in p: return "od-ds-sakuramil-methylene-chloride"
    if "loss on drying" in p: return "od-ds-sakuramil-loss-on-drying"
    if "residue on ignition" in p: return "od-ds-sakuramil-residue-on-ignition"
    if "d(0.1)" in (crit + p): return "od-ds-sakuramil-particle-size-distribution-d-0-1"
    if "d(0.5)" in (crit + p): return "od-ds-sakuramil-particle-size-distribution-d-0-5"
    if "d(0.9)" in (crit + p): return "od-ds-sakuramil-particle-size-distribution-d-0-9"
    return None


def build(S):
    G_DSM, G_DPM = ["ds-manufacturing", "core"], ["dp-manufacturing", "core"]
    # ================================================================ DS manufacturing process
    dsm = S.page("2.3.3.DS.M Manufacture")
    d1 = docref("doc-ds-synthetic-scheme", "Figure 1-1 Synthetic scheme of Sakuramil (2.3.3.DS.M.1)", dsm["url"], G_DSM)
    d2 = docref("doc-ds-block-flow-diagram", "Figure 1-2 (Block) flow diagram of Sakuramil manufacture (2.3.3.DS.M.1)", dsm["url"], G_DSM)
    rm = lambda n: "rm-" + slug(n)
    steps = [
        ("Step 1", "CP-4 is combined with methyl chloroformate, lithium-tert-butoxide, and tetrahydrofuran, then stirred. Layers are settled and separated. Precipitates are filtered, rinsed with tetrahydrofuran and dried to yield CP-5.",
         [("cp-4", "StartingMaterial", "Starting Material CP-4", "175-185 kg"), (rm("Methyl Chloroformate"), "ProcessingMaterial", "Methyl chloroformate", "55-120 L"),
          (rm("Lithium-tert-butoxide"), "ProcessingMaterial", "Lithium-tert-butoxide", "22-85 kg"), (rm("Tetrahydrofuran"), "ProcessingMaterial", "Tetrahydrofuran", "750-920 L"),
          ("cp-5", "ResultingMaterial", "In situ intermediate CP-5", None)], [], []),
        ("Step 2", "CP-5 is combined with sodium borohydride, magnesium chloride, and methanol, then filtered after the reaction completes. Hydrochloric acid is added to the filtrate, layers are settled and separated. Organic layer is distilled with ethanol, and the mixture is stirred with water. Resulting precipitate is filtered, rinsed and dried to yield CP-6.",
         [("cp-5", "IntermediateMaterial", "In situ Intermediate CP-5", "195-210 kg"), (rm("Sodium borohydride"), "ProcessingMaterial", "Sodium borohydride", "480-2120 kg"),
          (rm("Magnesium chloride"), "ProcessingMaterial", "Magnesium chloride", "22-35 kg"), (rm("Methanol"), "ProcessingMaterial", "Methanol", "105-320 L"),
          (rm("Hydrochloric Acid"), "ProcessingMaterial", "Hydrochloric acid", "54-59 L"), ("rm-ethanol", "ProcessingMaterial", "Ethanol", "final concentration 1000 L"),
          (rm("Water"), "ProcessingMaterial", "Water", "25 to 35% w/w of ethanol"), ("cp-6", "ResultingMaterial", "Intermediate CP-6", None)], [], []),
        ("Step 3", "CP-6 is combined with tetrahydrofuran, sodium carbonate, and ethyl chloroformate, then heated to reflux. Upon reaction completion, the mixture is filtered and quenched with sodium hydroxide, n-hexane is added, the layers are separated, and the organic layer is distilled with ethanol and stirred with water (CPP #3.1). After filtering and drying it results in CP-7.",
         [("cp-6", "IntermediateMaterial", "Intermediate CP-6", "220-240 kg"), (rm("Tetrahydrofuran"), "ProcessingMaterial", "Tetrahydrofuran", "598-3059 L"),
          (rm("Sodium carbonate"), "ProcessingMaterial", "Sodium carbonate", "41.8-43.1 kg"), (rm("Ethyl chloroformate"), "ProcessingMaterial", "Ethyl chloroformate", "159-592 L"),
          (rm("Sodium hydroxide"), "ProcessingMaterial", "Sodium hydroxide", "112-119 L"), (rm("nHexane"), "ProcessingMaterial", "n-Hexane", "52-55 L"),
          ("rm-ethanol", "ProcessingMaterial", "Ethanol", "final concentration 1400 L"), (rm("Water"), "ProcessingMaterial", "Water", "25 to 35% w/w of ethanol"),
          ("cp-7", "ResultingMaterial", "Intermediate CP-7", None)],
         [("cpp-ds-3-1", "CPP #3.1 Water addition in the crystallization (% by weight with respect to ethanol)", "25 – 35 %", {"low": q(25, "%"), "high": q(35, "%")})], []),
        ("Step 4", "CP-7 and CP-8 are combined in methylene chloride followed by the addition of tetra-n-butylammonium bromide and aqueous sodium hydroxide solution while mixing. Upon reaction completion, methylene chloride and water are added (CPP #4.1); ethanol content is monitored by IPC #1. The mixture is separated, washed, cooled (CPP #4.2, IPC #2) and concentrated with ethanol. After filtering and drying it results in CP-9 (Sakuramil).",
         [("cp-7", "IntermediateMaterial", "Intermediate CP-7", "240-260 kg"), ("cp-8", "StartingMaterial", "Starting Material CP-8", "200-220 kg"),
          (rm("Methylene chloride"), "ProcessingMaterial", "Methylene chloride", "720-760 L, then 805-815 L"), (rm("Tetra-n-butylammonium bromide"), "ProcessingMaterial", "Tetra-n-butylammonium bromide", "49-52 kg"),
          (rm("Sodium hydroxide"), "ProcessingMaterial", "Sodium hydroxide", "720-760 L"), (rm("Water"), "ProcessingMaterial", "Water", "98-105 L; then 20 to 35% w/w of ethanol"),
          (rm("Hydrochloric Acid"), "ProcessingMaterial", "Hydrochloric acid", "quantity not stated"), ("rm-ethanol", "ProcessingMaterial", "Ethanol", "final concentration 1800 L"),
          ("sakuramil", "ResultingMaterial", "CP-9 (Sakuramil)", None)],
         [("cpp-ds-4-1", "CPP #4.1 Water addition in the crystallization (% by weight with respect to ethanol)", "25 – 35 %", {"low": q(25, "%"), "high": q(35, "%")}),
          ("cpp-ds-4-2", "CPP #4.2 Cooling rate (°C/min)", "0.15 – 0.5 °C/min", {"low": q(0.15, "°C/min"), "high": q(0.5, "°C/min")})],
         [("ipc-ds-1-ethanol", "IPC #1 Ethanol", "≤ 5000 ppm", {"high": q(5000, "ppm")}, "ap-residual-solvents", "GC (residual solvents procedure)"),
          ("ipc-ds-2-cooling-rate", "IPC #2 Cooling rate", "0.15 – 0.5 °C/min", {"low": q(0.15, "°C/min"), "high": q(0.5, "°C/min")}, None, "Temperature measurement with temperature measurement device")]),
    ]
    ISSUES.append("Drug substance Step 4: the raw-material column lists water as '20 to 35% w/w of ethanol' whereas CPP #4.1 states 25-35 %; the CPP range was used for the control and the raw-material text kept verbatim.")
    acts = []
    for title, desc, mats, cpps, ipcs in steps:
        a = OrderedDict()
        a["extension"] = [ext(SD + "Extension-process-step-scale-pq", valueCoding={"system": CS_SCALE, "code": "PROD", "display": "Production Scale"})]
        a["extension"] += [pparam(f"Charge: {d}", text=qty) for sid, r, d, qty in mats if qty]
        a["extension"] += [pparam(n, text=t) for cid, n, t, rg in cpps]
        a["title"] = title
        a["description"] = desc
        a["code"] = [cc("Chemical synthesis step")]
        a["participant"] = [participant(sid, r, d) for sid, r, d, qty in mats]
        sub = []
        for cid, n, t, rg in cpps:
            make_od(cid, dict(name=n, cat="Critical process parameter", crit=t, range=rg, critical=True), dsm["url"], G_DSM)
            sub.append({"title": n, "code": [cc("Critical process parameter")], "definitionCanonical": canon("ObservationDefinition", cid)})
        for iid, n, t, rg, ap, meth in ipcs:
            make_od(iid, dict(name=n, cat="In-process control", crit=t, range=rg, method=meth), dsm["url"], G_DSM)
            s = {"title": n, "code": [cc("In-process control")], "definitionCanonical": canon("ObservationDefinition", iid)}
            if ap:
                s["documentation"] = [{"type": "depends-on", "label": "Analytical procedure", "resource": canon("PlanDefinition", ap)}]
            sub.append(s)
        if sub:
            a["action"] = sub
        acts.append(a)
    add("PlanDefinition", "ds-manufacturing-process", {
        "extension": [ext(SD + "Extension-plan-document-reference-pq", valueReference=ref("DocumentReference", d)) for d in ("doc-ds-synthetic-scheme", "doc-ds-block-flow-diagram")] +
                     [ext(SD + "Extension-history-of-process-pq", valueMarkdown="No routine reprocessing is carried out.")],
        "title": "Manufacturing process of Sakuramil drug substance (IROHA-corp.)",
        "type": cc("Manufacturing Process", CS_PLAN, "manufacturing-process", "Manufacturing Process"), "status": "active",
        "subjectReference": ref("SubstanceDefinition", "sakuramil"),
        "description": "Four-step synthesis CP-4 -> CP-5 (in situ) -> CP-6 -> CP-7 -> CP-9 (Sakuramil). Typical commercial batch size 350 kg.",
        "action": [{"title": "Overall process", "code": [cc("Overall Process", CS_MFGSTEP, "overall process", "Overall Process")], "action": acts}]}, G_DSM, source=dsm["url"])
    for sid in sorted({p[0] for s in steps for p in s[2]}):
        tag("ds-manufacturing", "SubstanceDefinition", sid)
    tag("ds-manufacturing", "Organization", "iroha-corp")

    # ================================================================ DP manufacturing process
    dpm = S.page("2.3.3.DP.M Manufacture - Core")
    docref("doc-dp-process-flow-diagram", "Figure 1 Flow diagram for the manufacturing process of Sakura Bloom 20 mg film-coated tablet (2.3.3.DP.M.2)", dpm["url"], G_DPM)
    equip = [("eq-bin-blender", "Bin blender (diffusion mixer)", "SUPAC Class: diffusion mixer; Subclass: bin blender", q(500, "L"), "Blender"),
             ("eq-fluid-bed-granulator", "Fluidized bed granulator / dryer", "SUPAC Class: wet granulator; Subclass: fluidized bed granulator (dryer integrated)", q(750, "L"), "Dryer"),
             ("eq-screening-mill", "Screening mill (oscillating bar)", "SUPAC Class: screening mill; Subclass: oscillating bar", None, None),
             ("eq-rotary-tablet-press", "Rotary tablet press (power assisted)", "SUPAC Class: rotary tablet press; Subclass: power assisted", None, None),
             ("eq-coating-vessel", "Vessel with stirrer (coating suspension)", "Vessel with stirrer", q(750, "L"), "mixing-vessel"),
             ("eq-pan-coater", "Pan coater (perforated coating system)", "SUPAC Class: pan coating; Subclass: perforated coating system", None, None)]
    add("DeviceDefinition", "eq-ds-temperature-probe", {"deviceName": [{"name": "Temperature measurement device (Step 4 cooling-rate IPC #2)", "type": "user-friendly-name"}],
        "classification": [{"type": cc("Temperature measurement device")}]}, G_DSM, source=dsm["url"])
    for did, name, cls, cap, eqc in equip:
        body = {"deviceName": [{"name": name, "type": "user-friendly-name"}],
                "classification": [{"type": cc(cls)}],
                "property": [{"type": cc("Automation"), "valueBoolean": True}]}
        if cap:
            body["property"].insert(0, {"type": cc("Capacity", "http://terminology.hl7.org/CodeSystem/device-property", "Capacity", "Capacity"), "valueQuantity": cap})
        add("DeviceDefinition", did, body, G_DPM, source=dpm["url"])
    R["DeviceDefinition/eq-screening-mill"]["property"].insert(0, {"type": cc("Speed range"), "valueRange": {"low": q(30, "rpm"), "high": q(108, "rpm")}})
    R["DeviceDefinition/eq-rotary-tablet-press"]["property"].insert(0, {"type": cc("Speed range"), "valueRange": {"low": q(10, "rpm"), "high": q(90, "rpm")}})
    R["DeviceDefinition/eq-pan-coater"]["property"].insert(0, {"type": cc("Capacity", "http://terminology.hl7.org/CodeSystem/device-property", "Capacity", "Capacity"), "valueRange": {"low": q(300, "L"), "high": q(390, "L")}})

    def dev(d):
        return {"type": "device", "typeReference": ref("DeviceDefinition", d)}

    def mat(sid, role, disp):
        return participant(sid, role, disp)

    ipc = lambda oid, n, crit, rng, meth, target=None, ap=None: (oid, dict(name=n, cat="In-process control", crit=crit, range=rng, method=meth, target=target), ap)
    cpp = lambda oid, n, crit, rng: (oid, dict(name=n, cat="Critical process parameter", crit=crit, range=rng, critical=True), None)
    dpsteps = [
        (1, "Pre-blending", "Blend 52.000 kg of cellulose, microcrystalline, 26.000 kg of croscarmellose sodium, 353.600 kg of lactose monohydrate and 52.000 kg of Sakuramil drug substance in a diffusion mixer (bin blender).",
         ("Mixing of ingredients", "Mixing of ingredients"), [dev("eq-bin-blender"), mat("microcrystalline-cellulose", "StartingMaterial", "Cellulose, microcrystalline"), mat("croscarmellose-sodium", "StartingMaterial", "Croscarmellose sodium"), mat("lactose-monohydrate", "StartingMaterial", "Lactose monohydrate"), mat("sakuramil", "StartingMaterial", "Sakuramil")],
         [pparam("Charge: Cellulose, microcrystalline", value=q(52.000, "kg")), pparam("Charge: Croscarmellose sodium", value=q(26.000, "kg")), pparam("Charge: Lactose monohydrate", value=q(353.600, "kg")), pparam("Charge: Sakuramil", value=q(52.000, "kg"))], []),
        (2, "Preparation of granulation liquid", "Dissolve 15.600 kg hydroxypropyl cellulose in purified water using a vessel with stirrer to prepare a granulation liquid free from lumps.",
         ("compounding", "Compounding Step"), [mat("hydroxypropyl-cellulose", "StartingMaterial", "Hydroxypropyl cellulose"), mat("purified-water", "ProcessingMaterial", "Purified water")],
         [pparam("Charge: Hydroxypropyl cellulose", value=q(15.600, "kg"))], []),
        (3, "Granulation", "Load the pre-blended material into a fluid bed granulator and add the granulation liquid to achieve wetting of pre-blended material and formation of granules.",
         None, [dev("eq-fluid-bed-granulator")],
         [pparam("Inlet air volume", text="40 - 45 m³/min"), pparam("Inlet air temperature", text="75 - 85 °C", coding=(CS_PROC, "TEMP", "Temperature")), pparam("Spray rate", text="900 - 1100 g/min")],
         [cpp("cpp-dp-3-inlet-air-volume", "Granulation - inlet air volume", "40 - 45 m³/min", {"low": q(40, "m³/min"), "high": q(45, "m³/min")}),
          cpp("cpp-dp-3-inlet-air-temperature", "Granulation - inlet air temperature", "75 - 85 °C", {"low": q(75, "°C"), "high": q(85, "°C")}),
          cpp("cpp-dp-3-spray-rate", "Granulation - spray rate", "900 - 1100 g/min", {"low": q(900, "g/min"), "high": q(1100, "g/min")}),
          ipc("ipc-dp-3-granule-particle-size", "Granule particle size", "Target: 150 µm; Range: 90-210 µm", {"low": q(90, "µm"), "high": q(210, "µm")}, "Laser diffraction particle size distribution analyzer", q(150, "µm"))]),
        (4, "Drying", "Dry the granules using the dryer integrated within the fluid bed granulator unit until loss on drying of 1 - 2 % is achieved.",
         ("drying", "Drying"), [dev("eq-fluid-bed-granulator")], [pparam("End point: loss on drying", text="1 - 2 %")],
         [ipc("ipc-dp-4-lod", "Loss on drying (granules)", "Target: 1 %; Range: ≤ 2 %", {"high": q(2, "%")}, "Weighing", q(1, "%"))]),
        (5, "Screening", "Sieve the dried granules using a screening mill.", ("particleSizeReduction", "Particle Size Reduction"), [dev("eq-screening-mill")], [], []),
        (6, "Lubricant addition", "Sieve 5.200 kg of magnesium stearate through a screen and add it to the granules.", None, [mat("magnesium-stearate", "StartingMaterial", "Magnesium stearate")],
         [pparam("Charge: Magnesium stearate", value=q(5.200, "kg"))], []),
        (7, "Final blending", "Blend the mixture using a diffusion mixer (bin blender) to obtain the final blend.", ("Mixing of ingredients", "Mixing of ingredients"), [dev("eq-bin-blender")], [], []),
        (8, "Tablet compression", "Compress the final blend using a tablet press to obtain the tablet cores.", None, [dev("eq-rotary-tablet-press")],
         [pparam("Rotation speed", text="20 - 30 rpm", coding=(CS_PROC, "ROTATIONSPEED", "Rotational Speed")), pparam("Compression force", text="6 - 14 kN")],
         [cpp("cpp-dp-8-rotation-speed", "Compression - rotation speed", "20 - 30 rpm", {"low": q(20, "rpm"), "high": q(30, "rpm")}),
          cpp("cpp-dp-8-compression-force", "Compression - compression force", "6 - 14 kN", {"low": q(6, "kN"), "high": q(14, "kN")}),
          ipc("ipc-dp-8-tablet-weight", "Uncoated tablet weight", "Target: 194.0 mg; Range: 188.2–199.8 mg", {"low": q(188.2, "mg"), "high": q(199.8, "mg")}, "Weighing", q(194.0, "mg")),
          ipc("ipc-dp-8-weight-variation", "Uncoated tablet weight variation", "Target: 100.0 %; Range: 95.0 % - 105 %", {"low": q(95.0, "%"), "high": q(105, "%")}, "Weighing", q(100.0, "%")),
          ipc("ipc-dp-8-hardness", "Uncoated tablet hardness", "Target: 7.3 kp; Range: 3–11.5 kp", {"low": q(3, "kp"), "high": q(11.5, "kp")}, "According to compendial requirement", q(7.3, "kp")),
          ipc("ipc-dp-8-assay", "Assay (tablet cores)", "95.0 - 105.0 %", {"low": q(95.0, "%"), "high": q(105.0, "%")}, "HPLC", None, "ap-dp-assay-degradation"),
          ipc("ipc-dp-8-udu", "Uniformity of dosage units (tablet cores)", "Meets the requirements of Ph. Eur., USP and JP harmonized procedure", None, "According to compendial requirement")]),
        (9, "Preparation of the coating suspension", "Prepare a homogeneous suspension of the Basic coating premix, red in purified water.", ("compounding", "Compounding Step"),
         [dev("eq-coating-vessel"), mat("coating-premix-red", "StartingMaterial", "Basic coating premix, red"), mat("purified-water", "ProcessingMaterial", "Purified water")],
         [pparam("Charge: Basic coating premix, red", value=q(15.600, "kg"))], []),
        (10, "Film-coating", "Film-coat the tablet cores using the film-coat suspension in a coating pan to achieve the desired film-coat weight gain, followed by drying.", None, [dev("eq-pan-coater")], [],
         [ipc("ipc-dp-10-lod", "Loss on drying (film-coated tablets)", "Target: 1 %; Range: ≤ 2 %", {"high": q(2, "%")}, "Weighing", q(1, "%")),
          ipc("ipc-dp-10-coat-weight-gain", "Film coat weight gain", "2 - 4 % of tablet weight", {"low": q(2, "%"), "high": q(4, "%")}, "Weight check")]),
        (11, "Inspection", "Collect 10 tablets to perform the Description test and Identification test (RTRT).", ("release", "Release Step"), [], [],
         [ipc("ipc-dp-11-appearance", "Appearance (inspection)", "Visual observation", None, "Visual examination"),
          ipc("ipc-dp-11-identification", "Identification (NIR, inspection)", "Identification using an NIR method", None, "NIR method", None, "ap-dp-identity-nir")]),
        (12, "Primary packaging", "The film-coated tablets are primary packaged (HDPE bottle or PA/AL/PVC blister).", ("filling", "Filling Step"), [], [], []),
        (13, "Secondary packaging", "The primary packaged product is packed in a cardboard-based secondary pack.", None, [], [], []),
    ]
    acts = []
    for n, title, desc, code, parts, params, ctrls in dpsteps:
        a = OrderedDict()
        a["extension"] = [ext(SD + "Extension-process-step-scale-pq", valueCoding={"system": CS_SCALE, "code": "PROD", "display": "Production Scale"})] + params
        a["title"] = f"Step {n} - {title}"
        a["description"] = desc
        a["code"] = [cc(code[1], CS_MFGSTEP, code[0], code[1]) if code else cc(title)]
        if parts:
            a["participant"] = parts
        sub = []
        for oid, t, ap in ctrls:
            make_od(oid, t, dpm["url"], G_DPM)
            s = {"title": t["name"], "code": [cc(t["cat"])], "definitionCanonical": canon("ObservationDefinition", oid)}
            if ap:
                s["documentation"] = [{"type": "depends-on", "label": "Analytical procedure", "resource": canon("PlanDefinition", ap)}]
            sub.append(s)
        if sub:
            a["action"] = sub
        acts.append(a)
    add("PlanDefinition", "dp-manufacturing-process", {
        "extension": [ext(SD + "Extension-plan-document-reference-pq", valueReference=ref("DocumentReference", "doc-dp-process-flow-diagram"))],
        "title": "Manufacturing process of Sakura Bloom 20 mg film-coated tablets (Aparna Pharmaceutical Manufacturing)",
        "type": cc("Manufacturing Process", CS_PLAN, "manufacturing-process", "Manufacturing Process"), "status": "active",
        "subjectReference": ref("MedicinalProductDefinition", "sakura-bloom-20mg"),
        "description": "Wet (fluid-bed) granulation, blending, compression and film-coating. Commercial batch size 520.00 kg (approx. 2,600,000 tablets). No overages. Critical steps: granulation (step 3) and compression (step 8); granule particle size and uncoated tablet hardness are controlled within a design space to ensure dissolution.",
        "action": [{"title": "Overall process", "code": [cc("Overall Process", CS_MFGSTEP, "overall process", "Overall Process")], "action": acts}]}, G_DPM, source=dpm["url"])
    for sid in ["sakuramil", "lactose-monohydrate", "microcrystalline-cellulose", "croscarmellose-sodium", "hydroxypropyl-cellulose", "magnesium-stearate", "coating-premix-red", "purified-water"]:
        tag("dp-manufacturing", "SubstanceDefinition", sid)
        tag("dp-manufacturing", "Ingredient", "ing-" + sid)
    tag("dp-manufacturing", "MedicinalProductDefinition", "sakura-bloom-20mg")
    tag("dp-manufacturing", "Organization", "aparna-pharm")

    # ================================================================ batches
    G_DSB = ["ds-batch-info", "core"]
    ds_batches = {"B221220": ("2022-12-20", "Production batch (commercial / stability)"), "B221221": ("2022-12-21", "Production batch (commercial / stability)"),
                  "B221222": ("2022-12-22", "Production batch (commercial / stability)"),
                  "B20200117": ("2020-11-17", "Registration stability batch"), "B20200120": ("2020-11-20", "Registration stability batch"), "B20200123": ("2020-11-23", "Registration stability batch")}
    others = [f"B2212{n}" for n in range(15, 31) if f"B2212{n}" not in ds_batches] + ["A221221", "A221222", "A221223"]
    for lot in list(ds_batches) + others:
        date, use = ds_batches.get(lot, (None, None))
        mb = []
        if date:
            mb.append(ext("manufacturingDate", valueDateTime=date))
        if lot.startswith("B2212") and lot in ds_batches:
            mb.append(ext("batchQuantity", valueQuantity=q(350, "kg")))
        if use:
            mb.append(ext("batchUtilization", valueCodeableConcept=cc(use)))
        mb.append(ext("assignedManufacturer", valueReference=ref("Organization", "iroha-corp")))
        body = OrderedDict()
        body["extension"] = [ext(MFGB, extension=mb), ext(SD + "Extension-manufacturing-process-pq", valueReference=ref("PlanDefinition", "ds-manufacturing-process"))]
        body["identifier"] = [{"system": BASE + "/lot-number", "value": lot}]
        body["instance"] = True
        body["status"] = "active"
        body["code"] = {"reference": ref("SubstanceDefinition", "sakuramil", "Sakuramil")}
        if lot.startswith("A"):
            body["description"] = "Drug substance batch used for clinical drug product batches (source not stated)."
        add("Substance", "ds-" + lot.lower(), body, G_DSB)
    tag("ds-batch-info", "SubstanceDefinition", "sakuramil")
    tag("ds-batch-info", "Organization", "iroha-corp")

    dpb = S.page("3.2.DP.C.1 Batch Analysis")
    G_DPB = ["dp-batch-info", "core"]
    dp_batches = [("ABC123", "2022-04", "Production-scale and commercial batch", ["B221215", "B221216"]),
                  ("ABC456", "2022-05", "Production-scale and commercial batch", ["B221217", "B221218", "B221219", "B221220"]),
                  ("ABC789", "2022-06", "Production-scale and commercial batch", ["B221221", "B221222", "B221223"]),
                  ("xyz123", "2021-04", "Clinical", ["A221221", "A221222", "A221223"]),
                  ("xyz456", "2021-05", "Clinical", ["A221221", "A221222", "A221223"]),
                  ("xyz789", "2021-06", "Clinical", ["A221221", "A221222", "A221223"])]
    ISSUES.append("Clinical drug-product batches xyz123/456/789 list a batch size of '2,600,00 tablets' (typo); 2,600,000 tablets was assumed. They all list the same drug-substance batches A221221-A221223 and no DS source.")

    def med(mid, lot, date, use, dsl, pack=None):
        body = OrderedDict()
        codeext = [ext(SD + "Extension-medication-definition-pq", valueReference=ref("MedicinalProductDefinition", "sakura-bloom-20mg"))]
        if pack:
            codeext.append(ext(SD + "Extension-package-definition-pq", valueReference=ref("PackagedProductDefinition", pack)))
        body["code"] = {"extension": codeext, "text": "Sakura Bloom 20 mg film-coated tablets" + ({"pack-hdpe-bottle": " (HDPE bottle)", "pack-pa-al-pvc-blister": " (PA/AL/PVC blister)"}.get(pack, ""))}
        body["status"] = "active"
        body["doseForm"] = cc("Film-coated tablet", EDQM, "10221000", "Film-coated tablet")
        bx = [ext(MFGB, extension=[ext("manufacturingDate", valueDateTime=date), ext("batchQuantity", valueQuantity=q(2600000, "tablets")),
                                    ext("batchUtilization", valueCodeableConcept=cc(use)), ext("assignedManufacturer", valueReference=ref("Organization", "aparna-pharm"))]),
              ext(SD + "Extension-batch-number-of-items-pq", valueQuantity=q(2600000, "tablets")),
              ext(SD + "Extension-manufacturing-process-pq", valueReference=ref("PlanDefinition", "dp-manufacturing-process"))]
        bx += [ext(SD + "Extension-batch-substance-batch-pq", valueReference=ref("Substance", "ds-" + d.lower())) for d in dsl]
        if pack:
            bx.append(ext(SD + "Extension-packaging-site-pq", valueReference=ref("Organization", "aparna-pharm")))
        body["batch"] = {"extension": bx, "lotNumber": lot}
        add("Medication", mid, body, G_DPB if not pack else ["dp-stability", "core"], source=dpb["url"])

    for lot, date, use, dsl in dp_batches:
        med("dp-" + lot.lower(), lot, date, use, dsl)
        for d in dsl:
            tag("dp-batch-info", "Substance", "ds-" + d.lower())
        if lot.startswith("ABC"):
            for pk in ("pack-hdpe-bottle", "pack-pa-al-pvc-blister"):
                med(f"dp-{lot.lower()}-{'bottle' if 'bottle' in pk else 'blister'}", lot, date, use, dsl, pk)
    tag("dp-batch-info", "Organization", "aparna-pharm")
    tag("dp-batch-info", "Organization", "iroha-corp")

    # batch formula
    bf = S.page("2.3.3.DP.M Manufacture - Core")
    add("Medication", "dp-batch-formula-commercial", {
        "code": {"extension": [ext(SD + "Extension-medication-definition-pq", valueReference=ref("MedicinalProductDefinition", "sakura-bloom-20mg"))], "text": "Batch formula - Sakura Bloom 20 mg film-coated tablets (commercial batch)"},
        "status": "active", "doseForm": cc("Film-coated tablet", EDQM, "10221000", "Film-coated tablet"),
        "totalVolume": q(520.000, "kg"),
        "ingredient": [{"item": {"concept": cc(n)}, "isActive": n == "Sakuramil", "strengthRatio": {"numerator": q(v, "kg"), "denominator": q(520.000, "kg")}} for n, v in
                       [("Sakuramil", 52.000), ("Lactose monohydrate", 353.600), ("Cellulose, microcrystalline", 52.000), ("Hydroxypropyl cellulose", 15.600),
                        ("Croscarmellose sodium", 26.000), ("Magnesium stearate", 5.200), ("Basic coating premix, red", 15.600)]] +
                      [{"item": {"concept": cc("Water, purified (q.s., removed during processing)")}, "isActive": False}],
        "batch": {"extension": [ext(MFGB, extension=[ext("batchQuantity", valueQuantity=q(520.000, "kg")), ext("batchUtilization", valueCodeableConcept=cc("Commercial batch formula (theoretical)"))]),
                                ext(SD + "Extension-batch-number-of-items-pq", valueQuantity=q(2600000, "tablets")),
                                ext(SD + "Extension-formulation-number-pq", valueString="Core batch weight 504.400 kg; film-coating 15.600 kg; no overages"),
                                ext(SD + "Extension-manufacturing-process-pq", valueReference=ref("PlanDefinition", "dp-manufacturing-process"))]},
    }, ["batch-formula", "core"], source=bf["url"])

    # ================================================================ DS batch analysis
    dsc32 = S.page("3.2.DS.C Control (Sakuramil) [IROHA-corp]")
    G = ["ds-batch-analysis", "core"]
    tabs = [t for c, t in Source.tables(dsc32["text"]) if t and t[0][0] == "Parameter"]
    rows = tabs[0]
    lots = rows[1][2:]
    cat, lastp = None, None
    per = {l: [] for l in lots}
    for r in rows[2:]:
        p, c, vals = r[0], r[1], r[2:]
        if p and not c and not any(vals):
            cat = p
            continue
        if p:
            lastp = p
        odid = ds_od(cat, p or lastp, c)
        if not odid:
            ISSUES.append(f"DS batch analysis row not mapped: {p} / {c}")
            continue
        for lot, v in zip(lots, vals):
            o = obs(slug(f"obs-ba-{lot}-{odid[14:]}", 64), odid, ref("Substance", "ds-" + lot.lower()), v, ref("Organization", "iroha-corp"), groups=G)
            per[lot].append(o)
    for lot in lots:
        report(f"dr-ba-ds-{lot.lower()}", "Batch Analysis Report", ref("Substance", "ds-" + lot.lower()), per[lot], ref("Organization", "iroha-corp"), G,
               triggered=ref("PlanDefinition", "spec-ds-sakuramil"), conclusion="All tested batches met the predefined acceptance criteria. No out-of-specification results or trends were observed.", source=dsc32["url"])
        tag("ds-batch-analysis", "Substance", "ds-" + lot.lower())
    tag("ds-batch-analysis", "SubstanceDefinition", "sakuramil")
    tag("ds-batch-analysis", "Organization", "iroha-corp")

    # ================================================================ DP batch analysis
    G = ["dp-batch-analysis", "core"]
    rows = [t for c, t in Source.tables(dpb["text"]) if t[0][0] == "Quality characteristic"][0]
    lots = rows[1][2:5]
    mapping = [("Description", "od-dp-description"), ("Identified as", "od-dp-identification-nir"), ("retention time", "od-dp-identification-hplc"),
               ("ultraviolet absorption", "od-dp-identification-uv"), ("200 uncoated", "od-dp-udu-nir"), ("Content Uniformity Test", "od-dp-udu-hplc"),
               ("dissolution model", "od-dp-dissolution-rtrt"), ("NLT 80%", "od-dp-dissolution-uv"), ("Assay by NIR", "od-dp-assay-nir"), ("Assay by HPLC", "od-dp-assay-hplc"),
               ("Specified CP-9-1", "od-dp-degradation-cp-9-1"), ("Any unspecified", "od-dp-degradation-unspecified"), ("Total degradation", "od-dp-degradation-total"),
               ("TAMC", "od-dp-met-tamc"), ("TYMC", "od-dp-met-tymc"), ("Specified micro-organism", "od-dp-met-e-coli")]
    per = {l: [] for l in lots}
    for r in rows[2:]:
        txt = r[0] + " || " + r[1]
        odid = next((o for k, o in mapping if k in txt), None)
        vals = r[2:5]
        if not odid or not any(v.strip() for v in vals):
            continue
        for lot, v in zip(lots, vals):
            o = obs(slug(f"obs-ba-{lot}-{odid[6:]}", 64), odid, ref("Medication", "dp-" + lot.lower()), v, ref("Organization", "dakina-analytica" if "met" not in odid else "kunchen-sa"), groups=G)
            per[lot].append(o)
    ISSUES.append("DP batch analysis Table 2-1 quotes the shelf-life limit for CP-9-1 (NMT 0.5 %) rather than the release limit (NMT 0.3 %); results are linked to the specification test definition, which carries both contexts.")
    ISSUES.append("Testing site for DP batch-analysis results is not stated per test; chemical tests were attributed to Dakina Analytica SA and microbiology to Kunchen SA per the facilities table (assumption).")
    for lot in lots:
        report(f"dr-ba-dp-{lot.lower()}", "Batch Analysis Report", ref("Medication", "dp-" + lot.lower()), per[lot], ref("Organization", "aparna-pharm"), G,
               triggered=ref("PlanDefinition", "spec-dp"), source=dpb["url"])
        tag("dp-batch-analysis", "Medication", "dp-" + lot.lower())
    for d in ["ap-dp-description"]:
        pass
    for o in ["aparna-pharm", "dakina-analytica", "kunchen-sa"]:
        tag("dp-batch-analysis", "Organization", o)
    tag("dp-batch-analysis", "SubstanceDefinition", "sakuramil")
    tag("dp-batch-analysis", "Ingredient", "ing-sakuramil")
    for k in list(R):
        if k.startswith("Observation/obs-ba-") and any(x in k for x in ("abc", "ABC")):
            pass
    # microbiology bundle
    for lot in lots:
        for o in per[lot]:
            if "met" in o:
                tag("dp-microbiology", "Observation", o)
        tag("dp-microbiology", "DiagnosticReport", f"dr-ba-dp-{lot.lower()}")
        tag("dp-microbiology", "Medication", "dp-" + lot.lower())
    tag("dp-microbiology", "MedicinalProductDefinition", "sakura-bloom-20mg")
    tag("dp-microbiology", "Organization", "kunchen-sa")

    build_stability(S)
    build_reference_standards(S)
    build_impurity_studies(S)


# ==================================================================== stability
def build_stability(S):
    G = ["dp-stability", "core"]
    conds = {"25c60": ("25 °C / 60 % RH (long-term)", 25), "30c75": ("30 °C / 75 % RH (long-term, zone IVB)", 30), "40c75": ("40 °C / 75 % RH (accelerated)", 40),
             "xenon-exposed": ("Photostability - xenon, exposed (≥ 1.2 million lux h and 200 W h/m²)", None), "xenon-unexposed": ("Photostability - xenon, unexposed (dark control)", None),
             "initial": ("Initial analysis", None), "lt-unspecified": ("Long-term storage (condition not specified)", None)}
    for k, (t, temp) in conds.items():
        tt = {"preference": "preferred", "type": cc("Sakura Bloom 20 mg film-coated tablets in commercial primary packaging")}
        if temp:
            tt["handling"] = [{"temperatureQualifier": cc(t), "instruction": f"Store at {t}"}]
        else:
            tt["handling"] = [{"instruction": t}]
        add("SpecimenDefinition", f"spd-dp-{k}", {"status": "active", "title": f"DP stability storage condition - {t}", "typeTested": [tt]}, G)
    for k, t, lo, hi in [("30c75", "30 °C ± 2 °C / 75 % RH ± 5 % RH (long-term)", 28, 32), ("40c75", "40 ± 2 °C / 75 ± 5 % RH (accelerated)", 38, 42)]:
        add("SpecimenDefinition", f"spd-ds-{k}", {"status": "active", "title": f"DS stability storage condition - {t}",
            "typeTested": [{"preference": "preferred", "type": cc("Sakuramil drug substance in LDPE bags"),
                            "handling": [{"temperatureQualifier": cc(t), "temperatureRange": {"low": q(lo, "°C"), "high": q(hi, "°C")}, "instruction": f"Store at {t}"}]}]}, ["ds-stability", "core"])

    # test sets
    def testset(aid, title, ods, groups):
        add("ActivityDefinition", aid, {"title": title, "status": "active", "kind": "ObservationRequest" if False else "ServiceRequest",
                                         "observationRequirement": [canon("ObservationDefinition", o) for o in ods]}, groups)
    chem = ["od-dp-assay-hplc", "od-dp-degradation-cp-9-1", "od-dp-degradation-unspecified", "od-dp-degradation-total"]
    phys = ["od-dp-description", "od-dp-dissolution-uv"]
    micro = ["od-dp-met-tamc", "od-dp-met-tymc", "od-dp-met-e-coli"]
    testset("ts-dp-stability-full", "DP stability test set: appearance, dissolution, assay, degradation products", phys + chem, G)
    testset("ts-dp-stability-met", "DP stability test set: microbial enumeration (release, 12, 24, 36 months; 6 months 40/75)", micro, G)
    ds_all = [k.split("/")[1] for k in R if k.startswith("ObservationDefinition/od-ds-sakuramil-") and "particle-size" not in k]
    testset("ts-ds-stability-full", "DS stability test set (full specification excluding PSD)", ds_all, ["ds-stability", "core"])
    testset("ts-ds-post-approval", "DS post-approval stability test set (description, ID IR, ID HPLC, related substances, assay)",
            [o for o in ds_all if any(x in o for x in ("appearance", "-ir", "-hplc", "cp-9-1", "cp-8", "unspecified", "total", "assay"))], ["ds-stability", "core"])

    def protocol(pid, title, subj, desc, plan, groups, source):
        acts = []
        for cond, tps, ts, note in plan:
            sub = []
            for tp, opt in tps:
                a = {"title": f"{tp} months" + (" (optional)" if opt else ""),
                     "timingTiming": {"repeat": {"boundsRange": {"low": q(tp, "months"), "high": q(tp, "months")}}},
                     "definitionCanonical": canon("ActivityDefinition", ts)}
                if opt:
                    a["description"] = "Optional testing if failures or significant changes occur at the next higher storage condition"
                sub.append(a)
            x = {"title": cond, "action": sub}
            if note:
                x["description"] = note
            acts.append(x)
        add("PlanDefinition", pid, {"title": title, "type": cc("Stability Study Protocol", CS_PLAN, "1244588", "Stability Study Protocol"), "status": "active",
                                    "subjectReference": ref(*subj), "description": desc, "action": acts}, groups, source=source)
    bot = S.page("2.3.3.DP.S. Storage - Bottle")["url"]
    allt = [0, 3, 6, 9, 12, 18, 24, 36]
    protocol("stability-protocol-dp-registration", "Registration stability protocol RSP1234-1G - Sakura Bloom 20 mg (HDPE bottle and PA/AL/PVC blister)", ("MedicinalProductDefinition", "sakura-bloom-20mg"),
             "Registration stability studies on three production-scale batches (ABC123, ABC456, ABC789) in commercial packs, updated with 36-month data (report RSR1234 Data-1G).",
             [("25 °C / 60 % RH", [(t, False) for t in [0, 3, 6, 12, 18, 24, 36]], "ts-dp-stability-full", None),
              ("30 °C / 75 % RH", [(t, False) for t in [3, 6, 12, 18, 24, 36]], "ts-dp-stability-full", None),
              ("40 °C / 75 % RH", [(t, False) for t in [3, 6]], "ts-dp-stability-full", None),
              ("Long-term (microbial enumeration)", [(t, False) for t in [0, 12, 24, 36]], "ts-dp-stability-met", "Skip testing at 12, 24 and 36 months and thereafter every 12 months and end of shelf life"),
              ("Photostability (ICH Q1B, xenon)", [(0, False)], "ts-dp-stability-full", "≥ 1.2 million lux h and 200 W h/m²; exposed vs unexposed samples")], G, bot)
    protocol("stability-protocol-dp-post-approval", "Stability protocol for post-approval changes - Sakura Bloom 20 mg", ("MedicinalProductDefinition", "sakura-bloom-20mg"),
             "Table 4 (2.3.3.DP.S.2): minimum long-term conditions for post-approval change studies; number of batches determined case by case.",
             [("25 °C / 60 % RH", [(0, False)] + [(t, True) for t in allt[1:]], "ts-dp-stability-full", None),
              ("30 °C / 65 % RH", [(t, True) for t in allt[1:]], "ts-dp-stability-full", None),
              ("30 °C / 75 % RH", [(t, False) for t in allt[1:]], "ts-dp-stability-full", None),
              ("40 °C / 75 % RH", [(3, False), (6, False)], "ts-dp-stability-full", None)], G, bot)
    protocol("stability-protocol-dp-commitment", "Stability testing plan for commitment batches - Sakura Bloom 20 mg", ("MedicinalProductDefinition", "sakura-bloom-20mg"),
             "Table 5 (2.3.3.DP.S.2): three production-scale commitment batches through the proposed shelf life. MET at release, 6 months 40/75 and 12/36 months long-term.",
             [("25 °C / 60 % RH", [(t, False) for t in allt], "ts-dp-stability-full", None),
              ("30 °C / 65 % RH", [(t, True) for t in allt[1:]], "ts-dp-stability-full", None),
              ("30 °C / 75 % RH", [(t, False) for t in allt[1:]], "ts-dp-stability-full", None),
              ("40 °C / 75 % RH", [(3, False), (6, False)], "ts-dp-stability-full", None),
              ("Microbial enumeration", [(0, False), (12, False), (36, False)], "ts-dp-stability-met", "Also after 6 months at 40 °C/75 % RH")], G, bot)
    dss = S.page("2.3.3.DS.S Storage")["url"]
    protocol("stability-protocol-ds-registration", "Registration stability studies - Sakuramil drug substance", ("SubstanceDefinition", "sakuramil"),
             "Accelerated (40 ± 2 °C / 75 ± 5 % RH; 0, 1, 3, 6 months) and long-term (30 ± 2 °C / 75 ± 5 % RH; 0-36 months) studies on batches B20200117, B20200120, B20200123 in LDPE bags. Re-test period 36 months, storage 15-30 °C.",
             [("40 °C / 75 % RH (accelerated)", [(t, False) for t in [0, 1, 3, 6]], "ts-ds-stability-full", None),
              ("30 °C / 75 % RH (long-term)", [(t, False) for t in allt], "ts-ds-stability-full", None)], ["ds-stability", "core"], S.page("3.2.DS.S Storage")["url"])
    protocol("stability-protocol-ds-post-approval", "Post-approval stability protocol - Sakuramil drug substance", ("SubstanceDefinition", "sakuramil"),
             "At least one production batch per year placed on long-term stability; quality characteristics No.1-5.",
             [("30 °C ± 2 °C / 75 % RH ± 5 % RH (long-term)", [(t, False) for t in [0, 6, 12, 24, 36]], "ts-ds-post-approval", None)], ["ds-stability", "core"], dss)

    # ---------------------------------------------------------------- DP stability data (bottle & blister)
    seen = set()
    for pack, pg in (("bottle", "Bottle (Sakura Bloom) [APM][FCT][20 mg] / 3.2.DP.S.5"), ("blister", "Blister (Sakura Bloom) [APM][FCT][20 mg] / 3.2.DP.S.5")):
        page = [p for p in S.pages if pg in p["short"]][0]
        reports = {}
        for cap, rows in Source.tables(page["text"]):
            capl = (cap or "").lower()
            if capl.startswith("table 2-1"):
                cols = chem; mode = "series"
            elif capl.startswith("table 2-2"):
                cols = phys; mode = "series"
            elif capl.startswith("table 3-7"):
                mode = "micro"
            elif re.match(r"table 3-\d (chemical|physical)", capl):
                mode = "photo"
                cols = chem if "chemical" in capl else phys
                photolot = re.search(r"batch (\w+)", capl).group(1).upper()
            else:
                continue
            lot, cond = None, None
            for r in rows:
                if mode == "series":
                    m = re.search(r"(ABC\d+)", r[0])
                    if m:
                        lot = m.group(1)
                    lab = r[1].strip()
                    vals = r[2:2 + len(cols)]
                    if lot and not lab and not any(v.strip() for v in vals) and cond == "initial":
                        cond = "25c60"
                        ISSUES.append(f"DP stability ({pack}, {cap[:12]}): storage-condition heading missing for {lot} after the initial result (blank row); assumed 25 °C/60 % RH by analogy with the other tables.")
                        continue
                    if not lot or lab.lower().startswith("storage"):
                        continue
                    if "initial" in lab.lower():
                        cond, tp = "initial", 0
                    elif "°c" in lab.lower():
                        cond = {"25": "25c60", "30": "30c75", "40": "40c75"}[re.search(r"(\d\d)\s*°", lab).group(1)]
                        continue
                    else:
                        mt = re.match(r"(\d+)\s*month", lab)
                        if not mt:
                            continue
                        tp = int(mt.group(1))
                        if cond == "initial":
                            ISSUES.append(f"DP stability ({pack}, {cap[:12]}): row '{lab}' for {lot} appears before any storage-condition heading; skipped.")
                            continue
                elif mode == "micro":
                    if r[1].strip() and re.match(r"ABC\d+", r[1].strip()):
                        lot = r[1].strip()
                    lab = r[2].strip()
                    if not lot or not lab or lab.startswith("Storage"):
                        continue
                    tp = 0 if "initial" in lab.lower() else int(re.match(r"(\d+)", lab).group(1))
                    cond = "initial" if tp == 0 else "lt-unspecified"
                    cols, vals = micro, r[3:6]
                else:  # photo
                    cells = [c for c in r if c.strip()]
                    labi = next((i for i, c in enumerate(r) if any(k in c.lower() for k in ("initial", "xenon"))), None)
                    if labi is None:
                        continue
                    lab = r[labi].lower()
                    cond = "initial" if "initial" in lab else ("xenon-unexposed" if "unexposed" in lab else "xenon-exposed")
                    tp = 0
                    lot = photolot
                    vals = r[labi + 1: labi + 1 + len(cols)]
                    if cols is phys and len(vals) >= 3:  # appearance, average, [min,max]
                        vals = [vals[0], f"{vals[1]} (6) [{vals[2]}]"]
                    if "photo" not in cond and cond != "initial":
                        pass
                    if cond == "initial":
                        cond = "photo-initial"
                key_ = (pack, lot, cond, tp, tuple(cols))
                if key_ in seen:
                    ISSUES.append(f"DP stability ({pack}): duplicate row for {lot} {cond} {tp} months in '{(cap or '')[:40]}'; first occurrence kept.")
                    continue
                seen.add(key_)
                cid = cond if cond != "photo-initial" else "initial"
                spid = slug(f"spc-{lot}-{pack}-{cond}-{tp}m", 64)
                if f"Specimen/{spid}" not in R:
                    sp = {"identifier": [{"system": BASE + "/stability-sample", "value": spid}],
                          "status": "available", "type": cc(f"Sakura Bloom 20 mg film-coated tablets, {'HDPE bottle' if pack == 'bottle' else 'PA/AL/PVC blister'}"),
                          "processing": [{"description": f"Stored at {conds[cid][0]}" + (f" for {tp} months" if tp else ""),
                                          "timePeriod": {"extension": [ext(SD + "Extension-batch-storage-duration-pq", valueDuration={"value": tp, "unit": "months", "system": UCUM, "code": "mo"})]}}]}
                    add("Specimen", spid, sp, G)
                subj = ref("Medication", f"dp-{lot.lower()}-{pack}")
                for od_id, v in zip(cols, vals):
                    if not v.strip() or v.strip() in ("-",):
                        continue
                    o = obs(slug(f"obs-st-{lot}-{pack}-{cond}-{tp}-{od_id[6:]}", 64), od_id, subj, v.replace("¹", ""), ref("Organization", "aparna-pharm"), [ref("Specimen", spid)], G,
                            triggered=ref("PlanDefinition", "stability-protocol-dp-registration"))
                    if o:
                        reports.setdefault((lot, cond if cond != "photo-initial" else "xenon-exposed" if False else cond), []).append((o, spid))
        for (lot, cond), items in reports.items():
            rid = slug(f"dr-st-dp-{lot}-{pack}-{cond}", 64)
            cid = "initial" if cond == "photo-initial" else cond
            report(rid, "Stability Study Report", ref("Medication", f"dp-{lot.lower()}-{pack}"), [o for o, _ in items], ref("Organization", "aparna-pharm"), G,
                   triggered=ref("PlanDefinition", "stability-protocol-dp-registration"), category=conds[cid][0] + (" (photostability study)" if cond.startswith("photo") or "xenon" in cond else ""),
                   specimen=[ref("Specimen", s) for s in dict.fromkeys(s for _, s in items)],
                   conclusion="Registration stability report RSR1234 Data-1G (36-month update)." if cond not in ("lt-unspecified",) else "Microbial enumeration test; long-term storage condition not specified in source.",
                   source=page["url"])
    ISSUES.append("DP photostability tables for ABC456 / ABC789 label the batches 'AB4563' / 'AB7893'; mapped to ABC456 / ABC789 based on table captions.")
    ISSUES.append("DP microbial enumeration stability tables (3-7) do not state the long-term storage condition; specimens were created with condition 'long-term (not specified)'.")
    for o in ["aparna-pharm"]:
        tag("dp-stability", "Organization", o)
    tag("dp-stability", "MedicinalProductDefinition", "sakura-bloom-20mg")
    tag("dp-stability", "SubstanceDefinition", "sakuramil")
    tag("dp-stability", "Ingredient", "ing-sakuramil")
    for lot, dsl in (("ABC123", ["B221215", "B221216"]), ("ABC456", ["B221217", "B221218", "B221219", "B221220"]), ("ABC789", ["B221221", "B221222", "B221223"])):
        for d in dsl:
            tag("dp-stability", "Substance", "ds-" + d.lower())
    for k in list(R):
        if k.startswith("ObservationDefinition/od-dp-"):
            tag("dp-stability", "ObservationDefinition", k.split("/")[1])

    # ---------------------------------------------------------------- DS stability data
    G = ["ds-stability", "core"]
    page = S.page("3.2.DS.S Storage")
    for cap, rows in Source.tables(page["text"]):
        if not rows or rows[0][0] != "Parameter":
            continue
        mcap = re.search(r"batch no\. (B\d+).*?Storage conditions: ([^/]+)", cap or "")
        if not mcap:
            continue
        lot = mcap.group(1)
        cond = "40c75" if "40" in mcap.group(2) else "30c75"
        tps = [int(x) for x in rows[1][2:] if x.strip().isdigit()]
        cat = None
        per = []
        for r in rows[2:]:
            p, c, vals = r[0].strip(), r[1].strip(), r[2:]
            if p and not c and not any(v.strip() for v in vals):
                cat = p
                continue
            odid = ds_od(cat, p, c)
            if not odid:
                ISSUES.append(f"DS stability row not mapped: {p}")
                continue
            for tp, v in zip(tps, vals):
                spid = f"spc-ds-{lot.lower()}-{cond}-{tp}m"
                if f"Specimen/{spid}" not in R:
                    add("Specimen", spid, {"identifier": [{"system": BASE + "/stability-sample", "value": spid}], "status": "available",
                        "type": cc("Sakuramil drug substance (LDPE bag)"), "subject": ref("Substance", "ds-" + lot.lower()),
                        "processing": [{"description": f"Stored at {'40 ± 2 °C / 75 ± 5 % RH' if cond == '40c75' else '30 ± 2 °C / 75 ± 5 % RH'}" + (f" for {tp} months" if tp else " (initial)"),
                                        "timePeriod": {"extension": [ext(SD + "Extension-batch-storage-duration-pq", valueDuration={"value": tp, "unit": "months", "system": UCUM, "code": "mo"})]}}]}, G)
                o = obs(slug(f"obs-st-{lot}-{cond}-{tp}-{odid[14:]}", 64), odid, ref("Substance", "ds-" + lot.lower()), v, ref("Organization", "iroha-corp"), [ref("Specimen", spid)], G,
                        triggered=ref("PlanDefinition", "stability-protocol-ds-registration"))
                if o:
                    per.append((o, spid))
        report(f"dr-st-ds-{lot.lower()}-{cond}", "Stability Study Report", ref("Substance", "ds-" + lot.lower()), [o for o, _ in per], ref("Organization", "iroha-corp"), G,
               triggered=ref("PlanDefinition", "stability-protocol-ds-registration"), category="Accelerated 40 ± 2 °C / 75 ± 5 % RH" if cond == "40c75" else "Long-term 30 ± 2 °C / 75 ± 5 % RH",
               specimen=[ref("Specimen", s) for s in dict.fromkeys(s for _, s in per)], source=page["url"])
        tag("ds-stability", "Substance", "ds-" + lot.lower())
    tag("ds-stability", "SubstanceDefinition", "sakuramil")
    tag("ds-stability", "Organization", "iroha-corp")


# ==================================================================== reference standards / characterization
def build_reference_standards(S):
    G = ["reference-standards", "core"]
    for sid, lot, sd, desc in [("rs-cp-9-primary-working-standard", "SAKU_20220114", "sakuramil", "CP-9 primary (working) reference standard: laboratory-scale batch SAKU_20220114 of Sakuramil, controlled in line with the drug substance specification."),
                               ("rs-cp-9-identification-standard", None, "sakuramil", "CP-9 identification standard: selected batch of Sakuramil spiked with impurities CP-9-1 and CP-8; prepared in-house."),
                               ("rs-cp-6-standard", None, "cp-6", "CP-6 standard, prepared in-house; controlled per the CP-6 intermediate specification."),
                               ("rs-cp-7-standard", None, "cp-7", "CP-7 standard, prepared in-house; controlled per the CP-7 intermediate specification."),
                               ("rs-usp-methylene-chloride", None, None, "USP Residual Solvent Class 2 - Methylene chloride RS (pharmacopeial material)"),
                               ("rs-usp-alcohol", None, None, "USP Alcohol Determination - Alcohol RS (pharmacopeial material)")]:
        body = OrderedDict()
        body["identifier"] = [{"system": BASE + "/reference-standard", "value": lot or sid}]
        body["instance"] = True
        body["status"] = "active"
        body["category"] = [cc("Reference standard")]
        body["code"] = {"reference": ref("SubstanceDefinition", sd)} if sd else {"concept": cc(desc.split(" (")[0])}
        body["description"] = desc
        add("Substance", sid, body, G, source=S.page("2.3.3.RS Reference Standards")["url"])
    pg = [("rs-cp-9-primary-working-standard", "sakuramil", "3.2.RS.C Control (CP-9 working standard)"),
          ("rs-cp-9-identification-standard", "cp-9-1", "3.2.RS.C Control (CP-9 identification standard)"),
          ("rs-cp-6-standard", "cp-6", "3.2.RS.C Control (CP-6 standard)")]
    make_spec("char-protocol-reference-standards", "Elucidation of structure of reference standards (MS, 1H NMR, 13C NMR)", ("SubstanceDefinition", "sakuramil"), [
        dict(id="od-char-ms-mz", name="Mass spectrometry (ESI) m/z", cat="Elucidation of structure", crit="Observed m/z consistent with predicted value", method="LC-IT-TOF MS, ESI"),
        dict(id="od-char-1h-nmr-signal", name="1H NMR signal assignment", cat="Elucidation of structure", crit="Spectrum consistent with proposed structure", method="1H NMR 500 MHz, D2O", code="NMR-H"),
        dict(id="od-char-13c-nmr-signal", name="13C NMR signal assignment", cat="Elucidation of structure", crit="Spectrum consistent with proposed structure", method="13C NMR 500 MHz, D2O", code="NMR-C")],
        ["reference-standards", "ds-characterization", "core"], ptype=("elucidation-of-structure", "Elucidation of Structure"), default_group="Characterization")
    for rsid, sd, title in pg:
        page = S.page(title)
        t = page["text"]
        res = []
        subj = ref("Substance", rsid)
        for mi, m in enumerate(re.finditer(r"m/z value of sample of ([\d.]+)\. The predicted m/z value of neutral charged ([\w\- ]+?) is (\d+(?:\.\d+)?)", t)):
            o = obs(slug(f"obs-char-{rsid[3:]}-ms-{mi+1}", 64), "od-char-ms-mz", subj, m.group(1), ref("Organization", "iroha-corp"), groups=G,
                    note=f"Predicted m/z for {m.group(2).strip()}: {m.group(3)}")
            R["Observation/" + o]["valueQuantity"] = {"value": float(m.group(1)), "unit": "m/z", "system": UCUM, "code": "{m/z}"}
            R["Observation/" + o]["component"] = [{"code": cc("Predicted m/z"), "valueQuantity": {"value": float(m.group(3)), "unit": "m/z", "system": UCUM, "code": "{m/z}"}}]
            res.append(o)
        for ti, (cap, rows) in enumerate(Source.tables(t)):
            if not rows or not rows[0][0].startswith("Chemical shift"):
                continue
            nuc = "13c" if "Carbons" in rows[0][1] else "1h"
            for i, r in enumerate(rows[1:]):
                shift = r[0]
                m = re.match(r"([\d.]+)(?:-([\d.]+))?", shift)
                o = obs(slug(f"obs-char-{rsid[3:]}-t{ti}-{nuc}-{i+1}", 64), f"od-char-{nuc}-nmr-signal", subj, f"δ {shift} ppm; {r[1]}; {r[2]}; {r[3]}", ref("Organization", "iroha-corp"), groups=G)
                comps = [{"code": cc("Chemical shift (δ)"), "valueQuantity": {"value": float(m.group(1)), "unit": "ppm", "system": UCUM, "code": "[ppm]"}}]
                if m.group(2):
                    comps[0]["code"] = cc("Chemical shift (δ, upper)")
                    comps.insert(0, {"code": cc("Chemical shift (δ, lower)"), "valueQuantity": {"value": float(m.group(2)), "unit": "ppm", "system": UCUM, "code": "[ppm]"}})
                comps += [{"code": cc("Number of nuclei"), "valueString": r[1]}, {"code": cc("Multiplicity"), "valueString": r[2]}, {"code": cc("Assignment"), "valueString": r[3]}]
                R["Observation/" + o]["component"] = comps
                res.append(o)
        report(f"dr-char-{rsid[3:]}", "Characterization Report", subj, res, ref("Organization", "iroha-corp"), G,
               triggered=ref("PlanDefinition", "char-protocol-reference-standards"), conclusion=f"Structure of {title.split('(')[1].split(')')[0]} confirmed by MS and NMR.", source=page["url"])
        tag("ds-characterization", "DiagnosticReport", f"dr-char-{rsid[3:]}")
        tag("ds-characterization", "Substance", rsid)
        for o in res:
            tag("ds-characterization", "Observation", o)
        tag("reference-standards", "SubstanceDefinition", sd)
    tag("reference-standards", "SubstanceDefinition", "cp-7")
    tag("reference-standards", "Organization", "iroha-corp")
    tag("ds-characterization", "Organization", "iroha-corp")
    for k in ["od-char-ms-mz", "od-char-1h-nmr-signal", "od-char-13c-nmr-signal"]:
        tag("ds-characterization", "ObservationDefinition", k)
    tag("ds-characterization", "PlanDefinition", "char-protocol-reference-standards")


# ==================================================================== impurity studies
def build_impurity_studies(S):
    G = ["impurities", "core"]
    rsp = S.page("Residual solvents carry over study reports")
    sol = [("Ethanol", 3, 5000, 500), ("Methanol", 2, 3000, 300), ("n-Hexane", 2, 290, 29), ("Tetrahydrofuran", 2, 720, 72), ("Benzene", 1, 2, 0.2), ("Toluene", 2, 890, 89)]
    make_spec("study-residual-solvent-carryover", "Carry-over study of unspecified residual solvents in Sakuramil (ICH Q3C)", ("SubstanceDefinition", "sakuramil"),
              [dict(id=f"od-carryover-{slug(n)}", name=f"Residual solvent {n} (ICH Q3C class {c})", cat="Residual solvents", crit=f"NMT {lim} ppm", unit="ppm",
                    desc=f"LOQ {loq} ppm", method="GC", ap="ap-residual-solvents") for n, c, lim, loq in sol] +
              [dict(id="od-carryover-residue-on-ignition", name="Residue on ignition", cat="Residue on ignition", crit="NMT 0.2 %", unit="%", method="USP <281>")],
              G, rsp["url"], ptype=("1244577", "Specification Protocol"), default_group="Carry-over study")
    for lot in ["B221228", "B221229", "B221230"]:
        res = [obs(f"obs-co-{lot.lower()}-{slug(n)}", f"od-carryover-{slug(n)}", ref("Substance", "ds-" + lot.lower()), "< LOQ", ref("Organization", "iroha-corp"), groups=G) for n, *_ in sol]
        res.append(obs(f"obs-co-{lot.lower()}-roi", "od-carryover-residue-on-ignition", ref("Substance", "ds-" + lot.lower()), "< 0.01 %", ref("Organization", "iroha-corp"), groups=G))
        report(f"dr-carryover-{lot.lower()}", "Impurities Report", ref("Substance", "ds-" + lot.lower()), res, ref("Organization", "iroha-corp"), G,
               triggered=ref("PlanDefinition", "study-residual-solvent-carryover"), conclusion="All unspecified residual solvents < LOQ; justifies omission from the drug substance specification.", source=rsp["url"])
        tag("impurities", "Substance", "ds-" + lot.lower())
    el = S.page("Elemental risk assessment")
    elems = []
    for cap, rows in Source.tables(el["text"]):
        if not rows or not rows[0][0].startswith("Sakuramil Batch"):
            continue
        hdr = rows[1][1:]
        loq = next(r for r in rows if r[0] == "LOQ")[1:]
        lim = next(r for r in rows if r[0].startswith("ICH Q3D"))[1:]
        klass = rows[0][1]
        for i, h in enumerate(hdr):
            m = re.match(r"(\w+),?\s*(.*)", h.strip())
            e, unit = m.group(1), (m.group(2) or "µg/g").strip()
            if unit != "µg/g":
                ISSUES.append(f"Elemental impurities: unit for {e} given as '{unit}' (likely a typo for µg/g); value copied as stated.")
            elems.append((e, unit, loq[i], lim[i].replace("*", "").strip(), klass))
            for r in rows[2:]:
                if not re.match(r"B\d+", r[0]):
                    continue
                tag("impurities", "Substance", "ds-" + r[0].lower())
    for e, unit, loq, lim, klass in elems:
        make_od(f"od-elemental-{e.lower()}", dict(name=f"Elemental impurity {e} (ICP-MS)", cat="Elemental impurities", crit=f"ICH Q3D oral limit {lim} {unit}",
                range={"high": {"value": float(lim), "unit": unit, **({"system": UCUM, "code": "ug/g"} if unit == "µg/g" else {})}}, desc=f"{klass}; LOQ {loq} {unit}", method="ICP-MS"), el["url"], G)
    add("PlanDefinition", "study-elemental-impurities", {"title": "ICH Q3D elemental impurities screening of Sakuramil drug substance (ICP-MS)",
        "type": cc("Specification Protocol", CS_PLAN, "1244577", "Specification Protocol"), "status": "active", "subjectReference": ref("SubstanceDefinition", "sakuramil"),
        "description": "Risk assessment per ICH Q3D: Class 1, 2A, 2B (Pd), 3 (Li) and other elements (Mg, B) screened in 12 batches.",
        "action": [{"title": "Elemental screening", "action": [{"title": f"{e}", "definitionCanonical": canon("ObservationDefinition", f"od-elemental-{e.lower()}")} for e, *_ in elems]}]}, G, source=el["url"])
    batches = {}
    for cap, rows in Source.tables(el["text"]):
        if not rows or not rows[0][0].startswith("Sakuramil Batch"):
            continue
        hdr = [re.match(r"(\w+)", h.strip()).group(1) for h in rows[1][1:]]
        for r in rows[2:]:
            if re.match(r"B\d+", r[0]):
                for e, v in zip(hdr, r[1:]):
                    batches.setdefault(r[0], []).append(obs(f"obs-el-{r[0].lower()}-{e.lower()}", f"od-elemental-{e.lower()}", ref("Substance", "ds-" + r[0].lower()), v, ref("Organization", "iroha-corp"), groups=G))
    for lot, res in batches.items():
        report(f"dr-elemental-{lot.lower()}", "Impurities Report", ref("Substance", "ds-" + lot.lower()), res, ref("Organization", "iroha-corp"), G,
               triggered=ref("PlanDefinition", "study-elemental-impurities"), conclusion="All elemental impurities below LOQ.", source=el["url"])
    ISSUES.append("Elemental impurity result tables list B221215-B221220 and B221223-B221228 (B221221/B221222 are absent) - recorded as stated.")
    docref("doc-ich-m7-risk-assessment", "ICH M7 risk assessment of potentially mutagenic impurities (3.2.DS.C)", S.page("ICH M7 Risk Assessment")["url"], G, dtype=False)
    docref("doc-nitrosamine-risk-assessment", "Nitrosamine risk assessment (3.2.DS.C)", S.page("Nitrosamine Risk Assessment")["url"], G, dtype=False)
    tag("impurities", "Organization", "iroha-corp")
    tag("impurities", "MedicinalProductDefinition", "sakura-bloom-20mg")
