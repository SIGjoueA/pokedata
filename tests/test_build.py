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

    def test_learnsets(self):
        # schema 1.1.0: one verification per set (form × game × method), every published set is verified
        self.assertEqual(self.one("""SELECT COUNT(*) FROM (SELECT DISTINCT form_id, game_id, method_id FROM learnset) s
            WHERE NOT EXISTS (SELECT 1 FROM verification v WHERE v.table_name='learnset'
            AND v.row_key=json_array(s.form_id, s.game_id, s.method_id) AND v.column_name='*'
            AND v.status IN ('game-data','unanimous','majority','manual','single-source'))"""), 0)
        self.assertEqual(self.one("SELECT COUNT(*) FROM verification WHERE table_name='learnset' AND json_array_length(row_key)<>3"), 0)
        has = lambda f, g, m, mv: self.one("SELECT COUNT(*) FROM learnset WHERE form_id=? AND game_id=? AND method_id=? AND move_id=?", f, g, m, mv) > 0
        self.assertTrue(has("6", "sw", "machine", 53))       # Charizard: Flamethrower is TR02 in Sword/Shield
        self.assertTrue(has("25", "e", "tutor", 9))          # Pikachu: Thunder Punch from an Emerald tutor
        self.assertTrue(has("25", "frlg", "tutor", 34))      # Body Slam from a FireRed/LeafGreen tutor
        self.assertFalse(has("25", "frlg", "tutor", 9))      # …but no Thunder Punch tutor in FR/LG
        self.assertTrue(has("25", "pt", "tutor", 9))         # Platinum tutors
        self.assertTrue(has("1", "dp", "machine", 15))       # HM01 Cut
        self.assertTrue(has("3", "xy", "tutor", 338))        # Frenzy Plant (X/Y tutor)
        self.assertEqual(self.one("SELECT level FROM learnset WHERE form_id='1' AND game_id='rb' AND method_id='level-up' AND move_id=33"), 1)
        self.assertGreater(self.one("SELECT COUNT(*) FROM learnset WHERE form_id='25' AND game_id='la' AND method_id='mastery'"), 0)

    def test_migrations(self):
        # 0001 + later migrations give the same tables, columns and indexes as schema.sql (0002 changes conventions only)
        def struct(scripts):
            d = sqlite3.connect(":memory:")
            for sc in scripts:
                d.executescript(sc)
            return sorted(d.execute("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall())
        mig = sorted((ROOT / "db" / "migrations").glob("*.sql"))
        self.assertEqual([p.name[:4] for p in mig], [f"{i:04d}" for i in range(1, len(mig) + 1)])
        strip = lambda rows: [(t, n, " ".join(l.split("--")[0] for l in (q or "").splitlines()).replace(f'"{n}"', n).split()) for t, n, q in rows]
        self.assertEqual(strip(struct([mig[0].read_text("utf-8")] + [p.read_text("utf-8") for p in mig[1:]])),
                         strip(struct([(ROOT / "db" / "schema.sql").read_text("utf-8")])))
        self.assertEqual(self.one("SELECT value FROM meta WHERE key='schema_version'"), "1.3.0")
        d = sqlite3.connect(":memory:")   # 0004 only widens the CHECK: a form-change row is accepted after the migrations
        for p in mig: d.executescript(p.read_text("utf-8"))
        d.execute("PRAGMA foreign_keys = OFF")
        d.execute("INSERT INTO availability (form_id, version_id, status) VALUES ('x', 'y', 'form-change')")


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

    def test_phase2(self):
        idx = json.loads((API / "index.json").read_text("utf-8"))
        if not idx["counts"].get("moves"):
            self.skipTest("phase 2 not built")
        m = json.loads((API / "move" / "85.json").read_text("utf-8"))   # Thunderbolt
        self.assertEqual(m["names"]["fr"], "Tonnerre")
        self.assertEqual(m["games"]["sv"]["power"], 90)
        self.assertEqual(m["games"]["rb"]["power"], 95)                 # 95 before Generation VI
        self.assertEqual(m["games"]["sv"]["damage_class"], "special")
        self.assertEqual(m["machines"]["rb"], "TM24")
        self.assertEqual(m["machines"]["sv"], "TM126")
        self.assertEqual(json.loads((API / "move" / "33.json").read_text("utf-8"))["games"]["rb"]["accuracy"], 95)
        db = sqlite3.connect(BUILD / "pokedata.sqlite")   # Yanma → Yanmega knowing Ancient Power: the condition now points to the move table
        self.assertIn((246,), db.execute("SELECT m.known_move_id FROM evolution e JOIN evolution_method m ON m.evolution_id=e.id WHERE e.to_form_id='469'").fetchall())

    def test_learnset_api(self):
        idx = json.loads((API / "index.json").read_text("utf-8"))
        self.assertIn("learnset", idx["endpoints"])
        ls = json.loads((API / "learnset" / "25.json").read_text("utf-8"))
        self.assertIn([85, 0], ls["games"]["sv"]["machine"])   # Pikachu: Thunderbolt by TM in Scarlet/Violet
        self.assertTrue(all(len(e) in (2, 3) for g in ls["games"].values() for m in g.values() for e in m))

    def test_phase3(self):
        db = sqlite3.connect(BUILD / "pokedata.sqlite")
        q = lambda sql, *a: db.execute(sql, a).fetchall()
        if not q("SELECT 1 FROM encounter LIMIT 1"):
            self.skipTest("phase 3 not built")
        # every (area, version, method) set of encounters is verified as a whole (convention A)
        self.assertEqual(q("""SELECT COUNT(*) FROM (SELECT DISTINCT area_id, version_id, method_id FROM encounter) e
            WHERE NOT EXISTS (SELECT 1 FROM verification v WHERE v.table_name='encounter'
              AND v.row_key=json_array(e.area_id, e.version_id, e.method_id))"""), [(0,)])
        self.assertEqual(q("SELECT COUNT(*) FROM availability a WHERE NOT EXISTS (SELECT 1 FROM verification v WHERE v.table_name='availability' AND v.row_key=json_array(a.form_id, a.version_id, a.status))"), [(0,)])
        # Kanto Route 3 and Hoenn Route 3 are distinct places
        self.assertTrue(q("SELECT 1 FROM location WHERE id='kanto-route-3'"))
        self.assertFalse(q("SELECT 1 FROM location WHERE id='route-3'"))
        # Pikachu in Viridian Forest (Red), levels 3–5
        self.assertIn((3, 5), q("SELECT min_level, max_level FROM encounter WHERE form_id='25' AND version_id='red' AND area_id='viridian-forest' AND method_id='walk'"))
        # Lickitung traded for Slowbro on Route 18 (Red)
        self.assertEqual(q("SELECT json_extract(extra,'$.gives_species_id') FROM encounter WHERE form_id='108' AND version_id='red' AND method_id='npc-trade'"), [(80,)])
        self.assertIn(("event",), q("SELECT status FROM availability WHERE form_id='151' AND version_id='red'"))
        self.assertIn(("trade-version-exclusive",), q("SELECT status FROM availability WHERE form_id='123' AND version_id='blue'"))   # Scyther: Red only
        self.assertIn(("transfer", "time-capsule:rb,y"), q("SELECT status, detail FROM availability WHERE form_id='1' AND version_id='gold'"))
        self.assertEqual(q("SELECT COUNT(*) FROM availability WHERE form_id LIKE '201-%' AND version_id='gold' AND status='wild'"), [(25,)])   # every Unown letter
        self.assertEqual(q("SELECT DISTINCT json_extract(extra,'$.shiny') FROM encounter WHERE form_id='130' AND area_id='lake-of-rage' AND method_id='static'"), [("always",)])
        # schema 1.2.0: in-game trades have their own status; Raichu in Yellow needs a trade (the starter Pikachu cannot evolve)
        self.assertIn(("npc-trade",), q("SELECT status FROM availability WHERE form_id='108' AND version_id='red'"))
        self.assertFalse(q("SELECT 1 FROM availability WHERE status='gift' AND ',' || detail || ',' LIKE '%,npc-trade,%'"))
        self.assertEqual(q("SELECT status, detail FROM availability WHERE form_id='26' AND version_id='yellow' ORDER BY status"),
                         [("trade-version-exclusive", "from:rb"), ("transfer", "time-capsule:c,gs")])
        games = {r[0] for r in q("SELECT DISTINCT v.game_id FROM encounter e JOIN version v ON v.id=e.version_id")}
        if "rs" in games:   # lot 2: generation 3 (the met location stored by the game)
            self.assertEqual(q("SELECT min_level, max_level FROM encounter WHERE form_id='261' AND version_id='ruby' AND area_id='hoenn-route-101' AND method_id='walk'"), [(2, 3)])
            self.assertEqual(q("SELECT area_id FROM encounter WHERE form_id='349' AND version_id='ruby' AND method_id='feebas-tile-fishing'"), [("hoenn-route-119",)])
            self.assertEqual(q("SELECT area_id FROM encounter WHERE form_id='101' AND version_id='ruby' AND method_id='static'"), [("team-magma-hideout",)])
            self.assertIn(("event",), q("SELECT status FROM availability WHERE form_id='386-attack' AND version_id='firered'"))   # Aurora Ticket
            self.assertEqual(q("SELECT json_extract(extra,'$.access') FROM encounter WHERE form_id='386-attack' AND version_id='firered'"), [("event-item",)])
            self.assertEqual(q("SELECT detail FROM availability WHERE form_id='252' AND version_id='firered' AND status='trade-version-exclusive'"), [("from:e,rs",)])
            self.assertEqual(q("SELECT odds FROM shiny_rule WHERE game_id='rs' AND method='base'"), [("1/8192",)])
            self.assertTrue(q("SELECT 1 FROM location WHERE id='underwater-route-124' AND pokeapi_id IS NULL"))   # created from the game's list
        if "dp" in games:   # lot 3: generation 4
            self.assertEqual(q("SELECT min_level, max_level FROM encounter WHERE form_id='396' AND version_id='diamond' AND area_id='sinnoh-route-201' AND method_id='walk'"), [(2, 3)])
            self.assertEqual(q("SELECT area_id, min_level FROM encounter WHERE form_id='483' AND version_id='diamond' AND method_id='static'"), [("spear-pillar", 47)])
            self.assertIn(("transfer", "pal-park:rs,e,frlg"), q("SELECT status, detail FROM availability WHERE form_id='252' AND version_id='diamond'"))
            self.assertTrue(q("SELECT 1 FROM availability a JOIN version v ON v.id=a.version_id WHERE v.game_id='hgss' AND status='gift' AND detail='pokewalker'"))
            self.assertIn(("event",), q("SELECT status FROM availability WHERE form_id='493' AND version_id='diamond'"))   # Mystery Gift (PKHeX MGDB)
            self.assertEqual(q("SELECT odds FROM shiny_rule WHERE game_id='hgss' AND method='base'"), [("1/8192",)])
        if "bw" in games:   # lot 4: generation 5
            self.assertIn(("transfer", "poke-transfer:dp,pt,hgss"), q("SELECT status, detail FROM availability WHERE form_id='387' AND version_id='black'"))
            self.assertEqual(q("SELECT odds FROM shiny_rule WHERE game_id='b2w2' AND method='shiny-charm'"), [("3/8192",)])
            self.assertEqual(q("SELECT area_id, json_extract(extra,'$.shiny') FROM encounter WHERE form_id='612' AND version_id='black-2' AND method_id='static'"), [("nature-preserve", "always")])
            self.assertEqual(q("SELECT json_extract(extra,'$.access') FROM encounter WHERE form_id='494' AND version_id='black'"), [("event-item",)])   # Liberty Pass
            self.assertTrue(q("SELECT 1 FROM encounter_condition_link WHERE condition_id='swarm-yes'"))
        if "xy" in games:   # lot 5: generation 6
            self.assertTrue(q("SELECT 1 FROM encounter WHERE form_id='557' AND version_id='x' AND area_id='ambrette-town' AND method_id='rock-smash'"))
            self.assertTrue(q("SELECT 1 FROM encounter WHERE version_id='omega-ruby' AND method_id='dexnav'"))
            self.assertTrue([d for (d,) in q("SELECT detail FROM availability WHERE form_id='252' AND version_id='x' AND status='transfer'") if d.startswith("poke-bank:")])
            self.assertEqual(q("SELECT odds FROM shiny_rule WHERE game_id='xy' AND method='base'"), [("1/4096",)])
        if "sm" in games:   # lot 6: generation 7 + Let's Go
            self.assertTrue(q("SELECT 1 FROM encounter WHERE version_id='sun' AND method_id='sos'"))
            self.assertTrue(q("SELECT 1 FROM shiny_lock WHERE form_id='789' AND game_id='sm'"))   # Cosmog
            self.assertTrue(q("SELECT 1 FROM shiny_lock WHERE form_id='25-starter' AND game_id='lgpe'"))
            self.assertFalse(q("SELECT 1 FROM availability a JOIN version v ON v.id=a.version_id WHERE v.game_id='lgpe' AND status='breed'"))
            self.assertTrue(q("SELECT 1 FROM location WHERE id='ultra-desert'"))
        if "sw" in games:   # lot 7: generation 8, Isle of Armor / Crown Tundra, BDSP, Legends: Arceus
            self.assertTrue(q("SELECT 1 FROM encounter WHERE version_id='the-isle-of-armor-sword'"))
            self.assertFalse(q("SELECT 1 FROM encounter WHERE version_id='sword' AND form_id='145-galar'"))   # Crown Tundra quest
            self.assertTrue(q("SELECT 1 FROM shiny_lock WHERE form_id='888' AND game_id='sw'"))
            self.assertFalse(q("SELECT 1 FROM availability a JOIN version v ON v.id=a.version_id WHERE v.game_id='la' AND status='breed'"))
            self.assertTrue(q("SELECT 1 FROM encounter e JOIN version v ON v.id=e.version_id WHERE v.game_id='bdsp' AND e.area_id='mt-coronet'"))
        # schema 1.3.0: forms reached by a change of form
        fc = dict(q("SELECT detail, COUNT(*) FROM availability WHERE status='form-change' GROUP BY detail"))
        for k in ("gender", "mega", "battle", "item-or-action"): self.assertTrue(fc.get(k), k)
        self.assertIn(("form-change", "mega"), q("SELECT status, detail FROM availability WHERE form_id='6-mega-x' AND version_id='x'"))
        self.assertIn(("form-change", "item-or-action"), q("SELECT status, detail FROM availability WHERE form_id='479-wash' AND version_id='platinum'"))
        self.assertFalse(q("SELECT 1 FROM availability WHERE status='form-change' AND form_id LIKE '%-totem%'"))
        self.assertFalse(q("SELECT 1 FROM availability WHERE status='form-change' AND form_id='6-mega-x' AND version_id='scarlet'"))
        if "sv" in games:   # lot 8: generation 9 + DLC, Legends: Z-A + Mega Dimension
            self.assertTrue(q("SELECT 1 FROM encounter e JOIN version v ON v.id=e.version_id WHERE v.game_id='svmask'"))
            self.assertFalse(q("SELECT 1 FROM encounter e JOIN version v ON v.id=e.version_id WHERE v.game_id='sv' AND e.form_id='144'"))   # Snacksworth (The Indigo Disk)
            self.assertTrue(q("SELECT 1 FROM encounter e JOIN version v ON v.id=e.version_id WHERE v.game_id='svdisk' AND e.form_id='144'"))
            self.assertTrue(q("SELECT 1 FROM encounter e JOIN version v ON v.id=e.version_id WHERE v.game_id='zadlc'"))
            self.assertFalse(q("SELECT 1 FROM availability a JOIN version v ON v.id=a.version_id WHERE v.game_id='za' AND status='breed'"))
        self.assertEqual(q("SELECT odds FROM shiny_rule WHERE game_id='gs' AND method='base'"), [("1/8192",)])
        # place names follow game_language for the games covered
        self.assertEqual(q("""SELECT COUNT(*) FROM location_game lg JOIN game_language gl ON gl.game_id=lg.game_id
            WHERE lg.game_id IN ('gs','c') AND NOT EXISTS (SELECT 1 FROM translation t WHERE t.entity_type='location'
              AND t.entity_id=lg.location_id AND t.field='name' AND t.language_id=gl.language_id
              AND (t.game_id=lg.game_id OR t.game_id IS NULL))"""), [(0,)])
        g = json.loads((API / "location" / "gs.json").read_text("utf-8"))
        self.assertTrue(any(l["id"] == "johto-route-32" for l in g["locations"]))
        p = json.loads((API / "pokemon" / "25" / "locations.json").read_text("utf-8"))
        self.assertEqual(p["forms"]["25"]["red"]["game"], "rb")

    def test_search(self):
        s = json.loads((API / "search" / "fr.json").read_text("utf-8"))
        self.assertIn(["pikachu", "Pikachu", 25], s)


if __name__ == "__main__":
    unittest.main()
