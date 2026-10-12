import json

import pytest

from mustra import webapi
from mustra.arabic import MAQAMAT
from mustra.data import DROMOI, MAKAMS


def call(func, *args, **kwargs):
    return json.loads(func(*args, **kwargs))


@pytest.fixture
def store(tmp_path):
    webapi.open_store(str(tmp_path / "songs.sqlite3"))
    webapi._seed_random(1)
    yield
    webapi._store.close()
    webapi._store = None


def test_catalog_lists_all_three_traditions():
    data = call(webapi.catalog)
    assert len(data["dromos"]) == len(DROMOI)
    assert len(data["makam"]) == len(MAKAMS)
    assert len(data["arabic"]) == len(MAQAMAT)
    assert {"key": "bayati", "name": "Bayati", "subtitle": "بياتي", "tonic": "D"} in data["arabic"]


@pytest.mark.parametrize("key", DROMOI)
def test_every_dromos_page(key):
    page = call(webapi.dromos, key)
    assert "error" not in page
    assert page["sections"] and all(len(r) == len(s["columns"])
                                    for s in page["sections"] for r in s["rows"])


@pytest.mark.parametrize("key", MAKAMS)
def test_every_makam_page(key):
    assert "error" not in call(webapi.makam, key)


@pytest.mark.parametrize("key", MAQAMAT)
def test_every_arabic_page(key):
    page = call(webapi.arabic_maqam, key)
    assert "error" not in page
    assert page["sections"][-1]["title"].startswith("Compared")


def test_dromos_page_content():
    page = call(webapi.dromos, "ousak", "A", 442)
    assert page["sections"][0]["title"] == ("Ascending on A, beside makam Uşşak and "
                                            "Arabic Bayati")
    assert page["sections"][0]["rows"][1][:2] == ["2", "B♭"]
    assert any(t["mark"] == "↑" and t["degree"] == 2 for t in page["tips"])
    assert {"kind": "arabic", "key": "bayati",
            "label": "Arabic Bayati (بياتي)"} in page["equivalents"]


def test_errors_come_back_as_json():
    assert "Unknown dromos" in call(webapi.dromos, "nope")["error"]
    assert "Cannot read note" in call(webapi.dromos, "ousak", "H#")["error"]
    assert "error" in call(webapi.identify, "D")


def test_identify_returns_links():
    data = call(webapi.identify, "D Eb F# G")
    assert {"kind": "dromos", "key": "hitzaz", "name": "Hitzaz"} in data["dromoi"]
    assert {"kind": "arabic", "key": "hijaz", "name": "Hijaz"} in data["arabic"]
    assert call(webapi.identify, "D, Ed, F")["arabic"][0]["key"] == "bayati"


def test_songs_need_an_open_store():
    webapi._store = None
    assert "not open" in call(webapi.songs, "dromos", "hitzaz")["error"]


def test_songs_flow(store, tmp_path):
    data = call(webapi.songs, "dromos", "hitzaz")
    assert data["pick"]["scale"] == "hitzaz" and data["count"] >= 4
    assert any(s["from"] == "Hicaz" for s in data["songs"])  # related makam songs

    song_id = data["pick"]["id"]
    assert call(webapi.report, song_id, "dromos", "hitzazkiar", "test",
                "Better song", "Someone", "dromos", "hitzaz") == {"ok": True}
    again = call(webapi.songs, "dromos", "hitzaz", song_id=song_id)
    assert again["pick"]["reports"][0]["scale_name"] == "Hitzazkiar"
    assert any(s["title"] == "Better song" for s in again["songs"])

    assert call(webapi.add_song, "New", "makam", "segah", "X", "1950")["ok"]
    assert "Year must be a number" in call(webapi.add_song, "Y", "makam", "segah",
                                           year="abc")["error"]
    out = call(webapi.export_contributions, str(tmp_path / "e.json"))
    assert out == {"songs": 2, "reports": 1}


def test_arabic_pages_use_the_makam_songs(store):
    data = call(webapi.songs, "arabic", "bayati")
    assert data["kind"] == "makam" and data["scale"] == "ussak"
