/* MusTra mobile front end.
 *
 * Runs the MusTra Python package in the browser with Pyodide and renders the
 * JSON returned by mustra.webapi. Everything is built with DOM calls (no
 * innerHTML with data), since song titles come from users.
 */
"use strict";

const APP_DIR = "/home/pyodide/app";
const DATA_DIR = "/data";
const DB_PATH = DATA_DIR + "/songs.sqlite3";
const ANDROID = window.MusTraAndroid || null;

const MODES = {
  dromos: { label: "Dromos", call: "dromos", hint: "Tonic: D, A, F#, Eb …" },
  makam: { label: "Makam", call: "makam", hint: "Tonic: D, A, F#, Eb … or with komas, e.g. B-1" },
  arabic: { label: "Arabic maqam", call: "arabic_maqam",
            hint: "Tonic: C, D, Bb … or with a quarter tone, e.g. Ed = E half-flat" },
  identify: { hint: "e.g. D Eb F# G · A B-1 C D (B-1 = B lowered by one koma) · D Ed F G (Ed = E half-flat)" },
};

const state = { mode: "dromos", catalog: null, choices: null, songsSeen: [], page: null, song: null };
let py = null;     // Pyodide instance
let api = null;    // mustra.webapi module

// -- helpers ------------------------------------------------------------------

const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function toast(text) {
  const t = el("div", { class: "toast", role: "status" }, text);
  document.body.append(t);
  setTimeout(() => t.remove(), 3200);
}

function store(key, value) {
  try {
    if (value === undefined) return localStorage.getItem("mustra." + key);
    localStorage.setItem("mustra." + key, value);
  } catch (e) { return null; }
}

function call(name, ...args) {
  const fn = api[name];
  const out = fn(...args.map((a) => (Array.isArray(a) ? py.toPy(a) : a)));
  return JSON.parse(out);
}

function persist() {
  return new Promise((resolve) => py.FS.syncfs(false, () => resolve()));
}

// -- boot ---------------------------------------------------------------------

async function boot() {
  const status = $("loading");
  try {
    status.textContent = "Preparing MusTra… (the first start downloads about 12 MB, then it works offline)";
    py = await loadPyodide({ indexURL: "pyodide/" });
    await py.loadPackage("sqlite3");
    const zip = await (await fetch("app/mustra.zip")).arrayBuffer();
    py.unpackArchive(zip, "zip", { extractDir: APP_DIR });
    py.runPython(`import sys\nif "${APP_DIR}" not in sys.path: sys.path.insert(0, "${APP_DIR}")`);
    api = py.pyimport("mustra.webapi");

    py.FS.mkdirTree(DATA_DIR);
    try {
      py.FS.mount(py.FS.filesystems.IDBFS, {}, DATA_DIR);
      await new Promise((resolve) => py.FS.syncfs(true, () => resolve()));
    } catch (e) {
      console.warn("Persistent storage unavailable; songs are kept for this session only.", e);
    }
    api.open_store(DB_PATH);
    await persist();

    state.catalog = call("catalog");
    state.choices = call("scale_choices");
    $("start").disabled = false;
    status.textContent = "Ready.";
  } catch (e) {
    console.error(e);
    status.textContent = "MusTra could not start: " + e.message;
    status.classList.add("error");
  }
}

// -- navigation -----------------------------------------------------------------

function showPage(id) {
  for (const page of document.querySelectorAll(".page")) page.hidden = page.id !== id;
  window.scrollTo(0, 0);
}

function end() {
  if (ANDROID && ANDROID.exit) { ANDROID.exit(); return; }
  showPage("welcome");
  toast("MusTra is closed. You can close this tab or switch apps.");
}

function setMode(mode, key) {
  state.mode = mode;
  store("mode", mode);
  for (const tab of document.querySelectorAll(".tabs button")) {
    tab.setAttribute("aria-selected", String(tab.dataset.mode === mode));
  }
  const identify = mode === "identify";
  $("name-wrap").hidden = identify;
  $("tonic-wrap").hidden = identify;
  $("notes-wrap").hidden = !identify;
  $("hint").textContent = MODES[mode].hint;
  if (!identify) {
    $("name-label").textContent = MODES[mode].label;
    const select = $("name");
    select.replaceChildren(...state.catalog[mode].map((item) =>
      el("option", { value: item.key }, item.subtitle ? `${item.name} · ${item.subtitle}` : item.name)));
    select.value = key || store("name." + mode) || state.catalog[mode][0].key;
    if (!select.value) select.value = state.catalog[mode][0].key;
    updateTonicPlaceholder();
  }
  run();
}

function updateTonicPlaceholder() {
  const item = state.catalog[state.mode]?.find((i) => i.key === $("name").value);
  $("tonic").placeholder = item ? `auto (${item.tonic})` : "auto";
}

// -- rendering ------------------------------------------------------------------

function renderError(message) {
  $("result").replaceChildren(el("p", { class: "error" }, message));
}

function run() {
  if (!api) return;
  const a4 = parseFloat($("a4").value || "440");
  if (!(a4 > 0)) { renderError("A4 must be a positive frequency."); return; }
  if (state.mode === "identify") { renderIdentify(); return; }
  const key = $("name").value;
  store("name." + state.mode, key);
  const page = call(MODES[state.mode].call, key, $("tonic").value, a4);
  if (page.error) { renderError(page.error); return; }
  state.page = page;
  state.songsSeen = [];
  const songBox = el("section", { class: "song", id: "song" });
  $("result").replaceChildren(...[
    el("h2", { class: "result-title" }, page.title),
    page.subtitle ? el("p", { class: "result-sub" }, page.subtitle) : null,
    el("p", {}, page.description),
    renderTheory(page),
    renderEquivalents(page.equivalents),
    songBox,
    page.sections.map(renderSection),
    page.tips.length || page.notes.length ? renderTips(page) : null,
    page.legend.map((line) => el("p", { class: "legend" }, line)),
  ].flat(Infinity).filter(Boolean));
  renderSongs({ pick: true });
}

function renderTheory(page) {
  const lines = page.corrections || [];
  return el("div", { class: "theory" },
    lines.length
      ? [el("p", { class: "corrected" }, "✎ Your corrections are in use (only on this device):"),
         lines.map((line) => el("p", { class: "small" }, line))]
      : el("p", { class: "muted small" }, "Found a mistake in this theory? Suggest a correction."),
    el("div", { class: "actions" },
      el("button", { class: "small", type: "button", onclick: () => openCorrect(page.kind, page.key) },
        lines.length ? "Correct again / history" : "Correct the theory")));
}

function renderEquivalents(items) {
  if (!items.length) return el("p", { class: "muted small" }, "No equivalent in the other traditions.");
  return el("div", { class: "chips" },
    el("span", { class: "muted small" }, "Equivalents:"),
    items.map((item) => el("button", {
      class: "chip", type: "button",
      onclick: () => { $("tonic").value = ""; setMode(item.kind, item.key); window.scrollTo(0, 0); },
    }, item.label)));
}

function renderSection(section) {
  return [
    el("h3", {}, section.title),
    el("div", { class: "table-wrap" }, el("table", {},
      el("thead", {}, el("tr", {}, section.columns.map((c) => el("th", { scope: "col" }, c)))),
      el("tbody", {}, section.rows.map((row) => el("tr", {}, row.map((cell) => el("td", {}, cell))))),
    )),
  ];
}

function renderTips(page) {
  return [
    el("h3", {}, "Playing tips"),
    el("ul", { class: "tips" },
      page.tips.map((t) => el("li", {},
        el("span", { class: "mark" }, t.mark),
        el("span", {}, el("span", { class: "note" }, t.note),
          ` (degree ${t.degree}${t.where ? ", " + t.where : ""}) — ${t.text}`))),
      page.notes.map((text) => el("li", {}, el("span", { class: "mark" }, "•"), el("span", {}, text)))),
  ];
}

function renderIdentify() {
  const text = $("notes").value.trim();
  if (!text) {
    $("result").replaceChildren(el("p", { class: "muted" }, "Type the notes above, starting from the tonic."));
    return;
  }
  const data = call("identify", text);
  if (data.error) { renderError(data.error); return; }
  const group = (title, items) => [
    el("h3", {}, title),
    items.length
      ? el("div", { class: "chips" }, items.map((i) => el("button", {
          class: "chip", type: "button", onclick: () => { $("tonic").value = ""; setMode(i.kind, i.key); },
        }, i.name)))
      : el("p", { class: "muted" }, "none"),
  ];
  $("result").replaceChildren(...[
    el("h2", { class: "result-title" }, text),
    el("p", { class: "result-sub" }, "Scales that start with these notes — tap one to open it"),
    group("Greek dromoi", data.dromoi), group("Turkish makams", data.makams),
    group("Arabic maqamat", data.arabic),
  ].flat(Infinity).filter(Boolean));
}

// -- songs --------------------------------------------------------------------------

function renderSongs({ pick = false, songId = null } = {}) {
  const box = $("song");
  if (!box || !state.page) return;
  const data = songId !== null
    ? call("songs", state.page.kind, state.page.key, [], songId)
    : call("songs", state.page.kind, state.page.key, state.songsSeen);
  if (data.error) { box.replaceChildren(el("p", { class: "error" }, data.error)); return; }
  const song = data.pick;
  state.song = song;
  state.songScale = { kind: data.kind, scale: data.scale, name: data.scale_name };
  if (song && pick) state.songsSeen.push(song.id);

  const details = song ? [song.artist, song.year, song.rhythm, song.key && `on ${song.key}`]
    .filter(Boolean).join(" · ") : "";
  const children = [el("h3", {}, `♪ Song suggestion for ${data.scale_name}`)];
  if (!song) {
    children.push(el("p", { class: "muted" }, "No songs yet for this one — be the first to suggest one."));
  } else {
    children.push(el("p", { class: "title" }, song.title));
    if (details) children.push(el("p", { class: "muted small" }, details));
    if (song.via_report) {
      children.push(el("p", { class: "warn" },
        `Listed under ${song.scale_name}; users say it belongs to ${data.scale_name}.`));
    } else if (song.scale !== data.scale || song.kind !== data.kind) {
      children.push(el("p", { class: "muted small" }, `From the related ${song.kind} ${song.scale_name}.`));
    }
    for (const r of song.reports) {
      children.push(el("p", { class: "warn" },
        `⚠ ${r.count === 1 ? "1 user says" : r.count + " users say"} it is really ${r.kind} ${r.scale_name}.`));
    }
    const origin = song.origin === "user" ? "Suggested by a user" : "Source";
    children.push(song.url
      ? el("p", { class: "small" }, `${origin}: `, el("a", { href: song.url, target: "_blank", rel: "noopener" }, song.source))
      : el("p", { class: "muted small" }, `${origin}: ${song.source}`));
  }
  children.push(el("div", { class: "actions" },
    el("button", { class: "small", type: "button", disabled: data.count < 2, onclick: () => renderSongs({ pick: true }) }, "Another"),
    el("button", { class: "small", type: "button", disabled: !song, onclick: openReport }, "Wrong?"),
    el("button", { class: "small", type: "button", onclick: openSuggest }, "Suggest a song"),
    el("button", { class: "small", type: "button", onclick: exportContributions }, "Export")));
  if (data.songs.length) {
    children.push(el("details", {},
      el("summary", {}, `All songs (${data.count} here, ${data.songs.length - data.count} related)`),
      el("ul", { class: "song-list" }, data.songs.map((s) => el("li", {},
        el("button", { type: "button", onclick: () => { renderSongs({ songId: s.id }); $("song").scrollIntoView({ behavior: "smooth" }); } },
          el("div", {}, s.title),
          el("div", { class: "meta" }, [s.artist, s.year, s.from || (s.via_report ? "user correction" : "")]
            .filter(Boolean).join(" · ") + (s.reports.length ? " · ⚠ disputed" : ""))))))));
  }
  box.replaceChildren(...children);
}

function fillScales(kindSelect, scaleSelect, preferKind, preferScale) {
  const refill = () => {
    const list = state.choices[kindSelect.value];
    scaleSelect.replaceChildren(...list.map((i) => el("option", { value: i.key }, i.name)));
    if (kindSelect.value === preferKind) scaleSelect.value = preferScale;
  };
  kindSelect.value = preferKind;
  kindSelect.onchange = refill;
  refill();
}

function openReport() {
  const song = state.song;
  if (!song) return;
  $("report-song").textContent = `“${song.title}” is listed under ${song.scale_name}.`;
  $("report-better-label").textContent = `Suggest a more suitable song for ${state.songScale.name} (optional)`;
  for (const id of ["report-comment", "report-title", "report-artist"]) $(id).value = "";
  $("report-error").textContent = "";
  fillScales($("report-kind"), $("report-scale"), state.songScale.kind, state.songScale.scale);
  $("report-dialog").showModal();
}

function openSuggest() {
  for (const id of ["suggest-title", "suggest-artist", "suggest-year", "suggest-source"]) $(id).value = "";
  $("suggest-error").textContent = "";
  fillScales($("suggest-kind"), $("suggest-scale"), state.songScale.kind, state.songScale.scale);
  $("suggest-dialog").showModal();
}

async function saveReport(event) {
  event.preventDefault();
  const out = call("report", state.song.id, $("report-kind").value, $("report-scale").value,
    $("report-comment").value, $("report-title").value, $("report-artist").value,
    state.songScale.kind, state.songScale.scale);
  if (out.error) { $("report-error").textContent = out.error; return; }
  await persist();
  $("report-dialog").close();
  renderSongs({ songId: state.song.id });
  toast("Thanks — your correction is saved on this device.");
}

async function saveSuggest(event) {
  event.preventDefault();
  const kind = $("suggest-kind").value, scale = $("suggest-scale").value;
  const out = call("add_song", $("suggest-title").value, kind, scale,
    $("suggest-artist").value, $("suggest-year").value, $("suggest-source").value);
  if (out.error) { $("suggest-error").textContent = out.error; return; }
  await persist();
  $("suggest-dialog").close();
  const here = kind === state.songScale.kind && scale === state.songScale.scale;
  renderSongs(here ? { songId: out.id } : { songId: state.song ? state.song.id : null });
  toast("Thanks — your song is saved on this device.");
}

function exportContributions() {
  const path = "/tmp/mustra_contributions.json";
  const out = call("export_contributions", path);
  if (out.error) { toast(out.error); return; }
  const text = py.FS.readFile(path, { encoding: "utf8" });
  const name = "mustra_contributions.json";
  if (ANDROID && ANDROID.share) { ANDROID.share(name, text); return; }
  const url = URL.createObjectURL(new Blob([text], { type: "application/json" }));
  const a = el("a", { href: url, download: name });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
  toast(`Exported ${out.songs} song(s), ${out.reports} report(s) and ${out.corrections} correction(s).`);
}

// -- theory corrections -----------------------------------------------------------

function openCorrect(kind, key) {
  const form = call("correction_form", kind, key);
  if (form.error) { toast(form.error); return; }
  state.correct = form;
  $("correct-title").textContent = `Correct ${form.kind_label} ${form.name}`;
  $("correct-banner").textContent = form.banner;
  $("correct-comment").value = "";
  $("correct-error").textContent = "";
  $("correct-fields").replaceChildren(...form.fields.map((f) => {
    const input = f.type === "makam"
      ? el("select", { id: "correct-" + f.name },
          kind === "dromos" ? el("option", { value: "" }, "none (Greek-born)") : null,
          form.makams.map((m) => el("option", { value: m.key }, m.name)))
      : el("input", { id: "correct-" + f.name, spellcheck: "false", autocapitalize: "off" });
    input.value = f.value;
    const was = f.type === "makam"
      ? (form.makams.find((m) => m.key === f.original) || { name: "none (Greek-born)" }).name
      : (f.original || "same as going up");
    return el("label", { class: "field" }, el("span", {}, f.label), input,
      el("small", {}, `${f.hint}. Original: ${was}`));
  }));
  const history = $("correct-history");
  const items = form.history.map((v) => el("li", {},
    el("p", { class: "head" }, `Version ${v.number} · ${v.created_at} · ${v.action}`,
      v.active ? el("span", { class: "active" }, "  in use") : null),
    v.summary.map((line) => el("p", {}, line)),
    v.comment ? el("p", { class: "muted" }, `“${v.comment}”`) : null,
    v.active ? null : el("button", { class: "small", type: "button",
      onclick: () => rollback(v.id, `version ${v.number}`) }, "Use this version")));
  items.push(el("li", {},
    el("p", { class: "head" }, "Version 0 · original theory",
      form.corrected ? null : el("span", { class: "active" }, "  in use")),
    form.corrected ? el("button", { class: "small", type: "button",
      onclick: () => rollback(0, "the original theory") }, "Back to the original") : null));
  history.replaceChildren(...items);
  $("correct-dialog").showModal();
}

async function afterCorrection(message) {
  await persist();
  state.catalog = call("catalog");
  const { kind, key } = state.correct;
  $("correct-dialog").close();
  if (state.mode === kind) setMode(kind, key); else run();
  toast(message);
}

async function saveCorrect(event) {
  event.preventDefault();
  const { kind, key, fields } = state.correct;
  const form = {};
  for (const f of fields) form[f.name] = $("correct-" + f.name).value;
  const out = call("save_correction", kind, key, JSON.stringify(form), $("correct-comment").value);
  if (out.error) { $("correct-error").textContent = out.error; return; }
  await afterCorrection("Saved as a new version on this device. Roll back any time.");
}

async function rollback(versionId, label) {
  const { kind, key } = state.correct;
  const out = call("rollback_correction", kind, key, versionId);
  if (out.error) { $("correct-error").textContent = out.error; return; }
  await afterCorrection(`Back to ${label}.`);
}

// -- wiring ---------------------------------------------------------------------------

// Android back button: close a dialog, else go back to the welcome page.
window.mustraBack = () => {
  const open = document.querySelector("dialog[open]");
  if (open) { open.close(); return true; }
  if (!$("lookup").hidden) { showPage("welcome"); return true; }
  return false;
};

$("start").addEventListener("click", () => {
  showPage("lookup");
  setMode(store("mode") || "dromos");
});
$("end").addEventListener("click", end);
$("end2").addEventListener("click", end);
$("back").addEventListener("click", () => showPage("welcome"));
for (const tab of document.querySelectorAll(".tabs button")) {
  tab.addEventListener("click", () => setMode(tab.dataset.mode));
}
$("controls").addEventListener("submit", (e) => { e.preventDefault(); run(); });
$("name").addEventListener("change", () => { $("tonic").value = ""; updateTonicPlaceholder(); run(); });
$("report-save").addEventListener("click", saveReport);
$("suggest-save").addEventListener("click", saveSuggest);
$("correct-save").addEventListener("click", saveCorrect);

if ("serviceWorker" in navigator && !ANDROID && location.protocol === "https:") {
  navigator.serviceWorker.register("sw.js").catch((e) => console.warn("No offline cache:", e));
}

boot();
