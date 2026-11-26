/* ePI Type 1-4 showcases: shared shell and FHIR helpers (no framework). Synthetic data only. */
const EP = (function () {
  const M = {};
  const $ = (sel, el) => (el || document).querySelector(sel);
  M.$ = $;
  M.$$ = (sel, el) => [...(el || document).querySelectorAll(sel)];
  M.IG = "https://build.fhir.org/ig/HL7/emedicinal-product-info/en/";

  M.TYPES = {
    1: { name: "Digital label", short: "Digital label", page: "type1.html", ig: "steps-to-create-epi1.html",
         adds: "The approved SmPC and package leaflet as FHIR documents: coded headings, XHTML narrative, images as Binary.",
         who: "Every marketing authorisation holder. The entry point of regulators' ePI programmes.",
         effort: "Convert the approved Word documents." },
    2: { name: "Product identification", short: "Product ID", page: "type2.html", ig: "steps-to-create-epi2.html",
         adds: "Product, packs with GTINs, manufactured item, administrable product, ingredients, substances, authorisations and organisations as resources, referenced from the sections that describe them.",
         who: "Companies with RIM or IDMP master data.",
         effort: "Type 1, plus mapping the master data." },
    3: { name: "Clinical information", short: "Clinical", page: "type3.html", ig: "steps-to-create-epi3.html",
         adds: "Clinical particulars as ClinicalUseDefinitions: the indication with its dosing, contraindications, interactions, warnings and undesirable effects, coded and with populations.",
         who: "Companies and regulators who want computable clinical content.",
         effort: "Type 2, plus coding sections 4.1 to 4.8." },
    4: { name: "Dynamic digital label", short: "Dynamic", page: "type4.html", ig: "build-epi4.html",
         adds: "Phrases in the narrative are linked to the resources that carry their meaning (textLink), so text and data stay connected and the label can be filtered and personalised.",
         who: "Publishers of patient apps, pharmacy and EHR systems.",
         effort: "Type 3, plus linking phrases to data." },
  };
  M.DOCNAME = { "smpc-en": "SmPC · English", "pil-en": "Package leaflet · English", "ifu-en": "Instructions for use · English" };

  M.esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  M.fmt = (n) => (typeof n === "number" ? n.toLocaleString("en-US") : n);
  M.plain = (div) => { const d = new DOMParser().parseFromString(`<body>${div || ""}</body>`, "text/html"); return d.body.textContent.replace(/\s+/g, " ").trim(); };

  // ---------- documents ----------
  M.code = (s) => ((s.code || {}).coding || [{}])[0].code || "";
  M.walk = function (sections, depth, parent, out) {
    out = out || [];
    for (const s of sections || []) {
      const item = { s, depth: depth || 0, parent: parent || null, code: M.code(s) };
      out.push(item);
      M.walk(s.section, (depth || 0) + 1, item, out);
    }
    return out;
  };
  M.textLinks = (s) => ((s.text || {}).extension || []).filter((x) => x.url === "http://hl7.org/fhir/StructureDefinition/textLink").map((x) => {
    const g = (n) => (x.extension || []).find((e) => e.url === n) || {};
    return { htmlid: g("htmlid").valueString, data: g("data").valueUri };
  });
  M.db = function (bundle) {
    const db = { byKey: new Map(), byType: new Map() };
    for (const e of bundle.entry) {
      const r = e.resource, k = r.resourceType + "/" + r.id;
      db.byKey.set(k, r);
      if (!db.byType.has(r.resourceType)) db.byType.set(r.resourceType, []);
      db.byType.get(r.resourceType).push(r);
    }
    db.get = (ref) => (ref ? db.byKey.get(typeof ref === "string" ? ref : ref.reference) || null : null);
    db.all = (t) => db.byType.get(t) || [];
    return db;
  };
  M.load = function (t) {
    return EPIDATA.docs.filter((d) => d.type === t).map((d) => {
      const comp = d.bundle.entry[0].resource;
      const secs = M.walk(comp.section);
      const images = {};
      (comp.contained || []).filter((c) => c.resourceType === "Binary").forEach((b) => { images["#" + b.id] = `data:${b.contentType};base64,${b.data}`; });
      return { ...d, comp, secs, db: M.db(d.bundle), images, name: M.DOCNAME[d.key] };
    });
  };

  // ---------- coded values ----------
  const SYS = { "http://snomed.info/sct": "SNOMED CT", "http://www.whocc.no/atc": "ATC", "http://standardterms.edqm.eu": "EDQM",
    "https://spor.ema.europa.eu/rmswi": "EMA SPOR", "https://www.gs1.org/gtin": "GS1 GTIN", "http://unitsofmeasure.org": "UCUM" };
  M.sys = (s) => SYS[s] || (/example\.org/.test(s || "") ? "local (synthetic)" : /emedicinal-product-info/.test(s || "") ? "ePI IG" : (s || "").split("/").pop());
  M.cc = (c) => (c ? c.text || ((c.coding || [])[0] || {}).display || ((c.coding || [])[0] || {}).code || "" : "");
  M.coding = (c) => ((c && c.coding) || []).map((x) => `<span class="code-pill" title="${M.esc(x.system)}"><b>${M.esc(M.sys(x.system))}</b> ${M.esc(x.code)} <span>${M.esc(x.display || "")}</span></span>`).join(" ");
  M.qty = (q) => (q ? q.value + (q.unit ? " " + q.unit : "") : "");
  M.cudKind = (r) => r.type;
  M.cudBody = (r) => r[{ "undesirable-effect": "undesirableEffect" }[r.type] || r.type] || {};
  M.cudConcept = function (r) {
    const b = M.cudBody(r);
    switch (r.type) {
      case "indication": case "contraindication": return (b.diseaseSymptomProcedure || {}).concept;
      case "undesirable-effect": return (b.symptomConditionEffect || {}).concept;
      case "warning": return b.code;
      case "interaction": return { text: (b.interactant || []).map((i) => M.cc(i.itemCodeableConcept)).join(", "), coding: (b.interactant || []).flatMap((i) => (i.itemCodeableConcept || {}).coding || []) };
    }
    return null;
  };
  M.translation = (concept, lang) => { const e = ((concept || {})._text || {}).extension || []; const t = e.find((x) => (x.extension || []).some((y) => y.url === "lang" && y.valueCode === lang)); return t ? t.extension.find((y) => y.url === "content").valueString : null; };

  M.label = function (r) {
    if (!r) return "";
    switch (r.resourceType) {
      case "MedicinalProductDefinition": return r.name[0].productName;
      case "SubstanceDefinition": return ((r.name || [])[0] || {}).name || r.id;
      case "Ingredient": return (((((r.substance || {}).code || {}).reference || {}).reference) || "").split("/").pop().replace(/-/g, " ") + " · " + M.cc(r.role);
      case "ClinicalUseDefinition": { const c = M.cudConcept(r); return (r.type === "interaction" ? "Interaction: " : "") + (M.cc(c) || r.id); }
      case "Group": return r.name;
      case "PackagedProductDefinition": return "Pack · " + (r.name || "").replace(/^.* - /, "");
      case "RegulatedAuthorization": return ((r.identifier || [])[0] || {}).value;
      case "AdministrableProductDefinition": return M.cc(r.administrableDoseForm) + " · " + M.cc((r.routeOfAdministration || [])[0] && r.routeOfAdministration[0].code);
      case "Composition": return r.title;
      case "Binary": return r.id;
      default: return r.name || r.title || r.id;
    }
  };

  M.summary = function (r, db) {
    if (!r) return "";
    const row = (k, v) => (v ? `<dt>${M.esc(k)}</dt><dd>${v}</dd>` : "");
    const ref = (x) => { if (!x) return ""; const t = db && db.get(x.reference || x); return t ? `<a href="#" data-ref="${M.esc(t.resourceType + "/" + t.id)}">${M.esc(M.label(t))}</a>` : M.esc(x.reference || x); };
    const e = M.esc;
    let kv = "";
    switch (r.resourceType) {
      case "MedicinalProductDefinition":
        kv = row("Name", e(r.name[0].productName)) + row("Identifier", (r.identifier || []).map((i) => `<span class="mono">${e(i.value)}</span>`).join(", ")) +
          row("Dose form", M.coding(r.combinedPharmaceuticalDoseForm) || e(M.cc(r.combinedPharmaceuticalDoseForm))) + row("Route", (r.route || []).map(M.coding).join(" ")) +
          row("Legal status", e(M.cc(r.legalStatusOfSupply))) + (r.characteristic || []).map((c) => row(M.cc(c.type), e(c.valueQuantity ? M.qty(c.valueQuantity) : M.cc(c.valueCodeableConcept)))).join("");
        break;
      case "ManufacturedItemDefinition":
        kv = row("Dose form", M.coding(r.manufacturedDoseForm)) + row("Manufacturer", (r.manufacturer || []).map(ref).join(", ")) +
          (r.property || []).filter((p) => !p.valueAttachment).map((p) => row(M.cc(p.type), e(p.valueQuantity ? M.qty(p.valueQuantity) : M.cc(p.valueCodeableConcept)))).join("");
        break;
      case "AdministrableProductDefinition":
        kv = row("Dose form", M.coding(r.administrableDoseForm)) + row("Route", (r.routeOfAdministration || []).map((x) => M.coding(x.code)).join(" ")) + row("Produced from", (r.producedFrom || []).map(ref).join(", "));
        break;
      case "Ingredient": {
        const st = ((r.substance || {}).strength || [])[0] || {};
        kv = row("Role", e(M.cc(r.role))) + row("Function", e((r.function || []).map(M.cc).join(", "))) + row("Substance", ref(((r.substance || {}).code || {}).reference)) + row("Strength", e(st.textPresentation));
        break;
      }
      case "SubstanceDefinition":
        kv = row("Name", e(M.label(r))) + row("Identifier", (r.identifier || []).map((i) => e(i.value)).join(", ")) + row("Classification", e((r.classification || []).map(M.cc).join(", "))) + row("Description", e(r.description));
        break;
      case "PackagedProductDefinition": {
        const inner = ((r.packaging || {}).packaging || [])[0] || {};
        const sl = (inner.shelfLifeStorage || [])[0];
        kv = row("GTIN", (r.identifier || []).map((i) => `<span class="mono">${e(i.value)}</span>`).join(", ")) + row("Contains", e((r.containedItemQuantity || []).map(M.qty).join(", "))) +
          row("Container", e(M.cc(inner.type)) + (inner.quantity ? " × " + inner.quantity : "")) + row("Shelf life", sl ? e(M.qty(sl.periodDuration) + " · " + M.cc(sl.type).replace(/^Shelf life of the medicinal product as packaged for sale - /, "")) : "") +
          row("Storage", sl ? e((sl.specialPrecautionsForStorage || []).map(M.cc).join("; ")) : "") + row("For", (r.packageFor || []).map(ref).join(", "));
        break;
      }
      case "RegulatedAuthorization":
        kv = row("Number", `<span class="mono">${e(((r.identifier || [])[0] || {}).value)}</span>`) + row("Type", e(M.cc(r.type))) + row("Region", e((r.region || []).map(M.cc).join(", "))) +
          row("Status", e(M.cc(r.status)) + (r.statusDate ? " since " + e(r.statusDate) : "")) + row("Holder", ref(r.holder)) + row("Subject", (r.subject || []).map(ref).join("<br>"));
        break;
      case "Organization": {
        const a = ((r.contact || [])[0] || {}).address;
        kv = row("Name", e(r.name)) + row("Role", e((r.type || []).map(M.cc).join(", "))) + row("Address", a ? e([...(a.line || []), a.postalCode, a.city, a.country].filter(Boolean).join(", ")) : "") + row("Part of", ref(r.partOf));
        break;
      }
      case "Group":
        kv = row("Name", e(r.name)) + (r.characteristic || []).map((c) => row(M.cc(c.code), e(c.valueRange ? [c.valueRange.low ? "≥ " + M.qty(c.valueRange.low) : "", c.valueRange.high ? "< " + M.qty(c.valueRange.high) : ""].filter(Boolean).join(" and ") : M.cc(c.valueCodeableConcept)))).join("");
        break;
      case "ClinicalUseDefinition": {
        const b = M.cudBody(r);
        kv = row("Type", `<span class="chip k-${r.type}">${e(r.type)}</span>`) + row("Population", (r.population || []).map(ref).join(", "));
        if (r.type === "indication") {
          const dg = ((r.extension || []).find((x) => /dosing-guideline/.test(x.url)) || {}).valueDosage;
          kv += row("Condition", M.coding(b.diseaseSymptomProcedure.concept) + `<div class="small">${e(b.diseaseSymptomProcedure.concept.text)}</div>`) + row("Intended effect", e(M.cc((b.intendedEffect || {}).concept)));
          if (dg) kv += row("Dosing", e(dg.text) + `<div class="small muted mono">dose ${e(M.qty(dg.doseAndRate[0].doseQuantity))} · ${dg.timing.repeat.frequency}× per ${dg.timing.repeat.period} ${dg.timing.repeat.periodUnit} · max ${e(M.qty(dg.maxDosePerPeriod[0].numerator))}/${e(dg.maxDosePerPeriod[0].denominator.unit)}</div>`);
        } else if (r.type === "contraindication") {
          kv += row("Condition", M.coding(b.diseaseSymptomProcedure.concept) + `<div class="small">${e(b.diseaseSymptomProcedure.concept.text)}</div>`) +
            row("With other therapy", (b.otherTherapy || []).map((o) => M.coding(o.treatment.concept)).join(" "));
        } else if (r.type === "interaction") {
          kv += row("Interactant", (b.interactant || []).map((i) => M.coding(i.itemCodeableConcept)).join(" ")) + row("Interaction type", e(M.cc(b.type))) + row("Effect", e(M.cc((b.effect || {}).concept))) + row("Management", e((b.management || []).map(M.cc).join("; ")));
        } else if (r.type === "undesirable-effect") {
          const c = b.symptomConditionEffect.concept;
          kv += row("Effect", M.coding(c)) + row("Patient term", e(c.text)) + row("System organ class", e(M.cc(b.classification))) + row("Frequency", e(M.cc(b.frequencyOfOccurrence)));
        } else if (r.type === "warning") {
          kv += row("Concept", M.coding(b.code)) + row("Warning", e(b.description));
        }
        break;
      }
      case "Composition":
        kv = row("Type", M.coding(r.type)) + row("Language", e(r.language)) + row("Version", e(r.version)) + row("Status", e(r.status)) + row("Date", e(r.date));
        break;
      default:
        kv = row("Label", e(M.label(r)));
    }
    const tag = ((r.meta || {}).tag || []).find((t) => t.code === "reused-from-pqi");
    return `<dl class="kv">${kv}</dl>${tag ? `<p class="callout small" style="margin-top:10px">${e(tag.display)}. <a href="../pqi-types/type2.html">See it in the PQI showcases →</a></p>` : ""}`;
  };

  // ---------- JSON viewer ----------
  M.json = function (obj, db) {
    const s = JSON.stringify(obj, (k, v) => (k === "data" && typeof v === "string" && v.length > 120 ? v.slice(0, 60) + "…(base64, " + v.length + " chars)" : v), 2);
    return M.esc(s).replace(/(&quot;(?:[^&]|&(?!quot;))*?&quot;)(\s*:)?|\b(true|false|null)\b|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g, (m, str, colon, bool, num) => {
      if (str) {
        if (colon) return `<span class="k">${str}</span>${colon}`;
        const raw = str.slice(6, -6);
        if (db && /^[A-Z][A-Za-z]+\/[A-Za-z0-9\-.]+$/.test(raw) && db.get(raw)) return `<span class="s">&quot;<a data-ref="${raw}">${raw}</a>&quot;</span>`;
        return `<span class="s">${str}</span>`;
      }
      if (bool) return `<span class="b">${bool}</span>`;
      return `<span class="n">${num}</span>`;
    });
  };

  // ---------- narrative ----------
  M.narrative = function (div, opts) {
    opts = opts || {};
    const doc = new DOMParser().parseFromString(`<body>${div || ""}</body>`, "text/html");
    doc.querySelectorAll("script,style,iframe,object,embed,link,meta,form").forEach((n) => n.remove());
    doc.querySelectorAll("*").forEach((el) => { for (const a of [...el.attributes]) if (/^on/i.test(a.name) || ((a.name === "href" || a.name === "src") && /^\s*javascript:/i.test(a.value))) el.removeAttribute(a.name); });
    doc.querySelectorAll("img").forEach((img) => { const src = img.getAttribute("src"); img.dataset.binary = src; if (opts.images && opts.images[src]) img.setAttribute("src", opts.images[src]); else img.setAttribute("src", ""); img.classList.add("tablet"); });
    if (opts.links) for (const [id, info] of Object.entries(opts.links)) {
      const el = doc.getElementById(id);
      if (!el) continue;
      el.classList.add("lnk");
      if (info.cls) el.classList.add(info.cls);
      el.dataset.link = id;
      el.title = info.title || "";
    }
    doc.querySelectorAll("[id]").forEach((el) => { el.dataset.htmlid = el.id; el.removeAttribute("id"); });
    return doc.body.innerHTML;
  };

  // a section and its subsections as one readable block; opts.links(s) -> {htmlid: {title, cls}}
  M.sectionHtml = function (s, d, opts, depth) {
    opts = opts || {};
    depth = depth || 0;
    const code = M.code(s);
    const div = s.text && s.text.div ? M.narrative(s.text.div, { images: d.images, links: opts.links ? opts.links(s) : null }) : "";
    const cls = opts.secClass ? opts.secClass(s) : "";
    return `<div class="sec ${cls}" data-code="${M.esc(code)}">${depth || opts.showTitle ? `<h4><span class="code">${M.esc(code)}</span>${M.esc(s.title)}</h4>` : ""}${div}` +
      (s.section || []).map((c) => M.sectionHtml(c, d, opts, depth + 1)).join("") + "</div>";
  };
  M.linkMap = (db) => (s) => { const m = {}; M.textLinks(s).forEach((l) => { const r = db.get(l.data); m[l.htmlid] = { title: l.data + (r ? " · " + M.label(r) : "") }; }); return m; };

  // ---------- generated blocks (must match build_epi_types.py) ----------
  M.ueItems = (cuds) => cuds.filter((r) => r.type === "undesirable-effect").map((r) => {
    const b = r.undesirableEffect, c = b.symptomConditionEffect.concept;
    return { id: r.id, term: c.coding[0].display, en: c.text, soc: b.classification.text, freq: b.frequencyOfOccurrence.coding[0].code };
  });
  const byRank = () => Object.keys(EPIDATA.freq).sort((a, b) => EPIDATA.freq[a].rank - EPIDATA.freq[b].rank);
  M.ueTable = function (items) {
    const rows = [];
    for (const soc of EPIDATA.soc) for (const f of byRank()) {
      const hits = items.filter((i) => i.soc === soc && i.freq === f).sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
      if (hits.length) rows.push(`<tr><td>${soc}</td><td>${EPIDATA.freq[f].en}</td><td>` + hits.map((i) => `{{CUD/${i.id}|${i.term}}}`).join(", ") + "</td></tr>");
    }
    return '<div id="gen-ue-table"><table><tr><th>System organ class</th><th>Frequency</th><th>Adverse reaction</th></tr>' + rows.join("") + "</table></div>";
  };
  M.pilSideEffects = function (items, lang) {
    const parts = [];
    for (const f of byRank()) {
      const hits = items.filter((i) => i.freq === f).sort((a, b) => EPIDATA.soc.indexOf(a.soc) - EPIDATA.soc.indexOf(b.soc) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
      if (hits.length) parts.push(`<p><b>${EPIDATA.freq[f][lang + "_pil"]}</b></p><ul>` + hits.map((i) => `<li>{{CUD/${i.id}|${i[lang]}}}</li>`).join("") + "</ul>");
    }
    return '<div id="gen-pil-se">' + parts.join("") + "</div>";
  };
  // markup -> html with spans (Type 4 style); returns {html, links:[[htmlid, ref]]}
  M.expand = function (markup, prefix) {
    const links = []; let n = 0;
    const ABBR = { CUD: "ClinicalUseDefinition" };
    const html = markup.replace(/\{\{([A-Za-z]+)\/([A-Za-z0-9\-.]+)\|(.+?)\}\}/gs, (m, t, id, text) => { n++; const h = `${prefix || "x"}-${id}-${n}`; links.push([h, (ABBR[t] || t) + "/" + id]); return `<span id="${h}">${text}</span>`; });
    return { html, links };
  };

  // ---------- patient rules ----------
  const key = (c) => c.system + "|" + c.code;
  M.codesOf = (cc) => ((cc && cc.coding) || []).map(key);
  M.groupMatch = function (g, p) {
    const res = (g.characteristic || []).map((c) => {
      const k = M.codesOf(c.code)[0] || "", r = c.valueRange || {};
      const v = /\|age$/.test(k) ? p.age : /\|egfr$/.test(k) ? p.egfr : undefined;
      if (v == null || v === "" || isNaN(v)) return null;
      return (!r.low || v >= r.low.value) && (!r.high || v < r.high.value);
    });
    return res.includes(false) ? false : res.includes(null) ? null : true;
  };
  M.evaluate = function (p, db) {
    const has = (set, codes) => codes.find((c) => set.has(c));
    const out = [];
    for (const r of db.all("ClinicalUseDefinition")) {
      const b = M.cudBody(r);
      const groups = (r.population || []).map((x) => db.get(x)).filter(Boolean);
      if (r.type === "indication") {
        for (const g of groups) if (M.groupMatch(g, p) === false) out.push({ r, level: "stop", why: `Outside the indicated population: ${g.name}`, via: "Group/" + g.id });
      } else if (r.type === "contraindication") {
        const c = has(p.conditions, M.codesOf(b.diseaseSymptomProcedure.concept));
        if (c) out.push({ r, level: "stop", why: `Contraindicated: ${M.cc(b.diseaseSymptomProcedure.concept)}`, via: c });
        for (const o of b.otherTherapy || []) { const m = has(p.meds, M.codesOf(o.treatment.concept)); if (m) out.push({ r, level: "stop", why: `Contraindicated with ${M.cc(o.treatment.concept)}`, via: m }); }
      } else if (r.type === "warning") {
        const c = has(p.conditions, M.codesOf(b.code));
        const g = groups.find((x) => M.groupMatch(x, p) === true);
        if (c || g) out.push({ r, level: "caution", why: b.description, via: c || "Group/" + g.id });
      } else if (r.type === "interaction") {
        for (const i of b.interactant || []) {
          const m = has(new Set([...p.meds, ...p.foods]), M.codesOf(i.itemCodeableConcept));
          if (m) out.push({ r, level: /^contraindicated/i.test(M.cc((b.management || [])[0])) ? "stop" : "caution", why: `${M.cc(i.itemCodeableConcept)}: ${M.cc((b.effect || {}).concept)}. ${M.cc((b.management || [])[0])}.`, via: m });
        }
      }
    }
    return out.sort((a, b) => (a.level === b.level ? 0 : a.level === "stop" ? -1 : 1));
  };
  const S = "http://snomed.info/sct|", A = "http://www.whocc.no/atc|", L = "http://example.org/fhir-gra/CodeSystem/synthetic-concept|";
  M.OPTIONS = {
    conditions: [[S + "77386006", "Pregnant"], [L + "breastfeeding", "Breast-feeding"], [S + "235856003", "Liver disease"], [S + "38341003", "Hypertension"],
      [S + "709044004", "Chronic kidney disease"], [L + "galactose-intolerance", "Galactose intolerance / lactase deficiency"], [S + "421961002", "Allergy to Sakuramil or excipients"]],
    meds: [[A + "J02AB02", "Ketoconazole"], [A + "J02AC02", "Itraconazole"], [A + "J01FA09", "Clarithromycin"], [A + "C08DB01", "Diltiazem"], [A + "C08DA01", "Verapamil"], [A + "J04AB02", "Rifampicin"], [A + "B01AA03", "Warfarin"]],
    foods: [[L + "grapefruit-juice", "Grapefruit juice, more than 1 L a day"]],
  };
  M.PERSONAS = [
    { id: "hana", name: "Hana, 52", note: "High cholesterol and high blood pressure; takes diltiazem.", age: 52, egfr: 85, conditions: [S + "38341003"], meds: [A + "C08DB01"], foods: [] },
    { id: "tomas", name: "Tomás, 67", note: "Severe kidney disease (eGFR 24); takes warfarin.", age: 67, egfr: 24, conditions: [S + "709044004"], meds: [A + "B01AA03"], foods: [] },
    { id: "claire", name: "Claire, 34", note: "Pregnant; lactase deficiency.", age: 34, egfr: 100, conditions: [S + "77386006", L + "galactose-intolerance"], meds: [], foods: [] },
    { id: "ken", name: "Ken, 45", note: "Just prescribed clarithromycin; drinks a lot of grapefruit juice.", age: 45, egfr: 90, conditions: [], meds: [A + "J01FA09"], foods: [L + "grapefruit-juice"] },
    { id: "lena", name: "Lena, 16", note: "Familial high cholesterol, aged 16.", age: 16, egfr: 110, conditions: [], meds: [], foods: [] },
    { id: "none", name: "No risk factors", note: "Adult, normal kidney function, no other medicines.", age: 48, egfr: 95, conditions: [], meds: [], foods: [] },
  ];
  M.patient = (o) => ({ age: o.age, egfr: o.egfr, conditions: new Set(o.conditions), meds: new Set(o.meds), foods: new Set(o.foods) });
  M.patientForm = function (p) {
    const box = (grp, [k, l]) => `<label class="toggle"><input type="checkbox" data-grp="${grp}" value="${M.esc(k)}" ${p[grp].includes(k) ? "checked" : ""}><span>${M.esc(l)}</span></label>`;
    return `<div class="pform"><div class="grid g2" style="gap:10px"><label class="small">Age (years)<input class="input" type="number" id="pAge" value="${p.age}"></label><label class="small">eGFR (mL/min/1.73 m²)<input class="input" type="number" id="pEgfr" value="${p.egfr}"></label></div>
      <div class="pane-label" style="padding-left:0">Conditions</div>${M.OPTIONS.conditions.map((o) => box("conditions", o)).join("")}
      <div class="pane-label" style="padding-left:0">Other medicines</div>${M.OPTIONS.meds.map((o) => box("meds", o)).join("")}
      <div class="pane-label" style="padding-left:0">Food and drink</div>${M.OPTIONS.foods.map((o) => box("foods", o)).join("")}</div>`;
  };
  M.readForm = function (el) {
    const p = { age: +M.$("#pAge", el).value, egfr: +M.$("#pEgfr", el).value, conditions: [], meds: [], foods: [] };
    M.$$("input[data-grp]", el).forEach((i) => { if (i.checked) p[i.dataset.grp].push(i.value); });
    return p;
  };

  // ---------- inspector ----------
  M.inspect = function (o) {
    const el = $("#insp");
    el.classList.add("open");
    el.innerHTML = `<div class="insp-head"><div><div class="chips" style="margin-bottom:6px">${(o.chips || []).join("")}</div><h3>${M.esc(o.title)}</h3>${o.path ? `<div class="path">${M.esc(o.path)}</div>` : ""}</div><button class="x" aria-label="Close inspector">×</button></div>
      <div class="insp-body">${o.html || ""}${o.json ? `<details ${o.openJson ? "open" : ""}><summary class="small" style="cursor:pointer;color:var(--muted);margin-bottom:6px">FHIR JSON</summary><pre class="json">${M.json(o.json, o.db)}</pre></details>` : ""}</div>`;
    $(".x", el).onclick = M.closeInspector;
    el.querySelectorAll("[data-ref]").forEach((a) => a.addEventListener("click", (ev) => { ev.preventDefault(); if (o.db) M.inspectResource(a.dataset.ref, o.db); }));
  };
  M.closeInspector = () => { const el = $("#insp"); if (!el) return; el.classList.remove("open"); el.innerHTML = ""; };
  M.inspectResource = function (ref, db, extraHtml) {
    const r = db.get(ref);
    if (!r) return;
    M.inspect({ title: M.label(r), path: r.resourceType + "/" + r.id, db, json: r,
      chips: [`<span class="chip rt acc">${r.resourceType}</span>`, r.type && r.resourceType === "ClinicalUseDefinition" ? `<span class="chip k-${r.type}">${M.esc(r.type)}</span>` : ""],
      html: (extraHtml || "") + M.summary(r, db) });
  };
  M.typeChip = (t) => `<span class="chip" style="background:var(--t${t}-soft);color:var(--t${t});font-weight:700">Type ${t}</span>`;
  M.COLORS = { MedicinalProductDefinition: "#0071e3", PackagedProductDefinition: "#ff9500", ManufacturedItemDefinition: "#5ac8fa", AdministrableProductDefinition: "#64d2ff",
    Ingredient: "#0a8fa8", SubstanceDefinition: "#30b0c7", Organization: "#af52de", RegulatedAuthorization: "#5e5ce6", ClinicalUseDefinition: "#248a3d", Group: "#8e8e93" };
  M.col = (t) => M.COLORS[t] || "#aeaeb2";

  // ---------- shell + router ----------
  M.shell = function (cfg) {
    const t = M.TYPES[cfg.type];
    document.body.classList.add("type" + cfg.type);
    document.body.innerHTML = `<div class="app">
      <header class="top">
        <button class="pane-toggle" id="paneToggle" aria-controls="pane" aria-expanded="true" title="Hide or show the side panel"><svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><rect x="1.5" y="2.5" width="15" height="13" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M6.5 2.5v13" stroke="currentColor" stroke-width="1.5"/></svg></button>
        <div class="brand"><a class="back" href="../../showcases-epi-types.html">← ePI Types 1–4</a>
          <div class="brand-text"><b>ePI Type ${cfg.type} · ${M.esc(t.name)}</b><small>${M.esc(cfg.subtitle || "HL7 FHIR ePI · synthetic Sakura Bloom SmPC and package leaflet")}</small></div></div>
        <nav class="ladder" aria-label="ePI types">${[1, 2, 3, 4].map((n) => `<a href="${M.TYPES[n].page}" ${n === cfg.type ? 'aria-current="page"' : ""} title="Type ${n}: ${M.esc(M.TYPES[n].name)}"><span class="dot" style="background:var(--t${n})"></span>Type ${n} <span class="lbl">${M.esc(M.TYPES[n].short)}</span></a>`).join("")}</nav>
        <span class="synthetic" title="Fictitious product and invented clinical content. Every resource is tagged HTEST.">Synthetic data</span>
      </header>
      <div class="workspace">
        <nav class="pane" id="pane" aria-label="Showcases">
          <details class="about" id="about"><summary><span><span class="tname">ePI Type ${cfg.type}</span><h2>${M.esc(t.name)}</h2></span><span class="chev" aria-hidden="true">▾</span></summary>
            <dl><dt>Adds</dt><dd>${M.esc(t.adds)}</dd><dt>For</dt><dd>${M.esc(t.who)}</dd><dt>Effort</dt><dd>${M.esc(t.effort)}</dd></dl></details>
          <div class="pane-label">Showcases</div>
          <div class="tabs">${cfg.views.map((v, i) => `<a href="#${v.id}" data-view="${v.id}"><span class="n">${i + 1}</span><span>${M.esc(v.title)}<small>${M.esc(v.sub)}</small></span></a>`).join("")}</div>
          <div class="pane-foot">${cfg.foot || ""}<br>Download: ${cfg.downloads || EPIDATA.docs.filter((d) => d.type === cfg.type).map((d) => `<a href="${d.file}" download>${M.esc(d.key)}.json</a>`).join(" · ")}<br><a href="${M.IG}${t.ig}" target="_blank" rel="noopener">ePI Type ${cfg.type} in the IG ↗</a></div>
        </nav>
        <main id="main" tabindex="-1"></main>
        <aside class="insp" id="insp" aria-label="FHIR inspector"></aside>
      </div></div>`;
    const app = $(".app"), tog = $("#paneToggle");
    const setPane = (show) => { app.classList.toggle("pane-closed", !show); tog.setAttribute("aria-expanded", show); $("#pane").inert = !show; };
    let paneOpen = !matchMedia("(max-width: 820px)").matches;
    try { const v = localStorage.getItem("epi-types-pane"); if (v) paneOpen = v === "open"; } catch (e) {}
    setPane(paneOpen);
    tog.onclick = () => { const show = app.classList.contains("pane-closed"); setPane(show); try { localStorage.setItem("epi-types-pane", show ? "open" : "closed"); } catch (e) {} };
    const about = $("#about");
    let open = true;
    try { open = localStorage.getItem("epi-types-about") !== "closed"; } catch (e) {}
    about.open = open && !matchMedia("(max-width: 820px)").matches;
    about.addEventListener("toggle", () => { try { localStorage.setItem("epi-types-about", about.open ? "open" : "closed"); } catch (e) {} });
    const go = () => {
      const [id, ...rest] = decodeURIComponent(location.hash.slice(1)).split("/");
      const v = cfg.views.find((x) => x.id === id) || cfg.views[0];
      M.$$(".tabs a").forEach((a) => (a.dataset.view === v.id ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
      const main = $("#main");
      if (main.dataset.view !== v.id) { M.closeInspector(); main.scrollTop = 0; }
      main.dataset.view = v.id;
      document.title = `${v.title} · ePI Type ${cfg.type} | FHIR for Global Regulatory Affairs`;
      v.render(main, rest.join("/"));
    };
    window.addEventListener("hashchange", go);
    go();
  };
  M.head = (eyebrow, title, text, benefit) => `<div class="view-head"><span class="eyebrow">${eyebrow}</span><h2>${title}</h2><p>${text}</p></div>${benefit ? `<div class="benefit"><b>Benefit</b><span>${benefit}</span></div>` : ""}`;
  M.docSwitch = (docs, cur, attr) => `<div class="seg" role="group" aria-label="Document">${docs.map((d) => `<button ${attr || "data-doc"}="${d.key}" aria-pressed="${d.key === cur}">${M.esc(d.name)}</button>`).join("")}</div>`;
  return M;
})();
