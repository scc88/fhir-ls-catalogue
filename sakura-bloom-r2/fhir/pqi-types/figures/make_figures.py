#!/usr/bin/env python3
"""Build the figures that replace the labelled placeholders in the PQI Type 1-4 examples.

Every figure is rebuilt from data in the ICH M4Q(R2) Sakura Bloom mock-up (the narrative around the
placeholder, the QOS tables in source/sakura-bloom-r2-extract.json and the FHIR resources), from the
HL7 PQI example data (uv-dx-pq/input/examples-pdf), or from ICH M7. Where the mock-up names a factor but
gives no number, the number is made up and the figure says so in its DocumentReference description.

Needs: matplotlib, rdkit.   Writes: *.png and manifest.json next to this script.
Usage:  python3 make_figures.py      then   python3 ../fix_pqi_types.py
"""
import json
import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
INK, MUTED, LINE, HEAD, ACC = "#1d1d1f", "#6e6e73", "#c7c7cc", "#eef1f6", "#0b4ea2"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK, "axes.edgecolor": INK,
                     "svg.fonttype": "none", "mathtext.fontset": "dejavusans"})
MANIFEST = {}

MOCKUP = "Redrawn for the PQI examples from data given in the ICH Sakura Bloom mock-up"
SYNTH = "Synthetic illustration made for the PQI examples"


def register(fig_ids, fn, title, description):
    for f in fig_ids if isinstance(fig_ids, list) else [fig_ids]:
        MANIFEST[f] = {"file": fn, "title": title, "description": f"{title}. {description}"}


def save(fig, fn):
    fig.savefig(os.path.join(HERE, fn), dpi=150, facecolor="white", bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


# ---------------------------------------------------------------- formulas
def formula(fn, lines, notes=None, width=7.5):
    h = 0.75 * len(lines) + (0.32 * len(notes) if notes else 0) + 0.2
    fig = plt.figure(figsize=(width, h))
    y = 1 - 0.5 / h
    for ln in lines:
        fig.text(0.04, y, ln, fontsize=15, va="center")
        y -= 0.75 / h
    for n in notes or []:
        fig.text(0.04, y + 0.2 / h, n, fontsize=9.5, color=MUTED, va="center")
        y -= 0.32 / h
    save(fig, fn)


def assay(sub):
    return r"$\mathrm{Content\ of\ " + sub.replace("-", "\\text{-}") + r"\ (\%)} = \dfrac{A_M}{A_S} \times \dfrac{C_S}{C_M} \times V$"


IMP = r"$\mathrm{Impurity\ (\%)} = \dfrac{IWP}{IWR} \times \dfrac{PR}{PP} \times \dfrac{C}{50^{*}} \times RF$"
DIL = r"$50^{*} = \dfrac{1000}{20}$"
DIL_NOTE = ["* exemplary dilution factor: 1000 = dilution of the reference solution, 20 = volume of the test solution"]


def formulas():
    for fid, sub, sec in [("fig-3cb5acc2", "CP-4", "3.2.S.2.3"), ("fig-f8cfa3af", "CP-8", "3.2.S.2.3"),
                          ("fig-c37f64d3", "CP-6", "3.2.S.2.4"), ("fig-fca29d81", "CP-9", "3.2.S.4.2")]:
        fn = f"calc-assay-{sub.lower()}.png"
        formula(fn, [assay(sub)], [f"AM, AS: peak areas of {sub} in the test and reference solutions; CM, CS: weights (mg); V: assay of the {sub} standard (%)"], width=8.2)
        register(fid, fn, f"Calculation of the assay of {sub} (HPLC, external standard)",
                 f"{MOCKUP}: the formula is typeset from the variable definitions in the {sec} procedure; same structure as the assay calculation in the HL7 PQI example 3.2.P.5.2 analytical procedure.")
    formula("calc-enantiomer-cp-4.png", [r"$\mathrm{Enantiomer\ (\%)} = \dfrac{r_i}{r_t} \times 100$"],
            ["ri: response of the enantiomer peak; rt: sum of the CP-4 and CP-4 enantiomer responses (test solution)"])
    register("fig-f242b2ef", "calc-enantiomer-cp-4.png", "Calculation of the CP-4 enantiomer content (chiral HPLC)",
             f"{MOCKUP}: typeset from the variable definitions in the 3.2.S.2.3 procedure.")
    formula("calc-impurities-rf.png", [IMP],
            ["IWP, IWR: integration values in the test and reference solutions; PR, PP: initial concentrations (mg/mL);",
             "C: content of the reference substance (%); RF: response correction factor"], width=8.6)
    register(["fig-498bc2d6", "fig-4014f47e", "fig-9454a19c", "fig-9cbf8c6c"], "calc-impurities-rf.png",
             "Calculation of specified and unspecified impurities against the reference substance, with response correction factor",
             f"{MOCKUP}: typeset from the variable definitions and dilution factor given in the procedure; the response-factor correction follows the HL7 PQI example 3.2.P.5.2 analytical procedure.")
    formula("calc-dilution-factor.png", [DIL], DIL_NOTE, width=7.6)
    register(["fig-b2f4b126", "fig-02b55165", "fig-9ff338b0", "fig-b5581a7f"], "calc-dilution-factor.png",
             "Exemplary dilution factor used in the impurity calculation",
             f"{MOCKUP}: values given in the procedure (20 mL test solution, 1:1000 reference dilution).")
    formula("calc-impurities-rf-cp-9.png", [IMP, DIL], DIL_NOTE + ["RF: CP-9-1 = 1.23, CP-8 = 2.01 (as given in the procedure)"], width=8.6)
    register("fig-08ad9626", "calc-impurities-rf-cp-9.png", "Calculation of related substances of Sakuramil (CP-9), with dilution factor",
             f"{MOCKUP}: typeset from the variable definitions, dilution factor and response factors given in the 3.2.S.4.2 procedure.")
    formula("calc-dp-assay.png", [r"$C_V\ (\%) = \dfrac{PA_{TV} \times m_{RV} \times V_T \times C_{RV} \times 2}{PA_{RV} \times V_R \times m_{DV} \times n}$"],
            ["PA: peak areas (test solution 1, reference solution); mRV: mass of reference (mg); VT, VR: volumes (mL); CRV: reference content (%);",
             "2: dilution factor of test solution 1; mDV: declared content (mg per unit); n: number of units"], width=9.4)
    register("fig-3838218f", "calc-dp-assay.png", "Calculation of the assay of Sakuramil in Sakura Bloom 20 mg film-coated tablets",
             f"{MOCKUP}: typeset from the symbol table that follows it in the 3.2.P.5.2 procedure; same structure as the HL7 PQI example 3.2.P.5.2 assay calculation.")
    formula("calc-dp-degradation.png", [r"$D_{pi}\ (\%) = \dfrac{PA_{Ti} \times m_{RV} \times V_T \times C_{RV} \times 2}{PA_{RV} \times V_R \times m_{DV} \times n \times Z_i}$"],
            ["PATi: peak area of the individual degradation product; Zi: relative UV response factor (CP-9-1: 0.77; unspecified: 1.00)",
             "other symbols as for the assay calculation"], width=9.4)
    register("fig-4919fb3a", "calc-dp-degradation.png", "Calculation of individual degradation products in Sakura Bloom 20 mg film-coated tablets",
             f"{MOCKUP}: typeset from the symbol table that follows it in the 3.2.P.5.2 procedure; response-factor correction as in the HL7 PQI example 3.2.P.5.2 procedure.")


# ---------------------------------------------------------------- tables
def table(fn, title, header, rows, widths, note=None, fs=9, header_rows=True, title_on=True):
    W = sum(widths)
    cpi = lambda w: max(4, int((w - 0.12) * 72 / (fs * 0.56)))
    wrapped = [[textwrap.wrap(str(c), cpi(w)) or [""] for c, w in zip(r, widths)] for r in rows]
    hwrap = [textwrap.wrap(h, cpi(w)) or [""] for h, w in zip(header, widths)] if header else None
    lh = fs / 72 * 1.45
    rh = [max(len(c) for c in r) * lh + 0.14 for r in wrapped]
    hh = (max(len(c) for c in hwrap) * lh + 0.16) if hwrap else 0
    th = 0.42 if title_on and title else 0
    nh = 0.3 * len(note) if note else 0
    H = th + hh + sum(rh) + nh + 0.1
    fig = plt.figure(figsize=(W + 0.2, H))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(-0.1, W + 0.1); ax.set_ylim(H, 0); ax.axis("off")
    y = 0.05
    if th:
        ax.text(0, y + 0.16, title, fontsize=fs + 2, fontweight="bold", va="center"); y += th
    def draw(cells, h, bg, bold=False):
        x = 0
        for c, w in zip(cells, widths):
            ax.add_patch(Rectangle((x, y), w, h, facecolor=bg, edgecolor=LINE, lw=0.8))
            ax.text(x + 0.06, y + 0.08, "\n".join(c), fontsize=fs, va="top", fontweight="bold" if bold else "normal", linespacing=1.35)
            x += w
    if hwrap:
        draw(hwrap, hh, HEAD, True); y += hh
    for c, h in zip(wrapped, rh):
        draw(c, h, "white"); y += h
    for n in note or []:
        ax.text(0, y + 0.18, n, fontsize=fs - 1, color=MUTED, va="center"); y += 0.3
    save(fig, fn)


SYN_NUM = "the factors come from the mock-up text; numeric levels the mock-up does not give are made up"


def risk_tables():
    table("ra-focus-areas.png", "Table 3-1  Focus areas in the risk assessment of the Sakuramil manufacturing process",
          ["Step", "Focus area", "Unit operation", "Main materials / controls"],
          [["Step 3", "FA1", "Charging", "CP-6, tetrahydrofuran (THF), sodium carbonate"],
           ["", "FA2", "Carbamoylation at reflux", "Ethyl chloroformate"],
           ["", "FA3", "Filtration and quench", "Sodium hydroxide solution"],
           ["", "FA4", "Extraction and phase separation", "n-Hexane"],
           ["", "FA5", "Solvent exchange", "Ethanol"],
           ["", "FA6", "Crystallization, isolation, drying of CP-7", "Water addition (CPP #3.1)"],
           ["Step 4", "FA1", "Charging", "CP-7, CP-8, methylene chloride"],
           ["", "FA2", "Coupling reaction", "TBAB, aqueous sodium hydroxide"],
           ["", "FA3", "Quench and phase separation", "Methylene chloride, water"],
           ["", "FA4", "Solvent exchange", "Ethanol (IPC #1, ≤ 5000 ppm)"],
           ["", "FA5", "Crystallization", "Water addition (CPP #4.1), cooling rate (CPP #4.2, IPC #2)"],
           ["", "FA6", "Filtration, washing, drying of Sakuramil", "—"]],
          [0.8, 0.9, 3.0, 3.6])
    register("fig-84e85761", "ra-focus-areas.png", "Table 3-1 Focus Area in Risk Assessment for Manufacturing Process of Sakuramil",
             f"{MOCKUP}: focus areas FA1-FA6 derived from the Step 3 and Step 4 process descriptions, CPPs and IPCs of the drug substance manufacturing process.")

    H, M, L = "High", "Medium", "Low"
    table("ra-cande-parameters.png", "Table 3-2  Examples of process parameters assessed at the initial risk assessment (C&E matrix)",
          ["Step / FA", "Process parameter", "Attribute potentially affected", "Initial risk"],
          [["3 / FA1", "THF volume", "CP-7-1, other impurities", H], ["3 / FA2", "Ethyl chloroformate stoichiometry", "CP-7-1", H],
           ["3 / FA2", "Sodium carbonate amount", "CP-7-1, conversion", H], ["3 / FA2", "Sodium carbonate particle size", "Reaction rate, purity", M],
           ["3 / FA2", "Agitation speed", "Reaction rate", M], ["3 / FA3", "Quench time and agitation", "Residual ethyl chloroformate", L],
           ["3 / FA6", "Water addition (% w/w of ethanol)", "CP-7-1 purge, yield", H], ["4 / FA2", "Sodium hydroxide amount", "Conversion, CP-8", M],
           ["4 / FA2", "Agitation speed", "Conversion (phase dispersion)", H], ["4 / FA2", "Reaction temperature (12-25 °C)", "Conversion, impurities", M],
           ["4 / FA5", "Water addition (% w/w of ethanol)", "CP-8 purge", H], ["4 / FA5", "Cooling rate", "CP-8 purge", H],
           ["4 / FA6", "Drying temperature and time", "Residual solvents", L]],
          [1.0, 2.8, 2.6, 1.2], note=["Parameters as named in the mock-up text; risk levels assigned for the PQI examples."])
    register("fig-16083f0c", "ra-cande-parameters.png", "Table 3-2 Examples of Process Parameters Assessed at Initial Risk Assessment",
             f"{SYNTH}: the parameters are those the mock-up text names for Steps 3 and 4; the risk levels are made up.")

    table("ra-cqa-matrix.png", "Table 3-3  Designation of possibility which affect Sakuramil CQAs through a risk assessment",
          ["Unit operation", "Assay", "CP-7-1", "CP-8", "CP-8-25I / -24I", "PMI (CP-3 to CP-6)", "Unspecified", "Residual solvents"],
          [["Step 3 reaction", L, H, "—", "—", L, M, L], ["Step 3 crystallization", L, M, "—", "—", L, M, M],
           ["Step 4 reaction", M, L, H, M, L, M, L], ["Step 4 crystallization", M, L, H, M, L, M, M], ["Step 4 drying", L, "—", "—", "—", "—", L, H]],
          [1.9, 0.75, 0.8, 0.75, 1.15, 1.2, 1.0, 1.15], note=["High: studied by DoE. Medium: studied by fate-and-purge or stress. Low: no further study."])
    register("fig-4adc4b56", "ra-cqa-matrix.png", "Table 3-3 Designation of Possibility Which Affect on Sakuramil CQA through a Risk Assessment",
             f"{SYNTH}: rows and CQAs follow the mock-up (CP-7-1 formed in Step 3, CP-8 purged in Step 4 crystallization, PMIs controlled in starting material and intermediate specifications); the ratings are made up.")

    table("ra-focus-identified.png", "Table 3-4  Focus areas identified for the Sakuramil manufacturing process",
          ["Focus area", "Quality attributes", "Parameters studied", "Study"],
          [["Step 3 reaction (FA2)", "CP-7-1 (ethyl homolog), other impurities", "Ethyl chloroformate and base stoichiometry, THF volume", "Central composite DoE (Table 3-5)"],
           ["Step 3 crystallization (FA6)", "CP-7-1, total impurities", "Water addition, cooling rate, final temperature, hold time", "DoE (Table 3-6)"],
           ["Step 4 reaction (FA2)", "CP-8, unreacted CP-7", "Sodium hydroxide, TBAB, reaction temperature", "Hybrid response surface (Table 3-8)"],
           ["Step 4 crystallization (FA5)", "CP-8, PMIs", "Water addition, cooling rate and five further factors", "2^(7-3) fractional factorial (Table 3-9)"]],
          [2.0, 2.3, 2.9, 2.2])
    register("fig-a611e8db", "ra-focus-identified.png", "Table 3-4 Focus Areas Identified for the Sakuramil Manufacturing Process",
             f"{MOCKUP}: focus areas, attributes, parameters and designs as described in the 3.2.S.2.2 narrative.")


def doe_tables():
    table("doe-step3-reaction.png", "Table 3-5  Step 3 reaction DoE (central composite design)",
          ["Factor", "Low (−1)", "Centre (0)", "High (+1)", "Standard process"],
          [["Ethyl chloroformate (equiv.)", "1.5", "2.5", "3.5", "2.5"], ["Sodium carbonate (equiv.)", "1.5", "2.25", "3.0", "2.0"],
           ["THF volume (L/kg CP-6)", "6", "8", "10", "8"]],
          [2.8, 1.0, 1.0, 1.0, 1.5],
          note=["20 runs: 8 factorial, 6 axial (α = 1.68) and 6 centre points, at reflux (66 °C), sampled up to 36 h.",
                "Responses: CP-7-1 (%), other impurities (%), conversion. Acceptance criterion for CP-7-1 in CP-7: ≤ 0.15 %."])
    register("fig-95354845", "doe-step3-reaction.png", "Table 3-5 Step 3 Reaction DoE",
             f"{SYNTH}: {SYN_NUM}. The standard charge of 2.5 equiv. ethyl chloroformate, reflux at 66 °C, the 36-hour hold and the 0.15 % criterion are from the mock-up.")
    table("doe-step3-crystallization.png", "Table 3-6  Step 3 crystallization DoE",
          ["Factor", "Low", "High", "Standard process"],
          [["Water addition (% w/w of ethanol)", "25", "35", "30-32"], ["Cooling rate (°C/min)", "0.1", "0.5", "0.3"],
           ["Final temperature (°C)", "0", "10", "5"], ["Hold time before isolation (h)", "1", "6", "2"]],
          [3.2, 1.0, 1.0, 1.6],
          note=["Water addition range = proven acceptable range of CPP #3.1 (25-35 %; operating range 30-32 %).",
                "Input: crude CP-7 with a non-typical, high level of CP-7-1, so that purge can be observed."])
    register("fig-f930ba12", "doe-step3-crystallization.png", "Table 3-6 Step 3 Crystallization DoE",
             f"{SYNTH}: the water-addition range is the CPP #3.1 proven acceptable range from the mock-up QOS; the other levels are made up.")
    table("mva-step3.png", "Table 3-7  Summary of multivariate analysis results for Step 3",
          ["Parameter", "Range studied", "Effect on CP-7-1", "Effect on other impurities", "Designation"],
          [["Ethyl chloroformate (equiv.)", "1.5-3.5", "Increases at high charge; largest effect is the interaction with base", "None", "Non-critical: clean at the standard 2.5 equiv."],
           ["Sodium carbonate (equiv.)", "1.5-3.0", "Increases at low charge; always < 0.15 % with carbonate", "None", "Non-critical"],
           ["THF volume (L/kg)", "6-10", "Increases at high concentration (low volume)", "Lower when less concentrated", "Non-critical"],
           ["Water addition in crystallization (% w/w)", "25-35", "Slight purge only", "Total impurities 0.3-0.5 %", "Critical: CPP #3.1"],
           ["Cooling rate / hold time", "0.1-0.5 °C/min / 1-6 h", "No change", "No new impurities", "Non-critical"]],
          [2.4, 1.3, 2.0, 1.9, 1.7])
    register("fig-e09ee9bb", "mva-step3.png", "Table 3-7 Summary of Multivariate Analysis Results for Step 3",
             f"{SYNTH}: effects summarised from the mock-up conclusions (CP-7-1 rises with high ethyl chloroformate, low carbonate and high concentration, stays below 0.15 % with carbonate; total impurities 0.3-0.5 %; water addition is CPP #3.1); ranges as in Tables 3-5 and 3-6.")
    table("doe-step4-reaction.png", "Table 3-8  Step 4 reaction DoE (3-parameter hybrid response surface design)",
          ["Factor", "Low", "Centre", "High", "Standard process"],
          [["Sodium hydroxide (equiv.)", "2.0", "3.0", "4.0", "3.0"], ["TBAB (mol %)", "2", "5", "8", "5"],
           ["Reaction temperature (°C)", "12", "18.5", "25", "18-22"]],
          [2.6, 0.9, 0.9, 0.9, 1.5],
          note=["Agitation fixed at a speed that disperses both phases (at 200 rpm only 70 % conversion after 24 h).",
                "Responses: CP-8 remaining (%), unreacted CP-7 (%). The whole studied range is the design space."])
    register("fig-c257a28d", "doe-step4-reaction.png", "Table 3-8 Step 4 Reaction DoE",
             f"{SYNTH}: the temperature range (12-25 °C), the agitation observation and the responses are from the mock-up; the other levels are made up.")
    table("doe-step4-crystallization.png", "Table 3-9  Step 4 crystallization DoE (2^(7-3) fractional factorial, 16 runs)",
          ["", "Factor", "Low (−)", "High (+)"],
          [["A", "Water addition (% w/w of ethanol)", "25", "35"], ["B", "Cooling rate (°C/min)", "0.15", "0.5"],
           ["C", "Seeding temperature (°C)", "35", "45"], ["D", "Seed load (% w/w)", "0.5", "2.0"],
           ["E", "Final temperature (°C)", "0", "10"], ["F", "Hold time (h)", "1", "4"], ["G", "Agitation (rpm)", "100", "200"]],
          [0.4, 3.0, 1.0, 1.0],
          note=["Crude Sakuramil spiked with 3 % CP-8 (2-3 times the maximum from the reaction DoE).",
                "Water addition and cooling rate ranges = proven acceptable ranges of CPP #4.1 and CPP #4.2."])
    register("fig-7d09f749", "doe-step4-crystallization.png", "Table 3-9 Step 4 Crystallization DoE",
             f"{SYNTH}: the design, spike level and the water-addition and cooling-rate ranges (CPP #4.1, #4.2) are from the mock-up; the other five factors and levels are made up.")
    table("mva-step4.png", "Table 3-15  Summary of multivariate analysis results for Step 4",
          ["Parameter", "Range studied", "Effect", "Designation"],
          [["Sodium hydroxide / TBAB / temperature", "See Table 3-8", "CP-8 < 1 % in all runs; 5 % unreacted CP-7 purges", "Non-critical"],
           ["Water addition in crystallization", "25-35 % w/w", "CP-8 rises at high water with fast cooling", "Critical: CPP #4.1"],
           ["Cooling rate", "0.15-0.5 °C/min", "CP-8 rises at fast cooling with high water", "Critical: CPP #4.2 (IPC #2)"],
           ["Seeding, final temperature, hold, agitation", "See Table 3-9", "No impurity > 0.1 %", "Non-critical"]],
          [2.7, 1.5, 3.2, 1.8])
    register("fig-c3394d41", "mva-step4.png", "Table 3-15 Summary of Mulitvariate Analysis Results for Step 4",
             f"{MOCKUP}: conclusions and CPPs as stated in the 3.2.S.2.2 narrative and the CPP resources; ranges as in Tables 3-8 and 3-9.")


def cpp_diagram():
    fig, ax = plt.subplots(figsize=(10, 4.4)); ax.set_xlim(0, 10); ax.set_ylim(0, 4.4); ax.axis("off")
    def box(x, y, w, h, t, fc, ec, bold=False, fs=9.5):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec, lw=1.2))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.35)
    def arrow(x1, y1, x2, y2):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.3))
    ax.text(0.1, 4.2, "Figure 4-1  CPP and CQA (IMA) identified for Step 3 and Step 4", fontsize=11, fontweight="bold")
    box(0.1, 2.3, 1.7, 1.4, "Step 3\nCP-6 → CP-7", "#eef1f6", ACC, True)
    box(0.1, 0.4, 1.7, 1.4, "Step 4\nCP-7 + CP-8\n→ Sakuramil", "#eef1f6", ACC, True)
    box(2.4, 2.45, 2.9, 1.1, "CPP #3.1\nWater addition in crystallization\n25-35 % w/w of ethanol", "#fff4e5", "#b25000")
    box(2.4, 1.05, 2.9, 1.0, "CPP #4.1\nWater addition in crystallization\n25-35 % w/w of ethanol", "#fff4e5", "#b25000")
    box(2.4, 0.0, 2.9, 0.9, "CPP #4.2  Cooling rate\n0.15-0.5 °C/min (IPC #2)", "#fff4e5", "#b25000")
    box(6.0, 2.45, 1.8, 1.1, "IMA in CP-7\nCP-7-1 ≤ 0.15 %", "#e8f7ec", "#248a3d")
    box(6.0, 0.55, 1.8, 1.1, "CQA\nCP-8 ≤ 0.10 %", "#e8f7ec", "#248a3d")
    box(8.3, 1.4, 1.6, 1.4, "Sakuramil drug\nsubstance:\nPurity - related\nsubstances", "#f5f5f7", INK, True, 9)
    arrow(1.8, 3.0, 2.4, 3.0); arrow(1.8, 1.1, 2.4, 1.5); arrow(1.8, 0.9, 2.4, 0.45)
    arrow(5.3, 3.0, 6.0, 3.0); arrow(5.3, 1.5, 6.0, 1.2); arrow(5.3, 0.45, 6.0, 0.95)
    arrow(7.8, 3.0, 8.3, 2.4); arrow(7.8, 1.1, 8.3, 1.8)
    save(fig, "cpp-cqa-step3-step4.png")
    register("fig-2ba025f0", "cpp-cqa-step3-step4.png", "Figure 4-1 CPP and CQA (IMA) Identified for Step 3 and Step 4",
             f"{MOCKUP}: CPPs and proven acceptable ranges from the CPP resources (cpp-ds-3-1, cpp-ds-4-1, cpp-ds-4-2) and IPC #2; limits for CP-7-1 and CP-8 from the narrative and the drug substance specification.")


def dissolution_table():
    table("dissolution-table-4.png", "Table 4  Dissolution test method and specifications",
          ["Parameter", "Details"],
          [["Apparatus", "USP Apparatus II (rotating paddle), Ph. Eur. 2.9.3, USP <711>, JP <6.10>"],
           ["Medium / volume", "McIlvaine buffer pH 4.0 / 900 mL"], ["Agitation speed", "50 ± 2 rpm"], ["Temperature", "37 ± 0.5 °C"],
           ["Specification", "Not less than 80 % (Q) of the declared content after 30 minutes, acceptance table 1 of the harmonized Ph. Eur., USP and JP (release: levels 1 and 2; stability: levels 1, 2 and 3)"]],
          [2.0, 6.0])
    register("fig-e29689b4", "dissolution-table-4.png", "Table 4 Dissolution test method and specifications",
             f"{MOCKUP}: content taken from Table 4 of 2.3.4.DP.D Description in the mock-up extract.")


def m7_tables():
    table("m7-classes.png", "Table 1-1  Classification of substances into classes (ICH M7)",
          ["Class", "Definition", "Proposed action for control"],
          [["1", "Known mutagenic carcinogens", "Control at or below the compound-specific acceptable limit"],
           ["2", "Known mutagens with unknown carcinogenic potential (bacterial mutagenicity positive*, no rodent carcinogenicity data)", "Control at or below acceptable limits (appropriate TTC)"],
           ["3", "Alerting structure, unrelated to the structure of the drug substance; no mutagenicity data", "Control at or below acceptable limits (appropriate TTC) or do a bacterial mutagenicity assay: if non-mutagenic, Class 5; if mutagenic, Class 2"],
           ["4", "Alerting structure, same alert in the drug substance or related compounds (e.g. process intermediates) tested non-mutagenic", "Treat as a non-mutagenic impurity"],
           ["5", "No structural alert, or alerting structure with enough data to show lack of mutagenicity or carcinogenicity", "Treat as a non-mutagenic impurity"]],
          [0.7, 4.3, 3.8])
    register("fig-2a90a174", "m7-classes.png", "Table 1-1 Classification of substances into classes",
             "Redrawn for the PQI examples from ICH M7(R2) Table 1, which the mock-up cites; wording condensed.")
    hdr = ["Substance", "Role / origin", "DEREK Nexus", "SARAH Nexus", "ICH M7 class", "Control"]
    widths = [1.4, 2.2, 1.1, 1.1, 1.0, 3.0]
    rows = [["CP-3", "Impurity of starting material CP-4", "Positive", "Positive", "Class 3", "NMT 0.3 % in the CP-4 starting material specification"],
            ["CP-4", "Starting material SM1 (Step 1)", "Positive", "Positive", "Class 3", "NMT 0.3 % in the CP-6 intermediate specification"],
            ["CP-5", "Intermediate (Step 1)", "Positive", "Positive", "Class 3", "NMT 0.1 % (unspecified) in the CP-6 specification; ICH M7 Option 3"],
            ["CP-6", "Intermediate (Step 2)", "Positive", "Positive", "Class 3", "NMT 37.5 ppm in the drug substance; ICH M7 Option 1"],
            ["CP-7", "Intermediate (Step 3)", "Negative", "Negative", "Class 5", "Non-mutagenic; CP-7 specification"],
            ["CP-7-1", "By-product of Step 3 (ethyl homolog)", "Negative", "Negative", "Class 5", "Non-mutagenic; NMT 0.15 % in the drug substance"],
            ["CP-8", "Starting material SM2 (Step 4)", "Negative", "Negative", "Class 5", "Non-mutagenic; NMT 0.10 % in the drug substance"],
            ["CP-9-1", "Degradation product", "Negative", "Negative", "Class 5", "Non-mutagenic; NMT 0.15 % in the drug substance"],
            ["Methyl chloroformate", "Reagent (Step 1)", "Negative", "Negative", "Class 5", "Non-mutagenic; no specific control"],
            ["Ethyl chloroformate", "Reagent (Step 3)", "Negative", "Negative", "Class 5", "Non-mutagenic; no specific control"]]
    ids = ["fig-a2a791ed", "fig-c5cd1501", "fig-9715e701", "fig-c407d1c7", "fig-58d396c2", "fig-7e96d536", "fig-5367c0ec", "fig-85c8672c", "fig-2a1a6548", "fig-49fcade0"]
    for i, (fid, r) in enumerate(zip(ids, rows)):
        fn = f"m7-results-{i + 1:02d}.png"
        table(fn, "Table 1-2  Results of ICH M7 risk assessment" if i == 0 else None, hdr if i == 0 else None, [r], widths, title_on=(i == 0))
        register(fid, fn, f"Table 1-2 Results of ICH M7 Risk Assessment ({r[0]}, part {i + 1} of 10)",
                 f"{MOCKUP}: classes, (Q)SAR outcomes and controls follow the rationale and control strategy in the mock-up text (Class 3 = aniline-containing, positive in both (Q)SAR systems); roles from the manufacturing process.")


# ---------------------------------------------------------------- plots and structures
def linearity():
    import numpy as np
    level = np.array([60, 78, 94, 112, 130]); conc = level / 1000
    area = np.array([[39.9512, 39.9592, 39.9552], [51.7055, 51.7015, 51.7095], [62.3582, 62.3532, 62.3482], [74.3156, 74.3216, 74.3096], [85.2542, 85.2642, 85.2592]])
    x = np.repeat(conc, 3); y = area.ravel()
    b, a = np.polyfit(x, y, 1); r2 = 1 - ((y - (a + b * x)) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    xx = np.linspace(0.05, 0.14, 10)
    ax.plot(xx, a + b * xx, color=ACC, lw=1.4, label=f"y = {b:.2f}x + {a:.3f}   R² = {r2:.5f}")
    ax.scatter(x, y, s=22, color=INK, zorder=3, label="CP-9 reference standard #B837020 (3 injections per level)")
    ax.set_xlabel("Concentration of Sakuramil (mg/mL)"); ax.set_ylabel("CP-9 peak area (mAU)")
    ax.set_title("Figure 2-4  Linearity plot: Sakuramil", loc="left", fontweight="bold", fontsize=11)
    ax.grid(alpha=.3); ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    save(fig, "linearity-sakuramil.png")
    register("fig-d69c883f", "linearity-sakuramil.png", "Figure 2-4 Linearity Plot: Sakuramil",
             f"{MOCKUP}: points from Table 2-7 (5 levels, 60-130 %, 3 injections); the regression line is fitted to those points.")


def xrpd():
    import numpy as np
    peaks = [(8.9, .45), (10.9, .58), (12.1, .14), (12.9, .07), (13.7, .65), (14.3, .62), (15.1, .48), (15.5, .32), (17.7, .17), (18.2, .2),
             (18.8, .52), (19.1, 1.0), (20.1, .4), (21.0, .08), (21.9, .15), (22.4, .27), (22.7, .2), (23.2, .36), (23.9, .26), (25.1, .27),
             (26.2, .12), (26.7, .19), (27.4, .1), (28.2, .2), (28.9, .1), (29.5, .22), (30.3, .2), (31.8, .1), (33.0, .05), (34.2, .07),
             (38.5, .07), (40.9, .07), (42.1, .05)]
    t = np.linspace(5, 45, 4000)
    fig, ax = plt.subplots(figsize=(9, 5))
    rng = np.random.default_rng(7)
    for k, lab in enumerate(["Initial", "6 months", "24 months", "36 months"]):
        y = 0.05 + 0.02 * np.exp(-(t - 5) / 6)
        for p, h in peaks:
            y += h * (1 - 0.03 * k) * np.exp(-0.5 * ((t - p) / 0.085) ** 2)
        y += rng.normal(0, 0.006, t.size)
        ax.plot(t, y + 1.15 * k, lw=0.8, color=["#0b4ea2", "#0a8fa8", "#5e5ce6", "#248a3d"][k])
        ax.text(45.3, 1.15 * k + 0.08, lab, fontsize=9, va="bottom")
    ax.set_xlim(5, 45); ax.set_yticks([]); ax.set_xlabel("2θ (°)"); ax.set_ylabel("Intensity (offset)")
    ax.set_title("XRPD overlay, Sakuramil drug substance, 25 °C / 60 % RH", loc="left", fontweight="bold", fontsize=11)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    save(fig, "xrpd-overlay-25c60.png")
    register("fig-e4ec73a4", "xrpd-overlay-25c60.png", "XRPD overlay of Sakuramil drug substance at initial, 6, 24 and 36 months (25 °C/60 % RH)",
             f"{SYNTH}: traces built on the peak positions of the HL7 PQI example XRPD pattern (input/examples-pdf) used in Figure 1-9, showing no change of form, as the mock-up states; it does not show measured Sakura Bloom data.")


def structures():
    from rdkit import Chem
    from rdkit.Chem import Draw, rdDepictor
    from rdkit.Chem.Draw import rdMolDraw2D
    rdDepictor.SetPreferCoordGen(True)
    def draw(smi, fn, legend):
        m = Chem.MolFromSmiles(smi); rdDepictor.Compute2DCoords(m)
        d = rdMolDraw2D.MolDraw2DCairo(900, 560); o = d.drawOptions()
        o.legendFontSize = 26; o.addStereoAnnotation = True; o.bondLineWidth = 2; o.padding = 0.08
        d.DrawMolecule(m, legend=legend); d.FinishDrawing()
        open(os.path.join(HERE, fn), "wb").write(d.GetDrawingText())
    draw("CCOC(=O)N[C@H]1C[C@@H](CCC)N(C(=O)OCC)c2ccc(C(F)(F)F)cc21", "structure-cp-7-1.png",
         "CP-7-1 (ethyl homolog of CP-7)  C19H25F3N2O4")
    register("fig-3ae48670", "structure-cp-7-1.png", "Figure 3-2 CP-7-1, Ethyl Homolog",
             "Structure drawn for the PQI examples from the structure of CP-7 given in the ICH Sakura Bloom mock-up, with the methyl carbamate replaced by an ethyl carbamate as the mock-up describes; (2R,4S) as in CP-7.")
    draw("CC(C)OC(=O)N1c2ccc(C(F)(F)F)cc2[C@@H](N(Cc2cc(C(F)(F)F)cc(C(F)(F)F)c2)C(C)=O)C[C@]1(C)OCC", "structure-cp-9-1.png",
         "CP-9-1  C28H29F9N2O4")
    register("fig-fd6f7eab", "structure-cp-9-1.png", "Structural formula of impurity CP-9-1",
             "Structure drawn for the PQI examples from the IUPAC name given in the ICH Sakura Bloom mock-up.")


def schemes():
    fig, ax = plt.subplots(figsize=(10, 2.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 2.6); ax.axis("off")
    def box(x, w, t, fc="#eef1f6", ec=ACC):
        ax.add_patch(FancyBboxPatch((x, 0.75), w, 1.1, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec, lw=1.2))
        ax.text(x + w / 2, 1.3, t, ha="center", va="center", fontsize=9.5, linespacing=1.35)
    box(0.1, 1.5, "Aniline precursor\n+ Br$_2$")
    box(3.0, 2.5, "Intermediate\n2-bromo-4-fluoroaniline · HBr")
    box(7.0, 2.9, "SM2 CP-8\n1-bromo-3,5-bis(trifluoromethyl)-\nbenzene", "#e8f7ec", "#248a3d")
    for x1, x2, lab in [(1.6, 3.0, "Step 1\nbromination"), (5.5, 7.0, "Step 2\nNaNO$_2$, H$_3$PO$_4$")]:
        ax.annotate("", (x2, 1.3), (x1, 1.3), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.3))
        ax.text((x1 + x2) / 2, 1.95, lab, ha="center", fontsize=8.5, color=MUTED)
    ax.text(0.1, 2.45, "Route of synthesis of starting material SM2 CP-8 (supplier process)", fontsize=11, fontweight="bold")
    ax.text(0.1, 0.35, "No secondary or tertiary amine in the route; the primary amine intermediate cannot form an N-nitrosamine.", fontsize=8.5, color=MUTED)
    save(fig, "route-sm2-cp-8.png")
    register("fig-505a109a", "route-sm2-cp-8.png", "Route of synthesis of starting material SM2 CP-8",
             f"{MOCKUP}: two-step route, reagents and intermediate as described in the nitrosamine risk evaluation text (names kept as in the mock-up).")

    fig, ax = plt.subplots(figsize=(10, 3.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 3.6); ax.axis("off")
    ax.text(0.1, 3.4, "Vulnerable amines and nitrite sources in the Sakuramil route", fontsize=11, fontweight="bold")
    steps = [("Step 1", "CP-4 → CP-5", "No nitrite source", "No risk", "#e8f7ec", "#248a3d"),
             ("Step 2", "CP-5 → CP-6", "Water, acidic conditions", "Cannot be fully\nexcluded: N-nitroso-\nCP-5 → N-nitroso-CP-6", "#fff4e5", "#b25000"),
             ("Step 3", "CP-6 → CP-7", "No nitrite source", "N-nitroso-CP-6, if\npresent, carried\nforward only", "#f5f5f7", MUTED),
             ("Step 4", "CP-7 + CP-8\n→ Sakuramil", "Residual nitrite from\nSM2 possible; basic,\n12-25 °C", "Negligible", "#e8f7ec", "#248a3d")]
    for i, (s, tr, src, risk, fc, ec) in enumerate(steps):
        x = 0.1 + i * 2.48
        ax.add_patch(FancyBboxPatch((x, 0.2), 2.3, 2.9, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec, lw=1.2))
        ax.text(x + 1.15, 2.8, s, ha="center", fontsize=10, fontweight="bold")
        ax.text(x + 1.15, 2.4, tr, ha="center", va="top", fontsize=9, linespacing=1.25)
        ax.text(x + 1.15, 1.5, src, ha="center", va="center", fontsize=8.5, color=MUTED, linespacing=1.3)
        ax.text(x + 1.15, 0.65, risk, ha="center", va="center", fontsize=9, fontweight="bold", color=ec if ec != MUTED else INK, linespacing=1.3)
    save(fig, "nitrosamine-vulnerable-amines.png")
    register("fig-c330fd2d", "nitrosamine-vulnerable-amines.png", "Vulnerable amines and nitrite sources in the Sakuramil manufacturing process",
             f"{SYNTH}: summarises the nitrosamine risk evaluation text of the mock-up step by step; it adds no data.")


if __name__ == "__main__":
    formulas(); risk_tables(); doe_tables(); cpp_diagram(); dissolution_table(); m7_tables(); linearity(); xrpd(); structures(); schemes()
    with open(os.path.join(HERE, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(dict(sorted(MANIFEST.items())), f, indent=1, ensure_ascii=False)
    print(len(MANIFEST), "placeholder figures mapped to", len({v["file"] for v in MANIFEST.values()}), "images")
