#!/usr/bin/env python3
"""Build the product resources for the Type 2 showcase: WonderDrug 250 mg/5 mL powder for oral suspension.

    python3 showcases/epi-types/build/build_wonderdrug.py

Values follow the HL7 ePI IG example "bundle-epi-type2-example-wonderdrug-suspension" (a non-authorised, illustrative
example). The IG bundle has no SubstanceDefinition; the ones here add names, UNII identifiers and molecular formulas.
Ingredient functions and the per-bottle sucrose/sodium benzoate amounts are derived (concentration x 100 mL).
The powder (ManufacturedItemDefinition) and the oral suspension (AdministrableProductDefinition) are kept apart, which
is the point of the showcase.

Writes showcases/epi-types/fhir/Bundle-wonderdrug-suspension-product.json and data/wonderdrug-suspension.js
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
UCUM = "http://unitsofmeasure.org"
EDQM = "http://standardterms.edqm.eu"
UNII = "http://fdasis.nlm.nih.gov"
HTEST = {"system": "http://terminology.hl7.org/CodeSystem/v3-ActReason", "code": "HTEST", "display": "test health data"}
KNOWN = "http://example.org/fhir-gra/StructureDefinition/excipient-with-known-effect"


def tx(t):
    return {"text": t}


def q(v, unit, code=None):
    return {"value": v, "unit": unit, "system": UCUM, "code": code or unit}


def ratio(n, nu, d, du, nc=None, dc=None):
    return {"numerator": q(n, nu, nc), "denominator": q(d, du, dc)}


def m(r):
    r.setdefault("meta", {})["security"] = [HTEST]
    return r


MPD = "MedicinalProductDefinition/mpd-wonderdrug-suspension"
MID = "ManufacturedItemDefinition/mid-wonderdrug-powder"
APD = "AdministrableProductDefinition/apd-wonderdrug-suspension"
ORG = "Organization/org-wonderpharma"
DEV = "DeviceDefinition/devicedefinition-wonderdrug-oral-syringe"

R = []
R.append(m({"resourceType": "MedicinalProductDefinition", "id": "mpd-wonderdrug-suspension",
    "identifier": [{"system": "http://example.org/fhir-gra/product-id", "value": "WD-250-5-POS"}],
    "type": tx("Medicinal product"), "domain": tx("Human use"), "status": tx("Active"),
    "combinedPharmaceuticalDoseForm": tx("Powder for oral suspension"),
    "route": [{"coding": [{"system": EDQM, "code": "20053000", "display": "Oral use"}], "text": "Oral use"}],
    "legalStatusOfSupply": tx("Medicinal product not subject to medical prescription"),
    "classification": [{"coding": [{"system": "http://www.whocc.no/atc", "code": "N02BE01", "display": "paracetamol"}], "text": "N02BE01 · paracetamol"}],
    "name": [{"productName": "WonderDrug 250 mg/5 mL powder for oral suspension",
              "part": [{"part": "WonderDrug", "type": tx("Invented name")}, {"part": "250 mg/5 mL", "type": tx("Strength")},
                       {"part": "powder for oral suspension", "type": tx("Pharmaceutical dose form")}]}]}))

R.append(m({"resourceType": "ManufacturedItemDefinition", "id": "mid-wonderdrug-powder", "status": "active",
    "name": "WonderDrug powder for oral suspension, in the bottle as supplied",
    "manufacturedDoseForm": tx("Powder for oral suspension"), "unitOfPresentation": tx("Bottle"),
    "manufacturer": [{"reference": ORG}],
    "property": [{"type": tx("Colour"), "valueCodeableConcept": tx("White to off-white")},
                 {"type": tx("Physical form"), "valueCodeableConcept": tx("Powder")},
                 {"type": tx("Reconstitution"), "valueMarkdown": "Add 90 mL of water to the powder in the bottle and shake for 1 minute to make 100 mL of suspension."}]}))

R.append(m({"resourceType": "AdministrableProductDefinition", "id": "apd-wonderdrug-suspension", "status": "active",
    "formOf": [{"reference": MPD}], "producedFrom": [{"reference": MID}],
    "administrableDoseForm": tx("Oral suspension"), "unitOfPresentation": tx("Millilitre"),
    "device": {"reference": DEV},
    "property": [{"type": tx("Appearance"), "valueCodeableConcept": tx("White, orange-flavoured suspension")},
                 {"type": tx("Volume after reconstitution"), "valueQuantity": q(100, "mL")},
                 {"type": tx("Handling"), "valueCodeableConcept": tx("Shake well before each use")}],
    "routeOfAdministration": [{"code": {"coding": [{"system": EDQM, "code": "20053000", "display": "Oral use"}], "text": "Oral use"}}]}))

R.append(m({"resourceType": "DeviceDefinition", "id": "devicedefinition-wonderdrug-oral-syringe",
    "deviceName": [{"name": "Oral syringe, 5 mL", "type": "user-friendly-name"}],
    "description": "5 mL oral syringe graduated in 0.25 mL steps, supplied in the pack to measure each dose.",
    "property": [{"type": tx("Capacity"), "valueQuantity": q(5, "mL")}, {"type": tx("Graduation"), "valueQuantity": q(0.25, "mL")}]}))

SUBS = [  # id, name, UNII, formula, molecular weight
    ("paracetamol", "Paracetamol", "362O9ITL9D", "C8H9NO2", 151.16),
    ("sucrose", "Sucrose", "C151H8M554", "C12H22O11", 342.30),
    ("xanthan-gum", "Xanthan gum", "TTV12P4NEE", None, None),
    ("sodium-benzoate", "Sodium benzoate (E211)", "OJ245FE5EU", "C7H5NaO2", 144.10),
    ("orange-flavour", "Orange flavour", None, None, None),
]
for sid, name, unii, formula, mw in SUBS:
    r = {"resourceType": "SubstanceDefinition", "id": f"sd-{sid}", "name": [{"name": name}]}
    if unii:
        r["identifier"] = [{"system": UNII, "value": unii}]
    if formula:
        r["molecularWeight"] = [{"amount": q(mw, "g/mol")}]
        r["structure"] = {"molecularFormula": formula}
    if sid == "orange-flavour":
        r["description"] = "Flavouring preparation; composition not stated."
    R.append(m(r))

# id, substance, role, function, known effect, strengths (MID per bottle, APD per 5 mL)
INGS = [
    ("paracetamol", "Active", "Active ingredient", False, ratio(5, "g", 1, "bottle", "g", "{bottle}"), ratio(250, "mg", 5, "mL")),
    ("sucrose", "Excipient", "Sweetener", True, ratio(50, "g", 1, "bottle", "g", "{bottle}"), ratio(2.5, "g", 5, "mL")),
    ("xanthan-gum", "Excipient", "Suspending agent", False, None, None),
    ("sodium-benzoate", "Excipient", "Preservative", True, ratio(100, "mg", 1, "bottle", "mg", "{bottle}"), ratio(5, "mg", 5, "mL")),
    ("orange-flavour", "Excipient", "Flavouring", False, None, None),
]
ROLE = {"Active": ("100000072072", "Active"), "Excipient": ("100000072082", "Excipient")}
for sid, role, fn, known, per_bottle, per_5ml in INGS:
    strengths = []
    if per_bottle:
        strengths.append({"presentationRatio": per_bottle, "textPresentation": f'{per_bottle["numerator"]["value"]:g} {per_bottle["numerator"]["unit"]} per bottle',
                          "basis": tx("Powder, as supplied in the bottle")})
    if per_5ml:
        strengths.append({"concentrationRatio": per_5ml, "textPresentation": f'{per_5ml["numerator"]["value"]:g} {per_5ml["numerator"]["unit"]} per 5 mL',
                          "basis": tx("Oral suspension, after reconstitution")})
    r = {"resourceType": "Ingredient", "id": f"ing-{sid}", "status": "active", "for": [{"reference": MPD}, {"reference": MID}, {"reference": APD}],
         "role": {"coding": [{"system": "https://spor.ema.europa.eu/rmswi", "code": ROLE[role][0], "display": ROLE[role][1]}], "text": role},
         "function": [tx(fn)], "substance": {"code": {"reference": {"reference": f"SubstanceDefinition/sd-{sid}"}}}}
    if strengths:
        r["substance"]["strength"] = strengths
    if known:
        r["extension"] = [{"url": KNOWN, "valueBoolean": True}]
    R.append(m(r))

R.append(m({"resourceType": "PackagedProductDefinition", "id": "ppd-wonderdrug-suspension",
    "name": "WonderDrug 250 mg/5 mL powder for oral suspension - 1 bottle with 5 mL oral syringe",
    "identifier": [{"system": "https://www.gs1.org/gtin", "value": "05391000000024"}],
    "type": tx("Medicinal product package"), "packageFor": [{"reference": MPD}], "status": tx("Active"),
    "containedItemQuantity": [q(1, "bottle", "{bottle}")],
    "description": "One bottle of powder (100 mL of suspension after reconstitution) with a 5 mL oral syringe, in a box.",
    "manufacturer": [{"reference": ORG}],
    "packaging": {"type": tx("Box"), "quantity": 1, "material": [tx("Cardboard")], "packaging": [
        {"type": tx("Bottle"), "quantity": 1,
         "material": [tx("High-density polyethylene (HDPE)")],
         "property": [{"type": tx("Closure"), "valueCodeableConcept": tx("Child-resistant polypropylene cap")},
                      {"type": tx("Volume after reconstitution"), "valueQuantity": q(100, "mL")}],
         "shelfLifeStorage": [
             {"type": tx("Unopened"), "periodDuration": q(36, "months", "mo"), "specialPrecautionsForStorage": [tx("Do not store above 25 °C")]},
             {"type": tx("After reconstitution"), "periodDuration": q(14, "days", "d"), "specialPrecautionsForStorage": [tx("Store in a refrigerator (2 °C to 8 °C)")]}],
         "containedItem": [{"item": {"reference": {"reference": MID}}, "amount": q(1, "bottle", "{bottle}")}]},
        {"type": tx("Oral syringe"), "quantity": 1, "material": [tx("Polypropylene")],
         "containedItem": [{"item": {"reference": {"reference": DEV}}, "amount": q(1, "syringe", "{syringe}")}]}]}}))

R.append(m({"resourceType": "Organization", "id": "org-wonderpharma",
    "identifier": [{"system": "http://example.org/fhir-gra/organization-id", "value": "ORG-100000001"}],
    "active": True, "type": [tx("Marketing authorisation holder"), tx("Manufacturer")], "name": "WonderPharma Ltd.",
    "contact": [{"address": {"line": ["1 Example Street"], "city": "Dublin 2", "postalCode": "D02 X123", "country": "IE"},
                 "telecom": [{"system": "phone", "value": "+353 1 000 0000"}, {"system": "email", "value": "medinfo@wonderpharma.example.com"},
                             {"system": "url", "value": "https://www.wonderpharma.example.com"}]}]}))

R.append(m({"resourceType": "RegulatedAuthorization", "id": "ra-wonderdrug-suspension",
    "identifier": [{"system": "http://example.org/fhir-gra/marketing-authorisation-number", "value": "PA0000/001/002"}],
    "subject": [{"reference": MPD}, {"reference": "PackagedProductDefinition/ppd-wonderdrug-suspension"}],
    "type": tx("Marketing authorisation"), "region": [tx("Ireland")], "status": tx("Active"), "statusDate": "2020-01-15",
    "basis": [tx("Known active substance")], "holder": {"reference": ORG}}))

bundle = {"resourceType": "Bundle", "id": "wonderdrug-suspension-product", "meta": {"security": [HTEST]}, "type": "collection",
          "timestamp": "2026-11-26T09:00:00Z",
          "entry": [{"fullUrl": f"http://example.org/fhir-gra/epi/{r['resourceType']}/{r['id']}", "resource": r} for r in R]}
have = {f"{r['resourceType']}/{r['id']}" for r in R}
bad = [ref for ref in json.dumps(bundle).split('"reference": "')[1:] if ref.split('"')[0] not in have]
assert not bad, bad
(OUT / "fhir" / "Bundle-wonderdrug-suspension-product.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(OUT / "data" / "wonderdrug-suspension.js").write_text(
    "/* Generated by build/build_wonderdrug.py. Values adapted from the HL7 ePI IG WonderDrug suspension example (illustrative). */\nwindow.WDDATA = "
    + json.dumps({"file": "fhir/Bundle-wonderdrug-suspension-product.json", "bundle": bundle}, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
print(len(R), "resources")
