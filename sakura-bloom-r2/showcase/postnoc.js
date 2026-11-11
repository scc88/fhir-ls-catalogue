/* Simulated Post-NOC intake: FHIR PQI change bundles received by API, compared with the approved
   baseline and categorised per Health Canada "Post-Notice of Compliance (NOC) Changes: Quality Document"
   (Appendix 1 human pharmaceuticals, Appendix 7 Level IV examples). Pure logic; no DOM. */
const POSTNOC = (function () {
  const BASE = "http://example.org/sakura-bloom-r2/fhir/";
  const clone = (x) => JSON.parse(JSON.stringify(x));
  const LEVELS = {
    I: { code: "I", name: "Level I · Supplement", short: "Supplement", filing: "SNDS / SANDS with supporting data", timing: "Implement only after a Notice of Compliance is issued" },
    II: { code: "II", name: "Level II · Notifiable Change", short: "Notifiable Change", filing: "Not applicable to human pharmaceuticals", timing: "" },
    III: { code: "III", name: "Level III · Annual Notification", short: "Annual Notification", filing: "Level III form; data available within 30 days on request", timing: "May be implemented without prior review" },
    IV: { code: "IV", name: "Level IV · Record of Change", short: "Record of Change", filing: "Not filed; kept in the product record under GMP", timing: "May be implemented without prior review" },
  };
  // human pharmaceuticals: Level II does not apply, so escalation from III goes to I
  const NEXT = { IV: "III", III: "I", I: "I" };

  function diff(a, b, path, out) {
    path = path || ""; out = out || [];
    if (JSON.stringify(a) === JSON.stringify(b)) return out;
    const isObj = (x) => x && typeof x === "object";
    if (isObj(a) && isObj(b) && Array.isArray(a) === Array.isArray(b)) {
      const keys = Array.isArray(a) ? [...Array(Math.max(a.length, b.length)).keys()] : [...new Set([...Object.keys(a), ...Object.keys(b)])];
      for (const k of keys) {
        if (k === "text" || k === "meta") continue;
        diff(a[k], b[k], path + (Array.isArray(a) ? "[" + k + "]" : (path ? "." : "") + k), out);
      }
      return out;
    }
    out.push({ path, before: a, after: b });
    return out;
  }

  const width = (r) => (r ? (r.high ? r.high.value : Infinity) - (r.low ? r.low.value : -Infinity) : Infinity);
  // true when the new range accepts values the old one rejected
  const widens = (nw, old) => {
    const hi = (r) => (r && r.high ? r.high.value : Infinity), lo = (r) => (r && r.low ? r.low.value : -Infinity);
    return hi(nw) > hi(old) || lo(nw) < lo(old);
  };

  function evalResults(PQI, db, odId, ctx, range) {
    const rs = PQI.resultsFor(db, odId).filter((x) => !ctx || PQI.contextFor(db, x.obs) === ctx || !PQI.contextFor(db, x.obs));
    const fails = rs.filter((x) => PQI.evaluate(db, x.obs, range).status === "fail");
    const failsNow = rs.filter((x) => PQI.evaluate(db, x.obs).status === "fail");
    return { n: rs.length, fails, failsNow };
  }

  function build(PQI, db) {
    const g = (k) => db.byKey.get(k);
    const subs = [];
    const mk = (id, received, title, summary, changes, docs) => subs.push({ id, received, title, summary, changes, docs });
    // ---- S1: tighten DP CP-9-1 shelf-life limit
    {
      const r = clone(g("ObservationDefinition/od-dp-degradation-cp-9-1"));
      r.qualifiedValue.find((q) => q.context.text === "Shelf-life").range.high.value = 0.4;
      r.qualifiedValue.find((q) => q.context.text === "Shelf-life").extension[0].valueString = "Not more than 0.4%";
      mk("PNC-2026-0418", "2026-11-02T09:14:00-05:00", "Tighten CP-9-1 shelf-life limit to NMT 0.4 %", "Specified degradation product CP-9-1, drug product shelf-life criterion tightened from NMT 0.5 % to NMT 0.4 %.", [r], ["P.5.1", "P.5.6"]);
    }
    // ---- S2: relax DP total degradation products
    {
      const r = clone(g("ObservationDefinition/od-dp-degradation-total"));
      r.qualifiedValue.forEach((q) => { q.range.high.value = 1.5; q.extension[0].valueString = "Not more than 1.5%"; });
      mk("PNC-2026-0421", "2026-11-03T11:02:00-05:00", "Relax total degradation products to NMT 1.5 %", "Drug product total degradation products criterion relaxed from NMT 1.0 % to NMT 1.5 % at release and shelf-life.", [r], ["P.5.1", "P.5.6", "P.5.4"]);
    }
    // ---- S3: shelf-life extension 36 -> 48 months (HDPE bottle)
    {
      const r = clone(g("PackagedProductDefinition/pack-hdpe-bottle"));
      r.packaging.packaging[0].shelfLifeStorage.forEach((s) => (s.periodDuration.value = 48));
      mk("PNC-2026-0430", "2026-11-04T15:40:00-05:00", "Extend shelf life to 48 months (HDPE bottle)", "Shelf life of the HDPE bottle presentation extended from 36 to 48 months for all climatic zones.", [r], ["P.8.1", "P.8.2"]);
    }
    // ---- S4: batch size increase 520 kg -> 1,040 kg
    {
      const r = clone(g("Medication/dp-batch-formula-commercial"));
      r.totalVolume.value = 1040;
      r.ingredient.forEach((i) => { if (i.strengthRatio) { i.strengthRatio.numerator.value = +(i.strengthRatio.numerator.value * 2).toFixed(3); i.strengthRatio.denominator.value = 1040; } });
      const mb = r.batch.extension.find((e) => /manufacturingBatch/.test(e.url));
      mb.extension.find((e) => e.url === "batchQuantity").valueQuantity.value = 1040;
      r.batch.extension.find((e) => /number-of-items/.test(e.url)).valueQuantity.value = 5200000;
      mk("PNC-2026-0436", "2026-11-05T08:55:00-05:00", "Increase commercial batch size to 1,040 kg", "Drug product commercial batch size doubled from 520 kg (≈2.6 million tablets) to 1,040 kg (≈5.2 million tablets); same equipment train, larger granulator.", [r], ["P.2", "P.3.2", "P.5.4", "P.8.2", "R.1.2", "P.3.5"]);
    }
    // ---- S5: expand granulation spray-rate range (CPP)
    {
      const r = clone(g("ObservationDefinition/cpp-dp-3-spray-rate"));
      r.qualifiedValue[0].range.low.value = 800; r.qualifiedValue[0].range.high.value = 1200;
      r.qualifiedValue[0].extension[0].valueString = "800 - 1200 g/min";
      mk("PNC-2026-0441", "2026-11-06T13:21:00-05:00", "Expand granulation spray-rate range to 800–1200 g/min", "Critical process parameter for granulation (step 3) widened from 900–1100 g/min, supported by development data.", [r], ["P.2"]);
    }
    // ---- S6: add a testing site
    {
      const org = { resourceType: "Organization", id: "maple-analytical", meta: { profile: [g("Organization/dakina-analytica").meta.profile[0]] }, identifier: [{ system: BASE + "organization-id", value: "maple-analytical" }], active: true,
        type: [{ coding: [{ system: "http://terminology.hl7.org/CodeSystem/pharmaceutical-organization-type", code: "analytical-testing-release", display: "Analytical Testing - Release" }], text: "Analytical Testing - Release" }],
        name: "Maple Analytical Laboratories Inc. (fictitious)", contact: [{ address: { use: "work", type: "physical", line: ["100 Example Street"], city: "Mississauga", state: "ON", country: "CA" } }] };
      const mpd = clone(g("MedicinalProductDefinition/sakura-bloom-20mg"));
      mpd.operation.find((o) => /Quality control testing/.test(o.type.concept ? o.type.concept.text : "")).organization.push({ reference: "Organization/maple-analytical" });
      mk("PNC-2026-0447", "2026-11-07T10:05:00-05:00", "Add a release-testing site (Maple Analytical Laboratories)", "Addition of a Canadian contract laboratory for release testing of the drug product (chemical tests).", [org, mpd], ["P.3.1"]);
    }
    // ---- S7: identical replacement of tablet press
    {
      const old = g("DeviceDefinition/eq-rotary-tablet-press");
      const r = clone(old); r.id = "eq-rotary-tablet-press-2"; r.deviceName[0].name = "Rotary tablet press (power assisted), replacement unit";
      mk("PNC-2026-0452", "2026-11-08T16:47:00-05:00", "Replace rotary tablet press with an identical unit", "Like-for-like replacement of the step 8 rotary tablet press (same SUPAC class and operating range).", [r], []);
    }
    // ---- S8: change post-approval stability commitment (MET time points)
    {
      const r = clone(g("PlanDefinition/stability-protocol-dp-commitment"));
      const met = r.action.find((a) => /Microbial/.test(a.title));
      met.action = met.action.filter((a) => !/^12 months/.test(a.title));
      mk("PNC-2026-0455", "2026-11-09T09:30:00-05:00", "Reduce microbial testing in the stability commitment", "Microbial enumeration on commitment batches at release and 36 months only (12-month pull removed).", [r], ["P.8.1", "P.8.2"]);
    }
    return subs.map((s) => classify(PQI, db, s));
  }

  // ---------------------------------------------------------------- classification
  function classify(PQI, db, s) {
    const g = (k) => db.byKey.get(k);
    const changes = [];
    for (const r of s.changes) {
      const base = g(r.resourceType + "/" + r.id);
      changes.push({ resource: r, base, kind: base ? "update" : "create", diffs: base ? diff(base, r) : [] });
    }
    const docs = new Set(s.docs);
    let item = null, sub = "", level = "III", conditions = [], support = [], factors = [], affected = null, critical = false, direction = null;
    const C = (n, text, status, evidence) => conditions.push({ n, text, status, evidence });
    const S = (n, ctd, text) => support.push({ n, ctd, text, present: docs.has(ctd) });
    const main = changes[0];
    const r = main.resource, base = main.base;

    if (r.resourceType === "ObservationDefinition" && r.id.startsWith("cpp-")) {
      const wNew = width(r.qualifiedValue[0].range), wOld = width(base.qualifiedValue[0].range);
      direction = widens(r.qualifiedValue[0].range, base.qualifiedValue[0].range) ? "expand" : "reduce"; critical = true;
      item = { n: 22, title: "Change in the approved design space", app: "Appendix 1, 3.2.P.2" };
      sub = direction === "expand" ? "Expansion of the approved design space" : "Reduction of the approved design space";
      level = direction === "expand" ? "I" : "III";
      S(1, "P.2", "Pharmaceutical development data supporting the design space change");
    } else if (r.resourceType === "ObservationDefinition") {
      const ctxs = r.qualifiedValue.map((q, i) => ({ ctx: q.context ? q.context.text : null, nw: q.range, old: base.qualifiedValue[i].range }));
      const relax = ctxs.some((c) => widens(c.nw, c.old));
      direction = relax ? "relax" : "tighten";
      const ds = (db.specOf.get(r.id) || new Set()).has("spec-ds-sakuramil");
      critical = /Assay|Degradation|Dissolution|impurit/i.test(r.title + " " + PQI.ccText(r.category[0]));
      const ctx = ctxs.find((c) => JSON.stringify(c.nw) !== JSON.stringify(c.old));
      affected = evalResults(PQI, db, r.id, ctx.ctx, ctx.nw);
      item = ds ? { n: 8, title: "Change in the specification for the drug substance involving test and acceptance criteria", app: "Appendix 1, 3.2.S.4" }
                : { n: 31, title: "Change in the specification for the drug product tests and acceptance criteria", app: "Appendix 1, 3.2.P.5" };
      if (direction === "tighten") {
        sub = "Tightening of an acceptance criterion"; level = "III";
        S(2, ds ? "S.4.1" : "P.5.1", "Updated, QC-approved specification"); S(8, ds ? "S.4.5" : "P.5.6", "Justification of the specification");
      } else {
        sub = "Relaxation of an acceptance criterion"; level = "III";
        C(1, "Not driven by unexpected events such as specification failures during manufacture or stability concerns", affected.failsNow.length ? "not_met" : "met",
          affected.failsNow.length ? affected.failsNow.length + " existing results already fail" : `None of ${affected.n} existing results fails the approved criterion`);
        C(4, "No change in assay limits and no change in the impurity profile that affects safety", /Degradation|impurit/i.test(r.title) ? "review" : "met",
          /Degradation|impurit/i.test(r.title) ? "Impurity limit is being relaxed: toxicological qualification needs assessor review" : "Assay limits unchanged");
        C(6, "Does not affect product performance (dissolution of modified-release products)", "met", "Immediate-release product; dissolution specification unchanged");
        C(7, "Does not concern sterility testing", "met", "Non-sterile oral solid");
        const compendial = /Ph\. Eur|USP|JP|compendial/i.test(JSON.stringify(g("PlanDefinition/" + [...(db.specOf.get(r.id) || [])][0]) || {}) + (r.method ? r.method.text : ""));
        C(8, "The relaxed criterion aligns with a Schedule B (compendial) monograph", compendial ? "met" : "not_met",
          compendial ? "Compendial criterion referenced" : "Sakuramil drug product is controlled by an in-house specification; no Schedule B monograph criterion to align with");
        S(2, "P.5.1", "Updated, QC-approved specification"); S(5, "P.5.3", "House vs compendial equivalency study (if Schedule B claimed)"); S(6, "P.5.4", "Results for at least one pilot-scale batch to the proposed specification"); S(8, "P.5.6", "Justification of the specification");
      }
    } else if (r.resourceType === "PackagedProductDefinition") {
      const nw = r.packaging.packaging[0].shelfLifeStorage[0].periodDuration.value, old = base.packaging.packaging[0].shelfLifeStorage[0].periodDuration.value;
      direction = nw > old ? "extend" : "reduce"; critical = true;
      item = { n: 37, title: "Change in the shelf life for the drug product", app: "Appendix 1, 3.2.P.8" };
      sub = direction === "extend" ? `Extension from ${old} to ${nw} months` : `Reduction from ${old} to ${nw} months`; level = "III";
      const others = diff(base, r).filter((d) => !/periodDuration/.test(d.path));
      C(1, "No change to the container closure in direct contact with the product or to the storage conditions", others.length ? "not_met" : "met", others.length ? "Other packaging elements changed" : "Only the shelf-life period changes");
      const series = PQI.stabilitySeries(db, "od-dp-assay-hplc").filter((x) => x.pack === "HDPE bottle" && /long-term/.test(x.condition));
      const maxT = Math.max(...series.flatMap((x) => x.points.map((p) => p.t)));
      const lots = [...new Set(series.map((x) => x.lot))];
      C(2, "Approved shelf life ≥ 24 months: full long-term data covering the proposed shelf life from at least three commercial batches", maxT >= nw && lots.length >= 3 ? "met" : "not_met",
        `Long-term data available to ${maxT} months on ${lots.length} commercial batches (${lots.join(", ")}); ${nw} months proposed`);
      C(3, "Stability data generated per the approved stability protocol", "met", "All results linked to protocol RSP1234-1G");
      const accFails = PQI.resultsFor(db, "od-dp-assay-hplc").filter((x) => x.si && /40 °C/.test(x.si.condition) && PQI.evaluate(db, x.obs).status === "fail").length;
      C(4, "No significant change (ICH Q1A) observed", accFails ? "not_met" : "met", accFails ? accFails + " accelerated results out of limit" : "No accelerated or long-term result out of limit");
      S(1, "P.8.1", "Summary of stability testing and results"); S(2, "P.8.1", "Proposed storage conditions and shelf life"); S(3, "P.8.2", "Updated stability protocol and commitment"); S(5, "P.8.3", `Stability results covering ${nw} months`);
      docs.delete("P.8.3");
    } else if (r.resourceType === "Medication") {
      const nw = r.totalVolume.value, old = base.totalVolume.value;
      direction = nw > old ? "scale-up" : "scale-down";
      item = { n: 24, title: "Change in the batch size for the drug product", app: "Appendix 1, 3.2.P.3" };
      sub = `Increase for an immediate-release product (${old} → ${nw} kg, ×${(nw / old).toFixed(1)})`; level = "III";
      const other = diff(base, r).filter((d) => !/totalVolume|strengthRatio|batchQuantity|valueQuantity\.value/.test(d.path));
      C(1, "Process and in-process control changes limited to those needed for the new batch size", other.length ? "review" : "met", other.length ? "Other differences found" : "Only batch quantities differ from the approved batch formula");
      const fails = (db.byType.get("Observation") || []).filter((o) => /Medication\/dp-/.test(o.subject.reference) && PQI.evaluate(db, o).status === "fail").length;
      C(2, "Not driven by unexpected specification failures or stability concerns", fails ? "not_met" : "met", fails ? fails + " failing results" : "No drug-product result out of limit in batch analysis or stability");
      C(3, "Relative to pivotal or approved, validated commercial batches", "met", "Approved commercial batch size 520 kg (ABC123, ABC456, ABC789)");
      C(4, "Three consecutive production-scale batches validated per approved protocol", docs.has("P.3.5") ? "attested" : "not_met", docs.has("P.3.5") ? "Process validation report supplied (P.3.5); sponsor attests three consecutive batches" : "No process validation evidence");
      C(5, "No effect on sterilization parameters", "met", "Non-sterile product");
      S(2, "P.2", "Comparative multi-point dissolution at original and proposed scale"); S(3, "P.3.2", "Proposed batch formula"); S(5, "P.5.4", "Results for one commercial-scale batch at proposed scale"); S(6, "P.8.2", "Stability commitment for first commercial batch"); S(7, "R.1.2", "Executed production documents"); S(8, "P.3.5", "Process validation of three consecutive batches");
    } else if (r.resourceType === "Organization") {
      item = { n: 23, title: "Replacement or addition of a drug product manufacturer / manufacturing site", app: "Appendix 1, 3.2.P.3" };
      sub = "Addition of a testing site"; level = "III"; direction = "add";
      C(3, "Satisfactory GMP compliance status of the proposed site", "review", "No GMP evidence in the bundle: verify against the inspection database before acceptance");
      S(1, "P.3.1", "Name and address of the proposed site and its responsibilities");
    } else if (r.resourceType === "DeviceDefinition") {
      const old = g("DeviceDefinition/eq-rotary-tablet-press");
      const same = JSON.stringify(old.classification) === JSON.stringify(r.classification) && JSON.stringify(old.property) === JSON.stringify(r.property);
      item = { n: "App. 7 ex. 9", title: "Replacement of equipment with an identical equipment", app: "Appendix 7, examples of Level IV changes" };
      sub = same ? "Same class, capacity and operating range as the approved equipment" : "Equipment differs from the approved unit"; level = same ? "IV" : "III"; direction = "replace";
      if (!same) item = { n: 25, title: "Change in the drug product manufacturing process", app: "Appendix 1, 3.2.P.3" };
      changes[0].diffs = diff(old, r).filter((d) => d.path !== "id");
    } else if (r.resourceType === "PlanDefinition") {
      item = { n: 39, title: "Change to the post-approval stability protocol or stability commitment", app: "Appendix 1, 3.2.P.8" };
      sub = "Reduced testing time points in the stability commitment"; level = "III"; direction = "reduce-testing";
      S(1, "P.8.1", "Proposed storage conditions and shelf life"); S(2, "P.8.2", "Updated, QC-approved stability protocol and commitment"); S(3, "P.8.2", "Justification for the change");
    }

    // escalation: any unmet condition moves the change to the next higher level
    const initial = level;
    const unmet = conditions.filter((c) => c.status === "not_met");
    if (unmet.length && level !== "I") level = NEXT[level];

    // risk score: transparent additive model on a 0-100 gradient
    const add = (pts, why) => factors.push({ pts, why });
    add({ IV: 5, III: 25, II: 45, I: 60 }[level], "Reporting category: " + LEVELS[level].short);
    if (critical) add(10, "Affects a critical quality attribute or parameter");
    if (/Degradation|impurit/i.test((r.title || "")) && direction === "relax") add(10, "Relaxes an impurity limit (patient safety)");
    if (["relax", "expand", "extend", "reduce-testing"].includes(direction)) add(8, "Widens a limit, range or period");
    if (direction === "tighten") add(-5, "Tightens control");
    unmet.forEach((c) => add(8, "Condition " + c.n + " not met"));
    conditions.filter((c) => c.status === "review").forEach((c) => add(4, "Condition " + c.n + " needs assessor review"));
    if (support.some((x) => !x.present)) add(4, "Supporting data missing from the bundle");
    if (affected && affected.fails.length) add(10, affected.fails.length + " existing results would fail the proposed criterion");
    const score = Math.max(2, Math.min(98, factors.reduce((a, f) => a + f.pts, 0)));
    return Object.assign(s, { changes, item, sub, level, initial, escalated: initial !== level, conditions, support, factors, score, affected, LEVELS });
  }

  function bundleOf(s) {
    return {
      resourceType: "Bundle", type: "transaction", id: s.id.toLowerCase(), timestamp: s.received,
      entry: [{ fullUrl: "urn:uuid:" + s.id.toLowerCase() + "-task", resource: { resourceType: "Task", status: "requested", intent: "proposal", code: { text: "Post-NOC quality change" }, description: s.summary, focus: { reference: "MedicinalProductDefinition/sakura-bloom-20mg" }, requester: { reference: "Organization/sakura-pharma" } }, request: { method: "POST", url: "Task" } }]
        .concat(s.changes.map((c) => ({ fullUrl: BASE + c.resource.resourceType + "/" + c.resource.id, resource: c.resource, request: { method: "PUT", url: c.resource.resourceType + "/" + c.resource.id } })))
        .concat(s.docs.map((d, i) => ({ fullUrl: "urn:uuid:" + s.id.toLowerCase() + "-doc-" + i, resource: { resourceType: "DocumentReference", status: "current", type: { text: "CTD " + d }, content: [{ attachment: { contentType: "application/pdf", title: "Supporting data " + d } }] }, request: { method: "POST", url: "DocumentReference" } }))),
    };
  }

  function responseOf(s) {
    return {
      resourceType: "Task", id: "review-" + s.id.toLowerCase(), status: s.level === "IV" ? "completed" : "ready", intent: "order",
      code: { text: "Post-NOC change assessment" },
      businessStatus: { text: s.LEVELS[s.level].name + (s.escalated ? " (escalated from " + s.LEVELS[s.initial].short + ")" : "") },
      priority: s.score >= 60 ? "urgent" : "routine",
      description: `HC Post-NOC Quality guidance ${s.item.app}, change ${s.item.n}: ${s.item.title} - ${s.sub}`,
      input: [{ type: { text: "Risk score (0-100)" }, valueInteger: s.score }, { type: { text: "Submission bundle" }, valueReference: { reference: "Bundle/" + s.id.toLowerCase() } }],
      note: [{ text: "Proposed category for assessor confirmation; generated automatically." }],
    };
  }
  return { build, bundleOf, responseOf, LEVELS };
})();
if (typeof module !== "undefined") module.exports = POSTNOC;
