# Sakura Bloom R2 – FHIR PQI dataset (ICH M4Q(R2) Module 2.3 and 3.2)

This folder holds a FHIR R5 dataset that follows the HL7 **Pharmaceutical Quality Information (PQI)** IG (`hl7.fhir.uv.pharm-quality` 1.0.0). It is built from the ICH M4Q(R2) **SakuraBloom R2** mock-up (V1.0, last updated 15 Sep 2025), published at <https://ich.org/page/ich-m4qr2-mock-ups> (Notion site `ichm4q.notion.site`).

The dataset is meant as a base. It covers the 2.3 and 3.2 content as fully as the profiles allow, so it can be used to demo advanced use cases: cross-module traceability, specification-vs-result checks, stability trending, control-strategy queries and lifecycle change impact.

> The mock-up describes a fictitious product. ICH states that the content is illustrative and not scientifically complete. Inconsistencies found in the source are listed in `reports/source-data-issues.md`. None were silently "corrected".

## Contents

| Path | What it is |
|---|---|
| `source/sakura-bloom-r2-extract.json` | A complete extract of the mock-up: 257 Notion pages under Module 2.3, Module 3.2 and the ToC. Text and tables are rendered from the Notion public API, and each page carries its Notion URL. |
| `generator/` | Python generator (`build.py` plus `part1…part4`) that rebuilds everything below from the extract. It is deterministic. |
| `fhir/resources/` | 2,121 individual R5 resources as `Type-id.json`. |
| `fhir/bundles/*.json` | 22 domain collection Bundles, each conforming to the matching PQI Bundle profile. |
| `fhir/bundles/analytical-procedures/` | 28 `Bundle-analytical-procedure-pq` bundles, one per procedure. The profile allows exactly one Protocol per bundle. |
| `fhir/dossier/sakura-bloom-r2-dossier-collection.json` | Every resource in one collection bundle. |
| `fhir/dossier/sakura-bloom-r2-transaction.json` | The same content as PUT transaction entries, for loading into a FHIR R5 server such as HAPI. |
| `fhir/dossier/module-2-3-quality-overview-document.json` / `module-3-2-body-of-data-document.json` | FHIR *document* bundles. Each one has a Composition first, followed by every resource it references, followed transitively. |
| `reports/` | Validation summaries and the source-issue log. |

Resources use the base `http://example.org/sakura-bloom-r2/fhir`. Bundle `fullUrl`s are `{base}/{Type}/{id}`, so relative references and canonicals resolve inside every bundle. Each resource's `meta.source` points to the Notion page it was derived from, which gives traceability back to the mock-up.

## Resource inventory

| Resource | # | Used for |
|---|---|---|
| Observation | 1,443 | Batch-analysis, stability, characterisation (MS/NMR), elemental impurity and residual-solvent results |
| ObservationDefinition | 186 | Every test or acceptance criterion: DS/DP/SM/SI/RM/excipient/RS/container specs, CPPs and IPCs. Ranges are machine-readable, and the verbatim criterion is kept in the `qualified-value-text` extension. |
| Specimen | 162 | Stability pulls (batch × pack × condition × time point; storage duration in the `batch-storage-duration` extension) |
| DiagnosticReport | 78 | Batch analysis (6), stability (DP 48, DS 6), characterisation (3), elemental (12) and carry-over (3) reports |
| PlanDefinition | 70 | 28 analytical procedures, 32 specifications, 2 manufacturing processes, 5 stability protocols, 3 impurity/characterisation protocols |
| DocumentReference | 52 | Links to 3.2.AP detailed procedures and 2.3.4 justifications, flow diagrams, M7 and nitrosamine risk assessments |
| SubstanceDefinition | 37 | Sakuramil (CP-9), with general properties, impurities and intermediates (CP-3 to CP-9-1), 10 excipients, coating premix (with its composition) and 15 raw materials |
| Substance | 28 | 22 drug-substance batches and 6 reference standards |
| Medication | 13 | 6 DP batches, 6 packaged stability batches (bottle/blister) and the batch formula |
| Ingredient | 12 | Full qualitative and quantitative composition, including the coating-premix components and the strength basis |
| Organization | 11 | Applicant, DS/DP manufacturers, testing labs, packagers, SM suppliers and US-addendum sites (DUNS/FEI) |
| SpecimenDefinition | 11 | Storage conditions (25/60, 30/75, 40/75, photostability; DS ±2 °C ranges) and test-sample definitions |
| DeviceDefinition | 7 | SUPAC equipment classes and capacities, plus the DS temperature probe |
| ActivityDefinition | 4 | Stability test sets |
| PackagedProductDefinition | 3 | HDPE bottle with CR closure, PA/AL/PVC blister, and bulk PETP/AL/PE bag. Each has a shelf life per climatic zone. |
| Composition | 2 | Module 2.3 (165 sections) and Module 3.2 (89 sections). Each section has the full narrative plus 537 `entry` links to the structured resources. |
| MedicinalProductDefinition / ManufacturedItemDefinition | 1 / 1 | Product identification, operations by site, and tablet core/film-coat component structure |

## M4Q(R2) to PQI mapping

| M4Q(R2) section (mock-up) | PQI bundle / resources |
|---|---|
| 2.3.1 General information | `bundle-dp`: MedicinalProductDefinition, ManufacturedItemDefinition, Composition |
| 2.3.2 QTPP, CQAs, overall control strategy | Composition section, with entries linking each control type: CPP/IPC ObservationDefinitions (criticality extension), spec PlanDefinitions and processes |
| 2.3.3.DS.D / 3.2.DS.D Description | `bundle-ds-general-properties`: SubstanceDefinition (names, CAS, formula, MW, 25 properties) |
| 2.3.3.DS.M Manufacture | `bundle-ds-manufacturing`: 4-step PlanDefinition with materials and quantities, CPP #3.1/#4.1/#4.2, IPC #1/#2, and flow diagrams |
| 2.3.3.SM / SI / RM | `bundle-materials-specifications`: specs for CP-4, CP-8, CP-6, CP-7 and 14 raw materials (a plain collection, because no PQI profile allows multiple protocols) |
| 2.3.3.DS.C / 3.2.DS.C | `bundle-ds-specification`, `bundle-ds-batch-analysis` (B221220–22), `bundle-impurities` (relationships, M7, Q3D for 12 batches, Q3C carry-over) |
| 2.3.3.DS.S / 3.2.DS.S | `bundle-container-closure` (LDPE bag spec), `bundle-ds-stability` (3 batches, accelerated and long-term, 432 results) |
| 2.3.3.RS / 3.2.RS | `bundle-reference-standards`, `bundle-ds-characterization` (MS m/z, ¹H/¹³C NMR assignments) |
| 2.3.3.EX | `bundle-dp-excipients`: compendial and non-compendial premix specs |
| 2.3.3.DP.D | `bundle-dp-composition` |
| 2.3.3.DP.M (batch formula, process, equipment, CPP/IPC) | `bundle-dp-batch-formula`, `bundle-dp-manufacturing` (13 steps, 5 CPPs, 11 IPCs, 6 devices) |
| 2.3.3.DP.C (RTRT and conventional, release and shelf-life) | `bundle-dp-specification`. Each ObservationDefinition carries separate *Batch release* and *Shelf-life* qualifiedValues. |
| 3.2.DP.C.1 Batch analysis | `bundle-dp-batch-analysis` (ABC123/456/789) and `bundle-dp-microbiology` |
| 2.3.3.DP.S / 3.2.DP.S (bottle, blister, bulk) | `bundle-container-closure`, `bundle-dp-stability` (registration protocol RSP1234-1G, 707 results including photostability and MET), post-approval and commitment protocols |
| 2.3.3.AP / 3.2.AP / 2.3.4.AP | 28 `bundle-ap-*`: method attributes as actions, with links to the 3.2 detail and 2.3.4 justification |
| 2.3.3.FA Facilities (incl. USA addendum) | `bundle-organizations`, plus `MedicinalProductDefinition.operation` (who does what) |
| 2.3.4 DSJ, 2.3.5 PLCM, regional addenda | Narrative in the Compositions. Commitments are linked to the stability protocols. |

The links that make the advanced use cases possible are:
- Spec PlanDefinition action → `definitionCanonical` ObservationDefinition, and `documentation[depends-on]` → analytical-procedure PlanDefinition.
- `Observation.instantiatesCanonical` → ObservationDefinition, so every result can be checked against its criterion.
- `Medication.batch` → `batch-substance-batch` → DS Substance batches. This gives DP-to-DS genealogy, e.g. ABC456 → B221217…B221220.
- Process steps → materials (`manufacturing-participant`), equipment (DeviceDefinition) and CPP/IPC ObservationDefinitions.
- Composition sections (2.3 and 3.2) → structured resources, which links the regulatory narrative to the data.

## Validation

The HL7 FHIR Validator 7.0.5 was run offline, without a terminology server, against `hl7.fhir.uv.pharm-quality` built from `fsh-generated/` in this repo.

| Run | Errors | Notes |
|---|---|---|
| 2,121 resources vs. the IG as published | 164 | 162 come from an **IG defect** (see below); 2 are offline-UCUM artefacts |
| The same, with the extension context corrected locally | **2** | Both are `mg` on `MedicinalProductDefinition.characteristic.valueQuantity`. UCUM cannot be checked without a terminology server. |
| 50 PQI bundles (context fix) | 62 | All of them are the same offline-UCUM `mg` issue, repeated through bundle slice matching |

The warnings are expected. They are: no terminology server (UCUM/EDQM codes not checked), missing `Observation.effective[x]` (the mock-up gives no test dates, and none were invented), and text-only interpretation ("Complies").

### PQI IG issues found while building this

1. **`Extension-batch-storage-duration-pq` cannot be used.** Its context is `Specimen.processing.time[x]:timePeriod`, which the validator rejects. A suggested fix in FSH is `Context: Specimen.processing.time` (or `Specimen.processing.time.ofType(Period)`).
2. **No snapshots can be generated for 4 profiles:** `Medication-batch-information-drug-pq`, `DiagnosticReport-analysis-drug-pq`, `Observation-test-result-drug-pq` and `Substance-drug-pq`. They slice `medication-manufacturingBatch` and `workflow-triggeredBy` as `0..*`, but those extensions have max `1`. As a result, resources claiming those profiles are effectively only validated against the core resources. Changing the slices to `0..1` should fix it.
3. **Bundle profiles that require exactly one `Protocol`** (analytical procedure, specification, stability, manufacturing) force one bundle per procedure or protocol. Real dossiers have several, e.g. DS registration and post-approval stability protocols, or 28 analytical procedures. Consider `1..*`.
4. **No natural home for some content.** Starting-material, intermediate and raw-material specs have no bundle profile. Specimen has no reference to its SpecimenDefinition, and `Specimen.subject` cannot be a Medication, so the DP stability specimen-to-batch link goes through `Observation.subject` instead. CPP/IPC criticality is only expressible on ObservationDefinition.

## Rebuild

```bash
python3 generator/build.py source/sakura-bloom-r2-extract.json   # OUT=<dir> to change the output folder
```
