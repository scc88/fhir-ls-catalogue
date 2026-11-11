/* Pure logic over FHIR PQI resources (no DOM). Shared by the page and the node check. */
const PQI = (function () {
  const M = {};
  M.load = function (resources) {
    const db = { byKey: new Map(), byUrl: new Map(), byType: new Map(), backrefs: new Map() };
    for (const r of resources) {
      const k = r.resourceType + "/" + r.id;
      db.byKey.set(k, r);
      if (r.url) db.byUrl.set(r.url, r);
      if (!db.byType.has(r.resourceType)) db.byType.set(r.resourceType, []);
      db.byType.get(r.resourceType).push(r);
    }
    // backreferences (references + canonicals)
    for (const r of resources) {
      const from = r.resourceType + "/" + r.id;
      walk(r, (v, key) => {
        let to = null;
        if (key === "reference" && typeof v === "string" && db.byKey.has(v)) to = v;
        else if (typeof v === "string" && v.startsWith("http://example.org/sakura-bloom-r2/fhir/")) {
          const t = db.byUrl.get(v);
          if (t) to = t.resourceType + "/" + t.id;
        }
        if (to && to !== from) {
          if (!db.backrefs.has(to)) db.backrefs.set(to, new Set());
          db.backrefs.get(to).add(from);
        }
      });
    }
    // observation -> report
    db.reportOf = new Map();
    for (const dr of db.byType.get("DiagnosticReport") || [])
      for (const x of dr.result || []) db.reportOf.set(x.reference, dr);
    // OD -> analytical procedure (via spec/process action documentation)
    db.apOf = new Map();
    db.specOf = new Map();
    for (const pd of db.byType.get("PlanDefinition") || []) {
      const visit = (acts) => (acts || []).forEach((a) => {
        if (a.definitionCanonical) {
          const od = db.byUrl.get(a.definitionCanonical);
          if (od && od.resourceType === "ObservationDefinition") {
            if (!db.specOf.has(od.id)) db.specOf.set(od.id, new Set());
            db.specOf.get(od.id).add(pd.id);
            for (const d of a.documentation || []) {
              const ap = db.byUrl.get(d.resource);
              if (ap) db.apOf.set(od.id, ap);
            }
          }
        }
        visit(a.action);
      });
      visit(pd.action);
    }
    return db;
  };

  function walk(o, fn, key) {
    if (Array.isArray(o)) o.forEach((x) => walk(x, fn, key));
    else if (o && typeof o === "object") for (const k of Object.keys(o)) { fn(o[k], k); walk(o[k], fn, k); }
  }
  M.walk = walk;

  M.ccText = (c) => (c ? c.text || (c.coding && c.coding[0] && (c.coding[0].display || c.coding[0].code)) || "" : "");

  M.label = function (r) {
    if (!r) return "";
    switch (r.resourceType) {
      case "MedicinalProductDefinition": return r.name[0].productName;
      case "SubstanceDefinition": return (r.name || [{}])[0].name || r.id;
      case "Substance": return (r.identifier || [{}])[0].value || r.id;
      case "Medication": return (r.batch && r.batch.lotNumber ? "Batch " + r.batch.lotNumber : "") + (r.code && /bottle|blister/i.test(r.code.text) ? " · " + (/bottle/i.test(r.code.text) ? "HDPE bottle" : "blister") : "") || r.code.text;
      case "Organization": return r.name;
      case "DeviceDefinition": return r.deviceName[0].name;
      case "Observation": return M.ccText(r.code) + " = " + M.valueText(r);
      case "Composition": return r.title;
      case "ManufacturedItemDefinition": return r.name;
      case "Ingredient": return M.ccText(r.function && r.function[0]) + " · " + r.id.replace("ing-", "");
      default: return r.title || r.name || (r.description && r.description.slice(0, 80)) || M.ccText(r.code) || r.id;
    }
  };

  M.valueText = function (o) {
    if (o.valueQuantity) {
      const q = o.valueQuantity;
      return (q.comparator ? q.comparator + " " : "") + fmt(q.value) + (q.unit ? (q.unit === "%" ? " %" : " " + q.unit) : "");
    }
    if (o.valueString != null) return o.valueString;
    return "";
  };
  function fmt(v) { return typeof v === "number" ? String(v) : v; }

  // acceptance criterion for an OD in a context ("Batch release" | "Shelf-life" | null)
  M.criterion = function (od, ctx) {
    const qvs = od.qualifiedValue || [];
    let qv = qvs[0];
    if (ctx) qv = qvs.find((x) => x.context && x.context.text === ctx) || qv;
    if (!qv) return null;
    const txt = (qv.extension || []).find((e) => /qualified-value-text/.test(e.url));
    return { ctx: qv.context ? qv.context.text : null, text: txt ? txt.valueString : "", range: qv.range || null };
  };

  M.contextFor = function (db, obs) {
    const dr = db.reportOf.get("Observation/" + obs.id);
    const code = dr ? M.ccText(dr.code) : "";
    if (/Stability/.test(code)) return "Shelf-life";
    if (/Batch Analysis/.test(code)) return "Batch release";
    return null;
  };

  M.odOf = (db, obs) => (obs.instantiatesCanonical ? db.byUrl.get(obs.instantiatesCanonical) : null);

  // evaluate an observation against its definition: pass | fail | info
  M.evaluate = function (db, obs, overrideRange) {
    const od = M.odOf(db, obs);
    if (!od) return { status: "info" };
    const crit = M.criterion(od, M.contextFor(db, obs));
    const range = overrideRange || (crit && crit.range);
    const q = obs.valueQuantity;
    if (!range || !q || typeof q.value !== "number") {
      const s = (obs.valueString || "").toLowerCase();
      if (/complies|no change|absent|positive|identified/.test(s) || (obs.interpretation || []).some((i) => /complies|absent/i.test(i.text))) return { status: "pass", crit };
      if (/< ?loq/.test(s)) return { status: "pass", crit, note: "below LOQ" };
      return { status: "info", crit };
    }
    const v = q.value, cmp = q.comparator;
    const lo = range.low ? range.low.value : null, hi = range.high ? range.high.value : null;
    let ok = true;
    if (hi != null && !(cmp === "<" ? v <= hi : v <= hi)) ok = false;
    if (lo != null && cmp !== "<" && v < lo) ok = false;
    // margin to nearest limit, relative to limit span
    let margin = null;
    if (hi != null && lo != null) margin = Math.min(hi - v, v - lo) / (hi - lo);
    else if (hi != null) margin = (hi - v) / hi;
    else if (lo != null) margin = (v - lo) / lo;
    return { status: ok ? (margin != null && margin < 0.15 && cmp !== "<" ? "near" : "pass") : "fail", crit, margin, lo, hi };
  };

  M.specimenInfo = function (db, obs) {
    const sp = obs.specimen ? db.byKey.get(obs.specimen.reference) : null;
    if (!sp) return null;
    const pr = (sp.processing || [])[0] || {};
    const ext = ((pr.timePeriod || {}).extension || [])[0];
    const months = ext && ext.valueDuration ? ext.valueDuration.value : 0;
    const desc = pr.description || "";
    let cond = "Initial";
    const m = desc.match(/Stored at (.+?)(?: for \d+ months| \(initial\))?$/);
    if (m) cond = m[1];
    return { months, condition: cond, specimen: sp };
  };

  // stability series: [{lot, pack, condition, points:[{t,v,cmp,obs}]}]
  M.stabilitySeries = function (db, odId, scope) {
    const out = new Map();
    for (const o of db.byType.get("Observation") || []) {
      if (!o.instantiatesCanonical || !o.instantiatesCanonical.endsWith("/" + odId)) continue;
      const dr = db.reportOf.get("Observation/" + o.id);
      if (!dr || !/Stability/.test(M.ccText(dr.code))) continue;
      const si = M.specimenInfo(db, o);
      if (!si || /photo/.test(si.specimen.id)) continue;
      const subj = db.byKey.get(o.subject.reference);
      const lot = subj.resourceType === "Medication" ? subj.batch.lotNumber : (subj.identifier || [{}])[0].value;
      const pack = subj.resourceType === "Medication" ? (/bottle/i.test(subj.code.text) ? "HDPE bottle" : "PA/AL/PVC blister") : "LDPE bag";
      const q = o.valueQuantity;
      if (!q || typeof q.value !== "number") continue;
      let cond = si.condition;
      if (/xenon|Photostability/i.test(cond) || /not specified/.test(cond)) continue;
      const key = lot + "|" + pack + "|" + cond;
      if (!out.has(key)) out.set(key, { lot, pack, condition: cond, points: [] });
      out.get(key).points.push({ t: si.months, v: q.value, cmp: q.comparator, obs: o });
    }
    // attach the initial point to every condition series of the same lot/pack
    const series = [...out.values()];
    for (const s of series) {
      if (/Initial/i.test(s.condition)) continue;
      const init = series.find((x) => x.lot === s.lot && x.pack === s.pack && /Initial/i.test(x.condition));
      if (init && !s.points.some((p) => p.t === 0)) s.points.push(...init.points);
      s.points.sort((a, b) => a.t - b.t);
    }
    return series.filter((s) => !/Initial/i.test(s.condition));
  };

  M.linearFit = function (pts) {
    const n = pts.length;
    if (n < 3) return null;
    const mx = pts.reduce((a, p) => a + p.t, 0) / n, my = pts.reduce((a, p) => a + p.v, 0) / n;
    let sxx = 0, sxy = 0;
    for (const p of pts) { sxx += (p.t - mx) ** 2; sxy += (p.t - mx) * (p.v - my); }
    if (!sxx) return null;
    const b = sxy / sxx, a = my - b * mx;
    return { a, b, at: (t) => a + b * t };
  };

  // all observations for an OD, enriched
  M.resultsFor = function (db, odId, overrideRange) {
    const out = [];
    for (const o of db.byType.get("Observation") || []) {
      if (!o.instantiatesCanonical || !o.instantiatesCanonical.endsWith("/" + odId)) continue;
      const dr = db.reportOf.get("Observation/" + o.id);
      const subj = db.byKey.get(o.subject.reference);
      out.push({ obs: o, report: dr, subject: subj, ev: M.evaluate(db, o, overrideRange), si: M.specimenInfo(db, o) });
    }
    return out;
  };

  // genealogy: DP batches -> DS batches
  M.genealogy = function (db) {
    const meds = (db.byType.get("Medication") || []).filter((m) => m.batch && m.batch.lotNumber && !/bottle|blister/i.test(m.code.text));
    return meds.map((m) => {
      const ds = (m.batch.extension || []).filter((e) => /batch-substance-batch/.test(e.url)).map((e) => db.byKey.get(e.valueReference.reference));
      const mb = (m.batch.extension || []).find((e) => /manufacturingBatch/.test(e.url));
      const get = (n) => { const x = (mb ? mb.extension : []).find((e) => e.url === n); return x ? x.valueDateTime || M.ccText(x.valueCodeableConcept) : ""; };
      return { med: m, lot: m.batch.lotNumber, date: get("manufacturingDate"), use: get("batchUtilization"), ds };
    });
  };

  M.sourcesOf = function (db, keys) {
    const s = new Set();
    for (const k of keys) { const r = db.byKey.get(k); if (r && r.meta && r.meta.source) s.add(r.meta.source); }
    return s;
  };
  return M;
})();
if (typeof module !== "undefined") module.exports = PQI;
