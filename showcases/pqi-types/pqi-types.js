/* PQI Type 1-4 showcases: shared shell and FHIR helpers (no framework). */
const PT = (function () {
  const M = {};
  const $ = (sel, el) => (el || document).querySelector(sel);
  M.$ = $;
  M.$$ = (sel, el) => [...(el || document).querySelectorAll(sel)];

  M.TYPES = {
    1: { name: "Structured document", short: "Structured", page: "type1.html",
         adds: "Coded ICH M4Q(R1) headings. Narrative and figures carry over from the Word template.",
         who: "Sponsors whose quality dossier is still authored in Word.",
         effort: "Convert the Word template." },
    2: { name: "Document + product data", short: "Product data", page: "type2.html",
         adds: "Product, packaging, ingredient, organization and authorization resources, a Product data section, and the document's subject and author.",
         who: "Sponsors with RIM or IDMP master data.",
         effort: "Type 1, plus mapping the master data." },
    3: { name: "Linked document", short: "Linked", page: "type3.html",
         adds: "Any PQI domain resource, with each section's narrative linked to the resources it discusses (textLink).",
         who: "Vendors of CMC authoring tools.",
         effort: "Type 2, plus linking narrative to data." },
    4: { name: "Data-first document", short: "Data-first", page: "type4.html",
         adds: "Resources replace narrative where they carry the content. Generated narrative is for display; the resources are the record.",
         who: "Sponsors with quality data in LIMS, MES or QMS systems.",
         effort: "Type 3, plus generating sections from those systems." },
  };
  M.IG = "https://build.fhir.org/ig/HL7/uv-dx-pq/en/";

  M.esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  M.fmt = (n) => (typeof n === "number" ? n.toLocaleString("en-US") : n);
  M.kfmt = (n) => (n >= 1e6 ? (n / 1e6).toFixed(1) + " M" : n >= 1e4 ? Math.round(n / 1e3) + " k" : M.fmt(n));
  M.plain = (div) => (div || "").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/\s+/g, " ").trim();

  // ---------- Composition helpers ----------
  M.code = (s) => { const c = s.code || {}; return ((c.coding || [])[0] || {}).code || c.text || s.title || ""; };
  M.walk = function (sections, depth, parent, out) {
    out = out || [];
    for (const s of sections || []) {
      const item = { s, depth: depth || 0, parent: parent || null, code: M.code(s) };
      out.push(item);
      M.walk(s.section, (depth || 0) + 1, item, out);
    }
    return out;
  };
  M.docCode = (comp) => { const top = (comp.section || []).filter((s) => M.code(s) !== "pqi-product-data"); return top.length ? M.code(top[0]) : comp.id; };
  M.shortTitle = (t) => String(t || "").replace(/\s*-\s*Sakura Bloom.*$/, "");
  M.isLeaf = (s) => !(s.section && s.section.length);
  M.textLinks = (entry) => (entry.extension || []).filter((x) => x.url === "http://hl7.org/fhir/StructureDefinition/textLink").map((x) => {
    const g = (n) => (x.extension || []).find((e) => e.url === n) || {};
    return { htmlid: g("htmlid").valueString, data: g("data").valueUri };
  });

  // ---------- resource db ----------
  M.db = function (resources, extra) {
    const db = { byKey: new Map(), byUrl: new Map(), byType: new Map(), registry: new Set() };
    const add = (r, reg) => {
      const k = r.resourceType + "/" + r.id;
      db.byKey.set(k, r);
      if (r.url) db.byUrl.set(r.url, r);
      if (!db.byType.has(r.resourceType)) db.byType.set(r.resourceType, []);
      db.byType.get(r.resourceType).push(r);
      if (reg) db.registry.add(k);
    };
    (resources || []).forEach((r) => add(r, false));
    (extra || []).forEach((r) => add(r, true));
    db.get = (ref) => {
      if (!ref) return null;
      if (db.byKey.has(ref)) return db.byKey.get(ref);
      if (db.byUrl.has(ref)) return db.byUrl.get(ref);
      const m = String(ref).match(/([A-Za-z]+\/[^/]+)$/);
      return m ? db.byKey.get(m[1]) || null : null;
    };
    db.reportOf = new Map();
    for (const dr of db.byType.get("DiagnosticReport") || []) for (const x of dr.result || []) db.reportOf.set(x.reference, dr);
    return db;
  };

  M.cc = (c) => (c ? c.text || ((c.coding || [])[0] || {}).display || ((c.coding || [])[0] || {}).code || "" : "");
  M.qty = (q) => (q ? (q.comparator ? q.comparator + " " : "") + q.value + (q.unit ? (q.unit === "%" ? " %" : " " + q.unit) : "") : "");
  M.label = function (r) {
    if (!r) return "";
    switch (r.resourceType) {
      case "MedicinalProductDefinition": return r.name[0].productName;
      case "SubstanceDefinition": return ((r.name || [])[0] || {}).name || r.id;
      case "Substance": return "Batch " + (((r.identifier || [])[0] || {}).value || r.id);
      case "Medication": return r.batch && r.batch.lotNumber ? "Batch " + r.batch.lotNumber + (/bottle/i.test(M.cc(r.code)) ? " · bottle" : /blister/i.test(M.cc(r.code)) ? " · blister" : "") : M.cc(r.code) || r.id;
      case "Organization": return r.name;
      case "DeviceDefinition": return ((r.deviceName || [])[0] || {}).name || r.id;
      case "Observation": return M.cc(r.code) + " = " + (r.valueQuantity ? M.qty(r.valueQuantity) : r.valueString || "");
      case "Ingredient": return M.cc((r.function || [])[0]) + ": " + r.id.replace(/^ing-/, "").replace(/-/g, " ");
      case "ManufacturedItemDefinition": return r.name;
      case "PackagedProductDefinition": return r.name;
      case "RegulatedAuthorization": return M.cc(r.type) + " " + (((r.identifier || [])[0] || {}).value || "");
      case "DocumentReference": return ((r.content || [])[0] || {}).attachment ? r.content[0].attachment.title || r.description : r.description || r.id;
      case "DiagnosticReport": return M.cc(r.code) + (r.category ? " · " + M.cc(r.category[0]) : "") + " · " + r.id.replace(/^dr-/, "");
      case "Specimen": return r.id;
      case "ObservationDefinition": return M.cc(r.code) || r.title || r.id;
      default: return r.title || r.name || M.cc(r.code) || (r.description || "").slice(0, 80) || r.id;
    }
  };
  M.criterionText = function (od) {
    return (od.qualifiedValue || []).map((qv) => {
      const t = (qv.extension || []).find((e) => /qualified-value-text/.test(e.url));
      const r = qv.range;
      const rng = r ? [r.low ? r.low.value : null, r.high ? r.high.value : null] : null;
      return { ctx: qv.context ? M.cc(qv.context) : "", text: t ? t.valueString : rng ? (rng[0] != null ? rng[0] : "") + "–" + (rng[1] != null ? rng[1] : "") : "" };
    });
  };

  // short structured summary of a resource, for the inspector
  M.summary = function (r, db) {
    if (!r) return "";
    const row = (k, v) => (v ? `<dt>${M.esc(k)}</dt><dd>${v}</dd>` : "");
    const ref = (x) => { if (!x) return ""; const t = db && db.get(x.reference || x); return t ? `<a href="#" data-ref="${M.esc(t.resourceType + "/" + t.id)}">${M.esc(M.label(t))}</a>` : M.esc(x.display || x.reference || x); };
    let kv = "", extra = "";
    switch (r.resourceType) {
      case "PlanDefinition": {
        const acts = [];
        const visit = (as, grp) => (as || []).forEach((a) => {
          if (a.definitionCanonical) acts.push({ grp, a, od: db && db.get(a.definitionCanonical) });
          visit(a.action, a.title && !a.definitionCanonical ? a.title : grp);
        });
        visit(r.action, "");
        kv = row("Type", M.esc(M.cc(r.type))) + row("Actions", acts.length || (r.action || []).length);
        if (acts.length) {
          extra = `<table class="t"><tr><th>Test</th><th>Acceptance criterion</th></tr>` + acts.slice(0, 60).map(({ grp, a, od }) => {
            const crit = od ? M.criterionText(od).map((c) => (c.ctx ? `<span class="muted">${M.esc(c.ctx)}:</span> ` : "") + M.esc(c.text)).join("<br>") : `<span class="muted">not resolved</span>`;
            return `<tr><td>${od ? `<a href="#" data-ref="ObservationDefinition/${M.esc(od.id)}">${M.esc(a.title)}</a>` : M.esc(a.title)}${grp ? `<div class="muted small">${M.esc(grp)}</div>` : ""}</td><td>${crit}</td></tr>`;
          }).join("") + `</table>` + (acts.length > 60 ? `<p class="muted small">+ ${acts.length - 60} more</p>` : "");
        } else if ((r.action || []).length) {
          extra = `<ol class="small">` + r.action.slice(0, 30).map((a) => `<li>${M.esc(a.title || a.description || M.cc(a.code))}</li>`).join("") + `</ol>`;
        }
        break;
      }
      case "ObservationDefinition":
        kv = row("Category", M.esc(M.cc((r.category || [])[0]))) + row("Criteria", M.criterionText(r).map((c) => (c.ctx ? `<b>${M.esc(c.ctx)}</b>: ` : "") + M.esc(c.text)).join("<br>"));
        break;
      case "DiagnosticReport": {
        kv = row("Subject", ref(r.subject)) + row("Performer", (r.performer || []).map(ref).join(", ")) + row("Results", (r.result || []).length);
        const obs = (r.result || []).map((x) => db && db.get(x.reference)).filter(Boolean);
        if (obs.length) extra = `<table class="t"><tr><th>Test</th><th>Result</th></tr>` + obs.slice(0, 40).map((o) => `<tr><td>${M.esc(M.cc(o.code))}${o.specimen ? `<div class="muted small mono">${M.esc(o.specimen.reference.replace("Specimen/", ""))}</div>` : ""}</td><td class="num">${M.esc(o.valueQuantity ? M.qty(o.valueQuantity) : o.valueString || "")}</td></tr>`).join("") + `</table>` + (obs.length > 40 ? `<p class="muted small">+ ${obs.length - 40} more</p>` : "");
        break;
      }
      case "Observation": {
        const od = db && db.get(r.instantiatesCanonical);
        kv = row("Value", M.esc(r.valueQuantity ? M.qty(r.valueQuantity) : r.valueString)) + row("Subject", ref(r.subject)) + row("Definition", od ? ref({ reference: "ObservationDefinition/" + od.id }) : "") +
          (od ? row("Criteria", M.criterionText(od).map((c) => (c.ctx ? c.ctx + ": " : "") + M.esc(c.text)).join("<br>")) : "");
        break;
      }
      case "Organization":
        kv = row("Name", M.esc(r.name)) + row("Identifiers", (r.identifier || []).map((i) => `<span class="mono">${M.esc(i.value)}</span> <span class="muted small">${M.esc(/519\.1/.test(i.system) ? "DUNS" : /4\.82/.test(i.system) ? "FEI" : i.system)}</span>`).join("<br>")) +
          row("Roles", (r.type || []).map((t) => `<span class="chip">${M.esc(M.cc(t))}</span>`).join(" ")) +
          row("Address", M.esc(((r.contact || [])[0] || {}).address ? [r.contact[0].address.city, r.contact[0].address.country].filter(Boolean).join(", ") : ""));
        break;
      case "SubstanceDefinition":
        kv = row("Name", M.esc(M.label(r))) + row("Identifier", (r.identifier || []).map((i) => M.esc(i.value)).join(", ")) + row("Classification", M.esc(M.cc((r.classification || [])[0]))) +
          row("Description", M.esc(r.description)) + row("Properties", (r.property || []).length) + row("Manufacturer", (r.manufacturer || []).map(ref).join(", "));
        break;
      case "Ingredient": {
        const st = (((r.substance || {}).strength || [])[0] || {});
        kv = row("Role", M.esc(M.cc(r.role))) + row("Function", M.esc(M.cc((r.function || [])[0]))) + row("Substance", ref(((r.substance || {}).code || {}).reference)) + row("Strength", M.esc(st.textPresentation || (st.presentationRatio ? M.qty(st.presentationRatio.numerator) + " / " + M.qty(st.presentationRatio.denominator) : "")));
        break;
      }
      case "MedicinalProductDefinition":
        kv = row("Name", M.esc(r.name[0].productName)) + row("Dose form", M.esc(M.cc(r.combinedPharmaceuticalDoseForm))) + row("Route", (r.route || []).map((x) => M.esc(M.cc(x))).join(", ")) + row("Identifier", M.esc(((r.identifier || [])[0] || {}).value)) + row("Description", M.esc(r.description));
        break;
      case "ManufacturedItemDefinition":
        kv = row("Dose form", M.esc(M.cc(r.manufacturedDoseForm))) + row("Unit", M.esc(M.cc(r.unitOfPresentation))) + (r.property || []).slice(0, 8).map((p) => row(M.cc(p.type), M.esc(p.valueCodeableConcept ? M.cc(p.valueCodeableConcept) : p.valueQuantity ? M.qty(p.valueQuantity) : p.valueString || ""))).join("");
        break;
      case "PackagedProductDefinition":
        kv = row("Type", M.esc(M.cc(r.type))) + row("Description", M.esc(r.description)) + row("Shelf life", (((r.packaging || {}).shelfLifeStorage) || []).map((s) => M.esc((s.periodDuration ? s.periodDuration.value + " " + s.periodDuration.unit : s.periodString || "") + " " + M.cc(s.type))).join("<br>"));
        break;
      case "RegulatedAuthorization":
        kv = row("Number", `<span class="mono">${M.esc(((r.identifier || [])[0] || {}).value)}</span>`) + row("Type", M.esc(M.cc(r.type))) + row("Region", (r.region || []).map((x) => M.esc(M.cc(x))).join(", ")) + row("Status", M.esc(M.cc(r.status)) + (r.statusDate ? " since " + M.esc(r.statusDate) : "")) + row("Holder", ref(r.holder)) + row("Note", M.esc(r.description));
        break;
      case "Medication":
        kv = row("Product", M.esc(M.cc(r.code))) + row("Lot", M.esc((r.batch || {}).lotNumber)) + row("Expiry", M.esc((r.batch || {}).expirationDate));
        break;
      case "Substance":
        kv = row("Identifier", M.esc(((r.identifier || [])[0] || {}).value)) + row("Code", ref(((r.code || {}).reference) || null) || M.esc(M.cc((r.code || {}).concept))) + row("Description", M.esc(r.description));
        break;
      case "DeviceDefinition":
        kv = row("Name", M.esc(M.label(r))) + row("Class", M.esc(M.cc((r.classification || [])[0] && r.classification[0].type)));
        break;
      case "DocumentReference": {
        const at = ((r.content || [])[0] || {}).attachment || {};
        const img = PT.images && PT.images[at.url];
        kv = row("Title", M.esc(at.title)) + row("Type", M.esc(M.cc(r.type))) + row("Provenance", M.esc((r.description || "").replace(at.title || "", "").replace(/^\.\s*/, ""))) + row("Attachment", `<span class="mono">${M.esc(at.url || "")}</span>`);
        if (img) extra = `<img src="${M.esc(img)}" alt="${M.esc(at.title || "")}" style="max-width:100%;border:1px solid var(--sep);border-radius:10px">`;
        break;
      }
      default:
        kv = row("Label", M.esc(M.label(r)));
    }
    return `<dl class="kv">${kv}</dl>${extra}`;
  };

  // ---------- JSON viewer ----------
  M.json = function (obj, db) {
    const s = JSON.stringify(obj, null, 2);
    return M.esc(s).replace(/(&quot;(?:[^&]|&(?!quot;))*?&quot;)(\s*:)?|\b(true|false|null)\b|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g, (m, str, colon, bool, num) => {
      if (str) {
        if (colon) return `<span class="k">${str}</span>${colon}`;
        const raw = str.slice(6, -6);
        if (db && /^[A-Z][A-Za-z]+\/[A-Za-z0-9\-.]+$/.test(raw) && db.get(raw)) return `<span class="s">&quot;<a data-ref="${raw}">${raw}</a>&quot;</span>`;
        if (db && /^http:\/\/example\.org\/sakura-bloom-r2\/fhir\/[A-Za-z]+\/[A-Za-z0-9\-.]+$/.test(raw) && db.get(raw)) { const t = db.get(raw); return `<span class="s">&quot;<a data-ref="${t.resourceType}/${t.id}">${raw}</a>&quot;</span>`; }
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
    doc.querySelectorAll("*").forEach((el) => {
      for (const a of [...el.attributes]) {
        if (/^on/i.test(a.name)) el.removeAttribute(a.name);
        if ((a.name === "href" || a.name === "src") && /^\s*javascript:/i.test(a.value)) el.removeAttribute(a.name);
      }
    });
    doc.querySelectorAll("img").forEach((img) => {
      const src = img.getAttribute("src");
      img.setAttribute("loading", "lazy");
      img.dataset.binary = src;
      if (opts.images && opts.images[src]) img.setAttribute("src", opts.images[src]);
    });
    doc.querySelectorAll("a[href]").forEach((a) => { a.setAttribute("target", "_blank"); a.setAttribute("rel", "noopener"); });
    if (opts.links) {
      for (const [id, info] of Object.entries(opts.links)) {
        const el = doc.getElementById(id);
        if (!el) continue;
        el.classList.add(el.tagName === "SPAN" || el.tagName === "A" ? "lnk" : "lnk-block");
        el.dataset.link = id;
        el.title = info.title || "";
      }
    }
    // keep anchors unique on the page
    doc.querySelectorAll("[id]").forEach((el) => { el.dataset.htmlid = el.id; el.removeAttribute("id"); });
    return doc.body.innerHTML;
  };

  // ---------- inspector ----------
  M.inspect = function (o) {
    const el = $("#insp");
    el.classList.add("open");
    el.innerHTML = `<div class="insp-head"><div><div class="chips" style="margin-bottom:6px">${(o.chips || []).join("")}</div><h3>${M.esc(o.title)}</h3>${o.path ? `<div class="path">${M.esc(o.path)}</div>` : ""}</div><button class="x" aria-label="Close inspector">×</button></div>
      <div class="insp-body">${o.html || ""}${o.json ? `<details ${o.openJson ? "open" : ""}><summary class="small" style="cursor:pointer;color:var(--muted);margin-bottom:6px">FHIR JSON</summary><pre class="json">${M.json(o.json, o.db)}</pre></details>` : ""}</div>`;
    $(".x", el).onclick = M.closeInspector;
    el.querySelectorAll("[data-ref]").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); if (o.db) M.inspectResource(a.dataset.ref, o.db); }));
  };
  M.closeInspector = () => { const el = $("#insp"); el.classList.remove("open"); el.innerHTML = ""; };
  M.inspectResource = function (ref, db, extraHtml) {
    const r = db.get(ref);
    if (!r) return;
    const reg = db.registry.has(r.resourceType + "/" + r.id);
    M.inspect({
      title: M.label(r), path: r.resourceType + "/" + r.id, db, json: r,
      chips: [`<span class="chip rt acc">${r.resourceType}</span>`, reg ? `<span class="chip warn" title="Referenced by canonical URL; not carried in the document bundle">resolved from registry</span>` : "",
        r.meta && r.meta.profile ? `<span class="chip rt" title="${M.esc(r.meta.profile[0])}">${M.esc(r.meta.profile[0].split("/").pop())}</span>` : ""],
      html: (extraHtml || "") + M.summary(r, db),
    });
  };
  M.typeChip = (t) => `<span class="chip" style="background:var(--t${t}-soft);color:var(--t${t});font-weight:700">Type ${t}</span>`;

  // ---------- shell + router ----------
  M.shell = function (cfg) {
    const t = M.TYPES[cfg.type];
    document.body.classList.add("type" + cfg.type);
    document.body.innerHTML = `<div class="app">
      <header class="top">
        <button class="pane-toggle" id="paneToggle" aria-controls="pane" aria-expanded="true" title="Hide or show the side panel"><svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><rect x="1.5" y="2.5" width="15" height="13" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.5"/><line x1="6.5" y1="2.5" x2="6.5" y2="15.5" stroke="currentColor" stroke-width="1.5"/></svg><span class="vh">Toggle side panel</span></button>
        <div class="brand"><a class="back" href="../../showcases-pqi-types.html">← PQI Types 1–4</a>
          <div class="brand-text"><b>PQI Type ${cfg.type} · ${M.esc(t.name)}</b><small>HL7 FHIR PQI · synthetic CTD Module 2.3 and 3.2 example data</small></div></div>
        <nav class="ladder" aria-label="PQI maturity types">${[1, 2, 3, 4].map((n) => `<a href="${M.TYPES[n].page}" ${n === cfg.type ? 'aria-current="page"' : ""} title="Type ${n}: ${M.esc(M.TYPES[n].name)}"><span class="dot" style="background:var(--t${n})"></span>T${n}<span class="lbl">${M.esc(M.TYPES[n].short)}</span></a>`).join("")}</nav>
        <span class="synthetic" title="Fictitious product. Every resource is tagged HTEST.">Synthetic data</span>
      </header>
      <div class="workspace">
        <nav class="pane" id="pane" aria-label="Showcases">
          <details class="about" id="about"><summary><span><span class="tname">PQI Type ${cfg.type}</span><h2>${M.esc(t.name)}</h2></span><span class="chev" aria-hidden="true">▾</span></summary>
            <dl><dt>Adds</dt><dd>${M.esc(t.adds)}</dd><dt>For</dt><dd>${M.esc(t.who)}</dd><dt>Effort</dt><dd>${M.esc(t.effort)}</dd></dl></details>
          <div class="pane-label">Showcases</div>
          <div class="tabs">${cfg.views.map((v, i) => `<a href="#${v.id}" data-view="${v.id}"><span class="n">${i + 1}</span><span>${M.esc(v.title)}<small>${M.esc(v.sub)}</small></span></a>`).join("")}</div>
          <div class="pane-foot">${cfg.foot || ""}<br>Profiles: <a href="${M.IG}build_type${cfg.type}.html" target="_blank" rel="noopener">PQI Type ${cfg.type} in the IG ↗</a></div>
        </nav>
        <main id="main" tabindex="-1"></main>
        <aside class="insp" id="insp" aria-label="FHIR inspector"></aside>
      </div></div>`;
    const app = $(".app"), tog = $("#paneToggle");
    const setPane = (show) => { app.classList.toggle("pane-closed", !show); tog.setAttribute("aria-expanded", show); $("#pane").inert = !show; };
    let paneOpen = !matchMedia("(max-width: 820px)").matches;
    try { const v = localStorage.getItem("pqi-types-pane"); if (v) paneOpen = v === "open"; } catch (e) {}
    setPane(paneOpen);
    tog.onclick = () => { const show = app.classList.contains("pane-closed"); setPane(show); try { localStorage.setItem("pqi-types-pane", show ? "open" : "closed"); } catch (e) {} };
    const about = $("#about");
    let open = true;
    try { open = localStorage.getItem("pqi-types-about") !== "closed"; } catch (e) {}
    about.open = open && !matchMedia("(max-width: 820px)").matches;
    about.addEventListener("toggle", () => { try { localStorage.setItem("pqi-types-about", about.open ? "open" : "closed"); } catch (e) {} });
    const go = () => {
      const [id, ...rest] = decodeURIComponent(location.hash.slice(1)).split("/");
      const v = cfg.views.find((x) => x.id === id) || cfg.views[0];
      M.$$(".tabs a").forEach((a) => (a.dataset.view === v.id ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
      const main = $("#main");
      if (main.dataset.view !== v.id) { M.closeInspector(); main.scrollTop = 0; }
      main.dataset.view = v.id;
      document.title = `${v.title} · PQI Type ${cfg.type} | FHIR for Global Regulatory Affairs`;
      v.render(main, rest.join("/"));
    };
    window.addEventListener("hashchange", go);
    go();
  };
  M.head = (eyebrow, title, text, benefit) => `<div class="view-head"><span class="eyebrow">${eyebrow}</span><h2>${title}</h2><p>${text}</p></div>${benefit ? `<div class="benefit"><b>Benefit</b><span>${benefit}</span></div>` : ""}`;

  // canonical list of M4Q(R1) Module 3.2 headings (level 3/4), for completeness checks
  M.M32 = [
    ["3.2.S.1", "General Information", ["3.2.S.1.1", "3.2.S.1.2", "3.2.S.1.3"]],
    ["3.2.S.2", "Manufacture", ["3.2.S.2.1", "3.2.S.2.2", "3.2.S.2.3", "3.2.S.2.4", "3.2.S.2.5", "3.2.S.2.6"]],
    ["3.2.S.3", "Characterisation", ["3.2.S.3.1", "3.2.S.3.2"]],
    ["3.2.S.4", "Control of Drug Substance", ["3.2.S.4.1", "3.2.S.4.2", "3.2.S.4.3", "3.2.S.4.4", "3.2.S.4.5"]],
    ["3.2.S.5", "Reference Standards or Materials", []],
    ["3.2.S.6", "Container Closure System", []],
    ["3.2.S.7", "Stability", ["3.2.S.7.1", "3.2.S.7.2", "3.2.S.7.3"]],
    ["3.2.P.1", "Description and Composition", []],
    ["3.2.P.2", "Pharmaceutical Development", ["3.2.P.2.1", "3.2.P.2.2", "3.2.P.2.3", "3.2.P.2.4", "3.2.P.2.5", "3.2.P.2.6"]],
    ["3.2.P.3", "Manufacture", ["3.2.P.3.1", "3.2.P.3.2", "3.2.P.3.3", "3.2.P.3.4", "3.2.P.3.5"]],
    ["3.2.P.4", "Control of Excipients", ["3.2.P.4.1", "3.2.P.4.2", "3.2.P.4.3", "3.2.P.4.4", "3.2.P.4.5", "3.2.P.4.6"]],
    ["3.2.P.5", "Control of Drug Product", ["3.2.P.5.1", "3.2.P.5.2", "3.2.P.5.3", "3.2.P.5.4", "3.2.P.5.5", "3.2.P.5.6"]],
    ["3.2.P.6", "Reference Standards or Materials", []],
    ["3.2.P.7", "Container Closure System", []],
    ["3.2.P.8", "Stability", ["3.2.P.8.1", "3.2.P.8.2", "3.2.P.8.3"]],
    ["3.2.A.1", "Facilities and Equipment", []],
    ["3.2.A.2", "Adventitious Agents Safety Evaluation", []],
    ["3.2.A.3", "Excipients", []],
    ["3.2.R", "Regional Information", []],
  ];
  return M;
})();
