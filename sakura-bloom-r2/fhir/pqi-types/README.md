# Sakura Bloom PQI examples, Types 1–4

**Synthetic example data.** These documents are fictitious. Their content comes from the ICH M4Q(R2) Sakura Bloom mock-up, the FDA example Quality Overall Summaries and the synthetic example data of the HL7 FHIR PQI team. They do not describe a real product, company or authorization. Every document is labelled as test data (`meta.security` HTEST) and carries this note in its Composition narrative.

| Folder | Module 2.3 | Module 3.2 |
|---|---|---|
| type1 | Structured document | Collection of 19 documents |
| type2 | + product data (subject, author, Product data section, US marketing authorization) | same |
| type3 | + section entries and textLink | same |
| type4 | + data-first sections (narrative generated from resources) | same |

Where the content comes from:

* **Text:** placed under the ICH M4Q(R1) headings from the Sakura Bloom mock-up. Headings the mock-up does not cover carry synthetic text, based on the FDA examples and the FHIR PQI team's example data, ending with a note that says so.
* **Figures:** each figure's DocumentReference says how it was made: redrawn from data in the mock-up (chromatograms, spectra, linearity plots, structures, flow diagrams, calculation formulas, tables), taken from the FDA example Quality Overall Summary (dissolution profiles, quality-attribute diagram, contour plots), taken from the FHIR PQI team's example data (IR, UV, XRPD, stability trend), redrawn from ICH M7 (Table 1-1), or a synthetic illustration. Where a figure needed a number the mock-up does not give, the description says the value was made up.
* **Marketing authorization:** made up.

## Fixes applied (`fix_pqi_types.py`)

The examples as first generated had three gaps. `fix_pqi_types.py` closes them in place; it is idempotent and needs only the Python standard library.

1. **Missing references (Types 3 and 4).** The documents referenced 178 ObservationDefinitions and 4 ActivityDefinitions by canonical URL without carrying them. Each document Bundle now also carries every resource it references, by canonical or plain reference and transitively, taken from `../dossier/sakura-bloom-r2-dossier-collection.json` (same canonical base). Every reference now resolves inside its own document.
2. **Uncoded operation.** `MedicinalProductDefinition.operation` for Aparna Pharmaceutical had an empty `type` in Type 2 (Types 3/4 only pointed to the drug product process). It now carries `type.concept.text` "Drug product manufacture" in every copy, including the base data in `../resources`, `../bundles` and `../dossier`; Types 3/4 keep the reference as well. The generator (`../../generator/part1_core.py`) emits the same.
3. **Placeholders.** 43 figures (45 citations) were labelled placeholders because the mock-up extract has no image for them. They are rebuilt by `figures/make_figures.py` (needs matplotlib and RDKit) and listed in `figures/manifest.json`:
   * calculation formulas typeset from the variable definitions in each analytical procedure (structure as in the HL7 PQI example 3.2.P.5.2 procedure);
   * Table 4 (dissolution) from the text table in 2.3.4.DP.D; Table 1-1 from ICH M7; Table 1-2 (M7 results) from the classification rationale and control strategy text;
   * the CP-7-1 and CP-9-1 structures from the mock-up's names; the Figure 2-4 linearity plot from Table 2-7; Figure 4-1 from the CPP resources;
   * the risk-assessment and DoE tables of 3.2.S.2.2 from the factors, ranges and conclusions in the narrative and the CPPs; levels the mock-up does not give are made up and marked as such;
   * the XRPD overlay on the peak positions of the HL7 PQI example pattern (synthetic, marked as such).

To regenerate: `python3 figures/make_figures.py` (optional), then `python3 fix_pqi_types.py`, then `python3 ../../showcase/pqi-types/build_pqi_types.py` for the showcases.
