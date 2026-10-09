import pytest

from mustra import builder, pitch
from mustra.cli import main
from mustra.data import DROMOI, MAKAMS


@pytest.mark.parametrize("key", MAKAMS)
def test_makam_steps_fill_an_octave(key):
    assert sum(MAKAMS[key].steps) == pitch.KOMAS_PER_OCTAVE
    assert len(MAKAMS[key].steps) == 7


@pytest.mark.parametrize("key", DROMOI)
def test_dromos_degrees_ascend(key):
    d = DROMOI[key]
    for form in filter(None, (d.ascending, d.descending)):
        assert form[0] == 0 and list(form) == sorted(set(form)) and form[-1] < 12
    assert d.makam is None or d.makam in MAKAMS


def test_rast_in_turkish_notation():
    names = [n.name for n in builder.build_makam("rast").notes]
    assert names == ["G", "A", "B♭¹", "C", "D", "E", "F♯⁴", "G"]
    perdes = [n.perde for n in builder.build_makam("rast").notes]
    assert perdes[:3] == ["Rast", "Dügah", "Segah"]


def test_rast_descends_with_acem():
    desc = builder.build_makam("rast", direction="desc").notes
    assert [n.name for n in desc][:2] == ["G", "F"]


def test_hicaz_transposed_to_d():
    names = [n.name for n in builder.build_makam("hicaz", "D").notes]
    assert names[:4] == ["D", "E♭⁴", "F♯⁴", "G"]


def test_dromos_spelling_and_greek():
    scale = builder.build_dromos("hitzaz")
    assert [n.name for n in scale.notes] == ["D", "E♭", "F♯", "G", "A", "B♭", "C", "D"]
    assert scale.notes[1].greek == "Μι♭"
    assert scale.notes[4].frequency == pytest.approx(440.0)


def test_dromos_transposition():
    names = [n.name for n in builder.build_dromos("hitzazkiar", "A").notes]
    assert names == ["A", "B♭", "C♯", "D", "E", "F", "G♯", "A"]


def test_lookup_accepts_turkish_greek_and_aliases():
    assert builder.find_makam("Uşşak")[0] == "ussak"
    assert builder.find_makam("KARCIĞAR")[0] == "karcigar"
    assert builder.find_dromos("Χιτζάζ")[0] == "hitzaz"
    assert builder.find_dromos("saba")[0] == "sabah"
    with pytest.raises(KeyError):
        builder.find_dromos("nonsense")


def _tip(dromos, degree, direction="asc"):
    return next(t for t in builder.dromos_tips(dromos, direction=direction)
                if t.degree == degree)


def test_ousak_second_is_raised():
    tip = _tip("ousak", 2)
    assert tip.deviation > 70 and "higher" in tip.text


def test_kiourdi_second_stays_low():
    tip = _tip("kiourdi", 2)
    assert -10 < tip.deviation < 0 and "falls back onto degree 1" in tip.text


def test_hitzaz_augmented_second_is_narrower():
    assert _tip("hitzaz", 2).deviation > 0
    assert _tip("hitzaz", 3).deviation < 0
    assert "leans up into degree 4" in _tip("hitzaz", 3).text


def test_hitzaz_bb_matches_descending_makam():
    tip = _tip("hitzaz", 6)
    assert abs(tip.deviation) < 10 and "descending" in tip.text


def test_rast_third_is_low():
    assert _tip("rast", 3).deviation == pytest.approx(-15, abs=1)


def test_houzam_tonic_is_the_microtone():
    tips = builder.dromos_tips("houzam")
    assert any("tonic itself is the microtone" in t.text for t in tips)


def test_matzore_needs_no_bends():
    tips = builder.dromos_tips("matzore")
    assert not any("play it" in t.text for t in tips)
    assert [t.degree for t in tips] == [7]  # only the leading-tone pull


def test_piraeus_has_no_makam_tips():
    assert builder.dromos_tips("piraeus") == []


def test_identify_tempered_notes():
    result = builder.identify(["D", "Eb", "F#", "G"])
    assert set(result["dromoi"]) == {"Hitzaz", "Hitzazkiar"}
    assert builder.identify(["D", "Eb", "F#", "G#"])["dromoi"] == ["Piraeus"]
    assert "Hicaz" in result["makams"]


def test_identify_koma_notes():
    result = builder.identify(["A", "B-1", "C", "D"])
    assert set(result["makams"]) == {"Uşşak", "Hüseyni", "Karcığar"}
    assert result["dromoi"] == []


def test_dromos_tonic_rejects_komas():
    with pytest.raises(ValueError):
        builder.build_dromos("ousak", "B-1")


@pytest.mark.parametrize("argv", [
    ["list"], ["makam", "saba", "--both"], ["dromos", "sabah", "--tonic", "A"],
    ["identify", "D", "Eb", "F"],
])
def test_cli_runs(argv, capsys):
    assert main(argv) == 0
    assert capsys.readouterr().out


def test_cli_reports_errors(capsys):
    assert main(["dromos", "xyz"]) == 1
    assert "Unknown dromos" in capsys.readouterr().err


def test_gui_builds_every_view(monkeypatch, tmp_path):
    tk = pytest.importorskip("tkinter")
    monkeypatch.setenv("MUSTRA_DB", str(tmp_path / "gui.sqlite3"))
    try:
        from mustra.gui import App
        app = App()
    except tk.TclError:
        pytest.skip("no display")
    try:
        app.show("main")
        from mustra.arabic import MAQAMAT
        for mode, names in (("Dromos", DROMOI), ("Makam", MAKAMS), ("Arabic", MAQAMAT)):
            app.mode.set(mode)
            app._mode_changed()
            for item in names.values():
                app.name.set(item.name)
                app.run()
                assert "error" not in app.output.tag_names("1.0")
        # song panel: suggestion, report with a replacement song, new suggestion
        app.mode.set("Dromos")
        app._mode_changed()
        app.name.set("Sabah")
        app.run()
        song = app.song_shown
        assert song is not None and song.scale == "sabah"
        app.store.report(song.id, "dromos", "houzam", "test")
        app._fill_song_panel(song=app.store.get(song.id))
        assert app.song_shown.reports == {("dromos", "houzam"): 1}
        app._fill_song_panel(pick=True)
        app._report_dialog()
        dialogs = [w for w in app.winfo_children() if isinstance(w, tk.Toplevel)]
        assert dialogs
        for d in dialogs:
            d.destroy()
        app._suggest_dialog()
        for d in [w for w in app.winfo_children() if isinstance(w, tk.Toplevel)]:
            d.destroy()
        app.mode.set("Identify")
        app._mode_changed()
        app.notes.insert(0, "D Eb F# G")
        app.run()
        assert "Hitzaz" in app.output.get("1.0", "end")
        assert "Hijaz" in app.output.get("1.0", "end")
    finally:
        app.destroy()
