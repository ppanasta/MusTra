"""Songs from the literature, used to seed the song database.

Every entry names where its dromos/makam attribution comes from.  Most Greek
attributions come from community repertoire lists compiled by rebetiko
musicians, not from peer-reviewed musicology. Treat them as starting points:
the app lets users report a wrong attribution and suggest better songs.

Fields: title, artist, year, rhythm, key, kind ("dromos"/"makam"), scale key,
source label, source URL.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeedSong:
    title: str
    artist: str
    year: int | None
    rhythm: str
    key: str
    kind: str
    scale: str
    source: str
    url: str


# -- sources ----------------------------------------------------------------
KITHARA = ("Λαϊκοί Δρόμοι — Ρεπερτόριο 164 τραγουδιών (kithara.gr forum list)",
           "https://forum.kithara.gr/index.php?topic=84181.0")
REMBETIKO_170 = ("170 τίτλοι των λαϊκών μας δρόμων (rembetiko.gr forum list)",
                 "https://rembetiko.gr/t/170-%CF%84%CE%AF%CF%84%CE%BB%CE%BF%CE%B9-"
                 "%CF%84%CF%89%CE%BD-%CE%BB%CE%B1%CF%8A%CE%BA%CF%8E%CE%BD-%CE%BC%CE%B1"
                 "%CF%82-%CE%B4%CF%81%CF%8C%CE%BC%CF%89%CE%BD/10892")
KLIKA = ("Δρόμος Χιτζάζ — η κλίκα", "https://klika.gr/index.php/peri-mousikis/"
         "mousiki-paideia/186-dromos-xitzaz.html")
BOUZOUKI_BLOG = ("Τρίχορδο μπουζούκι — ρεμπέτικα τραγούδια (blog)",
                 "https://bouzouki3coursebaglamasrebetikosongs.blogspot.com/2015/")
MISIRLOU = ("Carmelo Siciliano — Misirlou (Roubanis)",
            "https://www.carmelosiciliano.com/misirlou-roubanis/")
KATIBIM = ("Wikipedia — Kâtibim", "https://en.wikipedia.org/wiki/K%C3%A2tibim")
NOBEL = ("Nobel Medicus 63 (academic article on makam use)",
         "https://www.nobelmedicus.com/Content/journal/63/220-227.pdf")
TDV_KARCIGAR = ("TDV İslâm Ansiklopedisi — Karcığar",
                "https://islamansiklopedisi.org.tr/karcigar")
EKSI_KARCIGAR = ("Ekşi Sözlük — karcığar", "https://eksisozluk.com/karcigar--455931")
SALIHBORA_HICAZ = ("SalihBora.com — Hicâz makâmındaki eserler",
                   "https://www.salihbora.com/makam/hicaz/")
SALIHBORA_SABA = ("SalihBora.com — Sabâ makâmındaki eserler",
                  "https://www.salihbora.com/makam/saba/")
SALIHBORA_RAST = ("SalihBora.com — Rast makâmındaki eserler",
                  "https://www.salihbora.com/makam/rast/")
RENGI = ("Kültür ve Yaşam — Türk Müziğinin Rengi 8 Makam",
         "https://kulturveyasam.com/turk-muziginin-rengi-8-makam/")
KLARNETPARK_USSAK = ("Klarnetpark — Uşşak makamı", "https://www.klarnetpark.com/ussak-makami/")
GITAREGITIM_KURDI = ("Gitareğitim.net — Gitar ve makamsal diziler: Kürdi",
                     "https://www.gitaregitim.net/gitar-ve-makamsal-diziler-kurdi/")
HUSEYNI_SEMAI = ("Şarkılar Notalar — Hüseyni Saz Semaisi",
                 "https://sarkilarnotalar.blogspot.com/2011/11/huseyni-saz-semaisi.html")
CARGAH_MEDIPOL = ("Medipol — Çargâh makamı (Hanefi Özbek)",
                  "https://www.medipol.edu.tr/sites/default/files/document/"
                  "SD_47_98-101.sayfalar_Hanefi_Ozbek.pdf")


def _s(title, artist, year, rhythm, key, kind, scale, source):
    return SeedSong(title, artist, year, rhythm, key, kind, scale, *source)


SEED_SONGS: tuple[SeedSong, ...] = (
    # -- Greek dromoi -------------------------------------------------------
    _s("Το κουτσαβάκι", "Ανέστης Δελιάς", 1936, "Ζεϊμπέκικο", "Ρε", "dromos", "hitzaz", KITHARA),
    _s("Καρδιά παραπονιάρα", "Απόστολος Χατζηχρήστος", 1950, "Ζεϊμπέκικο", "Σολ",
       "dromos", "hitzaz", KITHARA),
    _s("Σε διώξαν απ' την Κοκκινιά", "Βασίλης Τσιτσάνης", 1950, "Ζεϊμπέκικο", "Ντο♯",
       "dromos", "hitzaz", KITHARA),
    _s("Δε ρωτώ ποια είσαι", "Βασίλης Τσιτσάνης", 1966, "Χασάπικο", "Ντο",
       "dromos", "hitzaz", KITHARA),
    _s("Νύχτωσε χωρίς φεγγάρι", "", None, "", "", "dromos", "hitzaz", KLIKA),
    _s("Φεγγάρι χλωμό", "", None, "", "", "dromos", "hitzaz", KLIKA),

    _s("Ο χαρμάνης", "Μάρκος Βαμβακάρης", 1933, "Χασάπικο", "Ρε",
       "dromos", "hitzazkiar", KITHARA),
    _s("Χρόνια μες στην Τρούμπα", "", None, "", "", "dromos", "hitzazkiar", KLIKA),
    _s("Άτακτη", "", None, "", "", "dromos", "hitzazkiar", KLIKA),
    _s("Μισιρλού (Misirlou)", "Τέτος Δημητριάδης (rec.)", 1927, "", "",
       "dromos", "hitzazkiar", MISIRLOU),

    _s("Εγώ μάγκας φαινόμουνα", "Μιχάλης Γενίτσαρης", 1936, "Ζεϊμπέκικο", "Ρε",
       "dromos", "ousak", KITHARA),
    _s("Δε θέλω άλλα γιατρικά", "Γιάννης Παπαϊωάννου", 1949, "Ζεϊμπέκικο", "Φα",
       "dromos", "ousak", KITHARA),
    _s("Εγώ είμαι ένα παλιόπαιδο", "Γαβαλάς", 1961, "Ζεϊμπέκικο", "Σολ",
       "dromos", "ousak", KITHARA),
    _s("Λέου λέου", "Αδέσποτο", None, "Ζεϊμπέκικο", "Λα", "dromos", "ousak", KITHARA),

    _s("Τα τάληρα", "Αδέσποτο", None, "Ζεϊμπέκικο", "Μι", "dromos", "sabah", KITHARA),
    _s("Πες μου ζωή τι φταίξαμε", "Μίμης Πλέσσας", 1972, "Ζεϊμπέκικο", "Σι",
       "dromos", "sabah", KITHARA),
    _s("Ήσουνα ξυπόλητη", "", None, "", "", "dromos", "sabah", REMBETIKO_170),

    _s("Καημό μες στην καρδούλα μου", "", None, "", "", "dromos", "houzam", REMBETIKO_170),
    _s("Η γάτα", "", None, "", "", "dromos", "houzam", REMBETIKO_170),

    _s("Μες στου Βάβουλα τη γούβα", "Κερομύτης", 1937, "Ζεϊμπέκικο", "Ρε",
       "dromos", "rast", KITHARA),
    _s("Χαρικλάκι", "", None, "", "", "dromos", "rast", REMBETIKO_170),
    _s("Αλεξανδριανή φελλάχα", "", None, "", "", "dromos", "rast", REMBETIKO_170),
    _s("Συννεφιασμένη Κυριακή", "Βασίλης Τσιτσάνης", None, "", "", "dromos", "rast",
       REMBETIKO_170),

    _s("Άσε με, άσε με", "Γιάννης Παπαϊωάννου", 1950, "Ζεϊμπέκικο", "Ρε",
       "dromos", "kiourdi", KITHARA),
    _s("Μη με πεισματώνεις", "Μάρκος Βαμβακάρης", 1938, "Χασαποσέρβικο", "Ρε",
       "dromos", "kiourdi", KITHARA),
    _s("Αθηναίισσα", "Ανέστης Δελιάς", 1937, "Ζεϊμπέκικο", "Ρε",
       "dromos", "kiourdi", KITHARA),

    _s("Περιπλανώμενη ζωή", "", None, "", "", "dromos", "karsigar", REMBETIKO_170),
    _s("Μοίρα με καταδίκασες", "", None, "", "", "dromos", "karsigar", REMBETIKO_170),
    _s("Για να σε κάνω άνθρωπο", "", None, "", "", "dromos", "karsigar", REMBETIKO_170),

    _s("Θέλω στα μπουζούκια", "", None, "", "", "dromos", "segah", REMBETIKO_170),
    _s("Τα μάτια σου τα αράπικα", "", None, "", "", "dromos", "segah", REMBETIKO_170),
    _s("Όταν καπνίζει ο λουλάς", "", None, "", "", "dromos", "segah", REMBETIKO_170),

    _s("Δεν έχω βγάλει το σχολείο", "", None, "", "", "dromos", "neveser", REMBETIKO_170),

    _s("Χρόνια στον Περαία", "", None, "", "", "dromos", "piraeus", REMBETIKO_170),
    _s("Ένας μάγκας στον τεκέ μου", "", None, "", "", "dromos", "piraeus", REMBETIKO_170),

    _s("Μη μου ξαναφύγεις πια", "Βασίλης Τσιτσάνης", None, "Ζεϊμπέκικο", "Ρε",
       "dromos", "minore", BOUZOUKI_BLOG),
    _s("Μαύρα μάτια, μαύρα φρύδια", "Μάρκος Βαμβακάρης", None, "Χασάπικο", "Ρε",
       "dromos", "minore", BOUZOUKI_BLOG),
    _s("Δεν είσαι πια γυναίκα μου", "Μητσάκης", 1949, "Χασάπικο", "Λα",
       "dromos", "minore", KITHARA),

    _s("Ατελείωτο (σόλο)", "Βασίλης Τσιτσάνης", None, "Χασαποσέρβικο", "Ρε",
       "dromos", "matzore", BOUZOUKI_BLOG),

    # -- Turkish makams -----------------------------------------------------
    _s("Kâtibim (Üsküdar'a gider iken)", "İstanbul türküsü", None, "Nim Sofyan", "",
       "makam", "nihavend", KATIBIM),
    _s("Kara bulutları kaldır aradan", "Sadettin Kaynak", None, "", "",
       "makam", "karcigar", EKSI_KARCIGAR),
    _s("O mâhtâbı aceb gösterir mi bana felek", "Hammâmîzâde İsmail Dede", None, "", "",
       "makam", "karcigar", TDV_KARCIGAR),
    _s("Bir gece ansızın gelebilirim", "Rüştü Şardağ", None, "", "",
       "makam", "rast", RENGI),
    _s("Hasretin onulmaz bir yara bende", "Ferit Sıdal", None, "", "",
       "makam", "rast", SALIHBORA_RAST),
    _s("El çek tabib el çek yaram üstünden", "", None, "", "", "makam", "hicaz", NOBEL),
    _s("Kara sevda gibi ruhumda duran gözlerine", "Selâhattin Pınar", None, "Aksak", "",
       "makam", "hicaz", SALIHBORA_HICAZ),
    _s("Bırakıp gittiğin akşam beni ey şûh-i şenim", "Zeki Ârif Ataergin", None, "", "",
       "makam", "hicaz", SALIHBORA_HICAZ),
    _s("Açmam açamam söyleyemem", "", None, "", "", "makam", "huzzam", NOBEL),
    _s("Bu akşam yine sensiz yollarda ağladım durdum", "Şükrü Tunar", None, "Aksak", "",
       "makam", "saba", SALIHBORA_SABA),
    _s("Bezm-i gamını sahn-ı gülistâna değişmem", "Neyzen Rızâ Bey", None,
       "Yürük semâî", "", "makam", "saba", SALIHBORA_SABA),
    _s("Bu aşkın ızdırâbı bilmem ne zaman biter", "Zeki Müren", None, "Curcuna", "",
       "makam", "saba", SALIHBORA_SABA),
    _s("Akşam oldu hüzünlendim ben yine", "", None, "", "", "makam", "ussak",
       KLARNETPARK_USSAK),
    _s("Bu akşam gün batarken gel", "", None, "", "", "makam", "ussak", KLARNETPARK_USSAK),
    _s("Fikrimin ince gülü", "", None, "", "", "makam", "kurdi", GITAREGITIM_KURDI),
    _s("Hüseyni Saz Semaisi", "Lavtacı Andon", None, "Saz semâisi", "",
       "makam", "huseyni", HUSEYNI_SEMAI),
    _s("Çargâh Saz Semâisi", "Cinuçen Tanrıkorur", None, "Saz semâisi", "",
       "makam", "cargah", CARGAH_MEDIPOL),
)
