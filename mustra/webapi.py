"""JSON API for the mobile app (iPhone web app and Android).

The mobile front end runs this package in the browser with Pyodide and calls
these functions; each returns a JSON string, so JavaScript only needs
``JSON.parse``.  Errors a user can cause (unknown name, bad note) come back as
``{"error": "..."}`` instead of an exception.
"""

from __future__ import annotations

import functools
import json
import random

from . import arabic, builder, corrections, pitch
from .data import DROMOI, MAKAMS
from .songs import Song, SongStore, scale_name

_store: SongStore | None = None

LEGEND_KOMA = ("Koma accidentals: B♭¹ = B lowered by one koma (≈ 23¢), F♯⁴ = F raised by "
               "four komas. 1 koma = 1/53 octave.")
LEGEND_QUARTER = ("Quarter-tone accidentals: E½♭ = E half-flat, F½♯ = F half-sharp (50¢). "
                  "Arabic notation rounds to quarter tones; real intonation of the "
                  "half-flat notes varies by region.")


def _json(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except (KeyError, ValueError) as exc:
            result = {"error": str(exc.args[0] if exc.args else exc)}
        return json.dumps(result, ensure_ascii=False)
    return wrapper


def _tonic(value):
    value = (value or "").strip()
    return value or None


def _equivalents(kind: str, key: str) -> list[dict]:
    eq = arabic.equivalents(kind, key)
    out = []
    if kind != "dromos":
        out += [{"kind": "dromos", "key": k, "label": f"Greek {DROMOI[k].name}"}
                for k in eq.dromoi]
    if kind != "makam":
        out += [{"kind": "makam", "key": k, "label": f"Turkish {MAKAMS[k].name}"}
                for k in eq.makams]
    if kind != "arabic":
        out += [{"kind": "arabic", "key": k,
                 "label": f"Arabic {arabic.MAQAMAT[k].name} ({arabic.MAQAMAT[k].arabic})"}
                for k in eq.arabic]
    return out


def _table(columns: list[str], rows: list[list]) -> dict:
    return {"columns": columns, "rows": [[str(c) for c in row] for row in rows]}


# -- catalog -------------------------------------------------------------------

@_json
def catalog() -> dict:
    return {
        "dromos": [{"key": k, "name": d.name, "subtitle": d.greek, "tonic": d.tonic}
                   for k, d in DROMOI.items()],
        "makam": [{"key": k, "name": m.name, "subtitle": "", "tonic": m.tonic}
                  for k, m in MAKAMS.items()],
        "arabic": [{"key": k, "name": a.name, "subtitle": a.arabic, "tonic": a.tonic}
                   for k, a in arabic.MAQAMAT.items()],
    }


# -- scale pages -----------------------------------------------------------------

@_json
def dromos(key: str, tonic: str | None = None, a4: float = 440.0) -> dict:
    key, d = builder.find_dromos(key)
    tonic = _tonic(tonic) or d.tonic
    parent = MAKAMS[d.makam].name if d.makam else None
    arab = arabic.arabic_for("dromos", key)
    directions = ["asc", "desc"] if d.descending else ["asc"]

    sections = []
    for direction in directions:
        notes = sorted(builder.build_dromos(key, tonic, direction, a4).notes,
                       key=lambda n: n.degree)
        label = "Ascending" if direction == "asc" else "Descending"
        if parent:
            mk = sorted(builder.build_makam(d.makam, tonic, direction, a4).notes,
                        key=lambda n: n.degree)
            ar = sorted(arabic.build(arab.name, tonic, direction, a4),
                        key=lambda n: n.degree) if arab else []
            cols = ["Deg", "Note", "Greek", parent, "Δ¢"]
            if arab:
                cols += [arab.name, "Δ¢"]
            rows = []
            for i, (n, m) in enumerate(zip(notes, mk)):
                row = [n.degree, n.name, n.greek, m.name, f"{m.cents - n.cents:+.0f}"]
                if arab:
                    row += [ar[i].name, f"{ar[i].cents - n.cents:+.0f}"]
                rows.append(row)
            title = f"{label} on {tonic}, beside makam {parent}" + (
                f" and Arabic {arab.name}" if arab else "")
        else:
            cols = ["Deg", "Note", "Greek", "Cents", "Hz"]
            rows = [[n.degree, n.name, n.greek, f"{n.cents:.0f}", f"{n.frequency:.1f}"]
                    for n in notes]
            title = f"{label} on {tonic}"
        sections.append({"title": title, **_table(cols, rows)})

    tips = []
    for direction in directions:
        for tip in builder.dromos_tips(key, tonic, direction):
            mark = "↑" if "bend up" in tip.text else "↓" if "hold it low" in tip.text else "•"
            where = "" if len(directions) == 1 else (
                "going up" if direction == "asc" else "coming down")
            tips.append({"mark": mark, "note": tip.dromos_note, "degree": tip.degree,
                         "where": where, "text": tip.text})
    return {
        "kind": "dromos", "key": key, "title": d.name, "subtitle": d.greek,
        "corrections": corrections.page_notes("dromos", key),
        "description": d.description + (f" From makam {parent}." if parent
                                         else " Greek-born, no makam parent."),
        "equivalents": _equivalents("dromos", key),
        "sections": sections, "tips": tips, "notes": list(d.tips),
        "legend": (list(builder.TECHNIQUE.values()) + [LEGEND_KOMA]) if parent else [],
    }


@_json
def makam(key: str, tonic: str | None = None, a4: float = 440.0) -> dict:
    key, m = builder.find_makam(key)
    tonic = _tonic(tonic) or m.tonic
    sections = []
    for direction in ("asc", "desc"):
        notes = builder.build_makam(key, tonic, direction, a4).notes
        label = "Ascending" if direction == "asc" else "Descending"
        start = notes[0 if direction == "asc" else -1].name
        sections.append({"title": f"{label} on {start}", **_table(
            ["Deg", "Note", "Perde", "Step", "Komas", "Cents", "Hz"],
            [[n.degree, n.name, n.perde, n.step.split(" ")[0], n.komas,
              f"{n.cents:.0f}", f"{n.frequency:.1f}"] for n in notes])})
    return {
        "kind": "makam", "key": key, "title": f"Makam {m.name}", "subtitle": "",
        "corrections": corrections.page_notes("makam", key),
        "description": f"{m.description} Seyir: {m.seyir}; güçlü (dominant): "
                       f"degree {m.guclu + 1}.",
        "equivalents": _equivalents("makam", key),
        "sections": sections, "tips": [], "notes": [],
        "legend": ["Steps: K koma, B bakiye, S küçük mücennep, M büyük mücennep, "
                   "T tanini, A artık ikili.", LEGEND_KOMA],
    }


@_json
def arabic_maqam(key: str, tonic: str | None = None, a4: float = 440.0) -> dict:
    key, a = arabic.find_maqam(key)
    tonic = _tonic(tonic) or a.tonic
    sections = []
    directions = ["asc", "desc"] if a.descending else ["asc"]
    for direction in directions:
        notes = arabic.build(key, tonic, direction, a4)
        label = "Ascending" if direction == "asc" else "Descending"
        start = notes[0 if direction == "asc" else -1].name
        sections.append({"title": f"{label} on {start}", **_table(
            ["Deg", "Note", "Name", "Step", "Cents", "Hz"],
            [[n.degree, n.name, n.arabic_name, n.step, f"{n.cents:.0f}",
              f"{n.frequency:.1f}"] for n in notes])})

    turkish = MAKAMS[a.makam]
    eq = arabic.equivalents("arabic", key)
    dromoi = [DROMOI[k] for k in eq.dromoi]
    ar = sorted(arabic.build(key, tonic), key=lambda n: n.degree)
    mk = builder.makam_positions(turkish)
    cols = ["Deg", "Arabic", turkish.name, "Δ¢"]
    for d in dromoi:
        cols += [d.name, "Δ¢"]
    rows = []
    for i, n in enumerate(ar):
        t = mk[i] * pitch.KOMA_CENTS
        row = [n.degree, f"{n.cents:.0f}", f"{t:.0f}", f"{t - n.cents:+.0f}"]
        for d in dromoi:
            fret = builder.dromos_positions(d)[i] * 100
            row += [f"{fret:.0f}", f"{fret - n.cents:+.0f}"]
        rows.append(row)
    sections.append({"title": "Compared with the Turkish makam and Greek dromos "
                              "(cents above the tonic)", **_table(cols, rows)})
    return {
        "kind": "arabic", "key": key, "title": f"Maqam {a.name}", "subtitle": a.arabic,
        "corrections": corrections.page_notes("arabic", key),
        "description": f"{a.description} Ghammaz (dominant): degree {a.ghammaz + 1}.",
        "equivalents": _equivalents("arabic", key),
        "sections": sections, "tips": [], "notes": [], "legend": [LEGEND_QUARTER],
    }


@_json
def identify(text: str) -> dict:
    notes = text.replace(",", " ").split()
    result = builder.identify(notes)
    by_name = {
        "dromoi": ("dromos", {d.name: k for k, d in DROMOI.items()}),
        "makams": ("makam", {m.name: k for k, m in MAKAMS.items()}),
        "arabic": ("arabic", {m.name: k for k, m in arabic.MAQAMAT.items()}),
    }
    out = {}
    for group, names in result.items():
        kind, keys = by_name[group]
        out[group] = [{"kind": kind, "key": keys[n], "name": n} for n in names]
    return out


# -- songs -------------------------------------------------------------------------

def open_store(path: str) -> None:
    """Open (or create) the song database; called once by the front end."""
    global _store
    if _store is not None:
        _store.close()
    _store = SongStore(path)
    _store.apply_corrections()


def _require_store() -> SongStore:
    if _store is None:
        raise ValueError("The song database is not open.")
    return _store


def _song(song: Song, origin: str = "") -> dict:
    return {
        "id": song.id, "title": song.title, "artist": song.artist, "year": song.year,
        "rhythm": song.rhythm, "key": song.song_key, "kind": song.kind,
        "scale": song.scale, "scale_name": scale_name(song.kind, song.scale),
        "source": song.source, "url": song.source_url, "origin": song.origin,
        "via_report": song.via_report, "from": origin,
        "reports": [{"kind": k, "scale": s, "scale_name": scale_name(k, s), "count": n}
                    for (k, s), n in song.reports.items()],
    }


def _song_scale(kind: str, key: str) -> tuple[str, str]:
    """Songs live under dromoi and makams; an Arabic maqam uses its makam."""
    if kind == "arabic":
        return "makam", arabic.find_maqam(key)[1].makam
    return kind, key


@_json
def songs(kind: str, key: str, exclude: list[int] | None = None,
          song_id: int | None = None) -> dict:
    store = _require_store()
    kind, key = _song_scale(kind, key)
    if song_id is not None:
        pick = store.get(int(song_id))
    else:
        pick = store.suggest(kind, key, set(exclude or []))
    here = store.songs_for(kind, key)
    related = store.related(kind, key)
    return {
        "kind": kind, "scale": key, "scale_name": scale_name(kind, key),
        "pick": _song(pick) if pick else None,
        "songs": [_song(s) for s in here]
                 + [_song(s, scale_name(s.kind, s.scale)) for s in related],
        "count": len(here),
    }


@_json
def report(song_id: int, kind: str, key: str, comment: str = "",
           better_title: str = "", better_artist: str = "",
           for_kind: str = "", for_key: str = "") -> dict:
    store = _require_store()
    store.report(int(song_id), kind, key, comment)
    if better_title.strip():
        fk, fs = _song_scale(for_kind, for_key)
        store.add_song(better_title, fk, fs, artist=better_artist)
    return {"ok": True}


@_json
def add_song(title: str, kind: str, key: str, artist: str = "", year: str = "",
             source: str = "") -> dict:
    store = _require_store()
    year = str(year).strip()
    if year and not year.isdigit():
        raise ValueError("Year must be a number, e.g. 1936.")
    song_id = store.add_song(title, kind, key, artist=artist,
                             year=int(year) if year else None, source=source)
    return {"ok": True, "id": song_id}


@_json
def export_contributions(path: str) -> dict:
    data = _require_store().export_json(path)
    return {"songs": len(data["songs"]), "reports": len(data["reports"]),
            "corrections": len(data["corrections"])}


# -- theory corrections ---------------------------------------------------------

def _version(v) -> dict:
    return {"id": v.id, "number": v.number, "action": v.action, "comment": v.comment,
            "created_at": v.created_at, "active": v.active, "summary": v.summary}


@_json
def correction_form(kind: str, key: str) -> dict:
    """Everything the "Correct the theory" dialog needs."""
    store = _require_store()
    corrections.original(kind, key)
    current = corrections.form_values(kind, key)
    original = corrections.original_values(kind, key)
    history = store.correction_history(kind, key)
    return {
        "kind": kind, "key": key, "name": corrections.scale_name(kind, key),
        "kind_label": corrections.KIND_LABELS[kind], "banner": corrections.BANNER,
        "fields": [{"name": f.name, "label": f.label, "hint": f.hint, "type": f.type,
                    "value": current[f.name], "original": original[f.name]}
                   for f in corrections.FIELDS[kind]],
        "makams": [{"key": k, "name": m.name} for k, m in MAKAMS.items()],
        "corrected": corrections.is_corrected(kind, key),
        "history": [_version(v) for v in reversed(history)],
    }


@_json
def save_correction(kind: str, key: str, form: str, comment: str = "") -> dict:
    """``form`` is a JSON object of field name -> text, as typed by the user."""
    store = _require_store()
    changes = corrections.parse_form(kind, key, json.loads(form))
    store.suggest_correction(kind, key, changes, comment)
    return {"ok": True, "summary": corrections.describe(kind, key)}


@_json
def rollback_correction(kind: str, key: str, version_id: int) -> dict:
    """Go back to an earlier version; 0 = the original theory."""
    _require_store().rollback_correction(kind, key, int(version_id))
    return {"ok": True, "summary": corrections.describe(kind, key)}


@_json
def scale_choices() -> dict:
    """Names for the report/suggest pickers (songs belong to dromoi and makams)."""
    return {"dromos": [{"key": k, "name": d.name} for k, d in DROMOI.items()],
            "makam": [{"key": k, "name": m.name} for k, m in MAKAMS.items()]}


def _seed_random(seed: int) -> None:
    """Tests only: deterministic suggestions."""
    random.seed(seed)
    if _store is not None:
        _store.rng = random.Random(seed)
