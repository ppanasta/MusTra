"""Theory corrections suggested by the user.

A user who thinks a dromos, makam or Arabic maqam is wrong (a step size, the
tonic, the dominant, the parent makam…) can correct it.  The correction is a
*suggestion*: it changes only that user's copy of MusTra, and an admin decides
whether it goes into the code for everyone in a release.

Every save is kept as a new version (see ``SongStore.correction_history``), so
users can see what they changed and roll back to any earlier version, or to
the original.  This module knows the editable fields, turns form text into
values, checks that a correction still gives a playable scale, and installs
the active corrections into the theory tables (``MAKAMS``, ``DROMOI``,
``MAQAMAT``), so every page, tip and Identify result uses them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from . import arabic, builder, pitch
from .data import DROMOI, MAKAMS

KINDS = ("dromos", "makam", "arabic")
KIND_LABELS = {"dromos": "Greek dromos", "makam": "Turkish makam",
               "arabic": "Arabic maqam"}

BANNER = ("Your corrections are suggestions: they change only your copy of MusTra, "
          "and every version is kept so you can roll back. Coming in a future "
          "release: send them to the MusTra team by email. An admin will review "
          "each suggestion and, if it is right, include it for everyone in a "
          "release.")

TABLES = {"dromos": DROMOI, "makam": MAKAMS, "arabic": arabic.MAQAMAT}
# The shipped theory, before any user correction.
ORIGINALS = {kind: dict(table) for kind, table in TABLES.items()}


@dataclass(frozen=True)
class Field:
    name: str        # attribute of the Dromos / Makam / ArabicMaqam
    label: str
    hint: str
    type: str        # "note", "numbers", "degree" or "makam"


FIELDS: dict[str, tuple[Field, ...]] = {
    "dromos": (
        Field("tonic", "Tonic", "A fretted note, e.g. D, A, F#", "note"),
        Field("ascending", "Frets going up",
              "7 numbers: semitones above the tonic, starting with 0, e.g. 0 1 3 5 7 8 10",
              "numbers"),
        Field("descending", "Frets coming down",
              "Same format; leave empty if it is the same as going up", "numbers"),
        Field("makam", "Parent makam",
              "The Turkish makam the tips compare with, or none (Greek-born)", "makam"),
    ),
    "makam": (
        Field("tonic", "Tonic", "e.g. A, G, or with komas: B-1", "note"),
        Field("steps", "Steps in komas", "7 numbers that add up to 53, e.g. 8 5 9 9 4 9 9",
              "numbers"),
        Field("guclu", "Güçlü (dominant)", "Degree 1 to 7, e.g. 4", "degree"),
    ),
    "arabic": (
        Field("tonic", "Tonic", "e.g. D, C, or with a quarter tone: Ed (E half-flat)", "note"),
        Field("steps", "Steps in quarter tones",
              "7 numbers that add up to 24, e.g. 3 3 4 4 2 4 4", "numbers"),
        Field("ghammaz", "Ghammaz (dominant)", "Degree 1 to 7, e.g. 4", "degree"),
        Field("makam", "Turkish counterpart", "The equivalent Turkish makam", "makam"),
    ),
}


def _check_kind(kind: str) -> None:
    if kind not in KINDS:
        raise ValueError(f"Kind must be one of {', '.join(KINDS)}, not {kind!r}.")


def find(kind: str, name: str) -> str:
    """Key of a dromos, makam or Arabic maqam, from any of its names."""
    _check_kind(kind)
    if kind == "dromos":
        return builder.find_dromos(name)[0]
    if kind == "makam":
        return builder.find_makam(name)[0]
    return arabic.find_maqam(name)[0]


def original(kind: str, key: str):
    _check_kind(kind)
    if key not in ORIGINALS[kind]:
        raise ValueError(f"Unknown {KIND_LABELS[kind]} {key!r}.")
    return ORIGINALS[kind][key]


def scale_name(kind: str, key: str) -> str:
    return original(kind, key).name


# -- values <-> form text ----------------------------------------------------------

def _value(item, field: Field):
    value = getattr(item, field.name)
    if field.type == "numbers":
        return list(value) if value is not None else None
    return value


def format_value(field: Field, value) -> str:
    """Form text for a value, e.g. [8, 5, 9] -> "8 5 9", guclu 3 -> "4"."""
    if value is None:
        return ""
    if field.type == "numbers":
        return " ".join(str(v) for v in value)
    if field.type == "degree":
        return str(value + 1)
    return str(value)


def display_value(field: Field, value) -> str:
    """Text for summaries and history, e.g. a makam key -> its name."""
    if field.type == "makam":
        return MAKAMS[value].name if value else "none (Greek-born)"
    if field.type == "numbers" and value is None:
        return "same as going up"
    if field.type == "degree":
        return f"degree {value + 1}"
    return format_value(field, value)


def form_values(kind: str, key: str) -> dict[str, str]:
    """Current values (with any correction) as form text."""
    item = TABLES[kind][key]
    return {f.name: format_value(f, _value(item, f)) for f in FIELDS[kind]}


def original_values(kind: str, key: str) -> dict[str, str]:
    item = original(kind, key)
    return {f.name: format_value(f, _value(item, f)) for f in FIELDS[kind]}


def _parse_numbers(field: Field, text: str) -> list[int] | None:
    text = text.strip()
    if not text:
        if field.name == "descending":
            return None
        raise ValueError(f"{field.label}: type 7 numbers.")
    parts = [p for p in re.split(r"[\s,;]+", text) if p]
    try:
        numbers = [int(p) for p in parts]
    except ValueError:
        raise ValueError(f"{field.label}: use whole numbers separated by spaces, "
                         f"e.g. {field.hint.split('e.g. ')[-1]}.") from None
    return numbers


def parse_form(kind: str, key: str, form: dict[str, str]) -> dict:
    """Turn form text into a full set of values for the scale.

    Fields missing from ``form`` keep their current value.  Returns only the
    fields that differ from the original theory (an empty dict means "back to
    the original").
    """
    _check_kind(kind)
    base = original(kind, key)
    current = TABLES[kind][key]
    values = {}
    for field in FIELDS[kind]:
        if field.name not in form:
            values[field.name] = _value(current, field)
            continue
        text = str(form[field.name] or "").strip()
        if field.type == "numbers":
            values[field.name] = _parse_numbers(field, text)
        elif field.type == "degree":
            if not text.isdigit() or not 1 <= int(text) <= 7:
                raise ValueError(f"{field.label}: give a degree from 1 to 7.")
            values[field.name] = int(text) - 1
        elif field.type == "makam":
            if not text or text.lower() in ("none", "-", "—"):
                if kind == "arabic":
                    raise ValueError(f"{field.label}: choose a Turkish makam.")
                values[field.name] = None
            else:
                values[field.name] = builder.find_makam(text)[0]
        else:
            if not text:
                raise ValueError(f"{field.label}: type a note, e.g. D.")
            same = text.lower() == str(_value(base, field)).lower()
            values[field.name] = _value(base, field) if same else text
    return {name: value for name, value in values.items()
            if value != _value(base, _field(kind, name))}


def _field(kind: str, name: str) -> Field:
    for field in FIELDS[kind]:
        if field.name == name:
            return field
    raise ValueError(f"{KIND_LABELS[kind]} has no field {name!r}.")


# -- checking and installing ------------------------------------------------------

def _corrected(kind: str, key: str, changes: dict):
    values = {}
    for name, value in changes.items():
        field = _field(kind, name)
        values[name] = tuple(value) if field.type == "numbers" and value is not None else value
    return replace(original(kind, key), **values)


def _check_values(kind: str, changes: dict) -> None:
    for name, value in changes.items():
        field = _field(kind, name)
        if field.type == "numbers" and value is not None:
            if len(value) != 7:
                raise ValueError(f"{field.label}: give exactly 7 numbers, not {len(value)}.")
            if kind == "dromos":
                if value[0] != 0:
                    raise ValueError(f"{field.label}: the first number is the tonic, 0.")
                if any(b <= a for a, b in zip(value, value[1:])) or value[-1] >= 12:
                    raise ValueError(f"{field.label}: each fret must be higher than the "
                                     "one before, and below the octave (12).")
            else:
                total = 53 if kind == "makam" else 24
                unit = "komas" if kind == "makam" else "quarter tones"
                if any(v <= 0 for v in value):
                    raise ValueError(f"{field.label}: every step must be at least 1.")
                if sum(value) != total:
                    raise ValueError(f"{field.label}: the steps add up to {sum(value)} "
                                     f"{unit}; an octave is {total}.")
        if field.type == "note" and kind != "arabic":
            letter, semis, komas = pitch.parse_note(value)
            if kind == "dromos" and komas:
                raise ValueError("A dromos tonic is a fretted note; koma offsets "
                                 "are not allowed.")
        if field.type == "note" and kind == "arabic":
            arabic.parse_note(value)
        if field.type == "makam" and value is not None and value not in MAKAMS:
            raise ValueError(f"Unknown makam {value!r}.")


def _try_build(kind: str, key: str) -> None:
    if kind == "dromos":
        builder.build_dromos(key, None, "asc")
        builder.build_dromos(key, None, "desc")
        builder.dromos_tips(key, None, "asc")
        builder.dromos_tips(key, None, "desc")
    elif kind == "makam":
        builder.build_makam(key, None, "asc")
        builder.build_makam(key, None, "desc")
    else:
        arabic.build(key, None, "asc")
        arabic.build(key, None, "desc")


def validate(kind: str, key: str, changes: dict) -> dict:
    """Check a correction; returns it, or raises ValueError with the reason."""
    _check_kind(kind)
    original(kind, key)
    _check_values(kind, changes)
    table = TABLES[kind]
    before = table[key]
    table[key] = _corrected(kind, key, changes)
    try:
        _try_build(kind, key)
    except (KeyError, ValueError) as exc:
        raise ValueError("This correction does not give a playable scale: "
                         f"{exc.args[0] if exc.args else exc}") from None
    finally:
        table[key] = before
    return changes


_active: dict[tuple[str, str], dict] = {}


def apply(active: dict[tuple[str, str], dict]) -> list[str]:
    """Install the user's corrections ({(kind, key): changes}) into the tables.

    Everything is first reset to the original theory.  A correction that no
    longer fits (e.g. a newer release removed something it refers to) is
    skipped; the messages say which.
    """
    for kind, table in TABLES.items():
        table.clear()
        table.update(ORIGINALS[kind])
    _active.clear()
    skipped = []
    for (kind, key), changes in active.items():
        if not changes:
            continue
        try:
            validate(kind, key, changes)
        except (KeyError, ValueError) as exc:
            skipped.append(f"{KIND_LABELS.get(kind, kind)} {key}: {exc.args[0]}")
            continue
        TABLES[kind][key] = _corrected(kind, key, changes)
        _active[(kind, key)] = changes
    return skipped


def is_corrected(kind: str, key: str) -> bool:
    return (kind, key) in _active


def describe(kind: str, key: str, changes: dict | None = None) -> list[str]:
    """Lines like "Steps in komas: 8 5 9 9 4 9 9 → 7 6 9 9 4 9 9"."""
    if changes is None:
        changes = _active.get((kind, key), {})
    base = original(kind, key)
    lines = []
    for field in FIELDS[kind]:
        if field.name in changes:
            was = display_value(field, _value(base, field))
            now = display_value(field, changes[field.name])
            lines.append(f"{field.label}: {was} → {now}")
    return lines


def used_by(kind: str, key: str) -> list[tuple[str, str]]:
    """The corrected scales a page uses: the scale itself, and for a dromos or
    Arabic maqam the makam (and Arabic maqam) it is compared with."""
    used = [(kind, key)]
    if kind == "dromos" and TABLES["dromos"][key].makam:
        makam = TABLES["dromos"][key].makam
        used.append(("makam", makam))
        used += [("arabic", k) for k, m in arabic.MAQAMAT.items() if m.makam == makam][:1]
    elif kind == "arabic":
        used.append(("makam", TABLES["arabic"][key].makam))
    return [item for item in used if is_corrected(*item)]


def page_notes(kind: str, key: str) -> list[str]:
    """Lines telling the user which of their corrections a page uses."""
    lines = []
    for other_kind, other_key in used_by(kind, key):
        prefix = "" if (other_kind, other_key) == (kind, key) else (
            f"{KIND_LABELS[other_kind]} {scale_name(other_kind, other_key)} — ")
        lines += [prefix + line for line in describe(other_kind, other_key)]
    return lines
