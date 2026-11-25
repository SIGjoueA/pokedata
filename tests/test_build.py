"""Sanity tests on the built database and the exported API (stdlib unittest)."""
import json, os, sqlite3, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from common import BUILD, LANGS, ROOT

API = ROOT / "site" / "api" / "v1"


class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = sqlite3.connect(BUILD / "pokedata.sqlite")

    def one(self, sql, *a):
        return self.db.execute(sql, a).fetchone()[0]

    def test_integrity(self):
        self.assertEqual(self.one("PRAGMA integrity_check"), "ok")
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_species(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM species"), 1025)
        self.assertEqual(self.one("SELECT MIN(id) || '-' || MAX(id) FROM species"), "1-1025")

    def test_each_species_has_one_default_form(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM (SELECT species_id FROM form WHERE is_default=1 GROUP BY species_id HAVING COUNT(*)=1)"), 1025)

    def test_names_follow_game_language(self):
        # every species has a name in every language of every game it appears in
        missing = self.db.execute("""
            SELECT DISTINCT f.species_id, gl.language_id FROM form_game fg JOIN form f ON f.id=fg.form_id
            JOIN game_language gl ON gl.game_id=fg.game_id
            WHERE gl.language_id IN (%s) AND NOT EXISTS (SELECT 1 FROM translation t WHERE t.entity_type='species'
              AND t.entity_id=CAST(f.species_id AS TEXT) AND t.field='name' AND t.language_id=gl.language_id)""" % ",".join("?" * len(LANGS)), LANGS).fetchall()
        self.assertEqual(missing, [])

    def test_known_values(self):
        r = self.db.execute("SELECT type1_id, type2_id, hp, atk, def, spa, spd, spe FROM form_game WHERE form_id='6' AND game_id='sv'").fetchone()
        self.assertEqual(r, ("fire", "flying", 78, 84, 78, 109, 85, 100))
        r = self.db.execute("SELECT type1_id, type2_id FROM form_game WHERE form_id='35' AND game_id='rb'").fetchone()
        self.assertEqual(r, ("normal", None))  # Clefairy is Normal before gen 6
        fr = self.one("SELECT text FROM translation WHERE entity_type='species' AND entity_id='25' AND field='name' AND language_id='fr'")
        self.assertEqual(fr, "Pikachu")

    def test_every_value_is_verified(self):
        for t, col in (("form_game", "stats"), ("form_game", "types")):
            n = self.one("SELECT COUNT(*) FROM form_game")
            v = self.one("SELECT COUNT(*) FROM verification WHERE table_name=? AND column_name=?", t, col)
            self.assertEqual(n, v)
        # disputed / seeded values stay in the provenance tables but never reach the data tables
        self.assertEqual(self.one("""SELECT COUNT(*) FROM translation t JOIN verification v ON v.table_name='translation'
            AND v.row_key=json_array(t.entity_type, t.entity_id, t.field, t.language_id, t.game_id, t.version_id)
            AND v.status IN ('disputed','seeded')"""), 0)
        self.assertEqual(self.one("""SELECT COUNT(*) FROM verification v WHERE v.status IN ('disputed','seeded')
            AND v.table_name NOT IN ('translation','pokedex_entry','move_game','machine')"""), 0)

    def test_no_wiki_prose(self):
        # only in-game strings: names, categories (genus), form names, in-game descriptions
        self.assertEqual(self.one("SELECT COUNT(*) FROM translation WHERE field NOT IN ('name','genus','form_name','flavor')"), 0)
        # categories are stored as the game-text string (PokeAPI), the wiki word list is only a cross-check
        self.assertEqual(self.one("""SELECT COUNT(*) FROM translation t WHERE t.field='genus' AND NOT EXISTS (
            SELECT 1 FROM citation c JOIN source_document d ON d.id=c.document_id WHERE c.table_name='translation'
            AND c.row_key=json_array(t.entity_type, t.entity_id, t.field, t.language_id, t.game_id, t.version_id)
            AND d.source_id='pokeapi' AND c.agrees=1)"""), 0)

    def test_evolutions(self):
        # Pikachu → Raichu with a Thunder Stone in Scarlet/Violet; Eevee → Sylveon needs a Fairy move + affection
        r = self.db.execute("""SELECT m.trigger, i.slug FROM evolution e JOIN evolution_method m ON m.evolution_id=e.id
            LEFT JOIN item i ON i.id=m.item_id WHERE e.from_form_id='25' AND e.to_form_id='26' AND m.game_id='sv'""").fetchall()
        self.assertIn(("use-item", "thunder-stone"), r)
        self.assertEqual(self.one("SELECT COUNT(*) FROM evolution e JOIN evolution_method m ON m.evolution_id=e.id WHERE e.to_form_id='700' AND m.known_move_type_id='fairy'") > 0, True)
        self.assertEqual(self.one("SELECT COUNT(*) FROM species WHERE evolution_chain_id IS NULL"), 0)

    def test_regional_dex(self):
        self.assertEqual(self.one("SELECT number FROM pokedex_entry WHERE pokedex_id='sv-paldea' AND species_id=906"), 1)
        self.assertEqual(self.one("SELECT number FROM pokedex_entry WHERE pokedex_id='b2w2-unova' AND species_id=494"), 0)
        self.assertEqual(self.one("SELECT COUNT(*) FROM pokedex_entry WHERE pokedex_id='rb-kanto'"), 151)


class Api(unittest.TestCase):
    def test_index(self):
        idx = json.loads((API / "index.json").read_text("utf-8"))
        self.assertEqual(idx["api_version"], "v1")
        self.assertEqual(idx["counts"]["species"], 1025)

    def test_pokemon(self):
        p = json.loads((API / "pokemon" / "25.json").read_text("utf-8"))
        self.assertEqual(p["names"]["ja"], "ピカチュウ")
        self.assertTrue(any(f["id"] == "25" and f["is_default"] for f in p["forms"]))
        self.assertTrue((API / "form" / "25-alola-cap.json").exists() or (API / "form" / "26-alola.json").exists())

    def test_phase1b(self):
        p = json.loads((API / "pokemon" / "25.json").read_text("utf-8"))
        self.assertEqual(p["genus"]["en"], "Mouse Pokémon")
        self.assertEqual(p["pokedex_numbers"]["rb-kanto"], 25)
        c = json.loads((API / "evolution" / f"{p['evolution_chain']}.json").read_text("utf-8"))
        self.assertTrue(any(e["from"] == "25" and e["to"] == "26" for e in c["evolutions"]))
        d = json.loads((API / "pokedex" / "sv-paldea.json").read_text("utf-8"))
        self.assertEqual(d["entries"][0], [1, 906])

    def test_search(self):
        s = json.loads((API / "search" / "fr.json").read_text("utf-8"))
        self.assertIn(["pikachu", "Pikachu", 25], s)


if __name__ == "__main__":
    unittest.main()
