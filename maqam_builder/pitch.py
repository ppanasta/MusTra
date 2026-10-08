"""Pitch arithmetic for the two tuning systems used by the builder.

* Turkish makam  -> 53 equal divisions of the octave ("Holdrian komas"),
  the theoretical basis of the Arel-Ezgi-Uzdilek (AEU) system.
* Greek dromos   -> 12-tone equal temperament, as played on the fretted
  bouzouki / baglama / guitar.
"""

from __future__ import annotations

import re

KOMAS_PER_OCTAVE = 53
KOMA_CENTS = 1200 / KOMAS_PER_OCTAVE  # ~22.64 cents

LETTERS = "CDEFGAB"

# Natural notes measured from C, in komas (Pythagorean spelling inside 53-TET)
# and in equal-tempered semitones.
NATURAL_KOMAS = {"C": 0, "D": 9, "E": 18, "F": 22, "G": 31, "A": 40, "B": 49}
NATURAL_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# A Western sharp/flat (apotome) is 5 komas in the 53-koma system.
SHARP_KOMAS = 5

GREEK_SOLFEGE = {"C": "Ντο", "D": "Ρε", "E": "Μι", "F": "Φα",
                 "G": "Σολ", "A": "Λα", "B": "Σι"}

# Turkish perde (fret/pitch) names of the middle octave, keyed by komas above
# C (pitch class).  In Turkish notation Rast is written on G.
PERDE_NAMES = {
    31: "Rast", 35: "Nim Zirgüle", 36: "Zirgüle", 39: "Dik Zirgüle",
    40: "Dügah", 44: "Kürdi", 45: "Dik Kürdi", 48: "Segah", 49: "Bûselik",
    52: "Dik Bûselik", 0: "Çargah", 4: "Nim Hicaz", 5: "Hicaz",
    8: "Dik Hicaz", 9: "Neva", 13: "Nim Hisar", 14: "Hisar",
    17: "Dik Hisar", 18: "Hüseyni", 22: "Acem", 23: "Dik Acem",
    26: "Eviç", 27: "Mahur", 30: "Dik Mahur",
}

# AEU interval names, by size in komas.
INTERVAL_NAMES = {
    1: "K (koma)",
    4: "B (bakiye)",
    5: "S (küçük mücennep)",
    8: "M (büyük mücennep)",
    9: "T (tanini)",
    12: "A (artık ikili)",
    13: "A (artık ikili)",
}

_SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_NOTE_RE = re.compile(r"^([A-Ga-g])([#b♯♭]*)([+-]\d+)?$")
_ET_ACCIDENTALS = {0: "", 1: "♯", 2: "𝄪", -1: "♭", -2: "𝄫"}


def _wrap(value: int, modulus: int) -> int:
    """Wrap ``value`` into the range (-modulus/2, modulus/2]."""
    value %= modulus
    return value - modulus if value > modulus // 2 else value


def parse_note(text: str) -> tuple[str, int, int]:
    """Parse ``"D"``, ``"Eb"``, ``"F#"`` or ``"B-1"`` (koma offset).

    Returns ``(letter, semitone_accidentals, extra_komas)``.
    """
    match = _NOTE_RE.match(text.strip())
    if not match:
        raise ValueError(
            f"Cannot read note {text!r}; use e.g. D, Eb, F#, or B-1 "
            "(B lowered by one koma)."
        )
    letter, accidentals, komas = match.groups()
    semis = accidentals.count("#") + accidentals.count("♯")
    semis -= accidentals.count("b") + accidentals.count("♭")
    return letter.upper(), semis, int(komas or 0)


def letter_at(tonic_letter: str, degree: int) -> str:
    """Letter name of scale degree ``degree`` (0 = tonic)."""
    return LETTERS[(LETTERS.index(tonic_letter) + degree) % 7]


def koma_accidental(offset: int) -> str:
    """Koma accidental, e.g. -1 -> '♭¹' (one koma flat), +4 -> '♯⁴'."""
    if offset == 0:
        return ""
    sign = "♯" if offset > 0 else "♭"
    return sign + str(abs(offset)).translate(_SUPERSCRIPT)


def spell_komas(letter: str, pitch_class: int) -> str:
    """Spell a 53-TET pitch class (komas above C) on a given letter."""
    offset = _wrap(pitch_class - NATURAL_KOMAS[letter], KOMAS_PER_OCTAVE)
    return letter + koma_accidental(offset)


def spell_semitones(letter: str, pitch_class: int) -> str:
    """Spell a 12-TET pitch class (semitones above C) on a given letter."""
    offset = _wrap(pitch_class - NATURAL_SEMITONES[letter], 12)
    if offset not in _ET_ACCIDENTALS:
        raise ValueError(f"Cannot spell pitch class {pitch_class} on {letter}")
    return letter + _ET_ACCIDENTALS[offset]


def greek_name(western: str) -> str:
    """'E♭' -> 'Μι♭' (Greek solfège)."""
    return GREEK_SOLFEGE[western[0]] + western[1:]


def perde_name(pitch_class: int) -> str:
    return PERDE_NAMES.get(pitch_class % KOMAS_PER_OCTAVE, "-")


def interval_name(komas: int) -> str:
    return INTERVAL_NAMES.get(komas, f"{komas} komas")


def frequency(semitones_from_a4: float, a4: float = 440.0) -> float:
    return a4 * 2 ** (semitones_from_a4 / 12)


def semitones_from_a4(letter: str, semis: int, octave: int = 4) -> int:
    """Equal-tempered distance of e.g. D4 from A4."""
    return NATURAL_SEMITONES[letter] + semis - 9 + 12 * (octave - 4)
