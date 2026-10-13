import json

import pytest

from mustra import builder, cli, corrections, webapi
from mustra.data import DROMOI, MAKAMS
from mustra.songs import SongStore


@pytest.fixture
def store():
    with SongStore(":memory:") as s:
        yield s


def test_form_values_match_the_shipped_theory():
    assert corrections.form_values("makam", "ussak") == {
        "tonic": "A", "steps": "8 5 9 9 4 9 9", "guclu": "4"}
    assert corrections.form_values("dromos", "ousak")["makam"] == "ussak"
    assert corrections.form_values("arabic", "bayati")["steps"] == "3 3 4 4 2 4 4"


def test_parse_form_keeps_only_real_changes():
    assert corrections.parse_form("makam", "ussak", corrections.form_values("makam", "ussak")) == {}
    assert corrections.parse_form("makam", "ussak", {"tonic": "a"}) == {}
    assert corrections.parse_form("makam", "ussak", {"steps": "7, 6, 9, 9, 4, 9, 9"}) == {
        "steps": [7, 6, 9, 9, 4, 9, 9]}
    assert corrections.parse_form("makam", "ussak", {"guclu": "5"}) == {"guclu": 4}
    assert corrections.parse_form("dromos", "ousak", {"makam": ""}) == {"makam": None}
    assert corrections.parse_form("dromos", "minore", {"descending": ""}) == {"descending": None}


@pytest.mark.parametrize("kind, key, form, message", [
    ("makam", "ussak", {"steps": "8 5 9 9 4 9 8"}, "add up to 52"),
    ("makam", "ussak", {"steps": "8 5 9"}, "exactly 7"),
    ("makam", "ussak", {"steps": "8 5 x 9 4 9 9"}, "whole numbers"),
    ("makam", "ussak", {"guclu": "8"}, "1 to 7"),
    ("makam", "ussak", {"tonic": "H"}, "Cannot read note"),
    ("dromos", "ousak", {"ascending": "1 2 3 5 7 8 10"}, "the tonic, 0"),
    ("dromos", "ousak", {"ascending": "0 3 1 5 7 8 10"}, "higher than"),
    ("dromos", "ousak", {"tonic": "B-1"}, "koma offsets"),
    ("arabic", "bayati", {"steps": "3 3 4 4 2 4 5"}, "add up to 25"),
    ("arabic", "bayati", {"makam": ""}, "choose a Turkish makam"),
])
def test_bad_corrections_are_refused(store, kind, key, form, message):
    with pytest.raises(ValueError, match=message):
        store.suggest_correction(kind, key, corrections.parse_form(kind, key, form))
    assert store.correction_history() == []


def test_a_correction_changes_every_result_that_uses_it(store):
    before = [t.text for t in builder.dromos_tips("ousak") if t.degree == 2][0]
    assert "+81¢" in before
    store.suggest_correction("makam", "ussak", {"steps": [7, 6, 9, 9, 4, 9, 9]},
                             "segah is lower in practice")
    assert MAKAMS["ussak"].steps == (7, 6, 9, 9, 4, 9, 9)
    after = [t.text for t in builder.dromos_tips("ousak") if t.degree == 2][0]
    assert "+58¢" in after
    assert corrections.page_notes("dromos", "ousak") == [
        "Turkish makam Uşşak — Steps in komas: 8 5 9 9 4 9 9 → 7 6 9 9 4 9 9"]
    assert corrections.ORIGINALS["makam"]["ussak"].steps == (8, 5, 9, 9, 4, 9, 9)


def test_dromos_parent_can_be_removed(store):
    store.suggest_correction("dromos", "ousak", {"makam": None})
    assert DROMOI["ousak"].makam is None
    assert builder.dromos_tips("ousak") == []
    assert corrections.describe("dromos", "ousak") == [
        "Parent makam: Uşşak → none (Greek-born)"]


def test_every_version_is_kept_and_can_be_rolled_back(store):
    first = store.suggest_correction("makam", "ussak", {"steps": [7, 6, 9, 9, 4, 9, 9]}, "v1")
    store.suggest_correction("makam", "ussak", {"steps": [7, 6, 9, 9, 4, 9, 9], "guclu": 4})
    assert MAKAMS["ussak"].guclu == 4

    store.rollback_correction("makam", "ussak", first)
    assert MAKAMS["ussak"].guclu == 3 and MAKAMS["ussak"].steps[0] == 7
    store.reset_correction("makam", "ussak")
    assert MAKAMS["ussak"] == corrections.ORIGINALS["makam"]["ussak"]
    assert not corrections.is_corrected("makam", "ussak")

    history = store.correction_history("makam", "ussak")
    assert [(v.number, v.action, v.active) for v in history] == [
        (1, "edit", False), (2, "edit", False), (3, "rollback", False), (4, "reset", True)]
    assert history[2].comment == "Rolled back to version 1"
    assert history[3].summary == ["Original theory"]
    with pytest.raises(ValueError, match="already uses the original"):
        store.reset_correction("makam", "ussak")
    with pytest.raises(ValueError, match="already in use"):
        store.rollback_correction("makam", "ussak", history[3].id)


def test_comment_only_feedback_is_kept_but_nothing_new_is_refused(store):
    store.suggest_correction("makam", "hicaz", {}, "the güçlü looks wrong to me")
    assert store.correction_history("makam", "hicaz")[0].comment
    with pytest.raises(ValueError, match="Nothing changed"):
        store.suggest_correction("makam", "hicaz", {})


def test_corrections_survive_a_restart_and_reload(tmp_path):
    path = tmp_path / "c.sqlite3"
    with SongStore(path) as s:
        s.suggest_correction("arabic", "bayati", {"ghammaz": 4})
    corrections.apply({})
    assert arabic_ghammaz() == 3
    with SongStore(path) as s:
        assert s.apply_corrections() == []
    assert arabic_ghammaz() == 4


def arabic_ghammaz():
    from mustra.arabic import MAQAMAT
    return MAQAMAT["bayati"].ghammaz


def test_a_correction_that_no_longer_fits_is_skipped():
    skipped = corrections.apply({("makam", "ussak"): {"steps": [1, 2, 3]}})
    assert skipped and "exactly 7" in skipped[0]
    assert MAKAMS["ussak"] == corrections.ORIGINALS["makam"]["ussak"]


def test_export_and_admin_review(store, tmp_path, capsys):
    store.suggest_correction("makam", "ussak", {"steps": [7, 6, 9, 9, 4, 9, 9]}, "Source: my teacher")
    data = store.export_json(tmp_path / "out.json")
    item = data["corrections"][0]
    assert item["original"] == {"steps": "8 5 9 9 4 9 9"}
    assert item["suggested"] == {"steps": "7 6 9 9 4 9 9"}
    assert item["comments"] == ["Source: my teacher"]
    assert cli.main(["review", str(tmp_path / "out.json")]) == 0
    out = capsys.readouterr().out
    assert "MAKAMS['ussak']" in out and "7 6 9 9 4 9 9" in out


def test_cli_correct_history_rollback(tmp_path, capsys):
    db = str(tmp_path / "cli.sqlite3")
    assert cli.main(["--db", db, "correct", "makam", "uşşak", "--steps", "7 6 9 9 4 9 9",
                     "--comment", "lower segah"]) == 0
    assert cli.main(["--db", db, "correct", "makam", "ussak", "--dominant", "5"]) == 0
    assert cli.main(["--db", db, "dromos", "ousak"]) == 0
    assert "With your corrections" in capsys.readouterr().out
    assert cli.main(["--db", db, "rollback", "makam", "ussak", "0"]) == 0
    assert cli.main(["--db", db, "history", "makam", "ussak"]) == 0
    out = capsys.readouterr().out
    assert "version 2" in out and "version 3" in out and "reset  ← in use" in out
    assert cli.main(["--db", db, "correct", "dromos", "ousak", "--steps", "1"]) == 1


def test_web_api_corrections():
    webapi.open_store(":memory:")
    form = json.loads(webapi.correction_form("dromos", "ousak"))
    assert [f["name"] for f in form["fields"]] == ["tonic", "ascending", "descending", "makam"]
    assert form["banner"] == corrections.BANNER and not form["corrected"]

    out = json.loads(webapi.save_correction("dromos", "ousak", json.dumps({"makam": "kurdi"}),
                                            "compare with Kürdi"))
    assert out["summary"] == ["Parent makam: Uşşak → Kürdi"]
    page = json.loads(webapi.dromos("ousak"))
    assert page["corrections"] == ["Parent makam: Uşşak → Kürdi"]
    assert "Kürdi" in page["sections"][0]["columns"]

    form = json.loads(webapi.correction_form("dromos", "ousak"))
    assert form["corrected"] and form["history"][0]["active"]
    assert "error" in json.loads(webapi.save_correction(
        "dromos", "ousak", json.dumps({"ascending": "0 1"})))
    assert json.loads(webapi.rollback_correction("dromos", "ousak", 0)) == {
        "ok": True, "summary": []}
    assert json.loads(webapi.dromos("ousak"))["corrections"] == []
