import json
import random

import pytest

from mustra.cli import main
from mustra.data import DROMOI, MAKAMS
from mustra.songs import SongStore, default_db_path
from mustra.songs_seed import SEED_SONGS


@pytest.fixture
def store(tmp_path):
    with SongStore(tmp_path / "songs.sqlite3", rng=random.Random(1)) as s:
        yield s


def test_seed_songs_point_at_known_scales_and_sources():
    for song in SEED_SONGS:
        table = DROMOI if song.kind == "dromos" else MAKAMS
        assert song.scale in table, song
        assert song.source and song.url.startswith("https://"), song


def test_seed_titles_are_unique_per_scale():
    keys = [(s.kind, s.scale, s.title) for s in SEED_SONGS]
    assert len(keys) == len(set(keys))


def test_seeding_is_idempotent(tmp_path):
    path = tmp_path / "songs.sqlite3"
    SongStore(path).close()
    with SongStore(path) as again:
        assert sum(again.counts().values()) == len(SEED_SONGS)


def test_songs_for_dromos(store):
    titles = [s.title for s in store.songs_for("dromos", "hitzaz")]
    assert "Το κουτσαβάκι" in titles
    assert all(s.origin == "literature" for s in store.songs_for("dromos", "hitzaz"))


def test_related_crosses_traditions(store):
    assert any(s.kind == "makam" and s.scale == "hicaz"
               for s in store.related("dromos", "hitzaz"))
    assert any(s.kind == "dromos" and s.scale == "hitzaz"
               for s in store.related("makam", "hicaz"))
    assert store.related("dromos", "piraeus") == []


def test_suggest_avoids_excluded_and_handles_empty(store):
    songs = store.songs_for("dromos", "ousak")
    exclude = {s.id for s in songs[:-1]}
    assert store.suggest("dromos", "ousak", exclude).id == songs[-1].id
    assert store.suggest("makam", "segah") is None


def test_report_moves_song_into_other_scale(store):
    song = store.songs_for("dromos", "sabah")[0]
    store.report(song.id, "dromos", "houzam", "sounds like Houzam to me")
    store.report(song.id, "dromos", "houzam")
    again = store.get(song.id)
    assert again.reports == {("dromos", "houzam"): 2}
    houzam = {s.id: s for s in store.songs_for("dromos", "houzam")}
    assert houzam[song.id].via_report
    # still listed where the literature put it, but flagged
    assert any(s.id == song.id and s.disputed for s in store.songs_for("dromos", "sabah"))


def test_report_validation(store):
    song = store.songs_for("dromos", "sabah")[0]
    with pytest.raises(ValueError):
        store.report(song.id, "dromos", "sabah")
    with pytest.raises(ValueError):
        store.report(song.id, "dromos", "nope")
    with pytest.raises(KeyError):
        store.report(99999, "dromos", "ousak")


def test_add_song_and_duplicates(store):
    song_id = store.add_song("Test song", "makam", "segah", artist="Someone", year=1950)
    song = store.get(song_id)
    assert song.origin == "user" and song.source == "Suggested by a user"
    assert store.suggest("makam", "segah").id == song_id
    with pytest.raises(ValueError):
        store.add_song("test SONG", "makam", "segah")
    with pytest.raises(ValueError):
        store.add_song("  ", "makam", "segah")
    with pytest.raises(ValueError):
        store.add_song("X", "makam", "segah", year=99)


def test_deleting_a_song_removes_its_reports(store):
    song_id = store.add_song("Temp", "dromos", "rast")
    store.report(song_id, "dromos", "matzore")
    with store.db:
        store.db.execute("DELETE FROM songs WHERE id = ?", (song_id,))
    assert store.db.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 0


def test_export_json(store, tmp_path):
    song_id = store.add_song("Mine", "dromos", "rast")
    store.report(song_id, "dromos", "matzore", "major really")
    out = tmp_path / "export.json"
    store.export_json(out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["songs"][0]["title"] == "Mine"
    assert data["reports"][0]["reported_scale"] == "matzore"


def test_default_db_path_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("MUSTRA_DB", str(tmp_path / "x.db"))
    assert default_db_path() == tmp_path / "x.db"


def test_cli_song_commands(tmp_path, capsys):
    db = str(tmp_path / "cli.sqlite3")
    assert main(["--db", db, "songs", "hitzaz"]) == 0
    assert "Suggested song" in capsys.readouterr().out
    assert main(["--db", db, "add-song", "New one", "--dromos", "ousak",
                 "--artist", "X"]) == 0
    assert "Added" in capsys.readouterr().out
    assert main(["--db", db, "report", "1", "--makam", "no-such-makam"]) == 1
    assert "Unknown makam" in capsys.readouterr().err
    assert main(["--db", db, "report", "1", "--dromos", "ousak", "--comment", "hm"]) == 0
    assert main(["--db", db, "export", str(tmp_path / "e.json")]) == 0
    assert "1 suggestion(s) and 1 report(s)" in capsys.readouterr().out


def test_data_from_before_the_rename_is_migrated(monkeypatch, tmp_path):
    from mustra import songs
    monkeypatch.delenv("MUSTRA_DB", raising=False)
    monkeypatch.setattr(songs, "_data_base", lambda: tmp_path)
    legacy = tmp_path / songs.LEGACY_DATA_FOLDER / "songs.sqlite3"
    legacy.parent.mkdir()
    with SongStore(legacy) as old:
        old.add_song("Kept across the rename", "dromos", "rast")
    path = default_db_path()
    assert path == tmp_path / "MusTra" / "songs.sqlite3"
    with SongStore(path) as new:
        assert any(s.title == "Kept across the rename"
                   for s in new.songs_for("dromos", "rast"))
