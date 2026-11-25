# PQI Types 1–4 showcases

Eleven interactive showcases, two or three per PQI maturity type, built on the Sakura Bloom examples in
`sakura-bloom-r2/fhir/pqi-types/`. The overview page is `showcases-pqi-types.html` at the site root.

| Page | Showcases |
|---|---|
| `type1.html` Structured document | Coded CTD navigator · Intake validation (Type 1 rules, simulated conversion mistakes, completeness map) · Figure register |
| `type2.html` Document + product data | Product data added in Type 2 (Type 1 table next to the structured resources, with full organization addresses; gaps filled with made-up values marked †) · Product data across the 20 documents (master data reuse) |
| `type3.html` Linked document | Linked reading (textLink) · Where is this discussed? (resource → passages) · Link integrity |
| `type4.html` Data-first document | Authored vs generated · Regenerate from source (QMS/LIMS change) · Maturity map and mixed-maturity collection builder |

Each view has its own URL fragment, for example `type3.html#reverse/PlanDefinition/spec-dp`.

## Files

- `pqi-types.css`, `pqi-types.js`: the shared shell (type ladder, navigation, inspector, narrative renderer, FHIR helpers).
- `data/*.js`: generated. Do not edit by hand.
- `img/`: generated. The figures, de-duplicated by content (260 Binary ids, 173 distinct images).

## Rebuild the data

```bash
python3 sakura-bloom-r2/showcase/pqi-types/build_pqi_types.py
```

Run it after the examples in `sakura-bloom-r2/fhir/pqi-types/` change. The output is deterministic.

The build still resolves any canonical reference a bundle does not carry from
`sakura-bloom-r2/fhir/dossier/sakura-bloom-r2-dossier-collection.json` and stores it in `PQIDATA.resources.registry`;
since `fix_pqi_types.py` was run on the examples, that list is empty and the Type 3 link-integrity view reports that
every reference resolves.
