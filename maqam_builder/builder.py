"""Build makam / dromos scales and generate intonation tips."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from . import pitch
from .data import DROMOI, MAKAMS, Dromos, Makam

TECHNIQUE = {
    "up": "↑ bend up: on bouzouki/baglama push the string sideways while "
          "holding the fret; on violin, oud or voice place the note higher.",
    "down": "↓ hold it low: a fretted note cannot go lower — touch it lightly "
            "in passing, or fret one semitone below and bend up to pitch; on "
            "violin, oud or voice place the note lower.",
}

# Leading tones: a degree within this many komas of a stable degree leans to it.
ATTRACTION_KOMAS = 5


@dataclass
class Note:
    degree: int                 # 1-based; 8 = octave
    name: str                   # spelled note (koma or tempered accidentals)
    greek: str
    cents: float                # above the tonic
    frequency: float
    komas: int | None = None    # makam only: komas above the tonic
    perde: str = ""             # makam only
    step: str = ""              # makam only: interval from previous degree


@dataclass
class Scale:
    title: str
    tonic: str
    direction: str
    notes: list[Note]


@dataclass
class Tip:
    degree: int
    dromos_note: str
    makam_note: str | None
    deviation: float | None     # cents: makam pitch minus fretted pitch
    text: str


def normalize(name: str) -> str:
    name = name.strip().lower().replace("ı", "i")
    name = unicodedata.normalize("NFKD", name)
    return "".join(c for c in name if not unicodedata.combining(c))


def _lookup(table: dict, name: str, kind: str):
    key = normalize(name)
    for k, item in table.items():
        names = {k, normalize(item.name), *(normalize(a) for a in item.aliases)}
        if key in names:
            return k, item
    raise KeyError(f"Unknown {kind} {name!r}. Known: {', '.join(table)}")


def find_makam(name: str) -> tuple[str, Makam]:
    return _lookup(MAKAMS, name, "makam")


def find_dromos(name: str) -> tuple[str, Dromos]:
    return _lookup(DROMOI, name, "dromos")


# --------------------------------------------------------------------------
# Makam (53-koma) scales
# --------------------------------------------------------------------------

def makam_positions(makam: Makam, direction: str = "asc") -> list[int]:
    """Koma positions above the tonic for degrees 1..8."""
    positions = [0]
    for step in makam.steps:
        positions.append(positions[-1] + step)
    if direction == "desc":
        for degree, delta in makam.descending.items():
            positions[degree] += delta
    return positions


def build_makam(name: str, tonic: str | None = None, direction: str = "asc",
                a4: float = 440.0) -> Scale:
    _, makam = find_makam(name)
    letter, semis, komas = pitch.parse_note(tonic or makam.tonic)
    tonic_pc = pitch.NATURAL_KOMAS[letter] + semis * pitch.SHARP_KOMAS + komas
    # Equal-tempered reference for the tonic, used only for frequencies.
    tonic_offset_cents = (semis * pitch.SHARP_KOMAS + komas) * pitch.KOMA_CENTS
    tonic_freq = pitch.frequency(
        pitch.semitones_from_a4(letter, 0) + tonic_offset_cents / 100, a4)

    positions = makam_positions(makam, direction)
    notes = []
    for i, pos in enumerate(positions):
        note_letter = pitch.letter_at(letter, i)
        pc = tonic_pc + pos
        name_ = pitch.spell_komas(note_letter, pc)
        cents = pos * pitch.KOMA_CENTS
        step = pitch.interval_name(pos - positions[i - 1]) if i else ""
        notes.append(Note(
            degree=i + 1, name=name_, greek=pitch.greek_name(name_),
            cents=cents, frequency=tonic_freq * 2 ** (cents / 1200),
            komas=pos, perde=pitch.perde_name(pc), step=step,
        ))
    if direction == "desc":
        notes.reverse()
    return Scale(f"Makam {makam.name}", tonic or makam.tonic, direction, notes)


# --------------------------------------------------------------------------
# Dromos (12-TET) scales
# --------------------------------------------------------------------------

def dromos_positions(dromos: Dromos, direction: str = "asc") -> list[int]:
    base = dromos.descending if direction == "desc" and dromos.descending else dromos.ascending
    return [*base, 12]


def build_dromos(name: str, tonic: str | None = None, direction: str = "asc",
                 a4: float = 440.0) -> Scale:
    _, dromos = find_dromos(name)
    letter, semis, komas = pitch.parse_note(tonic or dromos.tonic)
    if komas:
        raise ValueError("A dromos tonic is a fretted note; koma offsets are "
                         "not allowed.")
    tonic_pc = pitch.NATURAL_SEMITONES[letter] + semis
    tonic_freq = pitch.frequency(pitch.semitones_from_a4(letter, semis), a4)

    notes = []
    for i, pos in enumerate(dromos_positions(dromos, direction)):
        name_ = pitch.spell_semitones(pitch.letter_at(letter, i), tonic_pc + pos)
        notes.append(Note(
            degree=i + 1, name=name_, greek=pitch.greek_name(name_),
            cents=pos * 100.0, frequency=tonic_freq * 2 ** (pos / 12),
        ))
    if direction == "desc":
        notes.reverse()
    return Scale(f"Dromos {dromos.name} ({dromos.greek})", tonic or dromos.tonic,
                 direction, notes)


# --------------------------------------------------------------------------
# Tips: how to bend the fretted dromos toward the makam
# --------------------------------------------------------------------------

def _deviation_text(dev: float) -> str | None:
    size = abs(dev)
    if size < 10:
        return None
    up = dev > 0
    word = "higher" if up else "lower"
    if size < 20:
        amount = f"slightly {word}"
    elif size < 40:
        amount = f"noticeably {word}"
    elif size < 70:
        amount = f"about a quarter-tone {word}"
    else:
        amount = f"much {word} — close to the next fret, a true microtone"
    how = "bend up (↑)" if up else "hold it low (↓)"
    return f"play it {amount} ({dev:+.0f}¢) — {how}."


def _attraction_text(positions: list[int], stable: set[int], degree: int) -> str | None:
    """Describe the pull of a degree toward a neighbouring stable degree."""
    if degree in stable:
        return None
    pos = positions[degree]
    for target in sorted(stable):
        gap = positions[target] - pos
        if 0 < gap <= ATTRACTION_KOMAS:
            return f"leans up into degree {target + 1}"
        if 0 < -gap <= ATTRACTION_KOMAS:
            return f"falls back onto degree {target + 1}"
    return None


def dromos_tips(name: str, tonic: str | None = None, direction: str = "asc") -> list[Tip]:
    """Per-degree intonation tips comparing a dromos with its parent makam."""
    _, dromos = find_dromos(name)
    fretted = build_dromos(name, tonic, direction)
    notes = sorted(fretted.notes, key=lambda n: n.degree)
    if dromos.makam is None:
        return []

    makam = MAKAMS[dromos.makam]
    other = "desc" if direction == "asc" else "asc"
    makam_tonic = tonic or dromos.tonic
    forms = {
        d: (makam_positions(makam, d),
            sorted(build_makam(dromos.makam, makam_tonic, d).notes,
                   key=lambda n: n.degree))
        for d in (direction, other)
    }
    stable = {0, makam.guclu, 7}
    tips = []
    for i, note in enumerate(notes[:-1]):
        if i == 0:
            continue
        # Use the makam form (ascending/descending) closest to the fret.
        devs = {d: forms[d][0][i] * pitch.KOMA_CENTS - note.cents for d in forms}
        best = min(devs, key=lambda d: (abs(devs[d]), d != direction))
        positions, makam_notes = forms[best]
        dev = devs[best]
        parts = []
        if abs(dev) >= 100:
            parts.append(
                f"the makam uses a different note here "
                f"({positions[i] * pitch.KOMA_CENTS:.0f}¢ above the tonic vs "
                f"{note.cents:.0f}¢ on the frets) — the dromos has simplified it.")
        else:
            text = _deviation_text(dev)
            if text:
                parts.append(text)
        if best != direction:
            parts.append(f"(Matches the makam's {best}ending form.)")
        alt = forms[other if best == direction else direction]
        if alt[0][i] != positions[i]:
            alt_dir = other if best == direction else direction
            parts.append(
                f"The makam's {alt_dir}ending form uses {alt[1][i].name} here "
                f"({devs[alt_dir]:+.0f}¢ from the fret).")
        pull = _attraction_text(positions, stable, i)
        if pull:
            parts.append(f"In the makam this note {pull}.")
        if parts:
            tips.append(Tip(i + 1, note.name, makam_notes[i].name, dev, " ".join(parts)))

    # If (almost) every degree leans the same way, the tonic itself is the
    # microtone: say so, since that is easier to apply than five bends.
    devs = [t.deviation for t in tips if t.deviation is not None and abs(t.deviation) < 100]
    if len(devs) >= 4 and (all(d > 0 for d in devs) or all(d < 0 for d in devs)):
        shift = sorted(devs)[len(devs) // 2]
        word = "low" if shift > 0 else "high"
        tips.append(Tip(1, notes[0].name, None, -shift,
                        f"Equivalently: keep the frets and sing/bow the tonic "
                        f"about {abs(shift):.0f}¢ {word} — in the makam the "
                        f"tonic itself is the microtone."))
    return tips


# --------------------------------------------------------------------------
# Identify: notes -> dromos / makam names
# --------------------------------------------------------------------------

def identify(notes: list[str]) -> dict[str, list[str]]:
    """Find dromoi and makams whose scale starts with ``notes``.

    The first note is taken as the tonic and the rest as the following
    consecutive degrees (ascending or descending forms).  Notes with a koma
    offset (e.g. ``B-1``) are matched exactly against makams; plain notes
    are matched against the nearest semitone of each makam degree.
    """
    if len(notes) < 2:
        raise ValueError("Give at least two notes, starting from the tonic.")
    parsed = [pitch.parse_note(n) for n in notes]
    if len(parsed) > 8:
        raise ValueError("Give at most eight notes (tonic to octave).")
    exact = any(k for _, _, k in parsed)

    def rising(values: list[int], modulus: int) -> list[int]:
        out = [0]
        for prev, cur in zip(values, values[1:]):
            out.append(out[-1] + (cur - prev) % modulus)
        return out

    semis = rising([pitch.NATURAL_SEMITONES[l] + s for l, s, _ in parsed], 12)
    komas = rising([pitch.NATURAL_KOMAS[l] + s * pitch.SHARP_KOMAS + k
                    for l, s, k in parsed], pitch.KOMAS_PER_OCTAVE)
    n = len(parsed)

    dromoi = []
    if not exact:
        for d in DROMOI.values():
            forms = {tuple(dromos_positions(d, "asc")), tuple(dromos_positions(d, "desc"))}
            if any(list(f[:n]) == semis for f in forms):
                dromoi.append(d.name)

    makams = []
    for m in MAKAMS.values():
        for direction in ("asc", "desc"):
            pos = makam_positions(m, direction)[:n]
            if exact:
                hit = pos == komas
            else:
                hit = [round(p * pitch.KOMA_CENTS / 100) for p in pos] == semis
            if hit:
                makams.append(m.name)
                break
    return {"dromoi": dromoi, "makams": makams}
