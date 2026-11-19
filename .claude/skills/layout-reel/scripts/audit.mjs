// Auditoria de layout do Reel: mede a TINTA renderizada (pixels), não as caixas do CSS.
// Uso: node layout-audit.mjs [index.html] [tempos separados por vírgula]
// Verifica: (1) ritmo dos espaços (dentro do grupo < entre blocos < antes das marcas), (2) separadores no eixo x=540
// e centralizados no conteúdo, (3) título numa linha, (4) alinhamento à esquerda, (5) zona segura.
import { createRequire } from "node:module";
import { resolve } from "node:path";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const file = resolve(process.argv[2] || "index.html");
const TIMES = (process.argv[3] || "4.2,8.4,12.5,18,31.5,35.5,38.4,47.5,52.5,56.4,60,66").split(",").map(Number);
const AX = 540, SAFE = { x0: 65, x1: 1015, y0: 269, y1: 1580 };
const out = []; let fails = 0;
const ok = (c, name, detail) => { out.push(`${c ? "  ok " : "FALHA"}  ${name}${detail ? "  — " + detail : ""}`); if (!c) fails++; };

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto("file://" + file); await page.waitForTimeout(1200);
await page.evaluate(() => document.fonts.ready);

// mede a tinta de um conjunto de elementos (isolados sobre preto)
async function ink(selector, idx = 0) {
  await page.evaluate(([sel, i]) => {
    document.querySelectorAll("#root *").forEach((e) => e.setAttribute("data-prev-vis", e.style.visibility || ""));
    document.body.style.background = "#000"; document.getElementById("root").style.background = "#000";
    document.querySelectorAll("#root > *, #cardmask").forEach((e) => (e.style.visibility = "hidden"));
    const target = [...document.querySelectorAll(sel)].filter((e) => { const c = e.closest(".clip"); return c && getComputedStyle(c).display !== "none" && parseFloat(getComputedStyle(c).opacity) > 0.9; })[i];
    window.__t = target;
    target.closest(".clip").querySelectorAll("*").forEach((e) => (e.style.visibility = "hidden"));   // visibilidade herdada acenderia os vizinhos
    let n = target; while (n && n.id !== "root") { n.style.visibility = "visible"; n = n.parentElement; }
    target.querySelectorAll("*").forEach((e) => (e.style.visibility = "visible"));
  }, [selector, idx]);
  const png = await page.screenshot({ type: "png" });
  const box = await page.evaluate(async (b64) => {
    const img = new Image(); img.src = "data:image/png;base64," + b64; await img.decode();
    const c = document.createElement("canvas"); c.width = img.width; c.height = img.height; const x = c.getContext("2d"); x.drawImage(img, 0, 0);
    const d = x.getImageData(0, 0, c.width, c.height).data; let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let y = 0; y < c.height; y++) for (let xx = 0; xx < c.width; xx++) { const k = (y * c.width + xx) * 4; if (d[k] + d[k + 1] + d[k + 2] > 90) { if (xx < x0) x0 = xx; if (xx > x1) x1 = xx; if (y < y0) y0 = y; if (y > y1) y1 = y; } }
    return x1 < 0 ? null : { x0, y0, x1, y1 };
  }, png.toString("base64"));
  await page.evaluate(() => {
    document.querySelectorAll("#root *").forEach((e) => { e.style.visibility = e.getAttribute("data-prev-vis") || ""; e.removeAttribute("data-prev-vis"); });
    document.querySelectorAll("#root > *, #cardmask").forEach((e) => (e.style.visibility = ""));
    document.body.style.background = ""; document.getElementById("root").style.background = "";
  });
  return box;
}
// emula o runtime: só mostra os clipes dentro do seu intervalo
async function seek(t) {
  await page.evaluate((tt) => {
    window.__timelines.main.seek(tt, false);
    document.querySelectorAll(".clip").forEach((e) => {
      const s = parseFloat(e.dataset.start), d = parseFloat(e.dataset.duration);
      e.style.display = tt >= s && tt < s + d ? "" : "none";
    });
  }, t);
  await page.waitForTimeout(60);
}
async function dom(selector, idx = 0) {   // caixa aparada do texto (cap-height → linha de base), igual ao que a tipografia usa para alinhar
  return page.evaluate(([sel, i]) => {
    const t = [...document.querySelectorAll(sel)].filter((e) => { const c = e.closest(".clip"); return c && getComputedStyle(c).display !== "none" && parseFloat(getComputedStyle(c).opacity) > 0.9; })[i];
    if (!t) return null; const r = t.getBoundingClientRect(); return { x0: r.left, y0: r.top, x1: r.right, y1: r.bottom };
  }, [selector, idx]);
}
const gapY = (a, b) => (a && b ? b.y0 - a.y1 - 1 : null);
const cx = (b) => (b.x0 + b.x1) / 2, cy = (b) => (b.y0 + b.y1) / 2;

const R = { gapHF: [], gapFC: [], gapCD: [], gapDM: [], gapMK: [], gapKA: [] };
for (const t of TIMES) {
  await seek(t);
  const info = await page.evaluate(() => {
    const vis = (sel) => [...document.querySelectorAll(sel)].filter((e) => getComputedStyle(e.closest(".clip")).display !== "none" && parseFloat(getComputedStyle(e.closest(".clip")).opacity) > 0.95).length;
    const ttl = [...document.querySelectorAll(".ttl")].find((e) => getComputedStyle(e.closest(".clip")).display !== "none" && parseFloat(getComputedStyle(e.closest(".clip")).opacity) > 0.95);
    let lines = 0; if (ttl) { lines = ttl.getBoundingClientRect().height > 45 ? 2 : 1; }   // caixa aparada = altura das maiúsculas (≈25 px); 2 linhas passam de 45
    const frame = [...document.querySelectorAll('.clip')].find((e) => e.style.border && e.style.borderRadius === "24px" && e.style.display !== "none");
    const fr = frame ? frame.getBoundingClientRect() : null;
    return { hasCap: vis(".cap"), hasChip: vis(".chip"), hasHd: vis(".hd"), ttlLines: lines, frame: fr ? { x0: fr.left, y0: fr.top, x1: fr.right, y1: fr.bottom } : null };
  });
  const hdInk = info.hasHd ? await ink(".hd") : null;
  const hdK = info.hasHd ? await dom(".kick") : null, hdT = info.hasHd ? await dom(".ttl") : null;
  const hd = hdInk && { x0: hdInk.x0, x1: hdInk.x1, y0: hdK.y0, y1: hdT.y1 };   // topo = maiúsculas da linha pequena · fundo = linha de base do título
  const capInk = info.hasCap ? await ink(".cap") : null;
  const capD = info.hasCap ? await dom(".cap") : null;
  const cap = capInk && { x0: capInk.x0, x1: capInk.x1, y0: capD.y0, y1: capD.y1 };   // linha de base da última linha
  const chip = info.hasChip ? await ink(".chip") : null;
  const tag = `t=${t}s`;
  if (info.hasHd) ok(info.ttlLines === 1, `${tag} título numa linha`, `${info.ttlLines} linha(s)`);
  if (hd && info.frame) { const g = gapY(hd, info.frame); R.gapHF.push(g); }
  if (info.frame && cap) R.gapFC.push(gapY(info.frame, cap));
  if (cap && chip) R.gapCD.push(gapY(cap, chip));
  if (hd) { ok(hd.x0 >= SAFE.x0 && hd.x1 <= SAFE.x1, `${tag} cabeçalho na zona segura (x)`, `${hd.x0}–${hd.x1}`); ok(Math.abs(hd.x0 - 80) <= 4, `${tag} cabeçalho alinhado à esquerda do vídeo (x=80)`, `x0=${hd.x0}`); }
  if (cap) ok(cap.x0 >= SAFE.x0 && cap.x1 <= SAFE.x1, `${tag} legenda na zona segura (x)`, `${cap.x0}–${cap.x1}`);
  if (chip) { ok(Math.abs(cx(chip) - AX) <= 3, `${tag} dado centralizado no eixo`, `centro ${cx(chip).toFixed(1)}`); ok(chip.x0 >= SAFE.x0 && chip.x1 <= SAFE.x1, `${tag} dado na zona segura`, `${chip.x0}–${chip.x1}`); }
}

// rodapé (fixo): separadores no eixo, centralizados no conteúdo, ritmo interno
await seek(18);
const marks = [await ink("[id^=ft] img", 0), await ink("[id^=ft] img", 1)];                     // Boechat, 6º Leilão
const labs = [await dom("[id^=ft] .flab", 0), await dom("[id^=ft] .flab", 1), await dom("[id^=ft] .flab", 2)];
const logos2 = [await ink("[id^=ft] img", 2), await ink("[id^=ft] img", 3), await ink("[id^=ft] img", 4)];
const jireh = await ink("[id^=ft] img", 5);
const divs = await page.evaluate(() => [...document.querySelectorAll("[id^=ft] div")].filter((d) => d.style.width === "2px").map((d) => { const r = d.getBoundingClientRect(); return { x0: r.left, x1: r.right, y0: r.top, y1: r.bottom }; }));
const rowMarks = { y0: Math.min(...marks.map((m) => m.y0)), y1: Math.max(...marks.map((m) => m.y1)) };
const rowLab = { y0: Math.min(labs[0].y0, labs[1].y0), y1: Math.max(labs[0].y1, labs[1].y1) };
const rowLogo = { y0: Math.min(...logos2.map((m) => m.y0)), y1: Math.max(...logos2.map((m) => m.y1)) };
R.gapMK = [rowLab.y0 - rowMarks.y1 - 1]; R.gapKA = [labs[2].y0 - rowLogo.y1 - 1];
const gLabLogo = rowLogo.y0 - rowLab.y1 - 1, gAgJir = jireh.y0 - labs[2].y1 - 1;
await seek(18); const chip18 = await ink(".chip");
R.gapDM = [rowMarks.y0 - chip18.y1 - 1];
out.push("");
divs.forEach((d, i) => ok(Math.abs((d.x0 + d.x1) / 2 - AX) <= 1, `separador ${i + 1} no eixo x=540`, `centro ${((d.x0 + d.x1) / 2).toFixed(1)}`));
const d1 = divs[0], d2 = divs[1];
ok(Math.abs(cy(d1) - cy(rowMarks)) <= 2, "separador das marcas centralizado na altura das marcas", `sep ${cy(d1).toFixed(1)} · marcas ${cy(rowMarks).toFixed(1)}`);
ok(Math.abs(cy(d2) - (rowLab.y0 + rowLogo.y1) / 2) <= 2, "separador da linha 2 centralizado (rótulo → logo)", `sep ${cy(d2).toFixed(1)} · conteúdo ${((rowLab.y0 + rowLogo.y1) / 2).toFixed(1)}`);
const sym = (a, b) => Math.abs((AX - a) - (b - AX));
ok(sym(marks[0].x1, marks[1].x0) <= 90, "marcas distribuídas em torno do eixo", `Boechat termina a ${AX - marks[0].x1}px · 6º Leilão começa a ${marks[1].x0 - AX}px do eixo`);
ok(Math.abs(cx(labs[0]) - (AX - 158)) <= 3 && Math.abs(cx(labs[1]) - (AX + 158)) <= 3, "rótulos simétricos ao eixo", `${(AX - cx(labs[0])).toFixed(0)} | ${(cx(labs[1]) - AX).toFixed(0)}`);
ok(Math.abs(cx(jireh) - AX) <= 3 && Math.abs(cx(labs[2]) - AX) <= 3, "agência centralizada no eixo", `${cx(jireh).toFixed(1)} · ${cx(labs[2]).toFixed(1)}`);
ok(jireh.y1 <= SAFE.y1, "rodapé dentro da zona segura inferior", `termina em y=${jireh.y1} (limite ${SAFE.y1})`);
ok(rowLogo.y1 - rowLogo.y0 <= 52 && rowMarks.y1 - rowMarks.y0 <= 84 && rowLogo.y1 - rowLogo.y0 < rowMarks.y1 - rowMarks.y0, "créditos menores que as marcas principais", `marcas ${rowMarks.y1 - rowMarks.y0}px · logos ${rowLogo.y1 - rowLogo.y0}px de altura`);

// ritmo dos espaços
const avg = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN);
const spread = (a) => (a.length ? Math.max(...a) - Math.min(...a) : 0);
out.push(`  [detalhe] cabeçalho→vídeo por cena: ${TIMES.map((t,i)=>t+"s:"+R.gapHF[i]).join(" ")}`);
out.push(`  [detalhe] marcas y ${rowMarks.y0}–${rowMarks.y1} · rótulos ${rowLab.y0}–${rowLab.y1} · logos ${rowLogo.y0}–${rowLogo.y1} · agência ${labs[2].y0}–${labs[2].y1} · Jireh ${jireh.y0}–${jireh.y1} · logos individuais ${logos2.map(b=>b.y0+"–"+b.y1).join(" | ")}`);
const gHF = avg(R.gapHF), gFC = avg(R.gapFC), gCD = avg(R.gapCD.slice(-3)), gDM = R.gapDM[0], gMK = R.gapMK[0], gKA = R.gapKA[0];
out.push("");
out.push(`  Espaços medidos (tinta → tinta, px):  cabeçalho→vídeo ${gHF.toFixed(0)} · vídeo→legenda ${gFC.toFixed(0)} · legenda→dado ${gCD.toFixed(0)} (2 linhas) · dado→marcas ${gDM} · marcas→rótulos ${gMK} · rótulo→logo ${gLabLogo} · logos→agência ${gKA} · agência→Jireh ${gAgJir}`);
ok(spread(R.gapHF) <= 3 && spread(R.gapFC) <= 3, "espaços estáveis entre cenas (nada pula)", `cabeçalho→vídeo varia ${spread(R.gapHF)}px · vídeo→legenda varia ${spread(R.gapFC)}px`);
ok(gHF >= 40 && gFC >= 40 && gCD >= 40, "blocos de conteúdo com folga de pelo menos 40 px");
ok(Math.max(gHF, gFC, gCD) - Math.min(gHF, gFC, gCD) <= 6, "ritmo igual entre os blocos de conteúdo", `${[gHF, gFC, gCD].map((x) => x.toFixed(0)).join(" / ")}`);
ok(gDM >= 1.6 * Math.max(gHF, gFC, gCD), "espaço antes das marcas bem maior que entre blocos", `${gDM} vs ${Math.max(gHF, gFC, gCD).toFixed(0)}`);
ok(Math.max(gMK, gKA) <= 0.6 * Math.min(gHF, gFC, gCD) + 1, "espaços dentro do grupo de marcas menores que entre blocos", `${gMK} / ${gKA} vs ${Math.min(gHF, gFC, gCD).toFixed(0)}`);
ok(Math.abs(gMK - gKA) <= 3, "ritmo interno das marcas uniforme", `${gMK} / ${gKA}`);

// tela final
await seek(66);
const E = {}; for (const [k, sel] of [["dow", ".enddow"], ["dia", ".enddia"], ["dm", ".enddm"], ["rule", ".endrule"], ["cta", ".endcta"]]) { const d = await dom(sel); const i = await ink(sel); E[k] = { x0: i.x0, x1: i.x1, y0: d.y0, y1: d.y1 }; }
const capE = await dom(".cap");
out.push("");
out.push(`  Tela final (px): sábado→21 ${gapY(E.dow, E.dia)} · 21→data ${gapY(E.dia, E.dm)} · data→filete ${gapY(E.dm, E.rule)} · filete→chamada ${gapY(E.rule, E.cta)} · chamada→legenda ${gapY(E.cta, capE)}`);
ok(["dow", "dia", "dm", "rule", "cta"].every((k) => Math.abs(cx(E[k]) - AX) <= 3), "tela final centralizada no eixo", Object.entries(E).map(([k, b]) => `${k}:${cx(b).toFixed(0)}`).join(" "));
ok(gapY(E.cta, capE) >= 48 && gapY(E.dia, E.dm) >= 16, "tela final com intervalos claros", `chamada→legenda ${gapY(E.cta, capE)}`);

console.log(out.join("\n")); console.log(`\n${fails === 0 ? "AUDITORIA OK" : fails + " FALHA(S)"}`);
await browser.close(); process.exit(fails ? 1 : 0);
