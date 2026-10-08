"""Song suggestions stored in a local SQLite database.

Why SQLite: it ships with Python (nothing extra in the executable), keeps
everything in one file, and handles the relational part (songs ← reports)
with real queries.  The database lives in the user's data folder, so each
installation keeps its own reports and suggestions; ``export_json`` writes
them to a file that can be shared or merged into the seed list.

* ``songs``   — one row per song; ``origin`` is "literature" (seeded from
  ``songs_seed.py``) or "user" (suggested in the app).
* ``reports`` — "this song is not in X, it is in Y": a song can be reported
  any number of times.  A reported song is also offered under the scale the
  report names, flagged as a user correction.
"""

from __future__ import annotations

import json
import os
import random
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .data import DROMOI, MAKAMS
from .songs_seed import SEED_SONGS

SCHEMA_VERSION = 1
KINDS = ("dromos", "makam")

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS songs (
    id          INTEGER PRIMARY KEY,
    seed_key    TEXT UNIQUE,               -- set for literature songs only
    title       TEXT NOT NULL,
    artist      TEXT NOT NULL DEFAULT '',
    year        INTEGER,
    rhythm      TEXT NOT NULL DEFAULT '',
    song_key    TEXT NOT NULL DEFAULT '',  -- tonality, e.g. "Ρε"
    kind        TEXT NOT NULL CHECK (kind IN ('dromos', 'makam')),
    scale       TEXT NOT NULL,             -- key into DROMOI / MAKAMS
    source      TEXT NOT NULL DEFAULT '',
    source_url  TEXT NOT NULL DEFAULT '',
    origin      TEXT NOT NULL CHECK (origin IN ('literature', 'user')),
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS songs_scale ON songs (kind, scale);
CREATE TABLE IF NOT EXISTS reports (
    id          INTEGER PRIMARY KEY,
    song_id     INTEGER NOT NULL REFERENCES songs (id) ON DELETE CASCADE,
    kind        TEXT NOT NULL CHECK (kind IN ('dromos', 'makam')),
    scale       TEXT NOT NULL,             -- the scale the user says is correct
    comment     TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS reports_song ON reports (song_id);
CREATE INDEX IF NOT EXISTS reports_scale ON reports (kind, scale);
"""


@dataclass
class Song:
    id: int
    title: str
    artist: str
    year: int | None
    rhythm: str
    song_key: str
    kind: str
    scale: str
    source: str
    source_url: str
    origin: str
    # (kind, scale) -> number of users who say the song belongs there
    reports: dict[tuple[str, str], int] = field(default_factory=dict)
    # True when the song is listed under another scale and only appears here
    # because users reported it belongs here.
    via_report: bool = False

    @property
    def disputed(self) -> bool:
        return bool(self.reports)


def scale_name(kind: str, scale: str) -> str:
    table = DROMOI if kind == "dromos" else MAKAMS
    item = table.get(scale)
    return item.name if item else scale


def _check_scale(kind: str, scale: str) -> None:
    if kind not in KINDS:
        raise ValueError(f"Kind must be 'dromos' or 'makam', not {kind!r}.")
    if scale not in (DROMOI if kind == "dromos" else MAKAMS):
        raise ValueError(f"Unknown {kind} {scale!r}.")


def default_db_path() -> Path:
    """Per-user data folder; MAQAM_BUILDER_DB overrides it."""
    if os.environ.get("MAQAM_BUILDER_DB"):
        return Path(os.environ["MAQAM_BUILDER_DB"])
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "MaqamBuilder" / "songs.sqlite3"


def seed_key(kind: str, scale: str, title: str) -> str:
    return f"{kind}:{scale}:{title}"


class SongStore:
    def __init__(self, path: str | Path | None = None, rng: random.Random | None = None):
        self.path = Path(path) if path is not None else default_db_path()
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.rng = rng or random.Random()
        self._migrate()
        self._seed()

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> SongStore:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- setup -------------------------------------------------------------
    def _migrate(self) -> None:
        with self.db:
            self.db.executescript(SCHEMA)
            self.db.execute("INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)",
                            (str(SCHEMA_VERSION),))

    def _seed(self) -> None:
        """Add literature songs not yet in the database (safe on every start)."""
        with self.db:
            self.db.executemany(
                """INSERT OR IGNORE INTO songs
                   (seed_key, title, artist, year, rhythm, song_key, kind, scale,
                    source, source_url, origin)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'literature')""",
                [(seed_key(s.kind, s.scale, s.title), s.title, s.artist, s.year,
                  s.rhythm, s.key, s.kind, s.scale, s.source, s.url)
                 for s in SEED_SONGS],
            )

    # -- queries -----------------------------------------------------------
    def _song(self, row: sqlite3.Row, via_report: bool = False) -> Song:
        reports = {
            (r["kind"], r["scale"]): r["n"]
            for r in self.db.execute(
                "SELECT kind, scale, COUNT(*) AS n FROM reports WHERE song_id = ? "
                "GROUP BY kind, scale ORDER BY n DESC", (row["id"],))
        }
        return Song(row["id"], row["title"], row["artist"], row["year"], row["rhythm"],
                    row["song_key"], row["kind"], row["scale"], row["source"],
                    row["source_url"], row["origin"], reports, via_report)

    def get(self, song_id: int) -> Song:
        row = self.db.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
        if row is None:
            raise KeyError(f"No song with id {song_id}.")
        return self._song(row)

    def songs_for(self, kind: str, scale: str) -> list[Song]:
        """Songs listed under a scale, plus songs users reported into it."""
        _check_scale(kind, scale)
        listed = self.db.execute(
            "SELECT * FROM songs WHERE kind = ? AND scale = ? "
            "ORDER BY origin, year IS NULL, year, title", (kind, scale)).fetchall()
        reported = self.db.execute(
            "SELECT DISTINCT s.* FROM songs s JOIN reports r ON r.song_id = s.id "
            "WHERE r.kind = ? AND r.scale = ? AND NOT (s.kind = ? AND s.scale = ?) "
            "ORDER BY s.title", (kind, scale, kind, scale)).fetchall()
        return [self._song(r) for r in listed] + [self._song(r, True) for r in reported]

    def related(self, kind: str, scale: str) -> list[Song]:
        """Songs from the other tradition: the parent makam of a dromos, or the
        dromoi derived from a makam."""
        _check_scale(kind, scale)
        if kind == "dromos":
            parent = DROMOI[scale].makam
            return self.songs_for("makam", parent) if parent else []
        children = [k for k, d in DROMOI.items() if d.makam == scale]
        return [song for k in children for song in self.songs_for("dromos", k)]

    def suggest(self, kind: str, scale: str, exclude: set[int] | None = None) -> Song | None:
        """A random song for the scale, avoiding ``exclude`` while possible.

        Songs the users dispute are picked less often than undisputed ones.
        """
        songs = self.songs_for(kind, scale)
        if not songs:
            return None
        fresh = [s for s in songs if s.id not in (exclude or set())] or songs
        weights = [0.5 if s.disputed and not s.via_report else 1.0 for s in fresh]
        return self.rng.choices(fresh, weights=weights)[0]

    def counts(self) -> dict[tuple[str, str], int]:
        return {(r["kind"], r["scale"]): r["n"] for r in self.db.execute(
            "SELECT kind, scale, COUNT(*) AS n FROM songs GROUP BY kind, scale")}

    # -- user input --------------------------------------------------------
    def report(self, song_id: int, kind: str, scale: str, comment: str = "") -> int:
        """Record that a song belongs to another dromos/makam."""
        _check_scale(kind, scale)
        song = self.get(song_id)
        if (song.kind, song.scale) == (kind, scale):
            raise ValueError(f"'{song.title}' is already listed under "
                             f"{scale_name(kind, scale)}.")
        with self.db:
            cur = self.db.execute(
                "INSERT INTO reports (song_id, kind, scale, comment) VALUES (?, ?, ?, ?)",
                (song_id, kind, scale, comment.strip()))
        return cur.lastrowid

    def add_song(self, title: str, kind: str, scale: str, artist: str = "",
                 year: int | None = None, rhythm: str = "", song_key: str = "",
                 source: str = "", source_url: str = "") -> int:
        """Store a user's song suggestion."""
        _check_scale(kind, scale)
        title = title.strip()
        if not title:
            raise ValueError("A song needs a title.")
        duplicate = self.db.execute(
            "SELECT id FROM songs WHERE kind = ? AND scale = ? AND lower(title) = lower(?)",
            (kind, scale, title)).fetchone()
        if duplicate:
            raise ValueError(f"'{title}' is already listed under {scale_name(kind, scale)}.")
        if year is not None and not 1000 <= year <= 2100:
            raise ValueError("Year looks wrong.")
        with self.db:
            cur = self.db.execute(
                """INSERT INTO songs (title, artist, year, rhythm, song_key, kind, scale,
                                      source, source_url, origin)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'user')""",
                (title, artist.strip(), year, rhythm.strip(), song_key.strip(), kind,
                 scale, source.strip() or "Suggested by a user", source_url.strip()))
        return cur.lastrowid

    def export_json(self, path: str | Path) -> dict:
        """Write the user's suggestions and reports to a JSON file."""
        songs = [dict(r) for r in self.db.execute(
            "SELECT title, artist, year, rhythm, song_key, kind, scale, source, "
            "source_url, created_at FROM songs WHERE origin = 'user' ORDER BY id")]
        reports = [dict(r) for r in self.db.execute(
            "SELECT s.title, s.kind AS listed_kind, s.scale AS listed_scale, "
            "r.kind AS reported_kind, r.scale AS reported_scale, r.comment, r.created_at "
            "FROM reports r JOIN songs s ON s.id = r.song_id ORDER BY r.id")]
        data = {"format": "maqam_builder-contributions", "version": SCHEMA_VERSION,
                "songs": songs, "reports": reports}
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data
