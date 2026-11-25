"""Hand-maintained reference data (games, versions, regions, languages, sources).

Release dates and languages: Bulbapedia game pages, Nintendo eShop listings and official
press releases (see plan.md §11). Game ids are the Pokédex ids (core.json games[].id).
"""

LANGUAGES = [
    # id, native name, official, order, pokeapi code, note
    ("ja", "日本語", 1, 1, "ja-hrkt", "Japonais, texte en kana (mode par défaut des jeux)."),
    ("en", "English", 1, 2, "en", None),
    ("fr", "Français", 1, 3, "fr", None),
    ("de", "Deutsch", 1, 4, "de", None),
    ("it", "Italiano", 1, 5, "it", None),
    ("es", "Español (España)", 1, 6, "es", "Espagnol d'Espagne."),
    ("es-419", "Español (Latinoamérica)", 1, 7, "es-419", "Seulement pour les jeux qui l'ont : voir game_language."),
    ("ko", "한국어", 1, 8, "ko", None),
    ("zh-Hans", "简体中文", 1, 9, "zh-hans", None),
    ("zh-Hant", "繁體中文", 1, 10, "zh-hant", None),
    ("ja-Jpan", "日本語（漢字）", 0, 11, "ja", "Auxiliaire : mode kanji des jeux japonais."),
    ("ja-Latn", "Rōmaji", 0, 12, "ja-roma", "Auxiliaire : romanisation (marque déposée)."),
]

REGIONS = [("kanto", 1), ("johto", 2), ("hoenn", 3), ("sinnoh", 4), ("unova", 5), ("kalos", 6),
           ("alola", 7), ("galar", 8), ("hisui", 8), ("paldea", 9), ("kitakami", 9), ("blueberry", 9)]
GENERATIONS = [(1, "kanto"), (2, "johto"), (3, "hoenn"), (4, "sinnoh"), (5, "unova"), (6, "kalos"),
               (7, "alola"), (8, "galar"), (9, "paldea")]
# national dex ranges per generation
GEN_RANGES = [(1, 151, 1), (152, 251, 2), (252, 386, 3), (387, 493, 4), (494, 649, 5), (650, 721, 6),
              (722, 809, 7), (810, 905, 8), (906, 1025, 9)]

L_G1 = ["ja", "en", "fr", "de", "it", "es"]
L_G2 = L_G1 + ["ko"]          # Gold/Silver had a Korean release (not Crystal)
L_G4 = L_G1 + ["ko"]
L_G7 = L_G1 + ["ko", "zh-Hans", "zh-Hant"]
L_ALL = L_G7 + ["es-419"]

# id, kind, gen, base, release (first worldwide), platform, order, pokeapi version group, active, name, languages
GAMES = [
    ("rb", "main", 1, None, "1996-02-27", "Game Boy", 10, "red-blue", 0, "Pokémon Rouge / Bleu (Vert au Japon)", L_G1),
    ("y", "main", 1, None, "1998-09-12", "Game Boy", 20, "yellow", 0, "Pokémon Jaune", L_G1),
    ("gs", "main", 2, None, "1999-11-21", "Game Boy Color", 30, "gold-silver", 0, "Pokémon Or / Argent", L_G2),
    ("c", "main", 2, None, "2000-12-14", "Game Boy Color", 40, "crystal", 0, "Pokémon Cristal", L_G1),
    ("rs", "main", 3, None, "2002-11-21", "Game Boy Advance", 50, "ruby-sapphire", 0, "Pokémon Rubis / Saphir", L_G1),
    ("frlg", "remake", 3, None, "2004-01-29", "Game Boy Advance", 60, "firered-leafgreen", 0, "Pokémon Rouge Feu / Vert Feuille", L_G1),
    ("e", "main", 3, None, "2004-09-16", "Game Boy Advance", 70, "emerald", 0, "Pokémon Émeraude", L_G1),
    ("dp", "main", 4, None, "2006-09-28", "Nintendo DS", 80, "diamond-pearl", 0, "Pokémon Diamant / Perle", L_G4),
    ("pt", "main", 4, None, "2008-09-13", "Nintendo DS", 90, "platinum", 0, "Pokémon Platine", L_G4),
    ("hgss", "remake", 4, None, "2009-09-12", "Nintendo DS", 100, "heartgold-soulsilver", 0, "Pokémon Or HeartGold / Argent SoulSilver", L_G4),
    ("bw", "main", 5, None, "2010-09-18", "Nintendo DS", 110, "black-white", 0, "Pokémon Noir / Blanc", L_G4),
    ("b2w2", "main", 5, None, "2012-06-23", "Nintendo DS", 120, "black-2-white-2", 0, "Pokémon Noir 2 / Blanc 2", L_G4),
    ("xy", "main", 6, None, "2013-10-12", "Nintendo 3DS", 130, "x-y", 0, "Pokémon X / Y", L_G4),
    ("oras", "remake", 6, None, "2014-11-21", "Nintendo 3DS", 140, "omega-ruby-alpha-sapphire", 0, "Pokémon Rubis Oméga / Saphir Alpha", L_G4),
    ("sm", "main", 7, None, "2016-11-18", "Nintendo 3DS", 150, "sun-moon", 0, "Pokémon Soleil / Lune", L_G7),
    ("usum", "main", 7, None, "2017-11-17", "Nintendo 3DS", 160, "ultra-sun-ultra-moon", 0, "Pokémon Ultra-Soleil / Ultra-Lune", L_G7),
    ("lgpe", "remake", 7, None, "2018-11-16", "Nintendo Switch", 170, "lets-go-pikachu-lets-go-eevee", 0, "Pokémon : Let's Go, Pikachu / Évoli", L_G7),
    ("sw", "main", 8, None, "2019-11-15", "Nintendo Switch", 180, "sword-shield", 0, "Pokémon Épée / Bouclier", L_G7),
    ("swisle", "dlc", 8, "sw", "2020-06-17", "Nintendo Switch", 190, "the-isle-of-armor", 0, "Épée / Bouclier : L'île solitaire de l'Armure", L_G7),
    ("swcrown", "dlc", 8, "sw", "2020-10-22", "Nintendo Switch", 200, "the-crown-tundra", 0, "Épée / Bouclier : Les terres enneigées de la Couronne", L_G7),
    ("bdsp", "remake", 8, None, "2021-11-19", "Nintendo Switch", 210, "brilliant-diamond-shining-pearl", 0, "Pokémon Diamant Étincelant / Perle Scintillante", L_G7),
    ("la", "legends", 8, None, "2022-01-28", "Nintendo Switch", 220, "legends-arceus", 0, "Légendes Pokémon : Arceus", L_G7),
    ("sv", "main", 9, None, "2022-11-18", "Nintendo Switch", 230, "scarlet-violet", 0, "Pokémon Écarlate / Violet", L_G7),
    ("svmask", "dlc", 9, "sv", "2023-09-13", "Nintendo Switch", 240, "the-teal-mask", 0, "Écarlate / Violet : Le Masque Turquoise", L_G7),
    ("svdisk", "dlc", 9, "sv", "2023-12-14", "Nintendo Switch", 250, "the-indigo-disk", 0, "Écarlate / Violet : Le Disque Indigo", L_G7),
    ("za", "legends", 9, None, "2025-10-16", "Nintendo Switch / Switch 2", 260, "legends-za", 0, "Légendes Pokémon : Z-A", L_ALL),
    ("zadlc", "dlc", 9, "za", "2025-12-10", "Nintendo Switch / Switch 2", 270, "mega-dimension", 0, "Légendes Pokémon : Z-A – Méga-Dimension", L_ALL),
    ("frlgsw", "rerelease", 3, "frlg", "2026-02-27", "Nintendo Switch", 280, None, 0, "Pokémon Rouge Feu / Vert Feuille (Nintendo Switch)", L_G1),
    ("go", "mobile", None, None, "2016-07-06", "iOS / Android", 900, None, 1, "Pokémon GO",
     ["ja", "en", "fr", "de", "it", "es", "ko", "zh-Hant", "es-419"]),
    ("home", "service", None, None, "2020-02-12", "Nintendo Switch / iOS / Android", 910, None, 1, "Pokémon HOME", L_ALL),
    ("champions", "battle", 9, None, "2026-04-08", "Nintendo Switch / iOS / Android", 920, None, 1, "Pokémon Champions", L_ALL),
]
LANG_SINCE = {("go", "es-419"): ("2024-03-18", "0.305.0"), ("home", "es-419"): ("2026-04-02", "4.0.0"),
              ("go", "ko"): ("2017-01-24", None), ("go", "zh-Hant"): ("2017-04-01", None)}

# version id, game, pokeapi id
VERSIONS = [
    ("red", "rb", 1), ("blue", "rb", 2), ("red-japan", "rb", 44), ("green-japan", "rb", 45), ("blue-japan", "rb", 46),
    ("yellow", "y", 3), ("gold", "gs", 4), ("silver", "gs", 5), ("crystal", "c", 6),
    ("ruby", "rs", 7), ("sapphire", "rs", 8), ("emerald", "e", 9), ("firered", "frlg", 10), ("leafgreen", "frlg", 11),
    ("diamond", "dp", 12), ("pearl", "dp", 13), ("platinum", "pt", 14), ("heartgold", "hgss", 15), ("soulsilver", "hgss", 16),
    ("black", "bw", 17), ("white", "bw", 18), ("black-2", "b2w2", 21), ("white-2", "b2w2", 22),
    ("x", "xy", 23), ("y", "xy", 24), ("omega-ruby", "oras", 25), ("alpha-sapphire", "oras", 26),
    ("sun", "sm", 27), ("moon", "sm", 28), ("ultra-sun", "usum", 29), ("ultra-moon", "usum", 30),
    ("lets-go-pikachu", "lgpe", 31), ("lets-go-eevee", "lgpe", 32), ("sword", "sw", 33), ("shield", "sw", 34),
    ("the-isle-of-armor-sword", "swisle", 35), ("the-isle-of-armor-shield", "swisle", 50),
    ("the-crown-tundra-sword", "swcrown", 36), ("the-crown-tundra-shield", "swcrown", 51),
    ("brilliant-diamond", "bdsp", 37), ("shining-pearl", "bdsp", 38), ("legends-arceus", "la", 39),
    ("scarlet", "sv", 40), ("violet", "sv", 41), ("the-teal-mask-scarlet", "svmask", 42), ("the-teal-mask-violet", "svmask", 52),
    ("the-indigo-disk-scarlet", "svdisk", 43), ("the-indigo-disk-violet", "svdisk", 53),
    ("legends-za", "za", 47), ("mega-dimension", "zadlc", 48), ("champions", "champions", 49),
    ("firered-switch", "frlgsw", None), ("leafgreen-switch", "frlgsw", None), ("go", "go", None), ("home", "home", None),
]

SOURCES = [
    # id, name, tier, base_url, license, note
    ("pkhex", "PKHeX.Core (tables personnelles et textes extraits des jeux)", 1, "https://github.com/kwsch/PKHeX",
     "GPL-3.0 (code) ; données de jeu © Nintendo / Game Freak / TPC",
     "Tables personnelles et textes des jeux tels qu'extraits des fichiers de jeu ; lus via le paquet NuGet PKHeX.Core, sans copier son code. Noms de formes : liste éditée par PKHeX, traitée en rang 3."),
    ("bulbapedia", "Bulbapedia", 2, "https://bulbapedia.bulbagarden.net", "CC BY-NC-SA 2.5", "Faits seulement, aucune prose reprise."),
    ("serebii", "Serebii.net", 2, "https://www.serebii.net", "Tous droits réservés", "Faits seulement."),
    ("pokepedia", "Poképédia", 2, "https://www.pokepedia.fr", "CC BY-NC-SA 3.0 FR", "Faits seulement, aucune prose reprise."),
    ("pokeapi", "PokeAPI (CSV)", 3, "https://github.com/PokeAPI/pokeapi", "BSD-3-Clause (code)", "Amorce et correspondance des identifiants."),
    ("showdown", "Pokémon Showdown (data/)", 3, "https://github.com/smogon/pokemon-showdown", "MIT", "Données par génération (mods)."),
    ("official", "Sources officielles (pokemon.com, Nintendo eShop, communiqués)", 4, "https://www.pokemon.com", None, "Dates et langues."),
]

TYPES = ["normal", "fighting", "flying", "poison", "ground", "rock", "bug", "ghost", "steel", "fire", "water",
         "grass", "electric", "psychic", "ice", "dragon", "dark", "fairy"]
TYPE_GEN = {"dark": 2, "steel": 2, "fairy": 6, "stellar": 9}
# Gen 1/2 internal type ids → slug
GB_TYPES = {0: "normal", 1: "fighting", 2: "flying", 3: "poison", 4: "ground", 5: "rock", 7: "bug", 8: "ghost",
            9: "steel", 20: "fire", 21: "water", 22: "grass", 23: "electric", 24: "psychic", 25: "ice", 26: "dragon", 27: "dark"}
GROWTH = {0: "medium-fast", 1: "erratic", 2: "fluctuating", 3: "medium-slow", 4: "fast", 5: "slow"}
GROWTH_FORMULA = {"medium-fast": "n^3", "erratic": "par paliers (600 000 au niv. 100)", "fluctuating": "par paliers (1 640 000 au niv. 100)",
                  "medium-slow": "1.2n^3 - 15n^2 + 100n - 140", "fast": "0.8n^3", "slow": "1.25n^3"}
EGG = {1: "monster", 2: "water1", 3: "bug", 4: "flying", 5: "field", 6: "fairy", 7: "grass", 8: "human-like",
       9: "water3", 10: "mineral", 11: "amorphous", 12: "water2", 13: "ditto", 14: "dragon", 15: "undiscovered"}
