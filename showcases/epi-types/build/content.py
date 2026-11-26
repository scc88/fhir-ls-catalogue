# -*- coding: utf-8 -*-
"""Authored narrative for the synthetic Sakura Bloom ePI.

Every word below was written for this showcase. Sakura Bloom and Sakuramil are fictitious
(ICH M4Q(R2) mock-up product); the clinical content is invented and must not be used for any
clinical purpose. No text is taken from a real product label.

Markup
  {{Type/id|visible text}}  links a phrase to a resource. Abbreviations: CUD, ING, PPD, MPD,
                            MID, APD, ORG, RA, GRP, SD. Type 1 renders the text only, Types 2-3
                            add the resource to section.entry, Type 4 also wraps the phrase in a
                            <span id> and adds a textLink.
  [[UE_TABLE]] / [[PIL_SE]] generated from the undesirable-effect ClinicalUseDefinitions.
"""

SYNTH_NOTE_EN = ('<p><i>Synthetic example. Sakura Bloom and Sakuramil are fictitious. This text was written '
                 'for a FHIR ePI demonstration and must not be used for any clinical purpose.</i></p>')

# ---------------------------------------------------------------- SmPC (EN)
# (code, display, title, html, children)   code system: https://spor.ema.europa.eu/rmswi
SMPC = ("200000029791", "SUMMARY OF PRODUCT CHARACTERISTICS", "Summary of Product Characteristics", SYNTH_NOTE_EN, [
    ("200000029792", "1. NAME OF THE MEDICINAL PRODUCT", "1. Name of the medicinal product",
     "<p>{{MPD/sakura-bloom-20mg|Sakura Bloom 20 mg film-coated tablets}}</p>", []),
    ("200000029793", "2. QUALITATIVE AND QUANTITATIVE COMPOSITION", "2. Qualitative and quantitative composition",
     "<p>Each film-coated tablet contains {{ING/ing-sakuramil|20 mg Sakuramil}}.</p>"
     "<p><b>Excipient with known effect</b></p>"
     "<p>Each film-coated tablet contains {{ING/ing-lactose-monohydrate|136 mg lactose (as monohydrate)}}.</p>"
     "<p>For the full list of excipients, see section 6.1.</p>", []),
    ("200000029797", "3. PHARMACEUTICAL FORM", "3. Pharmaceutical form",
     "<p>{{APD/apd-sakura-bloom-20mg|Film-coated tablet}}.</p>"
     "<p>{{MID/sakura-bloom-20mg-tablet|Pale red, round, biconvex film-coated tablet, debossed with SB on one side and 20 on the other}}, "
     "approximately 8 mm in diameter.</p>"
     '<p><img src="#tablet-image" alt="Pale red round film-coated tablet debossed SB and 20"/></p>', []),
    ("200000029798", "4. CLINICAL PARTICULARS", "4. Clinical particulars", "<p>Clinical particulars.</p>", [
        ("200000029799", "4.1 Therapeutic indications", "4.1 Therapeutic indications",
         "<p>Sakura Bloom is indicated in {{GRP/grp-adults|adults}} as an adjunct to diet "
         "{{CUD/ind-hypercholesterolaemia|for the reduction of low-density lipoprotein cholesterol (LDL-C) in primary hypercholesterolaemia}}, "
         "when the response to diet and other non-pharmacological measures is inadequate.</p>", []),
        ("200000029800", "4.2 Posology and method of administration", "4.2 Posology and method of administration",
         "<p><b>Posology</b></p>"
         "<p><i>Adults</i></p>"
         "<p>The recommended starting dose is {{CUD/ind-hypercholesterolaemia|20 mg once daily}}. Depending on the LDL-C response, "
         "the dose may be increased to 40 mg once daily after at least 4 weeks of treatment. "
         "{{MPD/sakura-bloom-20mg|The maximum daily dose is 40 mg}}.</p>"
         "<p><i>Older people</i></p><p>No dose adjustment is needed.</p>"
         "<p><i>Renal impairment</i></p>"
         "<p>No dose adjustment is needed in mild or moderate renal impairment. "
         "{{CUD/warn-renal-severe|In severe renal impairment (eGFR below 30 mL/min/1.73 m²) the dose must not exceed 20 mg once daily}}.</p>"
         "<p><i>Hepatic impairment</i></p>"
         "<p>Sakura Bloom is {{CUD/ci-liver|contraindicated in patients with active liver disease}} (see section 4.3).</p>"
         "<p><i>Concomitant moderate CYP3A4 inhibitors</i></p>"
         "<p>{{CUD/int-cyp3a4-moderate|In patients taking diltiazem or verapamil the dose must not exceed 20 mg once daily}} (see section 4.5).</p>"
         "<p><i>Paediatric population</i></p>"
         "<p>The safety and efficacy of Sakura Bloom in children and adolescents under 18 years of age have not been established. No data are available.</p>"
         "<p><b>Method of administration</b></p>"
         "<p>{{APD/apd-sakura-bloom-20mg|Oral use}}. The tablet should be swallowed whole with water, with or without food, at about the same time each day.</p>", []),
        ("200000029805", "4.3 Contraindications", "4.3 Contraindications",
         "<ul>"
         "<li>{{CUD/ci-hypersensitivity|Hypersensitivity to the active substance or to any of the excipients listed in section 6.1}}.</li>"
         "<li>{{CUD/ci-liver|Active liver disease or unexplained persistent elevations of serum transaminases}}.</li>"
         "<li>{{CUD/ci-strong-cyp3a4|Concomitant use of strong CYP3A4 inhibitors such as ketoconazole, itraconazole or clarithromycin}} (see section 4.5).</li>"
         "<li>{{CUD/ci-pregnancy|Pregnancy}} and {{CUD/ci-breastfeeding|breast-feeding}} (see section 4.6).</li>"
         "</ul>", []),
        ("200000029806", "4.4 Special warnings and precautions for use", "4.4 Special warnings and precautions for use",
         "<p><b>Liver effects</b></p>"
         "<p>{{CUD/warn-liver-enzymes|Liver function tests should be performed before treatment starts, 12 weeks later and periodically thereafter. "
         "Treatment should be stopped if transaminases rise persistently above 3 times the upper limit of normal}}.</p>"
         "<p><b>Blood pressure</b></p>"
         "<p>Small increases in blood pressure were observed in clinical studies. "
         "{{CUD/warn-blood-pressure|Blood pressure should be checked before treatment and at each follow-up visit, particularly in patients with hypertension}}.</p>"
         "<p><b>Excipients</b></p>"
         "<p>{{CUD/warn-lactose|Patients with rare hereditary problems of galactose intolerance, total lactase deficiency or glucose-galactose malabsorption should not take this medicinal product}}.</p>"
         "<p>This medicinal product contains less than 1 mmol sodium (23 mg) per tablet, that is to say essentially sodium-free.</p>", []),
        ("200000029809", "4.5 Interaction with other medicinal products and other forms of interaction",
         "4.5 Interaction with other medicinal products and other forms of interaction",
         "<p>Sakuramil is metabolised mainly by cytochrome P450 3A4 (CYP3A4).</p>"
         "<p><b>Strong CYP3A4 inhibitors</b></p>"
         "<p>{{CUD/int-cyp3a4-strong|Ketoconazole increased Sakuramil exposure (AUC) about 4-fold}}. "
         "Use with strong CYP3A4 inhibitors is contraindicated (see section 4.3).</p>"
         "<p><b>Moderate CYP3A4 inhibitors</b></p>"
         "<p>{{CUD/int-cyp3a4-moderate|Diltiazem and verapamil increased Sakuramil exposure about 2-fold. The dose must not exceed 20 mg once daily}}.</p>"
         "<p><b>CYP3A4 inducers</b></p>"
         "<p>{{CUD/int-rifampicin|Rifampicin reduced Sakuramil exposure by about 70%. Concomitant use should be avoided}}.</p>"
         "<p><b>Grapefruit juice</b></p>"
         "<p>{{CUD/int-grapefruit|Large quantities of grapefruit juice (more than 1 litre a day) should be avoided}}.</p>"
         "<p><b>Warfarin</b></p>"
         "<p>{{CUD/int-warfarin|A small increase in INR was seen with warfarin. INR should be monitored when Sakura Bloom is started, stopped or its dose changed}}.</p>", []),
        ("200000029811", "4.6 Fertility, pregnancy and lactation", "4.6 Fertility, pregnancy and lactation",
         "<p><b>Pregnancy</b></p>"
         "<p>There are no data from the use of Sakuramil in pregnant women. Animal studies have shown reproductive toxicity (see section 5.3). "
         "{{CUD/ci-pregnancy|Sakura Bloom is contraindicated during pregnancy}}. Women of childbearing potential should use effective contraception during treatment.</p>"
         "<p><b>Breast-feeding</b></p>"
         "<p>It is unknown whether Sakuramil is excreted in human milk. {{CUD/ci-breastfeeding|Sakura Bloom is contraindicated during breast-feeding}}.</p>"
         "<p><b>Fertility</b></p><p>No human data are available. Animal studies did not show effects on fertility.</p>", []),
        ("200000029815", "4.7 Effects on ability to drive and use machines", "4.7 Effects on ability to drive and use machines",
         "<p>Sakura Bloom has minor influence on the ability to drive and use machines. "
         "{{CUD/ue-dizziness|Dizziness has been reported}}; patients who experience it should not drive or use machines.</p>", []),
        ("200000029816", "4.8 Undesirable effects", "4.8 Undesirable effects",
         "<p><b>Summary of the safety profile</b></p>"
         "<p>The most common adverse reactions were headache, nausea and myalgia. In clinical studies 3.1% of patients stopped treatment because of an adverse reaction.</p>"
         "<p><b>Tabulated list of adverse reactions</b></p>"
         "<p>Frequencies are defined as very common (≥1/10), common (≥1/100 to &lt;1/10), uncommon (≥1/1,000 to &lt;1/100), "
         "rare (≥1/10,000 to &lt;1/1,000) and very rare (&lt;1/10,000).</p>"
         "[[UE_TABLE]]"
         "<p><b>Reporting of suspected adverse reactions</b></p>"
         "<p>Healthcare professionals are asked to report any suspected adverse reactions via the national reporting system.</p>", []),
        ("200000029819", "4.9 Overdose", "4.9 Overdose",
         "<p>There is no specific treatment for overdose. Supportive measures should be taken and liver function monitored. "
         "Haemodialysis is not expected to remove Sakuramil because it is highly bound to plasma proteins.</p>", []),
    ]),
    ("200000029821", "5. PHARMACOLOGICAL PROPERTIES", "5. Pharmacological properties", "<p>Pharmacological properties.</p>", [
        ("200000029822", "5.1 Pharmacodynamic properties", "5.1 Pharmacodynamic properties",
         "<p>Pharmacotherapeutic group: lipid modifying agents, other. ATC code: not assigned (fictitious substance).</p>"
         "<p><b>Mechanism of action</b></p>"
         "<p>{{SD/sakuramil|Sakuramil}} is a fictitious substance created for the ICH M4Q(R2) mock-up. In this example it is described as an orally active agent that lowers LDL-C.</p>"
         "<p><b>Clinical efficacy</b></p>"
         "<p>In a fictitious 12-week, placebo-controlled study in 480 adults with primary hypercholesterolaemia, LDL-C fell by 31% with 20 mg and 38% with 40 mg, "
         "compared with 3% with placebo.</p>", []),
        ("200000029827", "5.2 Pharmacokinetic properties", "5.2 Pharmacokinetic properties",
         "<p><b>Absorption</b></p><p>Peak plasma concentrations are reached 2 to 4 hours after an oral dose. Food has no relevant effect.</p>"
         "<p><b>Distribution</b></p><p>Sakuramil is more than 99% bound to plasma proteins.</p>"
         "<p><b>Biotransformation</b></p><p>Sakuramil is metabolised mainly by CYP3A4 to inactive metabolites.</p>"
         "<p><b>Elimination</b></p><p>The terminal half-life is about 30 hours. Elimination is mainly in the faeces.</p>"
         "<p><b>Renal impairment</b></p><p>Exposure was about 1.6-fold higher in severe renal impairment (see section 4.2).</p>", []),
        ("200000029834", "5.3 Preclinical safety data", "5.3 Preclinical safety data",
         "<p>In fictitious repeat-dose studies, increased liver weight and transaminases were seen at exposures above 10 times the clinical exposure. "
         "Embryo-fetal toxicity was observed in rats at maternally toxic doses.</p>", []),
    ]),
    ("200000029836", "6. PHARMACEUTICAL PARTICULARS", "6. Pharmaceutical particulars", "<p>Pharmaceutical particulars.</p>", [
        ("200000029837", "6.1 List of excipients", "6.1 List of excipients",
         "<p><i>Tablet core</i></p><ul>"
         "<li>{{ING/ing-lactose-monohydrate|Lactose monohydrate}}</li>"
         "<li>{{ING/ing-microcrystalline-cellulose|Microcrystalline cellulose}}</li>"
         "<li>{{ING/ing-croscarmellose-sodium|Croscarmellose sodium}}</li>"
         "<li>{{ING/ing-hydroxypropyl-cellulose|Hydroxypropyl cellulose}}</li>"
         "<li>{{ING/ing-magnesium-stearate|Magnesium stearate}}</li></ul>"
         "<p><i>Film-coating</i></p><ul>"
         "<li>{{ING/ing-hypromellose|Hypromellose}}</li>"
         "<li>{{ING/ing-macrogol-6000|Macrogol 6000}}</li>"
         "<li>{{ING/ing-titanium-dioxide|Titanium dioxide (E171)}}</li>"
         "<li>{{ING/ing-iron-oxide-red|Iron oxide red (E172)}}</li></ul>", []),
        ("200000029838", "6.2 Incompatibilities", "6.2 Incompatibilities", "<p>Not applicable.</p>", []),
        ("200000029839", "6.3 Shelf life", "6.3 Shelf life",
         "<p>Blister: {{PPD/ppd-blister-28|3 years}}.</p><p>Bottle: {{PPD/ppd-bottle-30|3 years}}.</p>", []),
        ("200000029840", "6.4 Special precautions for storage", "6.4 Special precautions for storage",
         "<p>{{PPD/ppd-blister-28|This medicinal product does not require any special storage conditions}}.</p>", []),
        ("200000029841", "6.5 Nature and contents of container", "6.5 Nature and contents of container",
         "<p>{{PPD/ppd-blister-28|PA/Al/PVC blisters in a carton. Pack size: 28 film-coated tablets}}.</p>"
         "<p>{{PPD/ppd-bottle-30|White HDPE bottle with a child-resistant polypropylene closure and induction seal, in a carton. Pack size: 30 film-coated tablets}}.</p>"
         "<p>Not all pack sizes may be marketed.</p>", []),
        ("200000029842", "6.6 Special precautions for disposal", "6.6 Special precautions for disposal",
         "<p>No special requirements. Any unused medicinal product or waste material should be disposed of in accordance with local requirements.</p>", []),
    ]),
    ("200000029844", "7. MARKETING AUTHORISATION HOLDER", "7. Marketing authorisation holder",
     "<p>{{ORG/sakura-pharma-eu|Sakura Pharmaceuticals Europe B.V.<br/>Bloesemlaan 1<br/>1000 AA Amsterdam<br/>Netherlands}}</p>", []),
    ("200000029845", "8. MARKETING AUTHORISATION NUMBER(S)", "8. Marketing authorisation number(s)",
     "<p>{{RA/ra-sakura-bloom-001|EU/1/00/0000/001}} (28 film-coated tablets, blister)</p>"
     "<p>{{RA/ra-sakura-bloom-002|EU/1/00/0000/002}} (30 film-coated tablets, bottle)</p>", []),
    ("200000029846", "9. DATE OF FIRST AUTHORISATION/RENEWAL OF THE AUTHORISATION",
     "9. Date of first authorisation/renewal of the authorisation",
     "<p>Date of first authorisation: {{RA/ra-sakura-bloom-001|02 March 2026}}</p>", []),
    ("200000029847", "10. DATE OF REVISION OF THE TEXT", "10. Date of revision of the text", "<p>11/2026</p>", []),
])

# ---------------------------------------------------------------- Package leaflet
# PIL headings use a local example code system (codes pil-0 .. pil-6): the EMA list codes for
# package-leaflet headings were not verified for this showcase.
PIL = {
 "en": ("pil-0", "PACKAGE LEAFLET: INFORMATION FOR THE PATIENT", "Package leaflet: information for the patient",
   SYNTH_NOTE_EN +
   "<p><b>Sakura Bloom 20 mg film-coated tablets</b><br/>Sakuramil</p>"
   "<p>Read all of this leaflet carefully before you start taking this medicine because it contains important information for you.</p>"
   "<ul><li>Keep this leaflet. You may need to read it again.</li>"
   "<li>If you have any further questions, ask your doctor or pharmacist.</li>"
   "<li>This medicine has been prescribed for you only. Do not pass it on to others.</li>"
   "<li>If you get any side effects, talk to your doctor or pharmacist. See section 4.</li></ul>", [
   ("pil-1", "1. What Sakura Bloom is and what it is used for", "1. What Sakura Bloom is and what it is used for",
    "<p>Sakura Bloom contains the active substance {{SD/sakuramil|Sakuramil}}. It lowers the amount of LDL-cholesterol, sometimes called bad cholesterol, in your blood.</p>"
    "<p>Sakura Bloom is used {{CUD/ind-hypercholesterolaemia|together with a cholesterol-lowering diet in adults whose cholesterol is too high}} "
    "when diet and exercise alone have not been enough.</p>", []),
   ("pil-2", "2. What you need to know before you take Sakura Bloom", "2. What you need to know before you take Sakura Bloom",
    "<p><b>Do not take Sakura Bloom</b></p><ul>"
    "<li>{{CUD/ci-hypersensitivity|if you are allergic to Sakuramil or any of the other ingredients of this medicine}} (listed in section 6)</li>"
    "<li>{{CUD/ci-liver|if you have liver disease}}</li>"
    "<li>{{CUD/ci-strong-cyp3a4|if you take ketoconazole or itraconazole (for fungal infections) or clarithromycin (for bacterial infections)}}</li>"
    "<li>{{CUD/ci-pregnancy|if you are pregnant}} or {{CUD/ci-breastfeeding|breast-feeding}}</li></ul>"
    "<p><b>Warnings and precautions</b></p><p>Talk to your doctor or pharmacist before taking Sakura Bloom:</p><ul>"
    "<li>{{CUD/warn-liver-enzymes|Your doctor will do a blood test to check your liver before you start and during treatment}}.</li>"
    "<li>{{CUD/warn-blood-pressure|if you have high blood pressure. Your doctor will check your blood pressure regularly}}.</li>"
    "<li>{{CUD/warn-renal-severe|if you have severe kidney problems. You should not take more than 20 mg a day}}.</li></ul>"
    "<p><b>Children and adolescents</b></p><p>{{GRP/grp-adults|Do not give this medicine to children and adolescents under 18 years}}, because it has not been studied in this age group.</p>"
    "<p><b>Other medicines and Sakura Bloom</b></p><p>Tell your doctor or pharmacist if you are taking, have recently taken or might take any other medicines, in particular:</p><ul>"
    "<li>{{CUD/int-cyp3a4-moderate|diltiazem or verapamil (for high blood pressure or heart problems). You should not take more than 20 mg of Sakura Bloom a day}}</li>"
    "<li>{{CUD/int-rifampicin|rifampicin (for tuberculosis), which can stop Sakura Bloom working well}}</li>"
    "<li>{{CUD/int-warfarin|warfarin (to prevent blood clots). Your doctor may check your blood more often}}</li></ul>"
    "<p><b>Sakura Bloom with food and drink</b></p><p>{{CUD/int-grapefruit|Do not drink more than 1 litre of grapefruit juice a day}}.</p>"
    "<p><b>Pregnancy and breast-feeding</b></p><p>{{CUD/ci-pregnancy|Do not take Sakura Bloom if you are pregnant}} or {{CUD/ci-breastfeeding|breast-feeding}}. "
    "If you could become pregnant, use effective contraception while taking this medicine.</p>"
    "<p><b>Driving and using machines</b></p><p>{{CUD/ue-dizziness|Sakura Bloom can make some people feel dizzy}}. If this happens to you, do not drive or use machines.</p>"
    "<p><b>Sakura Bloom contains lactose and sodium</b></p><p>{{CUD/warn-lactose|If you have been told by your doctor that you have an intolerance to some sugars, contact your doctor before taking this medicine}}. "
    "This medicine contains less than 1 mmol sodium (23 mg) per tablet, that is to say essentially sodium-free.</p>", []),
   ("pil-3", "3. How to take Sakura Bloom", "3. How to take Sakura Bloom",
    "<p>Always take this medicine exactly as your doctor or pharmacist has told you. Check with your doctor or pharmacist if you are not sure.</p>"
    "<p>{{CUD/ind-hypercholesterolaemia|The recommended dose is one 20 mg tablet once a day}}. Your doctor may increase it to 40 mg once a day after at least 4 weeks. "
    "{{MPD/sakura-bloom-20mg|Do not take more than 40 mg a day}}.</p>"
    "<p>{{APD/apd-sakura-bloom-20mg|Swallow the tablet whole with a glass of water}}, with or without food, at about the same time each day.</p>"
    "<p><b>If you take more Sakura Bloom than you should</b></p><p>Contact your doctor or the nearest hospital emergency department.</p>"
    "<p><b>If you forget to take Sakura Bloom</b></p><p>Take the next dose at the usual time. Do not take a double dose to make up for a forgotten tablet.</p>"
    "<p><b>If you stop taking Sakura Bloom</b></p><p>Talk to your doctor first, because your cholesterol may rise again.</p>", []),
   ("pil-4", "4. Possible side effects", "4. Possible side effects",
    "<p>Like all medicines, this medicine can cause side effects, although not everybody gets them.</p>"
    "<p><b>Stop taking Sakura Bloom and see a doctor straight away if you get</b> {{CUD/ue-angioedema|swelling of the face, lips, tongue or throat}}.</p>"
    "[[PIL_SE]]"
    "<p><b>Reporting of side effects</b></p><p>If you get any side effects, talk to your doctor or pharmacist. You can also report side effects directly via the national reporting system.</p>", []),
   ("pil-5", "5. How to store Sakura Bloom", "5. How to store Sakura Bloom",
    "<p>Keep this medicine out of the sight and reach of children.</p>"
    "<p>Do not use this medicine after the expiry date which is stated on the carton and the blister or bottle after EXP.</p>"
    "<p>{{PPD/ppd-blister-28|This medicine does not require any special storage conditions}}.</p>"
    "<p>Do not throw away any medicines via wastewater or household waste. Ask your pharmacist how to throw away medicines you no longer use.</p>", []),
   ("pil-6", "6. Contents of the pack and other information", "6. Contents of the pack and other information",
    "<p><b>What Sakura Bloom contains</b></p>"
    "<ul><li>The active substance is Sakuramil. {{ING/ing-sakuramil|Each film-coated tablet contains 20 mg Sakuramil}}.</li>"
    "<li>The other ingredients are: tablet core: {{ING/ing-lactose-monohydrate|lactose monohydrate}}, {{ING/ing-microcrystalline-cellulose|microcrystalline cellulose}}, "
    "{{ING/ing-croscarmellose-sodium|croscarmellose sodium}}, {{ING/ing-hydroxypropyl-cellulose|hydroxypropyl cellulose}}, {{ING/ing-magnesium-stearate|magnesium stearate}}; "
    "film-coating: {{ING/ing-hypromellose|hypromellose}}, {{ING/ing-macrogol-6000|macrogol 6000}}, {{ING/ing-titanium-dioxide|titanium dioxide (E171)}}, "
    "{{ING/ing-iron-oxide-red|iron oxide red (E172)}}.</li></ul>"
    "<p><b>What Sakura Bloom looks like and contents of the pack</b></p>"
    "<p>{{MID/sakura-bloom-20mg-tablet|Sakura Bloom tablets are pale red, round film-coated tablets marked SB on one side and 20 on the other}}.</p>"
    '<p><img src="#tablet-image" alt="Pale red round film-coated tablet debossed SB and 20"/></p>'
    "<p>They come in {{PPD/ppd-blister-28|cartons of 28 tablets in blisters}} and {{PPD/ppd-bottle-30|bottles of 30 tablets}}. Not all pack sizes may be marketed.</p>"
    "<p><b>Marketing Authorisation Holder</b></p><p>{{ORG/sakura-pharma-eu|Sakura Pharmaceuticals Europe B.V., Bloesemlaan 1, 1000 AA Amsterdam, Netherlands}}</p>"
    "<p><b>Manufacturer</b></p><p>{{ORG/aparna-pharm|Aparna Pharmaceutical Manufacturing Pte. Ltd., 10 Green Road, Gulshan, Bangladesh}}</p>"
    "<p>This leaflet was last revised in 11/2026.</p>", []),
 ])
}

# frequency vocabulary used by the generated blocks
FREQ = {
  "common":   {"rank": 2, "en": "Common", "en_pil": "Common (may affect up to 1 in 10 people)"},
  "uncommon": {"rank": 3, "en": "Uncommon", "en_pil": "Uncommon (may affect up to 1 in 100 people)"},
  "rare":     {"rank": 4, "en": "Rare", "en_pil": "Rare (may affect up to 1 in 1,000 people)"},
}
SOC_ORDER = ["Immune system disorders", "Psychiatric disorders", "Nervous system disorders", "Vascular disorders",
             "Gastrointestinal disorders", "Hepatobiliary disorders", "Skin and subcutaneous tissue disorders",
             "Musculoskeletal and connective tissue disorders", "Investigations"]

# ---------------------------------------------------------------- Instructions for use (EN)
# Local example code system for headings (ifu-0 .. ifu-7). [[PICTO:n]] inserts step pictogram n
# (contained Binary picto-n, drawings made for this showcase).
IFU = ("ifu-0", "INSTRUCTIONS FOR USE", "Instructions for use",
  SYNTH_NOTE_EN +
  "<p><b>Sakura Bloom 20 mg film-coated tablets</b><br/>Opening the bottle and taking your tablet</p>"
  "<p>For the {{PPD/ppd-bottle-30|30-tablet bottle with a child-resistant cap}}. Read these steps the first time you open a new bottle.</p>"
  "<p><b>You will need:</b> the bottle and a glass of water.</p>", [
  ("ifu-1", "Step 1. Check the pack", "Step 1. Check the pack",
   "[[PICTO:1]]<p>Check the expiry date on the label and that the cap has not been opened.</p>", []),
  ("ifu-2", "Step 2. Push down and turn", "Step 2. Push down and turn",
   "[[PICTO:2]]<p>Press the cap down firmly and, while pressing, turn it anticlockwise to open.</p>", []),
  ("ifu-3", "Step 3. Remove the seal", "Step 3. Remove the seal",
   "[[PICTO:3]]<p>The first time only, peel off the foil seal using the tab. Do not use the bottle if the seal is broken.</p>", []),
  ("ifu-4", "Step 4. Take out one tablet", "Step 4. Take out one tablet",
   "[[PICTO:4]]<p>Tip one tablet into your hand. {{MID/sakura-bloom-20mg-tablet|Check it is pale red, round and marked SB}}.</p>", []),
  ("ifu-5", "Step 5. Swallow it whole", "Step 5. Swallow it whole",
   "[[PICTO:5]]<p>{{APD/apd-sakura-bloom-20mg|Swallow the tablet whole with a glass of water}}, with or without food. Do not crush or chew it.</p>", []),
  ("ifu-6", "Step 6. Close the cap", "Step 6. Close the cap",
   "[[PICTO:6]]<p>Turn the cap clockwise until it clicks, so children cannot open it. Keep the bottle out of the sight and reach of children.</p>", []),
  ("ifu-7", "If you have trouble opening the cap", "If you have trouble opening the cap",
   "<p>Ask your pharmacist about other ways to open it. Do not move the tablets to another container. "
   "For dosing, missed doses and side effects, read the package leaflet.</p>", []),
])

_S = 'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 110" width="120" height="110" fill="none" stroke="#172B4D" stroke-width="2.5" stroke-linejoin="round"'
PICTOS = {
 1: f'<svg {_S}><rect x="45" y="20" width="30" height="12" rx="3"/><path d="M40 38c0-3 3-6 6-6h28c3 0 6 3 6 6v56a3 3 0 0 1-3 3H43a3 3 0 0 1-3-3z"/><path d="M40 52h40M40 82h40"/><circle cx="60" cy="67" r="7" stroke="#0071e3"/><path d="M57 67l2 2 4-4" stroke="#0071e3"/></svg>',
 2: f'<svg {_S}><rect x="40" y="46" width="40" height="16" rx="4"/><path d="M42 66h36v34H42z"/><path d="M60 14v24M52 30l8 8 8-8" stroke="#0071e3"/><path d="M86 40a26 26 0 0 1 0 28M93 64l-7 4-1-8" stroke="#0071e3"/></svg>',
 3: f'<svg {_S}><path d="M38 52h44v48H38z"/><ellipse cx="60" cy="52" rx="22" ry="6"/><path d="M58 50c6-14 16-22 30-26l4 8c-12 4-20 10-24 20" fill="#EAF3FE" stroke="#0071e3"/></svg>',
 4: f'<svg {_S}><path d="M24 66c0 18 16 30 36 30s36-12 36-30"/><circle cx="60" cy="62" r="11" fill="#E8A9A2" stroke="#C4786F"/><path d="M60 16v26M52 34l8 8 8-8" stroke="#0071e3"/></svg>',
 5: f'<svg {_S}><path d="M70 30h24l-3 66H73z"/><path d="M71 50h22" stroke="#0071e3"/><circle cx="40" cy="44" r="18"/><path d="M32 52c4 4 12 4 16 0"/><path d="M54 70l12-12" stroke="#0071e3"/></svg>',
 6: f'<svg {_S}><rect x="40" y="38" width="40" height="16" rx="4"/><path d="M42 58h36v40H42z"/><path d="M34 30a26 26 0 0 0 0 28M27 54l7 4 1-8" stroke="#0071e3"/></svg>',
}
