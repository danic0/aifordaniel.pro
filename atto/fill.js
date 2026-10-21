// Writes the customer's details into their airline's PDF, inside the browser.
// Needs pdf-lib (global PDFLib) and FILLMAP (fillmap.js). Nothing is sent anywhere.
(function (root) {
  const pad = n => String(n).padStart(2, '0');
  const fmtDate = iso => { if (!iso) return ''; const [y, m, d] = iso.split('-'); return `${d}.${m}.${y}`; };

  // the customer's answers -> every value a form may ask for
  function values(d) {
    const out = [d.outNo, fmtDate(d.outDate)].filter(Boolean).join(' ');
    const ret = [d.retNo, fmtDate(d.retDate)].filter(Boolean).join(' ');
    const now = new Date();
    return {
      name: d.name, phone: d.phone, email: d.email, booking: d.booking, phone2: d.phone2, route: d.route,
      ins_company: d.insCompany, ins_policy: d.insPolicy, ins_excess: d.insExcess,
      out_no: d.outNo, out_date: fmtDate(d.outDate), ret_no: d.retNo, ret_date: fmtDate(d.retDate),
      flight_nos: [d.outNo, d.retNo].filter(Boolean).join(', '),
      flight_dates: [fmtDate(d.outDate), fmtDate(d.retDate)].filter(Boolean).join(', '),
      flights: [out, ret].filter(Boolean).join(', '),
      phone_email: [d.phone, d.email].filter(Boolean).join(' / '),
      today: `${pad(now.getDate())}.${pad(now.getMonth() + 1)}.${now.getFullYear()}`,
    };
  }

  // append the battery certificate pages (stored once on the site) to a document
  async function addCerts(doc, certBytes) {
    if (!certBytes) return;
    const { PDFDocument } = root.PDFLib;
    const c = await PDFDocument.load(certBytes);
    (await doc.copyPages(c, c.getPageIndices())).forEach(p => doc.addPage(p));
  }
  async function withCerts(bytes, certBytes) {
    const doc = await root.PDFLib.PDFDocument.load(bytes);
    await addCerts(doc, certBytes);
    return doc.save();
  }

  async function fillPdf(bytes, id, data, sigPng, certBytes) {
    const { PDFDocument, StandardFonts, rgb } = root.PDFLib;
    const doc = await PDFDocument.load(bytes);
    const font = await doc.embedFont(StandardFonts.Helvetica);
    const ink = rgb(0.06, 0.2, 0.5);
    const v = values(data);
    const pages = doc.getPages();
    const sig = sigPng ? await doc.embedPng(sigPng) : null;
    let form = null;
    for (const op of (root.FILLMAP[id] || [])) {
      if (op.t === 'field') {
        const val = v[op.key]; if (!val) continue;
        try {
          form = form || doc.getForm();
          const f = form.getTextField(op.name);
          f.setText(val); f.setFontSize(op.size); f.updateAppearances(font);
        } catch (e) { console.warn('field', op.name, e); }
      } else if (op.t === 'text') {
        const val = v[op.key]; if (!val) continue;
        const page = pages[op.p], H = page.getHeight();
        let size = op.size;
        if (op.maxw) while (size > 6 && font.widthOfTextAtSize(val, size) > op.maxw) size -= 0.25;
        page.drawText(val, { x: op.x, y: H - op.y, size, font, color: ink });
      } else if (op.t === 'sig' && sig) {
        const page = pages[op.p], H = page.getHeight();
        const [x0, y0, x1, y1] = op.box, bw = x1 - x0, bh = y1 - y0;
        const k = Math.min(bw / sig.width, bh / sig.height);
        const w = sig.width * k, h = sig.height * k;
        page.drawImage(sig, { x: x0 + (bw - w) / 2, y: H - y1, width: w, height: h });
      }
    }
    await addCerts(doc, certBytes);
    return doc.save();
  }

  root.ATTOFill = { fillPdf, values, withCerts };
})(typeof window !== 'undefined' ? window : globalThis);
