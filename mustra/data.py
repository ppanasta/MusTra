"""Makam and dromos definitions.

Makams are written the Turkish (AEU) way: a tonic perde plus the seven
step sizes in komas (1 koma = 1/53 octave).  The steps are the classic
AEU values: K=1, B=4, S=5, M=8, T=9, A=12/13.

Dromoi are written as semitone positions above the tonic, as played on a
fretted instrument.  Each dromos names the makam it descends from, and the
builder compares the two degree by degree to generate intonation tips.

Charts of the dromoi vary between teachers and regions; edit freely.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Makam:
    name: str
    tonic: str                  # Turkish notation, e.g. "A" or "B-1"
    steps: tuple[int, ...]      # ascending steps in komas (sum = 53)
    guclu: int                  # dominant degree, 0-based (4 = 5th)
    seyir: str                  # melodic direction
    description: str
    descending: dict[int, int] = field(default_factory=dict)  # degree -> Δkomas
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Dromos:
    name: str
    greek: str
    tonic: str
    ascending: tuple[int, ...]  # semitones above tonic, 7 degrees
    makam: str | None           # key into MAKAMS
    description: str
    descending: tuple[int, ...] | None = None
    tips: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()


MAKAMS: dict[str, Makam] = {
    "rast": Makam(
        "Rast", "G", (9, 8, 5, 9, 9, 8, 5), guclu=4, seyir="ascending",
        description="Rast pentachord + Rast tetrachord. The 3rd (segah) and "
                    "the 7th (eviç) sit a koma below their Western pitch.",
        descending={6: -4},  # eviç -> acem when descending
    ),
    "ussak": Makam(
        "Uşşak", "A", (8, 5, 9, 9, 4, 9, 9), guclu=3, seyir="ascending",
        description="Uşşak tetrachord on dügah + Bûselik pentachord on neva. "
                    "The 2nd (segah) is a 'three-quarter' tone above the tonic.",
    ),
    "huseyni": Makam(
        "Hüseyni", "A", (8, 5, 9, 9, 8, 5, 9), guclu=4, seyir="ascending-descending",
        description="Hüseyni pentachord + Uşşak tetrachord on hüseyni. Rises "
                    "with eviç (low F♯) and falls with acem (F).",
        descending={5: -4},
    ),
    "kurdi": Makam(
        "Kürdi", "A", (4, 9, 9, 9, 4, 9, 9), guclu=3, seyir="ascending",
        description="Kürdi tetrachord + Bûselik pentachord. A true small "
                    "semitone (bakiye) above the tonic.",
    ),
    "hicaz": Makam(
        "Hicaz", "A", (5, 12, 5, 9, 8, 5, 9), guclu=3, seyir="ascending",
        description="Hicaz tetrachord on dügah + Rast pentachord on neva; the "
                    "upper part turns to Uşşak/Bûselik (F natural) descending.",
        descending={5: -4},
    ),
    "hicazkar": Makam(
        "Hicazkâr", "G", (5, 12, 5, 9, 5, 12, 5), guclu=4, seyir="descending",
        description="Zirgüleli Hicaz on rast: Hicaz pentachord + Hicaz "
                    "tetrachord. Two augmented seconds.",
        aliases=("zirguleli hicaz",),
    ),
    "saba": Makam(
        "Saba", "A", (8, 5, 5, 13, 4, 9, 9), guclu=2, seyir="ascending",
        description="Saba tetrachord (a diminished fourth: dügah-segah-"
                    "çargah-hicaz) + Hicaz on çargah. It does not settle on "
                    "the octave: above the tonic the hicaz note returns.",
    ),
    "huzzam": Makam(
        "Hüzzam", "B-1", (5, 9, 5, 12, 5, 9, 8), guclu=2, seyir="descending",
        description="Hüzzam pentachord on segah: the tonic itself is the "
                    "microtonal segah perde; Hicaz colour on the 3rd (neva).",
    ),
    "segah": Makam(
        "Segah", "B-1", (5, 9, 9, 8, 5, 9, 8), guclu=2, seyir="ascending",
        description="Segah trichord + Hicaz/Uşşak on neva. Tonic is the "
                    "segah perde, a koma below B.",
    ),
    "karcigar": Makam(
        "Karcığar", "A", (8, 5, 9, 5, 12, 5, 9), guclu=3, seyir="ascending",
        description="Uşşak tetrachord + Hicaz pentachord on neva.",
    ),
    "neveser": Makam(
        "Nev'eser", "G", (9, 4, 13, 5, 5, 12, 5), guclu=4, seyir="ascending",
        description="Nikriz pentachord on rast + Hicaz tetrachord on neva.",
        aliases=("nev'eser", "nev eser"),
    ),
    "cargah": Makam(
        "Çargah", "C", (9, 9, 4, 9, 9, 9, 4), guclu=4, seyir="ascending",
        description="Çargah pentachord + Çargah tetrachord — the makam "
                    "counterpart of the Western major scale.",
    ),
    "nihavend": Makam(
        "Nihavend", "G", (9, 4, 9, 9, 4, 9, 9), guclu=4, seyir="descending",
        description="Bûselik pentachord + Kürdi tetrachord (Hicaz on neva "
                    "gives the raised 7th).",
        aliases=("nihavent",),
    ),
}


DROMOI: dict[str, Dromos] = {
    "matzore": Dromos(
        "Matzore", "Ματζόρε", "D", (0, 2, 4, 5, 7, 9, 11), "cargah",
        "The Greek major. Tempered intonation is correct here.",
        tips=("Descending phrases often borrow the minor 7th (C) — a "
              "Rast/Mixolydian colour.",),
        aliases=("major", "ματζόρε"),
    ),
    "minore": Dromos(
        "Minore", "Μινόρε", "D", (0, 2, 3, 5, 7, 8, 11), "nihavend",
        "Greek minor (≈ Nihavent): raised 7th going up, natural 7th coming down.",
        descending=(0, 2, 3, 5, 7, 8, 10),
        tips=("The C♯ is a leading tone — let it lean up into D; on the way "
              "down use C natural.",),
        aliases=("minor", "nihavent dromos", "μινόρε"),
    ),
    "rast": Dromos(
        "Rast", "Ραστ", "D", (0, 2, 4, 5, 7, 9, 11), "rast",
        "Looks like Matzore, but the 3rd and 7th are low.",
        descending=(0, 2, 4, 5, 7, 9, 10),
        tips=("The low F♯ (segah) is THE sound of Rast — never let it sound "
              "like a bright major 3rd.",
              "Going up use a low C♯; coming down C natural (acem)."),
        aliases=("ραστ",),
    ),
    "ousak": Dromos(
        "Ousak", "Ουσάκ", "D", (0, 1, 3, 5, 7, 8, 10), "ussak",
        "Phrygian on the frets, but the 2nd is the Uşşak segah.",
        tips=("Play the E♭ high — between E♭ and E. This is the main "
              "difference between Ousak and Kiourdi.",
              "Melodies circle around G (4th, neva) and fall to D through "
              "the high E♭."),
        aliases=("ussak", "uşşak", "ουσάκ"),
    ),
    "kiourdi": Dromos(
        "Kiourdi", "Κιουρντί", "D", (0, 1, 3, 5, 7, 8, 10), "kurdi",
        "Same frets as Ousak, but a true small semitone above the tonic.",
        tips=("Keep the E♭ clean, even a touch low — do not raise it as in "
              "Ousak.",),
        aliases=("kurdi", "kiourdi", "κιουρντί"),
    ),
    "hitzaz": Dromos(
        "Hitzaz", "Χιτζάζ", "D", (0, 1, 4, 5, 7, 8, 10), "hicaz",
        "The best-known dromos: augmented 2nd E♭–F♯ over the tonic.",
        tips=("The augmented 2nd is narrower than on the frets: E♭ slightly "
              "high, F♯ slightly low.",
              "The E♭ falls onto D in cadences; the F♯ is pulled to G.",
              "The makam rises through a low B (Rast on G); Greek Hitzaz "
              "normally keeps B♭, which is the makam's descending form."),
        aliases=("hicaz", "χιτζάζ"),
    ),
    "hitzazkiar": Dromos(
        "Hitzazkiar", "Χιτζαζκιάρ", "D", (0, 1, 4, 5, 7, 8, 11), "hicazkar",
        "Two augmented seconds: E♭–F♯ and B♭–C♯.",
        tips=("Both augmented seconds are narrower than tempered: raise E♭ and "
              "B♭ slightly, lower F♯ and C♯ slightly.",
              "C♯ is a strong leading tone into the octave D."),
        aliases=("hicazkar", "χιτζαζκιάρ"),
    ),
    "sabah": Dromos(
        "Sabah", "Σαμπάχ", "D", (0, 1, 3, 4, 7, 8, 10), "saba",
        "The 'crying' dromos: diminished 4th D–G♭.",
        tips=("Play E♭ high, as in Ousak — Sabah starts like Ousak and then "
              "breaks on the G♭.",
              "Linger on F (3rd) and G♭ (4th); resolving G♭ → F → E♭ → D is "
              "the signature phrase.",
              "Above the octave the G♭ returns: the dromos does not close on "
              "a pure octave like Western scales."),
        aliases=("saba", "sabach", "σαμπάχ"),
    ),
    "houzam": Dromos(
        "Houzam", "Χουζάμ", "E", (0, 1, 3, 4, 7, 8, 10), "huzzam",
        "Same frets as Sabah, but built on the microtonal segah note.",
        tips=("In the original the tonic itself is a microtone (segah, a "
              "koma below B in Turkish notation). Singers and violinists "
              "sit slightly low on the tonic.",
              "G (3rd) is the dominant; G–A♭–B is a Hicaz figure on top of it."),
        aliases=("huzzam", "hüzzam", "χουζάμ"),
    ),
    "segah": Dromos(
        "Segah", "Σεγκιάχ", "B", (0, 1, 3, 5, 7, 8, 10), "segah",
        "Phrygian on the frets; the tonic is the segah microtone.",
        tips=("Treat the tonic as a 'soft' note — it is a koma low in the "
              "original — and the step to C is a large semitone.",
              "Melodies settle on D (3rd) as often as on the tonic."),
        aliases=("segiah", "segkiach", "σεγκιάχ"),
    ),
    "karsigar": Dromos(
        "Karsigar", "Καρσιγάρ", "D", (0, 1, 3, 5, 6, 9, 10), "karcigar",
        "Ousak below, Hitzaz on the 4th above.",
        tips=("E♭ high as in Ousak.",
              "Upper part G–A♭–B–C is Hitzaz: A♭ slightly high, B slightly "
              "low."),
        aliases=("karcigar", "karşığar", "karcığar", "καρσιγάρ"),
    ),
    "neveser": Dromos(
        "Neveser", "Νεβεσέρ", "D", (0, 2, 3, 6, 7, 8, 11), "neveser",
        "Two augmented seconds: F–G♯ and B♭–C♯ (like the 'Hungarian minor').",
        tips=("G♯ is pulled up into A, C♯ up into D — play both slightly "
              "low before they resolve, as the makam does.",),
        aliases=("nev'eser", "νεβεσέρ"),
    ),
    "piraeus": Dromos(
        "Piraeus", "Πειραιώτικος", "D", (0, 1, 4, 6, 7, 8, 10), None,
        "A Greek-born dromos (no direct makam): Hitzaz with a raised 4th.",
        tips=("No Ottoman parent: tempered intonation is the norm.",
              "E♭ falls to D and G♯ pushes up to A — the two gravitational "
              "points of the dromos.",
              "Treat E♭–F♯ like Hitzaz: slightly narrower than the frets."),
        aliases=("pireotikos", "peiraiotikos", "piraiotikos", "πειραιώτικος"),
    ),
}
