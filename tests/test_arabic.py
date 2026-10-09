import pytest

from mustra import arabic, builder
from mustra.cli import main
from mustra.data import DROMOI, MAKAMS


@pytest.mark.parametrize("key", arabic.MAQAMAT)
def test_maqam_fills_an_octave_and_has_a_turkish_counterpart(key):
    m = arabic.MAQAMAT[key]
    assert sum(m.steps) == arabic.QUARTERS_PER_OCTAVE and len(m.steps) == 7
    assert m.makam in MAKAMS
    assert 0 < m.ghammaz < 7


def test_every_greek_dromos_with_a_makam_has_an_arabic_equivalent():
    for key, d in DROMOI.items():
        if d.makam:
            assert arabic.arabic_for("dromos", key) is not None, key


def test_rast_spelling_and_names():
    notes = arabic.build("rast")
    assert [n.name for n in notes] == ["C", "D", "E½♭", "F", "G", "A", "B½♭", "C"]
    assert [n.arabic_name for n in notes][:3] == ["Rast", "Dukah", "Sikah"]
    assert notes[2].cents == 350


def test_rast_descends_with_b_flat():
    assert [n.name for n in arabic.build("rast", direction="desc")][:2] == ["C", "B♭"]


def test_quarter_tone_tonic_and_transposition():
    huzam = arabic.build("huzam")
    assert huzam[0].name == "E½♭" and huzam[0].arabic_name == "Sikah"
    assert [n.name for n in arabic.build("bayati", "A")][:3] == ["A", "B½♭", "C"]
    assert arabic.build("kurd", "E½♭")[0].name == "E½♭"


@pytest.mark.parametrize("text,expected", [
    ("Ed", ("E", -1)), ("E½♭", ("E", -1)), ("E½b", ("E", -1)), ("Ft", ("F", 1)),
    ("F½#", ("F", 1)), ("Bb", ("B", -2)), ("C#", ("C", 2)),
])
def test_parse_note(text, expected):
    assert arabic.parse_note(text) == expected


def test_parse_note_rejects_junk():
    with pytest.raises(ValueError):
        arabic.parse_note("H")


def test_lookup_by_names_and_aliases():
    assert arabic.find_maqam("Qarjighar")[0] == "bayati_shuri"
    assert arabic.find_maqam("hijaz kar")[0] == "hijaz_kar"
    assert arabic.find_maqam("حجاز")[0] == "hijaz"
    with pytest.raises(KeyError):
        arabic.find_maqam("nope")


def test_equivalents_link_all_three_traditions():
    eq = arabic.equivalents("dromos", "ousak")
    assert eq.arabic == ["bayati"] and eq.makams == ["ussak"] and eq.dromoi == ["ousak"]
    assert arabic.equivalents("arabic", "hijaz").dromoi == ["hitzaz"]
    assert arabic.equivalents("dromos", "piraeus").arabic == []


def test_bayati_second_is_between_fret_and_turkish_theory():
    bayati = arabic.degree_cents(arabic.MAQAMAT["bayati"])[1]
    turkish = builder.makam_positions(MAKAMS["ussak"])[1] * 1200 / 53
    assert 100 < bayati < turkish


def test_identify_quarter_tone_notes():
    assert builder.identify(["D", "Ed", "F", "G"])["arabic"] == [
        "Bayati", "Husseini", "Bayati Shuri"]


def test_identify_plain_notes_includes_arabic_equivalents():
    result = builder.identify(["D", "Eb", "F#", "G"])
    assert result["arabic"] == ["Hijaz", "Hijaz Kar"]


def test_dromos_tips_mention_arabic_practice():
    tip = next(t for t in builder.dromos_tips("ousak") if t.degree == 2)
    assert "Arabic Bayati" in tip.text


def test_cli_arabic(capsys):
    assert main(["arabic", "saba"]) == 0
    out = capsys.readouterr().out
    assert "Turkish Saba" in out and "Greek Sabah" in out
    assert main(["identify", "C", "D", "Ed"]) == 0
    assert "Arabic: Rast" in capsys.readouterr().out
