"""Arabic maqamat in 24-tone equal temperament (quarter tones).

Arabic theory notates maqamat with 24 equal steps per octave: a half-flat
(½♭) or half-sharp (½♯) is a quarter tone, 50 cents.  This is a notational
convention: performers tune the "neutral" notes by ear and by region, so the
24-tone values are a reference, like the AEU komas on the Turkish side.

Each maqam names its Turkish counterpart; the Greek dromoi follow through
the Turkish makam they descend from (``Dromos.makam``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import pitch
from .data import DROMOI, MAKAMS

QUARTERS_PER_OCTAVE = 24
QUARTER_CENTS = 50.0

NATURAL_QUARTERS = {"C": 0, "D": 4, "E": 8, "F": 10, "G": 14, "A": 18, "B": 22}

# Arabic note names, by quarter tones above C (pitch class).
NOTE_NAMES = {
    0: "Rast", 2: "Zirkulah", 4: "Dukah", 6: "Kurd", 7: "Sikah", 8: "Busalik",
    10: "Jaharkah", 12: "Hijaz", 14: "Nawa", 16: "Hisar", 18: "Husseini",
    20: "ʿAjam", 21: "ʿAwj", 22: "Mahur",
}

_QUARTER_ACCIDENTALS = {0: "", 1: "½♯", 2: "♯", 3: "1½♯", 4: "♯♯",
                        -1: "½♭", -2: "♭", -3: "1½♭", -4: "♭♭"}
_STEP_NAMES = {1: "quarter tone", 2: "half tone", 3: "¾ tone", 4: "whole tone",
               5: "1¼ tone", 6: "1½ tones"}

# Letter, then accidentals: # / b / ♯ / ♭ (half steps), "½♭" "½b" or "d" for a
# half-flat, "½♯" "½#" or "t" for a half-sharp.
_NOTE_RE = re.compile(r"^([A-Ga-g])((?:½[#b♯♭]|[#b♯♭dt])*)$")


@dataclass(frozen=True)
class ArabicMaqam:
    name: str
    arabic: str                 # name in Arabic script
    tonic: str                  # e.g. "D", "Ed" (E half-flat)
    steps: tuple[int, ...]      # ascending steps in quarter tones (sum = 24)
    ghammaz: int                # dominant degree, 0-based
    makam: str                  # key into MAKAMS (Turkish counterpart)
    description: str
    descending: dict[int, int] = field(default_factory=dict)  # degree -> Δquarters
    aliases: tuple[str, ...] = ()


MAQAMAT: dict[str, ArabicMaqam] = {
    "rast": ArabicMaqam(
        "Rast", "راست", "C", (4, 3, 3, 4, 4, 3, 3), 4, "rast",
        "Jins Rast on C + Rast on G. E and B are half-flat; descending, the "
        "B half-flat becomes B♭ (Nahawand on G).", descending={6: -1}),
    "bayati": ArabicMaqam(
        "Bayati", "بياتي", "D", (3, 3, 4, 4, 2, 4, 4), 3, "ussak",
        "Jins Bayati on D + Nahawand on G. The half-flat 2nd is the colour of "
        "the maqam.", aliases=("bayat",)),
    "husseini": ArabicMaqam(
        "Husseini", "حسيني", "D", (3, 3, 4, 4, 3, 3, 4), 4, "huseyni",
        "Bayati on D + Bayati on A: like Bayati with a half-flat 6th; the 6th "
        "drops to B♭ descending.", descending={5: -1}, aliases=("husayni", "hussaini")),
    "kurd": ArabicMaqam(
        "Kurd", "كرد", "D", (2, 4, 4, 4, 2, 4, 4), 3, "kurdi",
        "Jins Kurd on D + Nahawand on G: no quarter tones."),
    "hijaz": ArabicMaqam(
        "Hijaz", "حجاز", "D", (2, 6, 2, 4, 2, 4, 4), 3, "hicaz",
        "Jins Hijaz on D + Nahawand on G. The E♭ is often played a little "
        "high and the F♯ a little low.", aliases=("hejaz",)),
    "hijaz_kar": ArabicMaqam(
        "Hijaz Kar", "حجاز كار", "C", (2, 6, 2, 4, 2, 6, 2), 4, "hicazkar",
        "Hijaz on C + Hijaz on G: two augmented seconds.", aliases=("hijazkar",)),
    "saba": ArabicMaqam(
        "Saba", "صبا", "D", (3, 3, 2, 6, 2, 4, 4), 2, "saba",
        "Jins Saba on D (a diminished fourth, D–G♭) + Hijaz on F. The scale "
        "does not close on a pure octave.", aliases=("sabah",)),
    "huzam": ArabicMaqam(
        "Huzam", "هزام", "Ed", (3, 4, 2, 6, 2, 4, 3), 2, "huzzam",
        "Jins Sikah on E half-flat + Hijaz on G. The tonic itself is a "
        "quarter-tone note.", aliases=("houzam", "huzzam")),
    "sikah": ArabicMaqam(
        "Sikah", "سيكاه", "Ed", (3, 4, 4, 3, 3, 4, 3), 2, "segah",
        "Jins Sikah on E half-flat + Rast on G. The tonic is the half-flat "
        "third of Rast.", aliases=("sika", "segah")),
    "bayati_shuri": ArabicMaqam(
        "Bayati Shuri", "بياتي شوري", "D", (3, 3, 4, 2, 6, 2, 4), 3, "karcigar",
        "Bayati on D + Hijaz on G. Also called Qarjighar.",
        aliases=("qarjighar", "karjighar", "bayati shuri")),
    "nawa_athar": ArabicMaqam(
        "Nawa Athar", "نوى أثر", "C", (4, 2, 6, 2, 2, 6, 2), 4, "neveser",
        "Nikriz on C + Hijaz on G: two augmented seconds.",
        aliases=("nawa athar", "nawathar")),
    "ajam": ArabicMaqam(
        "Ajam", "عجم", "Bb", (4, 4, 2, 4, 4, 4, 2), 4, "cargah",
        "Jins Ajam on B♭ + Ajam on F: the Arabic major, no quarter tones.",
        aliases=("ʿajam", "ajam ushayran")),
    "nahawand": ArabicMaqam(
        "Nahawand", "نهاوند", "C", (4, 2, 4, 4, 2, 6, 2), 4, "nihavend",
        "Nahawand on C + Hijaz on G ascending, Kurd on G descending (B♭).",
        descending={6: -2}, aliases=("nahawend", "nihavend")),
}


def parse_note(text: str) -> tuple[str, int]:
    """Parse ``"D"``, ``"Bb"``, ``"Ed"``/``"E½♭"`` (half-flat), ``"Ft"`` (half-sharp).

    Returns ``(letter, quarter_tones_from_natural)``.
    """
    match = _NOTE_RE.match(text.strip())
    if not match:
        raise ValueError(
            f"Cannot read note {text!r}; use e.g. D, Eb, F#, Ed (E half-flat) "
            "or Ft (F half-sharp).")
    letter, acc = match.groups()
    quarters = 0
    for token in re.findall(r"½[#b♯♭]|[#b♯♭dt]", acc):
        quarters += {"#": 2, "♯": 2, "b": -2, "♭": -2, "d": -1, "t": 1}.get(token, 0)
        if token.startswith("½"):
            quarters += 1 if token[1] in "#♯" else -1
    return letter.upper(), quarters


def has_quarter_tone(text: str) -> bool:
    try:
        return parse_note(text)[1] % 2 != 0
    except ValueError:
        return False


def spell_quarters(letter: str, pitch_class: int) -> str:
    offset = pitch._wrap(pitch_class - NATURAL_QUARTERS[letter], QUARTERS_PER_OCTAVE)
    if offset not in _QUARTER_ACCIDENTALS:
        raise ValueError(f"Cannot spell pitch class {pitch_class} on {letter}")
    return letter + _QUARTER_ACCIDENTALS[offset]


def note_name(pitch_class: int) -> str:
    return NOTE_NAMES.get(pitch_class % QUARTERS_PER_OCTAVE, "-")


def step_name(quarters: int) -> str:
    return _STEP_NAMES.get(quarters, f"{quarters} quarter tones")


def find_maqam(name: str) -> tuple[str, ArabicMaqam]:
    from .builder import normalize
    key = normalize(name).replace("-", " ")
    for k, m in MAQAMAT.items():
        names = {k, k.replace("_", " "), normalize(m.name), m.arabic,
                 *(normalize(a) for a in m.aliases)}
        if key in names:
            return k, m
    raise KeyError(f"Unknown Arabic maqam {name!r}. Known: {', '.join(MAQAMAT)}")


def positions(maqam: ArabicMaqam, direction: str = "asc") -> list[int]:
    out = [0]
    for step in maqam.steps:
        out.append(out[-1] + step)
    if direction == "desc":
        for degree, delta in maqam.descending.items():
            out[degree] += delta
    return out


@dataclass
class ArabicNote:
    degree: int
    name: str
    arabic_name: str
    quarters: int
    cents: float
    frequency: float
    step: str


def build(name: str, tonic: str | None = None, direction: str = "asc",
          a4: float = 440.0) -> list[ArabicNote]:
    """Notes of an Arabic maqam (degree 1..8), in playing order."""
    _, maqam = find_maqam(name)
    letter, offset = parse_note(tonic or maqam.tonic)
    tonic_pc = NATURAL_QUARTERS[letter] + offset
    tonic_freq = pitch.frequency(pitch.semitones_from_a4(letter, 0) + offset / 2, a4)
    pos = positions(maqam, direction)
    notes = []
    for i, q in enumerate(pos):
        spelled = spell_quarters(pitch.letter_at(letter, i), tonic_pc + q)
        notes.append(ArabicNote(
            degree=i + 1, name=spelled, arabic_name=note_name(tonic_pc + q),
            quarters=q, cents=q * QUARTER_CENTS,
            frequency=tonic_freq * 2 ** (q * QUARTER_CENTS / 1200),
            step=step_name(q - pos[i - 1]) if i else ""))
    if direction == "desc":
        notes.reverse()
    return notes


# -- equivalents across the three traditions --------------------------------

@dataclass
class Equivalents:
    arabic: list[str]           # keys into MAQAMAT
    makams: list[str]           # keys into MAKAMS
    dromoi: list[str]           # keys into DROMOI


def equivalents(kind: str, key: str) -> Equivalents:
    """The Arabic maqam, Turkish makam and Greek dromoi of the same family."""
    if kind == "arabic":
        makam = MAQAMAT[key].makam
    elif kind == "makam":
        makam = key
    elif kind == "dromos":
        makam = DROMOI[key].makam
    else:
        raise ValueError(f"Unknown kind {kind!r}")
    if makam is None:
        return Equivalents([], [], [])
    return Equivalents(
        arabic=[k for k, m in MAQAMAT.items() if m.makam == makam],
        makams=[makam] if makam in MAKAMS else [],
        dromoi=[k for k, d in DROMOI.items() if d.makam == makam],
    )


def arabic_for(kind: str, key: str) -> ArabicMaqam | None:
    found = equivalents(kind, key).arabic
    return MAQAMAT[found[0]] if found else None


def degree_cents(maqam: ArabicMaqam, direction: str = "asc") -> list[float]:
    return [q * QUARTER_CENTS for q in positions(maqam, direction)]
