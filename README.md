# MusTra

*Music & Translations*: one program that translates between three
traditions of modal music: Greek rebetiko dromoi, Turkish makams and Arabic
maqamat.

Calculate the notes of **Turkish (Anatolian) makams** and of the Greek
rebetiko **dromoi** (δρόμοι) derived from them, and get **intonation tips**
that tell you which fretted notes to push sharp or hold flat so the dromos
moves like the original makam.

Given a name you get the notes; given the first notes you get the name.

## Three tuning systems

| | Makam (Ottoman/Turkish) | Maqam (Arabic) | Dromos (Greek) |
|---|---|---|---|
| Tuning | 53 komas per octave (Arel-Ezgi-Uzdilek theory), 1 koma ≈ 22.6¢ | 24 quarter tones per octave, 1 quarter tone = 50¢ | 12-tone equal temperament (bouzouki frets) |
| Spelling | `B♭¹` = B lowered by 1 koma, `F♯⁴` = F raised by 4 komas | `E½♭` = E half-flat, `F½♯` = F half-sharp | `E♭`, `F♯` as usual |
| Extras | perde names (Rast, Dügah, Segah…), AEU step names (K, B, S, M, T, A) | Arabic note names (Rast, Dukah, Sikah…) | Greek solfège (Ρε, Μι♭…) |

Every page names the equivalent scale in the other two traditions, e.g.
Greek **Ousak** = Turkish **Uşşak** = Arabic **Bayati**:

| Greek dromos | Turkish makam | Arabic maqam |
|---|---|---|
| Matzore | Çargah | Ajam |
| Minore | Nihavend | Nahawand |
| Rast | Rast | Rast |
| Ousak | Uşşak | Bayati |
| — | Hüseyni | Husseini |
| Kiourdi | Kürdi | Kurd |
| Hitzaz | Hicaz | Hijaz |
| Hitzazkiar | Hicazkâr | Hijaz Kar |
| Sabah | Saba | Saba |
| Houzam | Hüzzam | Huzam |
| Segah | Segah | Sikah |
| Karsigar | Karcığar | Bayati Shuri (Qarjighar) |
| Neveser | Nev'eser | Nawa Athar |
| Piraeus | — | — |

## Download and run (no Python needed)

Ready-made programs are built automatically by GitHub Actions
(`.github/workflows/build.yml`) for every push:

| System | File | How to open |
|---|---|---|
| Windows | `MusTra-windows.exe` | double-click (if SmartScreen warns: *More info → Run anyway*) |
| macOS | `MusTra-macos.zip` | unzip, then right-click `MusTra.app` → *Open* the first time |
| Linux | `MusTra-linux` | `chmod +x MusTra-linux && ./MusTra-linux` |

Get them from the repository's **Actions** tab (open the latest *Build
executables* run → *Artifacts*), or from **Releases** once a version tag
such as `v1.0.0` is pushed. Each is a single portable file: nothing to install.

The program opens on a welcome page with instructions, Start/End buttons
and the list of references (clickable). Start leads to the lookup page:
choose **Dromos**, **Makam** or **Identify**, pick a name, optionally a
tonic, and the notes, makam comparison and playing tips appear.

The same file also works as a command-line tool when given arguments, e.g.
`MusTra-windows.exe dromos ousak`.

To write the text of a release, add `release-notes/<tag>.md` (e.g.
`release-notes/v1.1.0.md`) and push: the *Release notes* workflow copies it
into the GitHub Release with that tag.

### Building it yourself

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name MusTra run_gui.py   # -> dist/
```

PyInstaller builds for the system it runs on, so build the Windows `.exe` on
Windows (or let the workflow do it).

## Phones: iPhone and Android

Both phone versions show the same touch-friendly app (`mobile/web/`), which
runs this Python package inside the browser with
[Pyodide](https://pyodide.org) (Python compiled to WebAssembly). Results are
identical to the desktop program, and both work offline.

| Phone | How to get it |
|---|---|
| iPhone / iPad | Open the web app in **Safari**: <https://ppanasta.github.io/MusTra/>, tap **Share → Add to Home Screen**. The first start downloads about 15 MB; after that it works offline. |
| Android | Download `MusTra-android.apk` from the *MusTra for Android* release, open it, and allow "install unknown apps" for your browser or file manager when asked. |

Songs you suggest and corrections you make are stored on the phone (in the
web app's storage on iPhone, in the app on Android) and can be exported with
**Export**.

Built by `.github/workflows/mobile.yml`:

* **web**: unit tests, `python mobile/build_web.py` (front end + this package
  + the Pyodide runtime with sqlite3), then a real-browser test
  (`mobile/tests/smoke.py`, Playwright).
* **android**: wraps the web app in a WebView app (`mobile/android/`) and
  builds the APK with Gradle.
* **pages**: deploys the web app to GitHub Pages from `main`. Needs the
  repository to be public (or a paid plan) and **Settings → Pages → Source:
  GitHub Actions**.
* **release**: run the workflow by hand with a version to create the
  releases `ios-v<version>` and `android-v<version>`. They are not marked
  "latest", so the desktop download links keep pointing at the desktop
  release.

Android signing: without secrets, each build is signed with a temporary key,
so installing a newer APK over an older one needs an uninstall first (which
also clears the phone's songs; export them first). For seamless updates, add
the repository secrets `MUSTRA_KEYSTORE_BASE64` (a base64-encoded keystore),
`MUSTRA_KEYSTORE_PASSWORD`, `MUSTRA_KEY_ALIAS` and `MUSTRA_KEY_PASSWORD`.

To try the web app locally:

```bash
python mobile/build_web.py --out mobile/dist     # downloads Pyodide once into mobile/.cache
cd mobile/dist && python -m http.server 8000     # then open http://localhost:8000
```

## Command line (from source)

Python 3.10+, no dependencies. `python -m mustra` with no arguments
opens the window.

```bash
python -m mustra list                      # all dromoi and makams
python -m mustra makam hicaz               # Hicaz on dügah (A), Turkish notation
python -m mustra makam rast --tonic D      # transpose
python -m mustra makam huzzam --tonic B-1  # koma offsets allowed for makams
python -m mustra dromos ousak              # scale, makam comparison, tips
python -m mustra dromos hitzaz --tonic A
python -m mustra identify D Eb F# G        # -> Hitzaz, Hitzazkiar / Hicaz, Hicazkâr
python -m mustra identify A B-1 C D        # exact koma match against makams
python -m mustra arabic bayati             # Arabic maqam, equivalents, comparison
python -m mustra arabic huzam --tonic Ed   # Ed = E half-flat
python -m mustra identify D Ed F G         # quarter-tone match: Bayati, Husseini, ...
python -m mustra --a4 442 dromos sabah     # change the reference pitch
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

## Song suggestions

Every dromos and makam page suggests a song in that dromos/makam, taken
from the literature (each with its source, clickable in the app):
Greek rebetiko repertoire lists that give each song's dromos and key
([kithara.gr](https://forum.kithara.gr/index.php?topic=84181.0),
[rembetiko.gr](https://rembetiko.gr/)), and Turkish works-by-makam
collections and references (SalihBora.com, TDV İslâm Ansiklopedisi, …).
The seed list is in `mustra/songs_seed.py`.

Users can correct it:

* **Wrong dromos?** Say which dromos or makam the song is really in, and
  optionally suggest a more suitable song. The song then also shows up
  under the scale the user named, marked as a user correction, and it is
  suggested less often under the disputed one.
* **Suggest a song** for any dromos or makam, with an optional source.
* **Export my contributions** writes your suggestions and reports to a JSON
  file you can share, for example to improve the seed list.

From the command line:

```bash
python -m mustra songs hitzaz              # suggestion + all songs (ids in [brackets])
python -m mustra songs hicaz --makam
python -m mustra report 17 --dromos houzam --comment "heard it on the record"
python -m mustra add-song "Title" --dromos ousak --artist "Composer" --year 1936
python -m mustra export my_contributions.json
```

### Where the data lives

A **SQLite** database (`songs.sqlite3`): SQLite is built into Python, so the
executable stays a single file, and it stores the songs ↔ reports relation
with real queries. It is created on first use in the user's data folder:

| System | Location |
|---|---|
| Windows | `%APPDATA%\MusTra\songs.sqlite3` |
| macOS | `~/Library/Application Support/MusTra/songs.sqlite3` |
| Linux | `~/.local/share/MusTra/songs.sqlite3` |

Set `MUSTRA_DB` (or `--db` on the command line) to use another file.
Data from versions before the app was renamed (up to 1.1.0) is copied over
automatically on first start.
New literature songs from an updated version are added on start without
touching the user's own data.

The limitation: each computer keeps its own reports. Sharing corrections
between all users would need a small shared server (for example a hosted
database behind an API). Until then, the JSON export is the way to collect
contributions.

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
  `mustra/data.py`; add or adjust makams and dromoi there.

## Tests

```bash
python -m pytest
```
