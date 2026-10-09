"""Desktop window for Maqam Builder (Tkinter, no extra dependencies)."""

from __future__ import annotations

import sqlite3
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox
from tkinter import font as tkfont
from tkinter import ttk

from . import arabic, builder
from .cli import _equivalents_line
from .data import DROMOI, MAKAMS
from .songs import Song, SongStore, scale_name

# Purple palette
BG = "#F7F3FC"
CARD = "#FFFFFF"
PRIMARY = "#6A3FA0"
PRIMARY_DARK = "#4B2A78"
PRIMARY_LIGHT = "#E9DFF7"
TEXT = "#2B1D3F"
MUTED = "#76688A"
LINK = "#7B4BC4"
ERROR = "#A03F6A"

REFERENCES = [
    ("Carmelo Siciliano — The Theory of Rebetiko: From the Makams of Asia "
     "Minor to the Dromi of Piraeus",
     "https://www.carmelosiciliano.com/books/the-theory-of-rebetiko/"),
    ("Siciliano — Ousak mode and dromos",
     "https://www.carmelosiciliano.com/ousak-mode-dromos"),
    ("Siciliano — Kiourdi mode and dromos",
     "https://www.carmelosiciliano.com/kiourdi-mode-and-dromos/"),
    ("Siciliano — Pireotiko(s): mode and dromos",
     "https://www.carmelosiciliano.com/pireotikos/"),
    ("Wikipedia — Rebetiko (dromoi)", "https://en.wikipedia.org/wiki/Rebetiko"),
    ("Wikipedia — Turkish makam (Arel-Ezgi-Uzdilek theory, perde names)",
     "https://en.wikipedia.org/wiki/Turkish_makam"),
    ("Wikipedia — Holdrian comma (the 1/53-octave koma)",
     "https://en.wikipedia.org/wiki/Holdrian_comma"),
    ("Wikipedia — 53 equal temperament",
     "https://en.wikipedia.org/wiki/53_equal_temperament"),
    ("Wikipedia — Arabic maqam (24-tone notation, maqam families)",
     "https://en.wikipedia.org/wiki/Arabic_maqam"),
    ("Maqam World — Arabic maqamat and ajnas (Farraj & Abu Shumays)",
     "https://www.maqamworld.com/"),
    ("Song lists — Λαϊκοί Δρόμοι, Ρεπερτόριο 164 τραγουδιών (kithara.gr)",
     "https://forum.kithara.gr/index.php?topic=84181.0"),
    ("Song lists — 170 τίτλοι των λαϊκών μας δρόμων (rembetiko.gr)",
     "https://rembetiko.gr/t/170-%CF%84%CE%AF%CF%84%CE%BB%CE%BF%CE%B9-%CF%84%CF%89%CE%BD-"
     "%CE%BB%CE%B1%CF%8A%CE%BA%CF%8E%CE%BD-%CE%BC%CE%B1%CF%82-%CE%B4%CF%81%CF%8C%CE%BC%CF%89%CE%BD/10892"),
    ("Song lists — SalihBora.com, works by makam", "https://www.salihbora.com/makam/hicaz/"),
]

STEPS = [
    "Press Start.",
    "Choose what to look up: Dromos (Greek), Makam (Turkish), Arabic (Arabic "
    "maqam, in quarter tones) or Identify (type notes, get the name). Every page "
    "names the equivalent scales in the other two traditions.",
    "Pick a name from the list. Optionally type a tonic: D, A, F#, Eb … "
    "(for makams also B-1 = B lowered by one koma).",
    "Press Show. You get the notes with Greek names, cents and Hz, the "
    "original makam beside the dromos, and the playing tips.",
    "In the tips, ↑ means bend the note up and ↓ means hold it low. "
    "A koma accidental like B♭¹ means B lowered by one koma (≈ 23 cents).",
    "Under each dromos and makam you get a song suggestion drawn from the "
    "literature. Press Another song for a new one. If a song is in the wrong "
    "dromos/makam, press Wrong dromos? to give the right one and suggest a "
    "better song. Your corrections are saved on this computer.",
    "Back returns to this page; End closes the program.",
]

MODES = ("Dromos", "Makam", "Arabic", "Identify")

# Fonts with Greek, ♯/♭, superscripts and arrows; the first one installed wins.
UI_FONTS = ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Inter", "Noto Sans",
            "DejaVu Sans", "Arial")

LEGEND = ("Koma accidentals: B♭¹ = B lowered by one koma (≈ 23¢), F♯⁴ = F raised "
          "by four komas. 1 koma = 1/53 octave.")


def _pick_font(preferred, fallback: str) -> str:
    installed = {f.lower(): f for f in tkfont.families()}
    for name in preferred:
        if name.lower() in installed:
            return installed[name.lower()]
    return fallback


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Maqam Builder")
        self.geometry("960x720")
        self.minsize(760, 560)
        self.configure(bg=BG)

        base = _pick_font(UI_FONTS, tkfont.nametofont("TkDefaultFont").actual("family"))
        self.fonts = {
            "title": (base, 30, "bold"),
            "subtitle": (base, 13),
            "heading": (base, 14, "bold"),
            "body": (base, 11),
            "small": (base, 10),
            "song": (base, 15, "bold"),
        }
        self._style()
        self._store: SongStore | None = None
        self.song_shown: Song | None = None
        self.songs_seen: set[int] = set()

        self.pages = {"welcome": self._welcome(), "main": self._main()}
        self.current = "welcome"
        self.bind_all("<MouseWheel>", self._wheel)
        self.bind_all("<Button-4>", self._wheel)
        self.bind_all("<Button-5>", self._wheel)
        self.show("welcome")

    def _wheel(self, event) -> None:
        if getattr(event, "num", None) in (4, 5):
            units = -1 if event.num == 4 else 1
        else:
            units = -1 if event.delta > 0 else 1
            units *= max(1, abs(event.delta) // 120)
        target = self.welcome_canvas if self.current == "welcome" else self.output
        target.yview_scroll(units * 2, "units")

    @property
    def store(self) -> SongStore:
        if self._store is None:
            self._store = SongStore()
        return self._store

    def destroy(self) -> None:
        if self._store is not None:
            self._store.close()
        super().destroy()

    # -- styling -----------------------------------------------------------
    def _style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=TEXT, font=self.fonts["body"])
        style.configure("Card.TFrame", background=CARD)
        style.configure("TFrame", background=BG)
        for name, bg, fg, active in (
            ("Primary.TButton", PRIMARY, "white", PRIMARY_DARK),
            ("Ghost.TButton", BG, PRIMARY, PRIMARY_LIGHT),
        ):
            style.configure(name, background=bg, foreground=fg, borderwidth=1,
                            bordercolor=PRIMARY, focuscolor=bg, padding=(18, 8),
                            font=(self.fonts["body"][0], 11, "bold"))
            style.map(name, background=[("active", active)],
                      foreground=[("active", "white" if fg == "white" else PRIMARY_DARK)])
        style.configure("Small.TButton", background=PRIMARY_LIGHT, foreground=PRIMARY_DARK,
                        borderwidth=0, focuscolor=PRIMARY_LIGHT, padding=(10, 4),
                        font=(self.fonts["body"][0], 10, "bold"))
        style.map("Small.TButton", background=[("active", "#D9C8F0")])
        style.configure("Dialog.TRadiobutton", background=CARD, foreground=TEXT)
        style.map("Dialog.TRadiobutton", background=[("active", CARD)])
        style.configure("Mode.TRadiobutton", background=PRIMARY_LIGHT,
                        foreground=PRIMARY_DARK, padding=(14, 6), indicatorsize=0,
                        font=(self.fonts["body"][0], 11, "bold"))
        style.map("Mode.TRadiobutton",
                  background=[("selected", PRIMARY), ("active", "#D9C8F0")],
                  foreground=[("selected", "white")])
        style.configure("TCombobox", fieldbackground=CARD, background=PRIMARY_LIGHT,
                        bordercolor=PRIMARY_LIGHT, arrowcolor=PRIMARY, padding=4)
        style.map("TCombobox", fieldbackground=[("readonly", CARD)],
                  foreground=[("readonly", TEXT)],
                  selectbackground=[("readonly", CARD)],
                  selectforeground=[("readonly", TEXT)])
        style.configure("TEntry", fieldbackground=CARD, bordercolor=PRIMARY_LIGHT,
                        padding=4)
        style.configure("Result.Treeview", background=CARD, fieldbackground=CARD,
                        foreground=TEXT, rowheight=26, borderwidth=0,
                        font=self.fonts["body"])
        style.configure("Result.Treeview.Heading", background=PRIMARY_LIGHT,
                        foreground=PRIMARY_DARK, relief="flat", padding=(8, 5),
                        font=(self.fonts["body"][0], 10, "bold"))
        style.map("Result.Treeview", background=[("selected", PRIMARY_LIGHT)],
                  foreground=[("selected", PRIMARY_DARK)])
        style.map("Result.Treeview.Heading", background=[("active", PRIMARY_LIGHT)])
        style.configure("Vertical.TScrollbar", background=PRIMARY_LIGHT,
                        troughcolor=BG, bordercolor=BG, arrowcolor=PRIMARY)

    def _label(self, parent, text, font="body", fg=TEXT, bg=BG, **kw) -> tk.Label:
        return tk.Label(parent, text=text, font=self.fonts[font], fg=fg, bg=bg,
                        justify="left", anchor="w", **kw)

    def show(self, page: str) -> None:
        for frame in self.pages.values():
            frame.pack_forget()
        self.pages[page].pack(fill="both", expand=True)
        self.current = page

    # -- welcome page ------------------------------------------------------
    def _welcome(self) -> tk.Frame:
        outer = tk.Frame(self, bg=BG)
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        bar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        page = tk.Frame(canvas, bg=BG, padx=48, pady=36)
        window = canvas.create_window((0, 0), window=page, anchor="nw")
        canvas.configure(yscrollcommand=bar.set)
        page.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        self.welcome_canvas = canvas
        canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")

        self._label(page, "Maqam Builder", "title", PRIMARY_DARK).pack(anchor="w")
        self._label(page, "Turkish makams  ·  Greek rebetiko dromoi  ·  "
                          "microtonal playing tips", "subtitle", MUTED).pack(anchor="w")
        tk.Frame(page, bg=PRIMARY, height=3, width=80).pack(anchor="w", pady=(14, 22))

        card = tk.Frame(page, bg=CARD, padx=28, pady=22,
                        highlightbackground=PRIMARY_LIGHT, highlightthickness=1)
        card.pack(fill="x")
        self._label(card, "How to use", "heading", PRIMARY_DARK, CARD).pack(anchor="w")
        for i, step in enumerate(STEPS, 1):
            row = tk.Frame(card, bg=CARD)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=str(i), font=(self.fonts["body"][0], 10, "bold"),
                     fg="white", bg=PRIMARY, width=2).pack(side="left", anchor="n", padx=(0, 12))
            lbl = self._label(row, step, bg=CARD)
            lbl.pack(side="left", fill="x", expand=True)
            lbl.bind("<Configure>", lambda e, l=lbl: l.configure(wraplength=e.width))

        buttons = tk.Frame(page, bg=BG)
        buttons.pack(anchor="w", pady=24)
        ttk.Button(buttons, text="Start", style="Primary.TButton",
                   command=lambda: self.show("main")).pack(side="left")
        ttk.Button(buttons, text="End", style="Ghost.TButton",
                   command=self.destroy).pack(side="left", padx=12)

        self._label(page, "References", "heading", PRIMARY_DARK).pack(anchor="w", pady=(6, 6))
        for text, url in REFERENCES:
            link = self._label(page, "↗  " + text, fg=LINK, cursor="hand2")
            link.configure(font=self.fonts["body"] + ("underline",))
            link.pack(anchor="w", pady=2)
            link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
        self._label(page,
                    "Makam pitches follow Arel-Ezgi-Uzdilek theory (53 komas per "
                    "octave). Dromos charts follow common rebetiko practice and "
                    "differ between teachers. Use your ears.",
                    "small", MUTED, wraplength=760).pack(anchor="w", pady=(18, 0))
        return outer

    # -- lookup page -------------------------------------------------------
    def _main(self) -> tk.Frame:
        page = tk.Frame(self, bg=BG, padx=28, pady=20)

        top = tk.Frame(page, bg=BG)
        top.pack(fill="x")
        self._label(top, "Maqam Builder", "heading", PRIMARY_DARK).pack(side="left")
        ttk.Button(top, text="End", style="Ghost.TButton",
                   command=self.destroy).pack(side="right")
        ttk.Button(top, text="Back", style="Ghost.TButton",
                   command=lambda: self.show("welcome")).pack(side="right", padx=8)

        modes = tk.Frame(page, bg=BG)
        modes.pack(fill="x", pady=(16, 10))
        self.mode = tk.StringVar(value=MODES[0])
        for m in MODES:
            ttk.Radiobutton(modes, text=m, value=m, variable=self.mode,
                            style="Mode.TRadiobutton",
                            command=self._mode_changed).pack(side="left", padx=(0, 4))

        controls = tk.Frame(page, bg=BG)
        controls.pack(fill="x", pady=(0, 12))
        self.name_label = self._label(controls, "Dromos")
        self.name_label.grid(row=0, column=0, sticky="w")
        self.name = ttk.Combobox(controls, width=28, state="readonly")
        self.name.grid(row=1, column=0, sticky="w", padx=(0, 16))
        self.notes = ttk.Entry(controls, width=30)
        self.tonic_label = self._label(controls, "Tonic (optional)")
        self.tonic_label.grid(row=0, column=1, sticky="w")
        self.tonic = ttk.Entry(controls, width=10)
        self.tonic.grid(row=1, column=1, sticky="w", padx=(0, 16))
        self._label(controls, "A4 (Hz)").grid(row=0, column=2, sticky="w")
        self.a4 = ttk.Entry(controls, width=8)
        self.a4.insert(0, "440")
        self.a4.grid(row=1, column=2, sticky="w", padx=(0, 16))
        ttk.Button(controls, text="Show", style="Primary.TButton",
                   command=self.run).grid(row=1, column=3, sticky="w")
        self.hint = self._label(controls, "", "small", MUTED)
        self.hint.grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))

        box = tk.Frame(page, bg=CARD, highlightbackground=PRIMARY_LIGHT,
                       highlightthickness=1)
        box.pack(fill="both", expand=True)
        self.output = tk.Text(box, wrap="word", font=self.fonts["body"], bg=CARD,
                              fg=TEXT, relief="flat", padx=20, pady=14, cursor="arrow",
                              selectbackground=PRIMARY_LIGHT, insertbackground=PRIMARY)
        scroll = ttk.Scrollbar(box, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.output.pack(side="left", fill="both", expand=True)
        tags = {
            "title": dict(foreground=PRIMARY_DARK, font=(self.fonts["body"][0], 18, "bold"),
                          spacing3=2),
            "muted": dict(foreground=MUTED, spacing3=6),
            "equiv": dict(foreground=PRIMARY, font=(self.fonts["body"][0], 11, "bold"),
                          spacing3=6),
            "heading": dict(foreground=PRIMARY_DARK, font=self.fonts["heading"],
                            spacing1=14, spacing3=6),
            "tip": dict(lmargin1=4, lmargin2=24, spacing1=3, spacing3=3),
            "mark": dict(foreground=PRIMARY, font=(self.fonts["body"][0], 11, "bold")),
            "small": dict(foreground=MUTED, font=self.fonts["small"], spacing1=8),
            "error": dict(foreground=ERROR, font=(self.fonts["body"][0], 12, "bold")),
        }
        for name, options in tags.items():
            self.output.tag_configure(name, **options)

        for widget in (self.name, self.notes, self.tonic, self.a4):
            widget.bind("<Return>", lambda e: self.run())
        self.name.bind("<<ComboboxSelected>>", lambda e: self.run())
        self._mode_changed()
        return page

    def _mode_changed(self) -> None:
        mode = self.mode.get()
        if mode == "Identify":
            self.name.grid_remove()
            self.tonic.grid_remove()
            self.tonic_label.grid_remove()
            self.notes.grid(row=1, column=0, sticky="w", padx=(0, 16))
            self.name_label.configure(text="Notes, tonic first")
            self.hint.configure(text="e.g.  D Eb F# G   ·   A B-1 C D  (B-1 = B lowered by one "
                                     "koma)   ·   D Ed F G  (Ed = E half-flat)")
        else:
            self.notes.grid_remove()
            self.name.grid()
            self.tonic.grid()
            self.tonic_label.grid()
            table = {"Dromos": DROMOI, "Makam": MAKAMS, "Arabic": arabic.MAQAMAT}[mode]
            names = [item.name for item in table.values()]
            self.name.configure(values=names)
            if self.name.get() not in names:
                self.name.set(names[0])
            self.name_label.configure(text="Arabic maqam" if mode == "Arabic" else mode)
            self.hint.configure(text={
                "Dromos": "Tonic: D, A, F#, Eb …",
                "Makam": "Tonic: D, A, F#, Eb … or with komas, e.g. B-1",
                "Arabic": "Tonic: C, D, Bb … or with a quarter tone, e.g. Ed = E half-flat",
            }[mode])
        self.run()

    # -- results ---------------------------------------------------------
    def run(self) -> None:
        out = self.output
        out.configure(state="normal")
        out.delete("1.0", "end")
        for child in out.winfo_children():
            child.destroy()
        try:
            a4 = float(self.a4.get() or 440)
            if a4 <= 0:
                raise ValueError("A4 must be a positive frequency.")
            tonic = self.tonic.get().strip() or None
            mode = self.mode.get()
            if mode == "Dromos":
                self._show_dromos(self.name.get(), tonic, a4)
            elif mode == "Makam":
                self._show_makam(self.name.get(), tonic, a4)
            elif mode == "Arabic":
                self._show_arabic(self.name.get(), tonic, a4)
            else:
                self._show_identify(self.notes.get().split())
        except (KeyError, ValueError) as exc:
            out.delete("1.0", "end")
            self._write(str(exc.args[0] if exc.args else exc), "error")
        out.configure(state="disabled")

    def _write(self, text: str, *tags: str) -> None:
        self.output.insert("end", text, tags)

    def _table(self, columns, rows) -> None:
        tree = ttk.Treeview(self.output, columns=[c for c, _, _ in columns],
                            show="headings", height=len(rows), style="Result.Treeview",
                            selectmode="none")
        for name, width, anchor in columns:
            tree.heading(name, text=name, anchor=anchor)
            tree.column(name, width=width, anchor=anchor, stretch=False)
        for row in rows:
            tree.insert("", "end", values=row)
        tree.bind("<MouseWheel>", self._wheel)
        tree.bind("<Button-4>", self._wheel)
        tree.bind("<Button-5>", self._wheel)
        self.output.window_create("end", window=tree)
        self._write("\n")

    def _show_dromos(self, name: str, tonic: str | None, a4: float) -> None:
        _, dromos = builder.find_dromos(name)
        tonic = tonic or dromos.tonic
        self._write(f"{dromos.name}  ·  {dromos.greek}\n", "title")
        parent = MAKAMS[dromos.makam].name if dromos.makam else None
        origin = f"From makam {parent}." if parent else "Greek-born, no makam parent."
        self._write(f"{dromos.description}  {origin}\n", "muted")
        self._write(_equivalents_line("dromos", builder.find_dromos(name)[0]) + "\n", "equiv")
        self._song_panel("dromos", builder.find_dromos(name)[0])

        directions = ["asc", "desc"] if dromos.descending else ["asc"]
        for direction in directions:
            notes = sorted(builder.build_dromos(name, tonic, direction, a4).notes,
                           key=lambda n: n.degree)
            label = "Ascending" if direction == "asc" else "Descending"
            if parent:
                makam_notes = sorted(
                    builder.build_makam(dromos.makam, tonic, direction, a4).notes,
                    key=lambda n: n.degree)
                arab = arabic.arabic_for("dromos", builder.find_dromos(name)[0])
                arab_notes = sorted(arabic.build(arab.name, tonic, direction, a4),
                                    key=lambda n: n.degree) if arab else []
                beside = f"makam {parent}" + (f" and Arabic {arab.name}" if arab else "")
                self._write(f"{label} on {tonic}, with {beside} beside it\n", "heading")
                columns = [("Degree", 72, "center"), ("Note", 64, "center"),
                           ("Greek", 76, "center"), ("Makam note", 108, "center"),
                           ("Δ cents", 78, "center")]
                if arab:
                    columns += [("Arabic note", 108, "center"), ("Δ¢ Arabic", 90, "center")]
                columns += [("Hz", 80, "e")]
                rows = []
                for i, (n, m) in enumerate(zip(notes, makam_notes)):
                    row = [n.degree, n.name, n.greek, m.name, f"{m.cents - n.cents:+.0f}"]
                    if arab:
                        a = arab_notes[i]
                        row += [a.name, f"{a.cents - n.cents:+.0f}"]
                    rows.append(row + [f"{n.frequency:.2f}"])
            else:
                self._write(f"{label} on {tonic}\n", "heading")
                columns = [("Degree", 70, "center"), ("Note", 80, "center"),
                           ("Greek", 90, "center"), ("Cents", 90, "center"),
                           ("Hz", 90, "e")]
                rows = [(n.degree, n.name, n.greek, f"{n.cents:.0f}",
                         f"{n.frequency:.2f}") for n in notes]
            self._table(columns, rows)

        self._write("Playing tips\n", "heading")
        any_tip = False
        for direction in directions:
            for tip in builder.dromos_tips(name, tonic, direction):
                any_tip = True
                mark = "↑" if "bend up" in tip.text else "↓" if "hold it low" in tip.text else "•"
                where = "" if len(directions) == 1 else (
                    " going up" if direction == "asc" else " coming down")
                self._write(f"{mark}  ", "tip", "mark")
                self._write(f"{tip.dromos_note}", "tip", "mark")
                self._write(f"  (degree {tip.degree}{where}) — {tip.text}\n", "tip")
        for text in dromos.tips:
            any_tip = True
            self._write("•  ", "tip", "mark")
            self._write(text + "\n", "tip")
        if not any_tip:
            self._write("Tempered intonation is fine for this dromos.\n", "tip")
        if parent:
            for line in builder.TECHNIQUE.values():
                self._write(line + "\n", "small")
            self._write(LEGEND + "\n", "small")

    def _show_makam(self, name: str, tonic: str | None, a4: float) -> None:
        _, makam = builder.find_makam(name)
        tonic = tonic or makam.tonic
        self._write(f"Makam {makam.name}\n", "title")
        self._write(f"{makam.description}\nSeyir: {makam.seyir}  ·  güçlü (dominant): "
                    f"degree {makam.guclu + 1}\n", "muted")
        self._write(_equivalents_line("makam", builder.find_makam(name)[0]) + "\n", "equiv")
        self._song_panel("makam", builder.find_makam(name)[0])
        for direction in ("asc", "desc"):
            notes = builder.build_makam(name, tonic, direction, a4).notes
            label = "Ascending" if direction == "asc" else "Descending"
            self._write(f"{label} on {notes[0 if direction == 'asc' else -1].name}\n",
                        "heading")
            columns = [("Degree", 74, "center"), ("Note", 70, "center"),
                       ("Greek", 80, "center"), ("Perde", 110, "w"),
                       ("Step", 160, "w"), ("Komas", 74, "center"),
                       ("Cents", 74, "center"), ("Hz", 80, "e")]
            rows = [(n.degree, n.name, n.greek, n.perde, n.step, n.komas,
                     f"{n.cents:.1f}", f"{n.frequency:.2f}") for n in notes]
            self._table(columns, rows)
        self._write(LEGEND + "\n", "small")

    # -- songs -------------------------------------------------------------
    def _song_panel(self, kind: str, scale: str) -> None:
        """A card with a suggested song, actions, and the list of songs."""
        panel = tk.Frame(self.output, bg=PRIMARY_LIGHT, padx=16, pady=12)
        self.song_panel = panel
        self.song_scale = (kind, scale)
        self.songs_seen = set()
        self.output.window_create("end", window=panel, padx=0, pady=8)
        self._write("\n")
        self._fill_song_panel(pick=True)

    def _fill_song_panel(self, pick: bool = False, song: Song | None = None) -> None:
        panel = self.song_panel
        for child in panel.winfo_children():
            child.destroy()
        kind, scale = self.song_scale
        name = scale_name(kind, scale)
        label = lambda text, font="body", fg=TEXT, **kw: self._label(  # noqa: E731
            panel, text, font, fg, PRIMARY_LIGHT, **kw)

        try:
            songs = self.store.songs_for(kind, scale)
            related = self.store.related(kind, scale)
            if pick:
                song = self.store.suggest(kind, scale, self.songs_seen)
        except sqlite3.Error as exc:
            label(f"The song database could not be opened: {exc}", fg=ERROR).pack(anchor="w")
            return
        self.song_shown = song
        if song:
            self.songs_seen.add(song.id)

        label(f"♪  Song suggestion for {name}", "heading", PRIMARY_DARK).pack(anchor="w")
        if song is None:
            label("No songs yet for this one — be the first to suggest one.",
                  fg=MUTED).pack(anchor="w", pady=(4, 0))
        else:
            label(song.title, "song").pack(anchor="w", pady=(4, 0))
            details = "  ·  ".join(str(x) for x in (
                song.artist, song.year, song.rhythm,
                song.song_key and f"on {song.song_key}") if x)
            if details:
                label(details, fg=MUTED).pack(anchor="w")
            if (song.kind, song.scale) != (kind, scale) and not song.via_report:
                label(f"From the related {song.kind} {scale_name(song.kind, song.scale)}.",
                      "small", MUTED).pack(anchor="w")
            if song.via_report:
                label(f"Listed under {scale_name(song.kind, song.scale)}; users say it "
                      f"belongs to {name}.", "small", ERROR).pack(anchor="w")
            for (rkind, rscale), n in song.reports.items():
                who = "1 user says" if n == 1 else f"{n} users say"
                label(f"⚠  {who} it is really {rkind} {scale_name(rkind, rscale)}.",
                      "small", ERROR).pack(anchor="w")
            origin = "Suggested by a user" if song.origin == "user" else "Source"
            src = label(f"{origin}: {song.source}", "small",
                        LINK if song.source_url else MUTED,
                        cursor="hand2" if song.source_url else "")
            src.pack(anchor="w", pady=(4, 0))
            if song.source_url:
                src.configure(font=self.fonts["small"] + ("underline",))
                src.bind("<Button-1>", lambda e, u=song.source_url: webbrowser.open(u))

        buttons = tk.Frame(panel, bg=PRIMARY_LIGHT)
        buttons.pack(anchor="w", pady=(10, 4))
        total = len(songs)
        for text, command, enabled in (
            ("Another song", lambda: self._fill_song_panel(pick=True), total > 1),
            (f"Wrong {kind}?", self._report_dialog, song is not None),
            ("Suggest a song", self._suggest_dialog, True),
            ("Export my contributions", self._export, True),
        ):
            b = ttk.Button(buttons, text=text, style="Small.TButton", command=command)
            b.pack(side="left", padx=(0, 6))
            if not enabled:
                b.state(["disabled"])

        rows = [(s, "") for s in songs] + [(s, scale_name(s.kind, s.scale)) for s in related]
        if rows:
            label(f"All songs ({total} here, {len(related)} related) — click one to "
                  "show it above", "small", MUTED).pack(anchor="w", pady=(6, 2))
            tree = ttk.Treeview(panel, columns=("Title", "Artist", "Year", "From", "Reports"),
                                show="headings", height=min(len(rows), 6),
                                style="Result.Treeview", selectmode="browse")
            for col, width in (("Title", 270), ("Artist", 170), ("Year", 56),
                               ("From", 110), ("Reports", 76)):
                tree.heading(col, text=col, anchor="w")
                tree.column(col, width=width, anchor="w", stretch=False)
            by_iid = {}
            for s_, origin in rows:
                iid = tree.insert("", "end", values=(
                    s_.title, s_.artist, s_.year or "",
                    origin or ("users" if s_.via_report else name),
                    sum(s_.reports.values()) or ""))
                by_iid[iid] = s_
            tree.bind("<<TreeviewSelect>>", lambda e: tree.selection() and
                      self._fill_song_panel(song=by_iid[tree.selection()[0]]))
            if len(rows) <= 6:
                tree.bind("<MouseWheel>", self._wheel)
                tree.bind("<Button-4>", self._wheel)
                tree.bind("<Button-5>", self._wheel)
            tree.pack(anchor="w")

    def _dialog(self, title: str) -> tuple[tk.Toplevel, tk.Frame]:
        win = tk.Toplevel(self, bg=CARD)
        win.title(title)
        win.transient(self)
        win.resizable(False, False)
        body = tk.Frame(win, bg=CARD, padx=24, pady=20)
        body.pack(fill="both", expand=True)
        self._label(body, title, "heading", PRIMARY_DARK, CARD).pack(anchor="w", pady=(0, 8))
        return win, body

    def _scale_picker(self, parent, kind: str, scale: str):
        """Dromos/Makam radio + combobox; returns a function giving (kind, key)."""
        row = tk.Frame(parent, bg=CARD)
        row.pack(anchor="w", pady=(2, 8))
        kind_var = tk.StringVar(value=kind)
        combo = ttk.Combobox(row, width=24, state="readonly")

        def refill(*_):
            table = DROMOI if kind_var.get() == "dromos" else MAKAMS
            combo.configure(values=[i.name for i in table.values()])
            current = table.get(scale) if kind_var.get() == kind else None
            combo.set(current.name if current else next(iter(table.values())).name)

        for value, text in (("dromos", "Greek dromos"), ("makam", "Turkish makam")):
            ttk.Radiobutton(row, text=text, value=value, variable=kind_var,
                            style="Dialog.TRadiobutton", command=refill).pack(side="left")
        combo.pack(side="left", padx=(10, 0))
        refill()

        def value() -> tuple[str, str]:
            if kind_var.get() == "dromos":
                return "dromos", builder.find_dromos(combo.get())[0]
            return "makam", builder.find_makam(combo.get())[0]
        return value, combo

    def _entry(self, parent, label: str, width: int = 40) -> ttk.Entry:
        self._label(parent, label, "small", MUTED, CARD).pack(anchor="w")
        entry = ttk.Entry(parent, width=width)
        entry.pack(anchor="w", pady=(0, 8))
        return entry

    def _dialog_buttons(self, win, body, on_save) -> tk.Label:
        error = self._label(body, "", "small", ERROR, CARD)
        error.pack(anchor="w")
        row = tk.Frame(body, bg=CARD)
        row.pack(anchor="e", pady=(8, 0))

        def save():
            try:
                on_save()
            except (KeyError, ValueError, sqlite3.Error) as exc:
                error.configure(text=str(exc.args[0] if exc.args else exc))
                return
            win.destroy()

        ttk.Button(row, text="Cancel", style="Ghost.TButton",
                   command=win.destroy).pack(side="right")
        ttk.Button(row, text="Save", style="Primary.TButton",
                   command=save).pack(side="right", padx=8)
        win.bind("<Escape>", lambda e: win.destroy())
        win.grab_set()
        return error

    def _report_dialog(self) -> None:
        song = self.song_shown
        if song is None:
            return
        kind, scale = self.song_scale
        win, body = self._dialog("Wrong dromos / makam?")
        self._label(body, f"“{song.title}” is listed under "
                          f"{scale_name(song.kind, song.scale)}. It actually is:",
                    bg=CARD, wraplength=460).pack(anchor="w")
        picked, _ = self._scale_picker(body, kind, scale)
        comment = self._entry(body, "Why? (optional — e.g. where you read it, or what you hear)", 56)
        self._label(body, f"Suggest a more suitable song for {scale_name(kind, scale)} "
                          "(optional)", bg=CARD).pack(anchor="w", pady=(8, 2))
        title = self._entry(body, "Song title")
        artist = self._entry(body, "Composer / performer")

        def save():
            new_kind, new_scale = picked()
            self.store.report(song.id, new_kind, new_scale, comment.get())
            if title.get().strip():
                self.store.add_song(title.get(), kind, scale, artist=artist.get())
            self._fill_song_panel(song=self.store.get(song.id))

        self._dialog_buttons(win, body, save)

    def _suggest_dialog(self) -> None:
        kind, scale = self.song_scale
        win, body = self._dialog("Suggest a song")
        title = self._entry(body, "Song title", 48)
        artist = self._entry(body, "Composer / performer", 48)
        year = self._entry(body, "Year (optional)", 10)
        self._label(body, "It is in", bg=CARD).pack(anchor="w")
        picked, _ = self._scale_picker(body, kind, scale)
        source = self._entry(body, "Source (optional — book, record, link)", 48)

        def save():
            text = year.get().strip()
            if text and not text.isdigit():
                raise ValueError("Year must be a number, e.g. 1936.")
            new_kind, new_scale = picked()
            song_id = self.store.add_song(title.get(), new_kind, new_scale,
                                          artist=artist.get(),
                                          year=int(text) if text else None,
                                          source=source.get())
            if (new_kind, new_scale) == (kind, scale):
                self._fill_song_panel(song=self.store.get(song_id))
            else:
                self._fill_song_panel(song=self.song_shown)

        self.after(50, title.focus_set)
        self._dialog_buttons(win, body, save)

    def _export(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self, title="Export my contributions", defaultextension=".json",
            initialfile="maqam_builder_contributions.json",
            filetypes=[("JSON", "*.json")])
        if path:
            data = self.store.export_json(path)
            messagebox.showinfo(
                "Exported", f"Saved {len(data['songs'])} song suggestion(s) and "
                f"{len(data['reports'])} report(s) to\n{path}", parent=self)

    def _show_arabic(self, name: str, tonic: str | None, a4: float) -> None:
        key, maqam = arabic.find_maqam(name)
        tonic = tonic or maqam.tonic
        self._write(f"Maqam {maqam.name}  ·  {maqam.arabic}\n", "title")
        self._write(f"{maqam.description}\nGhammaz (dominant): degree "
                    f"{maqam.ghammaz + 1}\n", "muted")
        self._write(_equivalents_line("arabic", key) + "\n", "equiv")
        self._song_panel("makam", maqam.makam)

        directions = ["asc", "desc"] if maqam.descending else ["asc"]
        for direction in directions:
            notes = arabic.build(key, tonic, direction, a4)
            label = "Ascending" if direction == "asc" else "Descending"
            self._write(f"{label} on {notes[0 if direction == 'asc' else -1].name}\n",
                        "heading")
            columns = [("Degree", 70, "center"), ("Note", 80, "center"),
                       ("Name", 110, "w"), ("Step", 120, "w"),
                       ("Cents", 80, "center"), ("Hz", 90, "e")]
            self._table(columns, [(n.degree, n.name, n.arabic_name, n.step,
                                   f"{n.cents:.0f}", f"{n.frequency:.2f}") for n in notes])

        turkish = MAKAMS[maqam.makam]
        eq = arabic.equivalents("arabic", key)
        dromoi = [DROMOI[k] for k in eq.dromoi]
        others = f"makam {turkish.name}" + "".join(f" and dromos {d.name}" for d in dromoi)
        self._write(f"Compared with {others} (cents above the tonic)\n", "heading")
        ar = sorted(arabic.build(key, tonic), key=lambda n: n.degree)
        mk = sorted(builder.build_makam(maqam.makam).notes,
                    key=lambda n: n.degree)
        columns = [("Degree", 72, "center"), ("Arabic", 80, "center"),
                   (turkish.name, 100, "center"), ("Δ¢ Turkish", 96, "center")]
        for d in dromoi:
            columns += [(d.name, 90, "center"), (f"Δ¢ {d.name}", 96, "center")]
        rows = []
        for i, a in enumerate(ar):
            row = [a.degree, f"{a.cents:.0f}", f"{mk[i].cents:.0f}",
                   f"{mk[i].cents - a.cents:+.0f}"]
            for d in dromoi:
                fret = builder.dromos_positions(d)[i] * 100
                row += [f"{fret:.0f}", f"{fret - a.cents:+.0f}"]
            rows.append(row)
        self._table(columns, rows)
        self._write("Quarter-tone accidentals: E½♭ = E half-flat, F½♯ = F half-sharp "
                    "(50¢). Arabic notation rounds to quarter tones; the real "
                    "intonation of the half-flat notes varies by region, which is "
                    "why the Turkish and Arabic values differ.\n", "small")

    def _show_identify(self, notes: list[str]) -> None:
        if not notes:
            self._write("Type the notes above, starting from the tonic.\n", "muted")
            return
        result = builder.identify(notes)
        self._write("  ".join(notes) + "\n", "title")
        self._write("Matching scales that start with these notes\n", "muted")
        for label, key in (("Greek dromoi", "dromoi"), ("Turkish makams", "makams"),
                           ("Arabic maqamat", "arabic")):
            self._write(label + "\n", "heading")
            self._write(("  ·  ".join(result[key]) or "none") + "\n", "tip")


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
