"""Organizations, substances, product, ingredients, packaging."""
from lib import *

CS_SUBPROP = PQ + "/CodeSystem/cs-substance-property-pq-example"
CS_NAMETYPE = PQ + "/CodeSystem/cs-productNameType-pq-example"
CS_INGFUNC = "http://terminology.hl7.org/CodeSystem/ingredient-function"
CS_INGROLE = "http://hl7.org/fhir/ingredient-role"
DUNS = "urn:oid:1.3.6.1.4.1.519.1"
FEI = "urn:oid:2.16.840.1.113883.4.82"
LOCALORG = BASE + "/organization-id"


def build(S):
    fa = S.page("2.3.3.FA Facilities").get("url")
    fa_us = S.page("2.3.3.FA Facilities_USA").get("url")

    # ------------------------------------------------------------ organizations
    orgs = [
        ("sakura-pharma", "Sakura Pharmaceuticals Company, LTD", None, None, None, None, None,
         [("", "Applicant / owner of the drug substance technology (from 2.3.2.2)")], None),
        ("iroha-corp", "IROHA-corp.", "3002363512", "3002867083", ["Jiangkou R&D Park, No.10867"], "Huangyan", "CN",
         [("drug-substance-manufacture", "Drug Substance Manufacture"), ("analytical-testing-release", "Analytical Testing - Release"),
          ("analytical-testing-stability", "Analytical Testing - Stability"), ("storage", "Storage")],
         "DMF holder; manufacture of intermediates CP-6/CP-7 and drug substance Sakuramil; QC (IPC and release); stability testing; storage of packaged drug substance. Also manufacturer of starting materials CP-4 and CP-8."),
        ("aparna-pharm", "Aparna Pharmaceutical Manufacturing Pte. Ltd.", "489236805", "489236805", ["10 Green Road"], "Gulshan", "BD",
         [("drug-product-manufacture", "Drug Product Manufacture"), ("analytical-testing-release", "Analytical Testing - Release"),
          ("analytical-testing-stability", "Analytical Testing - Stability"), ("packaging", "Packaging")],
         "Manufacture of the drug product; in-process control testing; analytical testing of drug product and excipients; stability testing; primary and secondary packaging."),
        ("kunchen-sa", "Kunchen SA", "415714629", "415714629", ["Mangelsfeld"], "Bad Bocklet-Großenbach", "DE",
         [("analytical-testing-release", "Analytical Testing - Release")], "Analytical testing of the drug product (microbiological testing only)."),
        ("dakina-analytica", "Dakina Analytica SA", "487977499", "487977499", ["Via Nociola"], "Locarno", "CH",
         [("analytical-testing-release", "Analytical Testing - Release")], "Analytical testing of the drug product (all tests except microbiological testing)."),
        ("pack-alpha", "Pack Alpha Group", "484672803", "484672803", ["Pfeffingerstrasse 42"], "Reinach BL", "CH",
         [("primary-packaging", "Primary Packaging"), ("secondary-packaging", "Secondary Packaging"), ("analytical-testing-stability", "Analytical Testing - Stability")],
         "Primary and secondary packaging of the drug product; stability (per 2.3.3.FA Table 1-2)."),
        ("cocopharma", "Cocopharma AG", "494124732", "494124732", ["Strasse 3"], "Pratteln", "CH",
         [("primary-packaging", "Primary Packaging")], "Primary packaging of the drug product."),
        ("leukocare-science", "Leukocare Science", None, "3002867098", ["123 Roarstreet"], "Kingston", "US",
         [("", "Development laboratory")], "Development laboratory used for characterization study (US addendum)."),
        ("warehouse-yaohai", "Warehouse Yaohai", None, "3002867099", ["No.88 Dayu Road"], "Hefei", "CN",
         [("storage", "Storage")], "Alternative warehouse used for packaged final drug substance (US addendum)."),
        ("heto-corp", "HETO-corp.", None, None, ["Wilfand-Straße 56"], "Hilfing", "DE",
         [("", "Starting material manufacturer")], "Manufacturer of starting material CP-4."),
        ("abcr-gmbh", "abcr GmbH", None, None, ["Im Schlehert 10"], "Karlsruhe", "DE",
         [("", "Starting material manufacturer")], "Manufacturer of starting material CP-8."),
    ]
    postal = {"iroha-corp": "250105", "kunchen-sa": "97708", "dakina-analytica": "6600", "pack-alpha": "4153",
              "cocopharma": "4133", "leukocare-science": "12401", "warehouse-yaohai": "250105", "heto-corp": "36865", "abcr-gmbh": "76187"}
    for oid, name, duns, fei, line, city, country, types, desc in orgs:
        ids = []
        if duns:
            ids.append({"system": DUNS, "value": duns})
        if fei:
            ids.append({"system": FEI, "value": fei})
        if not ids:
            ids.append({"system": LOCALORG, "value": oid})
        body = {"identifier": ids, "active": True,
                "type": [cc(t, CS_ORGTYPE if c else None, c or None, t if c else None) for c, t in types],
                "name": name}
        if desc:
            body["description"] = desc
        if line:
            addr = {"use": "work", "type": "physical", "line": line, "city": city, "country": country}
            if oid in postal:
                addr["postalCode"] = postal[oid]
            if oid == "leukocare-science":
                addr["state"] = "NY"
            body["contact"] = [{"address": addr}]
        add("Organization", oid, body, ["organizations"], source=fa_us if oid in ("leukocare-science", "warehouse-yaohai") else fa)

    # ------------------------------------------------------------ drug substance
    dsd = S.page("2.3.3.DS.D Description")
    props = [
        ("appearance", "Appearance", cc("White solid")),
        ("solubility-water", "Solubility purified water", q(0.05, "mg/mL")),
        (None, "Solubility in ethanol (RT)", q(45, "mg/mL")),
        (None, "Solubility in acetone (RT)", q(71.3, "mg/mL")),
    ]
    sd_props = []
    for code, label, val in props:
        p = {"type": cc(label, CS_SUBPROP if code else None, code, label if code else None)}
        p["valueQuantity" if "value" in val and "text" not in val else "valueCodeableConcept"] = val
        sd_props.append(p)
    for medium, ph, v, comp in [("Deionized water", None, 0.05, None), ("0.1 N HCl", 1.2, 0.01, "<"),
                                ("Acetate buffer", 4.5, 5.0, None), ("Phosphate buffer", 6.8, 3.2, None), ("0.1 N NaOH", 8.0, 5.1, None)]:
        p = {"type": cc(f"Aqueous solubility as a function of pH (RT) - {medium}"), "valueQuantity": q(v, "mg/mL", comp)}
        if ph is not None:
            p["extension"] = [ext(SD + "Extension-substance-property-parameter-pq", extension=[
                ext("parameter", valueCoding={"system": CS_SUBPROP, "code": "pH", "display": "pH"}),
                ext("value", valueQuantity={"value": ph, "unit": "pH", "system": UCUM, "code": "[pH]"})])]
        sd_props.append(p)
    sd_props += [
        {"type": cc("pH", CS_SUBPROP, "pH", "pH"), "extension": [ext(SD + "Extension-substance-property-range-pq",
            valueRange={"low": {"value": 5.0, "unit": "pH", "system": UCUM, "code": "[pH]"}, "high": {"value": 9.0, "unit": "pH", "system": UCUM, "code": "[pH]"}})],
         "valueCodeableConcept": cc("5.0 - 9.0 (RT)")},
        {"type": cc("pKa (carboxylate)"), "valueQuantity": {"value": 12.6}},
        {"type": cc("pKa (phenol CF3)"), "valueQuantity": {"value": 15.3}},
        {"type": cc("pKa (carbamate)"), "valueQuantity": {"value": 24.2}},
        {"type": cc("Partition coefficient (log P, n-octanol/water)"), "valueQuantity": {"value": 6.3}},
        {"type": cc("Hygroscopy", CS_SUBPROP, "hygroscopy", "Hygroscopy"), "valueCodeableConcept": cc("Not hygroscopic")},
        {"type": cc("Melting point"), "valueQuantity": q(174, "°C")},
        {"type": cc("Polymorphism"), "valueCodeableConcept": cc("Only one polymorph observed in synthetic manufacture and extensive polymorph screening")},
        {"type": cc("Chirality"), "valueCodeableConcept": cc("Two chiral centres; no racemization observed in the manufacturing process")},
        {"type": cc("Isomerism"), "valueCodeableConcept": cc("An enantiomer and two diastereomers can be formed")},
        {"type": cc("Specific optical rotation (20 °C, aqueous solution)"), "valueQuantity": {"value": 145, "unit": "deg", "system": UCUM, "code": "deg"}},
        {"type": cc("Particle size distribution d(0.1) (laser diffraction)"), "valueQuantity": q(26, "nm")},
        {"type": cc("Particle size distribution d(0.5) (laser diffraction)"), "valueQuantity": q(40, "nm")},
        {"type": cc("Particle size distribution d(0.9) (laser diffraction)"), "valueQuantity": q(66, "nm")},
        {"type": cc("Light sensitivity"), "valueCodeableConcept": cc("Not sensitive to light")},
        {"type": cc("Biopharmaceutics Classification System"), "valueCodeableConcept": cc("BCS Class II (poorly soluble, highly permeable)")},
    ]
    add("SubstanceDefinition", "sakuramil", {
        "identifier": [{"system": "http://cas.org", "value": "262352-13-6"}],
        "status": cc("Active", "http://hl7.org/fhir/publication-status", "active", "Active"),
        "classification": [cc("Chemical (small molecule)")],
        "grade": [cc("In-house")],
        "description": "Sakuramil (company code CP-9), the drug substance of Sakura Bloom 20 mg film-coated tablets.",
        "manufacturer": [dict(ref("Organization", "iroha-corp", "IROHA-corp."), extension=[
            ext(SD + "Extension-site-utilization-pq", valueCoding={"system": CS_SITEUTIL, "code": "Primary manufacturing", "display": "Primary Manufacturing"})])],
        "characterization": [{"technique": cc("Mass spectrometry (ESI positive, Shimadzu LCM-IT-TOF)"), "description": "m/z 614.504 observed (predicted 614.505) on CP-9 primary working standard"},
                             {"technique": cc("1H NMR (Bruker 500 MHz, D2O)")}, {"technique": cc("13C NMR (Bruker 500 MHz, D2O)")}],
        "property": sd_props,
        "molecularWeight": [{"type": cc("Exact/average (free base)"), "amount": q(614.5, "g/mol")}],
        "structure": {"stereochemistry": cc("(2S,4S)"), "molecularFormula": "C27H27F9N2O4",
                      "representation": [{"type": cc("IUPAC name"), "representation": "Propan-2-yl (2S,4S)-4-[acetyl-[[3,5-bis(trifluoromethyl)phenyl]methyl]amino]-2-methoxy-2-methyl-6-(trifluoromethyl)-3,4-dihydroquinoline-1-carboxylate"}]},
        "code": [{"code": cc("262352-13-6", "http://cas.org", "262352-13-6")}, {"code": cc("CP-9")}],
        "name": [{"name": "Sakuramil", "type": cc("INN"), "preferred": True},
                 {"name": "Sakuramil", "type": cc("USAN")},
                 {"name": "Propan-2-yl (2S,4S)-4-[acetyl-[[3,5-bis(trifluoromethyl)phenyl]methyl]amino]-2-methoxy-2-methyl-6-(trifluoromethyl)-3,4-dihydroquinoline-1-carboxylate", "type": cc("IUPAC chemical name")},
                 {"name": "CP-9", "type": cc("Company code")}],
    }, ["ds-general-properties", "ds-characterization", "core"], source=dsd["url"])

    # ------------------------------------------------------------ related materials / impurities
    mats = [
        # id, name, formula, mw, iupac, cas, role
        ("cp-9-1", "CP-9-1", "C28H29F9N2O4", 628.52, "Propan-2-yl (2S,4S)-4-[acetyl-[[3,5-bis(trifluoromethyl)phenyl]methyl]amino]-2-ethoxy-2-methyl-6-(trifluoromethyl)-3,4-dihydroquinoline-1-carboxylate", None, "Specified impurity / degradation product (ethyl homolog of Sakuramil)"),
        ("cp-8", "CP-8", "C9H3BrF6", 307.03, "3,5-bis(trifluoromethyl)benzyl bromide", "32247-96-4", "Starting material (SM2); specified impurity in drug substance"),
        ("cp-6", "CP-6", "C15H19F3N2O2", 316.32, "Methyl (2R, 4S)-2-propyl-6-(trifluoromethyl)-1,2,3,4-tetrahydroquinoline-4-ylcarbamate", None, "Isolated intermediate (IM1); potentially mutagenic impurity"),
        ("cp-7", "CP-7", "C18H22F3N2O4", 387.38, "Ethyl (2R,4S)-2-propyl-4-(methoxycarbonylamino)-6-(trifluoromethyl)-3,4-dihydroxyquinoline-1(2H)-Carboxylate", None, "Isolated intermediate (IM2)"),
        ("cp-4", "CP-4", "C13H17F3N2O", 274.28, "(3R)-3-{[4-(Trifluoromethyl)phenyl]amino}hexanamide", None, "Starting material (SM1); potentially mutagenic"),
        ("cp-5", "CP-5", None, None, None, None, "In situ (non-isolated) intermediate; aniline structural alert"),
        ("cp-3", "CP-3", None, None, None, None, "Precursor intermediate of CP-4 (non-isolated); aniline structural alert; specified impurity in CP-4"),
        ("cp-7-1", "CP-7-1", None, None, None, None, "Ethyl homolog in CP-7; precursor of CP-9-1"),
        ("cp-8-25i", "CP-8-25I", None, None, None, None, "Specified impurity of starting material CP-8"),
        ("cp-8-24i", "CP-8-24I", None, None, None, None, "Specified impurity of starting material CP-8"),
    ]
    for mid, name, formula, mw, iupac, cas, role in mats:
        body = {"status": cc("Active", "http://hl7.org/fhir/publication-status", "active", "Active"),
                "classification": [cc(role)], "description": role}
        if mw:
            body["molecularWeight"] = [{"amount": q(mw, "g/mol")}]
        if formula or iupac:
            body["structure"] = {}
            if formula:
                body["structure"]["molecularFormula"] = formula
            if iupac:
                body["structure"]["representation"] = [{"type": cc("IUPAC name"), "representation": iupac}]
        if cas:
            body["code"] = [{"code": cc(cas, "http://cas.org", cas)}]
        body["name"] = [{"name": name, "type": cc("Company code"), "preferred": True}] + ([{"name": iupac, "type": cc("IUPAC chemical name")}] if iupac else [])
        if mid in ("cp-6", "cp-4"):
            body["property"] = [
                {"type": cc("Rule-based (Q)Sar", CS_SUBPROP, "1233444", "Rule-based (Q)Sar"), "valueCodeableConcept": cc("Positive (DEREK Nexus)")},
                {"type": cc("Statistical (Q)Sar", CS_SUBPROP, "123555", "Statistical (Q)Sar"), "valueCodeableConcept": cc("Positive (SARAH Nexus)")},
                {"type": cc("Mutagenicity Comment", CS_SUBPROP, "123557", "Mutagenicity Comment"), "valueCodeableConcept": cc("Aniline functionality eliminated in Step 3; purged by Step 3/4 crystallizations; controlled with CP-3/CP-4/CP-5 to a total of ≤ 37.5 ppm (TTC 1.5 µg/day / MDD 40 mg)")}]
        if mid == "cp-8":
            ISSUES.append("CP-8 is named '3,5-bis(trifluoromethyl)benzyl bromide' (C9H3BrF6, 307.03, CAS 32247-96-4) in 2.3.3.SM.D but '1-bromo-3,5-bis(trifluoromethyl)benzene' (C8H3BrF6, 293.01) in the impurity tables of 2.3.4.DS.C / 3.2.RS; the starting-material identity was used and the alternative recorded as a synonym.")
            body["name"].append({"name": "1-bromo-3,5-bis(trifluoromethyl)benzene", "type": cc("Name used in impurity tables (inconsistent in source)")})
        if mid in ("cp-4", "cp-8"):
            body["manufacturer"] = [ref("Organization", "iroha-corp"), ref("Organization", "heto-corp" if mid == "cp-4" else "abcr-gmbh")]
        if mid in ("cp-6", "cp-7"):
            body["manufacturer"] = [ref("Organization", "iroha-corp")]
        add("SubstanceDefinition", mid, body, ["impurities", "core"], source=S.page("2.3.3.SM Starting Material(s)").get("url"))

    # relationships of Sakuramil
    rels = [("cp-9-1", "PR-IMP", "Process impurity", "process", "Process Impurity", "Specified related substance; NMT 0.15 % (DS); NMT 0.3 %/0.5 % release/shelf-life (DP)"),
            ("cp-8", "ST-IMP", "Starting material, forced degradation product", "starting-material", "Starting Material", "Specified related substance; NMT 0.10 %"),
            ("cp-6", "INT-IMP", "Process intermediate, forced degradation product", "intermediate-material", "Intermediate Material", "Potentially mutagenic impurity; NMT 37.5 ppm"),
            ("cp-4", "ST-IMP", "Starting material, forced degradation product", "starting-material", "Starting Material", "Potentially mutagenic; controlled via CP-6 limit and purge"),
            ("cp-5", "INT-IMP", "Process intermediate, forced degradation product", "intermediate-material", "Intermediate Material", "Potentially mutagenic (structural alert); purged"),
            ("cp-3", "PR-IMP", "Process impurity", "process", "Process Impurity", "Potentially mutagenic (structural alert); purged"),
            ("cp-7", "INT-IMP", "Process intermediate, forced degradation product", "intermediate-material", "Intermediate Material", "Intermediate; purged in Step 4 crystallization")]
    R["SubstanceDefinition/sakuramil"]["relationship"] = [
        {"extension": [ext(SD + "Extension-impurity-origin-pq", valueCodeableConcept=cc(on, CS_IMPORIGIN, oc, on))],
         "substanceDefinitionReference": ref("SubstanceDefinition", t, t.upper()),
         "type": cc(tn + " - " + note, CS_IMPTYPE, tc, tn)} for t, tc, tn, oc, on, note in rels]
    for d in ["impurities"]:
        tag(d, "SubstanceDefinition", "sakuramil")

    # ------------------------------------------------------------ excipients
    exc = [("lactose-monohydrate", "Lactose monohydrate", ["Lactose hydrate"], "Animal origin (milk); TSE declarations per EMA/410/01 rev.3"),
           ("microcrystalline-cellulose", "Cellulose, microcrystalline", ["Microcrystalline cellulose"], None),
           ("croscarmellose-sodium", "Croscarmellose sodium", [], None),
           ("hydroxypropyl-cellulose", "Hydroxypropyl cellulose", [], None),
           ("magnesium-stearate", "Magnesium stearate", [], "Vegetable origin"),
           ("purified-water", "Water, purified", ["Purified water"], None),
           ("hypromellose", "Hypromellose", [], None),
           ("macrogol-6000", "Macrogol (type 6000)", ["Polyethylene glycol (6000)", "Macrogol 6000"], None),
           ("titanium-dioxide", "Titanium dioxide (E 171)", ["Titanium oxide"], None),
           ("iron-oxide-red", "Iron oxide, red (E 172)", ["Ferric oxide", "Red Ferric oxide"], None)]
    exs = S.page("2.3.3.EX Compendial excipients")["url"]
    for eid, name, syn, origin in exc:
        grades = [cc("Ph. Eur."), cc("USP/NF" if eid != "hypromellose" else "USP"), cc("JP")]
        if eid in ("titanium-dioxide", "iron-oxide-red"):
            grades.insert(1, cc("Regulation (EU) 231/2012"))
        body = {"status": cc("Active", "http://hl7.org/fhir/publication-status", "active", "Active"),
                "classification": [cc("Excipient (compendial)")], "grade": grades,
                "name": [{"name": name, "preferred": True, "synonym": [{"name": s} for s in syn]} if syn else {"name": name, "preferred": True}]}
        if origin:
            body["sourceMaterial"] = {"type": cc(origin)}
        add("SubstanceDefinition", eid, body, ["excipients", "core"], source=exs)
    premix = S.page("2.3.3.EX Non-compendial Excipients")
    add("SubstanceDefinition", "coating-premix-red", {
        "identifier": [{"system": BASE + "/material-code", "value": "KIRSCH2358"}],
        "status": cc("Active", "http://hl7.org/fhir/publication-status", "active", "Active"),
        "classification": [cc("Excipient (non-compendial mixture, commercially available)")], "grade": [cc("In-house")],
        "description": "Basic coating premix, red. Commercially available film-coating premix; minor adaptations of the quantitative composition may be needed to match the colour reference. None of the components are of animal origin.",
        "name": [{"name": "Basic coating premix, red", "preferred": True, "synonym": [{"name": "Coating premix red"}, {"name": "Coating Premix Red KIRSCH2358"}]}],
        "relationship": [{"substanceDefinitionReference": ref("SubstanceDefinition", c), "type": cc("Component of mixture"), "isDefining": True,
                          "amountQuantity": q(v, "%")} for c, v in [("hypromellose", 50.0), ("macrogol-6000", 20.0), ("titanium-dioxide", 25.0), ("iron-oxide-red", 5.0)]],
    }, ["excipients", "core"], source=premix["url"])

    # ------------------------------------------------------------ raw materials (reagents, solvents)
    rms = ["Methyl Chloroformate", "Lithium-tert-butoxide", "Tetrahydrofuran", "Sodium borohydride", "Magnesium chloride", "Methanol",
           "Hydrochloric Acid", "Sodium carbonate", "Ethyl chloroformate", "Sodium hydroxide", "nHexane", "Methylene chloride (Dichloromethane, DCM)",
           "Catalyst Tetra-n-butylammonium bromide", "Water"]
    for n in rms:
        rid = "rm-" + slug(n.replace("Catalyst ", "").replace(" (Dichloromethane, DCM)", ""))
        disp = n.replace("Catalyst ", "").replace("nHexane", "n-Hexane")
        add("SubstanceDefinition", rid, {"status": cc("Active", "http://hl7.org/fhir/publication-status", "active", "Active"),
            "classification": [cc("Raw material (reagent/solvent/catalyst) for Sakuramil synthesis")],
            "name": [{"name": disp, "preferred": True}]}, ["raw-materials", "core"], source=[p for p in S.pages if "2.3.3.RM.C" in p["short"] and "[" + n.split(" (")[0] in p["short"]][0]["url"])
    add("SubstanceDefinition", "rm-ethanol", {"status": cc("Active", "http://hl7.org/fhir/publication-status", "active", "Active"),
        "classification": [cc("Raw material (solvent) for Sakuramil synthesis")], "name": [{"name": "Ethanol", "preferred": True}]}, ["raw-materials", "core"])
    ISSUES.append("Ethanol is used in Steps 2-4 of the drug-substance process and controlled by IPC#1, but no 2.3.3.RM specification page exists for it; a SubstanceDefinition without specification was created.")

    # ------------------------------------------------------------ medicinal product
    gi = S.page("2.3.1 General information")
    add("MedicinalProductDefinition", "sakura-bloom-20mg", {
        "identifier": [{"system": BASE + "/product-id", "value": "SB-20MG-FCT"}],
        "type": cc("Medicinal product (small molecule)"),
        "domain": cc("Human use", "http://hl7.org/fhir/medicinal-product-domain", "Human", "Human use"),
        "status": cc("Active", "http://hl7.org/fhir/publication-status", "active", "Active"),
        "description": "Sakura Bloom 20 mg film-coated tablet: immediate-release film-coated tablet for oral administration, to be swallowed whole. Strength expressed as Sakuramil neutral, anhydrous base. Fictitious ICH M4Q(R2) mock-up product 'SakuraBloom R2'.",
        "combinedPharmaceuticalDoseForm": cc("Film-coated tablet", EDQM, "10221000", "Film-coated tablet"),
        "route": [cc("Oral use", EDQM, "20053000", "Oral use")],
        "name": [{"productName": "Sakura Bloom 20 mg film-coated tablets", "type": cc("Proprietary", CS_NAMETYPE, "Proprietary", "Proprietary"),
                  "part": [{"part": "Sakura Bloom", "type": cc("Invented name part")}, {"part": "20 mg", "type": cc("Strength part")}, {"part": "film-coated tablets", "type": cc("Pharmaceutical dose form part")}]}],
        "operation": [
            {"type": {"concept": cc("Drug substance manufacture")}, "organization": [ref("Organization", "iroha-corp")]},
            {"type": {"reference": ref("PlanDefinition", "dp-manufacturing-process")}, "organization": [ref("Organization", "aparna-pharm")]},
            {"type": {"concept": cc("Quality control testing (release)")}, "organization": [ref("Organization", "aparna-pharm"), ref("Organization", "dakina-analytica"), ref("Organization", "kunchen-sa")]},
            {"type": {"concept": cc("Primary packaging")}, "organization": [ref("Organization", "aparna-pharm"), ref("Organization", "pack-alpha"), ref("Organization", "cocopharma")]},
            {"type": {"concept": cc("Secondary packaging")}, "organization": [ref("Organization", "aparna-pharm"), ref("Organization", "pack-alpha")]},
            {"type": {"concept": cc("Stability testing")}, "organization": [ref("Organization", "aparna-pharm"), ref("Organization", "pack-alpha")]}],
        "characteristic": [
            {"type": cc("Drug release profile"), "valueCodeableConcept": cc("Immediate release")},
            {"type": cc("Maximum daily dose"), "valueQuantity": {"value": 40, "unit": "mg", "system": UCUM, "code": "mg"}},
            {"type": cc("Medical device(s) or co-packaged item(s)"), "valueCodeableConcept": cc("Not applicable")},
            {"type": cc("Method of administration"), "valueCodeableConcept": cc("To be swallowed whole")},
            {"type": cc("Shelf life (QTPP target)"), "valueCodeableConcept": cc("36 months at room temperature across all climatic zones")}],
    }, ["core", "dp", "dp-composition", "dp-specification", "dp-batch-info", "dp-excipients", "batch-formula"], source=gi["url"])

    dpd = S.page("2.3.3.DP.D Description")
    add("ManufacturedItemDefinition", "sakura-bloom-20mg-tablet", {
        "status": "active", "name": "Sakura Bloom 20 mg film-coated tablet",
        "manufacturedDoseForm": cc("Film-coated tablet", EDQM, "10221000", "Film-coated tablet"),
        "unitOfPresentation": cc("Tablet", EDQM, "15054000", "Tablet"),
        "manufacturer": [ref("Organization", "aparna-pharm")],
        "property": [{"type": cc("Colour"), "valueCodeableConcept": cc("Pale red")},
                     {"type": cc("Shape"), "valueCodeableConcept": cc("Round, biconvex")},
                     {"type": cc("Imprint / debossing"), "valueCodeableConcept": cc("'SB' on one side and '20' on the other side")},
                     {"type": cc("Total weight of film-coated tablet"), "valueQuantity": q(200.00, "mg")},
                     {"type": cc("Overage by mass (%)", PQ + "/CodeSystem/cs-manufactured-item-property-pq-example", "overage-by-mass", "Overage by mass (%)"), "valueQuantity": q(0, "%")}],
        "component": [
            {"type": cc("Tablet core"), "amount": [q(194.00, "mg")], "constituent": [
                {"amount": [q(a, "mg")], "function": [cc(f)], "hasIngredient": [{"reference": ref("Ingredient", "ing-" + i)}]} for i, a, f in
                [("sakuramil", 20.00, "Active ingredient"), ("lactose-monohydrate", 136.00, "Diluent"), ("microcrystalline-cellulose", 20.00, "Diluent"),
                 ("croscarmellose-sodium", 10.00, "Disintegrant"), ("hydroxypropyl-cellulose", 6.00, "Binder"), ("magnesium-stearate", 2.00, "Lubricant")]]},
            {"type": cc("Film-coating"), "amount": [q(6.00, "mg")], "constituent": [
                {"amount": [q(6.00, "mg")], "function": [cc("Coating agent")], "hasIngredient": [{"reference": ref("Ingredient", "ing-coating-premix-red")}]}],
             "component": [{"type": cc("Basic coating premix, red"), "constituent": [
                 {"amount": [q(a, "mg")] if a else [], "function": [cc(f)], "hasIngredient": [{"reference": ref("Ingredient", "ing-" + i)}]} for i, a, f in
                 [("hypromellose", 4.80, "Film-forming agent"), ("macrogol-6000", 0.60, "Polishing agent"), ("titanium-dioxide", 0.60, "Opacifier"), ("iron-oxide-red", None, "Colorant")]]}]}],
    }, ["core", "dp", "dp-composition", "container-closure"], source=dpd["url"])
    for comp in R["ManufacturedItemDefinition/sakura-bloom-20mg-tablet"]["component"][1]["component"][0]["constituent"]:
        if not comp["amount"]:
            del comp["amount"]

    ings = [("sakuramil", "Active", "Active ingredient", 20.00, "In-house", None, 52.000),
            ("lactose-monohydrate", "Excipient", "Diluent", 136.00, "Ph. Eur., USP/NF, JP", "diluent", 353.600),
            ("microcrystalline-cellulose", "Excipient", "Diluent", 20.00, "Ph. Eur., USP/NF, JP", "diluent", 52.000),
            ("croscarmellose-sodium", "Excipient", "Disintegrant", 10.00, "Ph. Eur., USP/NF, JP", "disintegrant", 26.000),
            ("hydroxypropyl-cellulose", "Excipient", "Binder", 6.00, "Ph. Eur., USP/NF, JP", None, 15.600),
            ("magnesium-stearate", "Excipient", "Lubricant", 2.00, "Ph. Eur., USP/NF, JP", "lubricant", 5.200),
            ("coating-premix-red", "Excipient", "Coating agent", 6.00, "In-house", None, 15.600),
            ("purified-water", "Excipient", "Solvent for coating suspension (removed during processing)", None, "Ph. Eur., USP/NF, JP", None, None),
            ("hypromellose", "Excipient", "Film-forming agent (component of coating premix)", 4.80, "Ph. Eur., USP, JP", None, None),
            ("macrogol-6000", "Excipient", "Polishing agent (component of coating premix)", 0.60, "Ph. Eur., USP/NF, JP", None, None),
            ("titanium-dioxide", "Excipient", "Opacifier (component of coating premix)", 0.60, "Ph. Eur., Regulation (EU) 231/2012, USP/NF, JP", None, None),
            ("iron-oxide-red", "Excipient", "Colorant (component of coating premix)", None, "Ph. Eur., Regulation (EU) 231/2012, USP/NF, JP", None, None)]
    rolecode = {"Active": ("100000072072", "Active"), "Excipient": ("100000072082", "Excipient")}
    for sid, role, func, amt, std, fcode, perbatch in ings:
        strength = []
        if amt is not None:
            strength.append({"presentationRatio": {"numerator": q(amt, "mg"), "denominator": {"value": 1, "unit": "tablet", "system": UCUM, "code": "{tablet}"}},
                             "textPresentation": f"{amt:.2f} mg per film-coated tablet"})
        else:
            strength.append({"textPresentation": "q.s."})
        if sid == "sakuramil":
            strength[0]["basis"] = cc("Neutral, anhydrous base form")
            strength[0]["referenceStrength"] = [{"substance": {"reference": ref("SubstanceDefinition", "sakuramil")},
                                                 "strengthRatio": {"numerator": q(20, "mg"), "denominator": {"value": 1, "unit": "tablet", "system": UCUM, "code": "{tablet}"}}}]
        if perbatch:
            strength.append({"presentationRatio": {"numerator": q(perbatch, "kg"), "denominator": q(520.000, "kg")},
                             "textPresentation": f"{perbatch:.3f} kg per commercial batch (520.000 kg, approx. 2,600,000 tablets)",
                             "basis": cc("Batch formula")})
        body = {"status": "active",
                "for": [ref("MedicinalProductDefinition", "sakura-bloom-20mg"), ref("ManufacturedItemDefinition", "sakura-bloom-20mg-tablet")],
                "role": cc(role, CS_INGROLE, rolecode[role][0], rolecode[role][1]),
                "function": [cc(func, CS_INGFUNC if fcode else None, fcode, fcode.capitalize() if fcode else None)],
                "substance": {"code": {"reference": ref("SubstanceDefinition", sid)}, "strength": strength}}
        if role == "Excipient":
            body["extension"] = [ext(SD + "Extension-novel-excipient-pq", valueBoolean=False),
                                 ext(SD + "Extension-suitability-for-use-pq", valueString=f"Complies with {std}")]
        add("Ingredient", "ing-" + sid, body, ["core", "dp-composition", "dp-specification", "batch-formula"] + (["dp-excipients"] if role == "Excipient" else []), source=dpd["url"])
        for g in ["dp-composition", "dp-specification", "batch-formula", "dp-excipients"]:
            tag(g, "SubstanceDefinition", sid)
    tag("dp-excipients", "Organization", "aparna-pharm")
    tag("dp-specification", "SubstanceDefinition", "cp-9-1")

    # ------------------------------------------------------------ packaging
    bot = S.page("2.3.3.DP.S. Storage - Bottle")["url"]
    bli = S.page("2.3.3.DP.S Storage - Blister")["url"]
    blk = S.page("2.3.3.DP.S Storage - Bulk")["url"]
    zones = [("Climatic zones I & II (EU)", "This medicinal product does not require any special storage requirement."),
             ("Climatic zones I & II (non-EU)", "Do not store above 30°C"), ("Climatic zones III & IVA", "Do not store above 30°C"), ("Climatic zone IVB", "Do not store above 30°C")]
    def shelf(months, zone, prec):
        return {"type": cc(f"Shelf life of the medicinal product as packaged for sale - {zone}"), "periodDuration": {"value": months, "unit": "months", "system": UCUM, "code": "mo"},
                "specialPrecautionsForStorage": [cc(prec)]}
    item = [{"item": {"reference": ref("ManufacturedItemDefinition", "sakura-bloom-20mg-tablet")}}]
    add("PackagedProductDefinition", "pack-hdpe-bottle", {
        "name": "Sakura Bloom 20 mg film-coated tablets - HDPE bottle with child-resistant closure",
        "type": cc("HDPE bottle pack"), "packageFor": [ref("MedicinalProductDefinition", "sakura-bloom-20mg")],
        "status": cc("Active", "http://hl7.org/fhir/publication-status", "active", "Active"),
        "description": "90 cc round HDPE bottle (Purell HDPE resin, titanium dioxide colorant, white) with 38 mm child-resistant induction seal closure (PP inner/outer cap, white lined pulpboard liner, PE inner seal), in a non-functional cardboard box.",
        "packaging": {"type": cc("Box (secondary, non-functional)", EDQM, "30009000", "Box"), "manufacturer": [ref("Organization", "pack-alpha"), ref("Organization", "aparna-pharm")],
            "packaging": [{"type": cc("Bottle", EDQM, "30008000", "Bottle"), "material": [cc("High-density polyethylene (HDPE Purell)"), cc("Titanium dioxide colorant")],
                "property": [{"type": cc("Container Size", CS_PKGPROP, "Container Size", "Container Size"), "valueQuantity": {"value": 90, "unit": "cc", "system": UCUM, "code": "cm3"}},
                             {"type": cc("Color", CS_PKGPROP, "Color", "Color"), "valueCodeableConcept": cc("White")},
                             {"type": cc("Quality Standard", CS_PKGPROP, "Quality Standard", "Quality Standard"), "valueCodeableConcept": cc("Complies with 21 CFR, Indirect Food Additives")}],
                "shelfLifeStorage": [shelf(36, z, p) for z, p in zones], "manufacturer": [ref("Organization", "pack-alpha"), ref("Organization", "cocopharma"), ref("Organization", "aparna-pharm")],
                "containedItem": item,
                "packaging": [{"type": cc("38 mm child-resistant induction seal closure"), "material": [cc("Polypropylene (inner cap, natural)"), cc("Polypropylene (outer cap, white)"), cc("White lined pulpboard liner"), cc("Polyethylene inner seal")],
                               "property": [{"type": cc("Quality Standard", CS_PKGPROP, "Quality Standard", "Quality Standard"), "valueCodeableConcept": cc("Complies with 21 CFR, Indirect Food Additives")}]}]}]},
    }, ["core", "container-closure", "dp-composition"], source=bot)
    add("PackagedProductDefinition", "pack-pa-al-pvc-blister", {
        "name": "Sakura Bloom 20 mg film-coated tablets - PA/AL/PVC blister",
        "type": cc("Blister pack"), "packageFor": [ref("MedicinalProductDefinition", "sakura-bloom-20mg")],
        "status": cc("Active", "http://hl7.org/fhir/publication-status", "active", "Active"),
        "description": "PA/AL/PVC cold-form blister (forming foil: polyamide / aluminium / PVC product-contact layer; lidding: 20 µm aluminium foil with heat-seal lacquer and nitrocellulose-free printing primer) in a non-functional cardboard box.",
        "packaging": {"type": cc("Box (secondary, non-functional)", EDQM, "30009000", "Box"),
            "packaging": [{"type": cc("Blister", EDQM, "30007000", "Blister"), "material": [cc("Polyamide (PA)"), cc("Aluminium"), cc("Polyvinyl chloride (PVC)")],
                "shelfLifeStorage": [shelf(36, z, p) for z, p in zones], "manufacturer": [ref("Organization", "pack-alpha"), ref("Organization", "cocopharma"), ref("Organization", "aparna-pharm")],
                "containedItem": item,
                "packaging": [{"type": cc("Forming component: PA/AL/PVC foil"), "material": [cc("Polyamide (PA) film (not in contact with product)"), cc("Aluminium foil (not in contact with product)"), cc("PVC film (product contact layer)")],
                               "property": [{"type": cc("Thickness", CS_PKGPROP, "Thickness", "Thickness"), "valueCodeableConcept": cc("≥ 150 µm (total)")},
                                            {"type": cc("Quality Standard", CS_PKGPROP, "Quality Standard", "Quality Standard"), "valueCodeableConcept": cc("Complies with foodstuff legislation")}]},
                              {"type": cc("Backing component: aluminium lidding foil"), "material": [cc("Heat seal lacquer (vinyl acryl resin) (product contact layer)"), cc("Aluminium foil 20 µm"), cc("Nitrocellulose-free printing primer")],
                               "property": [{"type": cc("Thickness", CS_PKGPROP, "Thickness", "Thickness"), "valueCodeableConcept": cc("≥ 20 µm (total)")}]}]}]},
    }, ["core", "container-closure", "dp-composition"], source=bli)
    add("PackagedProductDefinition", "pack-bulk-alu-bag", {
        "name": "Sakura Bloom 20 mg film-coated tablets - bulk (PETP/AL/PE bag in tinplate can)",
        "type": cc("Bulk drug product pack"), "packageFor": [ref("MedicinalProductDefinition", "sakura-bloom-20mg")],
        "status": cc("Active", "http://hl7.org/fhir/publication-status", "active", "Active"),
        "description": "Tightly sealed PETP/AL/PE aluminium composite bag placed in a tinplate can with hooded lid. Transport and intermediate storage not above +30 °C; excursions up to 40 °C permitted.",
        "packaging": {"type": cc("Tinplate can with hooded lid (secondary container)"),
            "packaging": [{"type": cc("Bag", EDQM, "30001000", "Bag"), "material": [cc("PETP/AL/PE aluminium composite")],
                "property": [{"type": cc("Quality Standard", CS_PKGPROP, "Quality Standard", "Quality Standard"), "valueCodeableConcept": cc("Complies with European and US regulation")}],
                "shelfLifeStorage": [{"type": cc("Holding time of packaged bulk drug product"), "periodDuration": {"value": 18, "unit": "months", "system": UCUM, "code": "mo"},
                                      "specialPrecautionsForStorage": [cc("Do not store above 30°C")]}], "containedItem": item}]},
    }, ["core", "container-closure"], source=blk)
    ISSUES.append("Pack sizes (number of tablets per bottle / blister) are not stated in the mock-up; containedItem.amount was omitted.")
