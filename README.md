# maqam_builder

Calculate the notes of **Turkish (Anatolian) makams** and of the Greek
rebetiko **dromoi** (δρόμοι) derived from them, and get **intonation tips**
that tell you which fretted notes to push sharp or hold flat so the dromos
moves like the original makam.

Given a name you get the notes; given the first notes you get the name.

## Two tuning systems

| | Makam (Ottoman/Turkish) | Dromos (Greek) |
|---|---|---|
| Tuning | 53 komas per octave (Arel-Ezgi-Uzdilek theory), 1 koma ≈ 22.6¢ | 12-tone equal temperament (bouzouki frets) |
| Spelling | `B♭¹` = B lowered by 1 koma, `F♯⁴` = F raised by 4 komas | `E♭`, `F♯` as usual |
| Extras | perde names (Rast, Dügah, Segah…), AEU step names (K, B, S, M, T, A) | Greek solfège (Ρε, Μι♭…) |

## Usage

Python 3.10+, no dependencies.

```bash
python -m maqam_builder list                      # all dromoi and makams
python -m maqam_builder makam hicaz               # Hicaz on dügah (A), Turkish notation
python -m maqam_builder makam rast --tonic D      # transpose
python -m maqam_builder makam huzzam --tonic B-1  # koma offsets allowed for makams
python -m maqam_builder dromos ousak              # scale, makam comparison, tips
python -m maqam_builder dromos hitzaz --tonic A
python -m maqam_builder identify D Eb F# G        # -> Hitzaz, Hitzazkiar / Hicaz, Hicazkâr
python -m maqam_builder identify A B-1 C D        # exact koma match against makams
python -m maqam_builder --a4 442 dromos sabah     # change the reference pitch
```

Names are forgiving: `uşşak`, `ussak`, `Ουσάκ`, `saba`/`sabah` all work.

### Example: Ousak

```
Original makam Uşşak transposed to D, for comparison:
Deg  Fret   Makam   Δ cents
  2  E♭     E♭¹         +81
  ...
Tips — playing the dromos so it moves like the makam:
    E♭ (degree 2, makam E♭¹): play it much higher — close to the next fret, a true
      microtone (+81¢) — bend up (↑).
  • Play the E♭ high — between E♭ and E. This is the main difference between Ousak
    and Kiourdi.
```

## How the tips are made

For each dromos, the parent makam is transposed onto the dromos tonic and
compared degree by degree:

* **Deviation**: how many cents the makam note is above or below the fret.
  Differences under 10¢ are ignored; bigger ones say *slightly*,
  *noticeably* or *about a quarter-tone* higher or lower. ↑ means bend up;
  ↓ means hold it low (on a fretted instrument: touch it lightly, or bend up
  from the fret below).
* **Ascending/descending forms**: each fret is matched to whichever makam
  form fits it best, and the other form is mentioned (e.g. Hitzaz's B♭ is
  the descending Hicaz; going up the makam uses a low B).
* **Attraction (çekim)**: a note within 5 komas of the tonic, the güçlü
  (dominant) or the octave is described as leaning into or falling onto it.
  That is the "pull" that gives makam melodies their movement.
* **Tonic shift**: when every degree leans the same way (Houzam, Segah), the
  tip says the tonic itself is the microtone.
* Every dromos also carries hand-written tips (characteristic phrases,
  differences from its neighbours).

## Included

**Dromoi:** Matzore, Minore, Rast, Ousak, Kiourdi, Hitzaz, Hitzazkiar,
Sabah, Houzam, Segah, Karsigar, Neveser, Piraeus (Peiraiotikos, Greek-born,
no makam parent).

**Makams:** Rast, Uşşak, Hüseyni, Kürdi, Hicaz, Hicazkâr, Saba, Hüzzam,
Segah, Karcığar, Nev'eser, Çargah, Nihavend.

## Caveats

* The koma values are the theoretical AEU ones. Real performers often take
  some notes lower than the theory, for example Uşşak's segah, which is often
  played around +50–65¢ above the E♭ rather than +81¢. Use your ears.
* Dromos charts differ between teachers and regions. Everything is in
  `maqam_builder/data.py`; add or adjust makams and dromoi there.

## Tests

```bash
python -m pytest
```
