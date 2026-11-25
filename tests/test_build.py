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
        fr = self.one("SELECT text FROM translation WHERE entity_type='species' AND entity_id='25' AND language_id='fr'")
        self.assertEqual(fr, "Pikachu")

    def test_every_value_is_verified(self):
        for t, col in (("form_game", "stats"), ("form_game", "types")):
            n = self.one("SELECT COUNT(*) FROM form_game")
            v = self.one("SELECT COUNT(*) FROM verification WHERE table_name=? AND column_name=?", t, col)
            self.assertEqual(n, v)
        self.assertEqual(self.one("SELECT COUNT(*) FROM verification WHERE status IN ('disputed','seeded')"), 0)

    def test_no_wiki_prose(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM translation WHERE field NOT IN ('name')"), 0)


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

    def test_search(self):
        s = json.loads((API / "search" / "fr.json").read_text("utf-8"))
        self.assertIn(["pikachu", "Pikachu", 25], s)


if __name__ == "__main__":
    unittest.main()
