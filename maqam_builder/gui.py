"""Desktop window for Maqam Builder (Tkinter, no extra dependencies)."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import font as tkfont
from tkinter import ttk

from . import builder
from .data import DROMOI, MAKAMS

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
]

STEPS = [
    "Press Start.",
    "Choose what to look up: Dromos (Greek), Makam (Turkish), or Identify "
    "(type notes, get the name).",
    "Pick a name from the list. Optionally type a tonic: D, A, F#, Eb … "
    "(for makams also B-1 = B lowered by one koma).",
    "Press Show. You get the notes with Greek names, cents and Hz, the "
    "original makam beside the dromos, and the playing tips.",
    "In the tips, ↑ means bend the note up and ↓ means hold it low. "
    "A koma accidental like B♭¹ means B lowered by one koma (≈ 23 cents).",
    "Back returns to this page; End closes the program.",
]

MODES = ("Dromos", "Makam", "Identify")

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
        }
        self._style()

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
            self.hint.configure(text="e.g.  D Eb F# G   or   A B-1 C D  (B-1 = B lowered by one koma)")
        else:
            self.notes.grid_remove()
            self.name.grid()
            self.tonic.grid()
            self.tonic_label.grid()
            table = DROMOI if mode == "Dromos" else MAKAMS
            names = [item.name for item in table.values()]
            self.name.configure(values=names)
            if self.name.get() not in names:
                self.name.set(names[0])
            self.name_label.configure(text=mode)
            self.hint.configure(
                text="Tonic: D, A, F#, Eb …" if mode == "Dromos"
                else "Tonic: D, A, F#, Eb … or with komas, e.g. B-1")
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

        directions = ["asc", "desc"] if dromos.descending else ["asc"]
        for direction in directions:
            notes = sorted(builder.build_dromos(name, tonic, direction, a4).notes,
                           key=lambda n: n.degree)
            label = "Ascending" if direction == "asc" else "Descending"
            if parent:
                makam_notes = sorted(
                    builder.build_makam(dromos.makam, tonic, direction, a4).notes,
                    key=lambda n: n.degree)
                self._write(f"{label} on {tonic}, with makam {parent} beside it\n",
                            "heading")
                columns = [("Degree", 70, "center"), ("Note", 80, "center"),
                           ("Greek", 90, "center"), ("Makam note", 110, "center"),
                           ("Δ cents", 90, "center"), ("Hz", 90, "e")]
                rows = [(n.degree, n.name, n.greek, m.name,
                         f"{m.cents - n.cents:+.0f}", f"{n.frequency:.2f}")
                        for n, m in zip(notes, makam_notes)]
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

    def _show_identify(self, notes: list[str]) -> None:
        if not notes:
            self._write("Type the notes above, starting from the tonic.\n", "muted")
            return
        result = builder.identify(notes)
        self._write("  ".join(notes) + "\n", "title")
        self._write("Matching scales that start with these notes\n", "muted")
        for label, key in (("Greek dromoi", "dromoi"), ("Turkish makams", "makams")):
            self._write(label + "\n", "heading")
            self._write(("  ·  ".join(result[key]) or "none") + "\n", "tip")


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
