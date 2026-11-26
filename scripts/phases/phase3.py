# Phase 3 — lieux et disponibilité (schéma 1.1.0), lot 1 : 1re et 2e générations (rb, y, gs, c).
# Exécuté par scripts/import_data.py après les phases 1b, 2 et 2b, dans le même espace de noms.
#
# Données de jeu (PKHeX, rang 1) : tables de rencontres (encounters_<gén>.json : emplacements sauvages, rencontres fixes,
#   cadeaux, échanges, œufs, distributions) et noms des lieux de rencontre (locations.json) en 10 langues.
# Contrôles : PokeAPI (rang 3 : locations, location_game_indices, location_names, encounters…), Bulbapedia (rang 2 :
#   « In-game trade », « Gift Pokémon », « Shiny Pokémon ») et Poképédia (rang 2 : « Pokémon chromatique »).
#
# Identifiants de lieu : identifiants PokeAPI (stables, uniques par région : kanto-route-3 ≠ hoenn-route-3).
#   Gén. 2 : le lieu de rencontre est stocké par le jeu (index = location_game_indices gén. 2 de PokeAPI, noms comparés).
#   Gén. 1 : le jeu ne stocke pas de lieu ; PKHeX numérote ses tables par carte, et chaque numéro est rattaché au lieu
#   PokeAPI dont la table (espèces × niveaux, même version, même méthode) est identique, par élimination ; un numéro
#   ambigu n'est pas publié. Les rencontres fixes, cadeaux et échanges de la gén. 1 (sans lieu dans le jeu) et les
#   échanges de la gén. 2 (lieu non stocké) ne sont placés que si PokeAPI et Bulbapedia donnent le même lieu.
# Zones : une zone par lieu (location_area.id = location.id) ; les étages et secteurs de PokeAPI ne sont pas publiés
#   (aucune donnée de jeu ne les distingue dans PKHeX pour ces générations).
# Taux : non publiés dans ce lot (seul PokeAPI les donne par zone ; rang 3 seul).
# Vérification par ensemble (convention A, comme learnset) : row_key = [area_id, version_id, method_id], colonne '*',
#   value_sha256 = empreinte de la liste triée des rencontres ; PokeAPI cité avec l'empreinte de sa propre liste
#   (même projection : forme, niveau min, niveau max, moment de la journée).
P3_GAMES = [g for g in os.environ.get("P3_GAMES", "rb,y,gs,c").split(",") if g]
P3_GEN = {g: GAME_GEN[g] for g in P3_GAMES}
_MOD_DK = {"rs": "3", "e": "3", "frlg": "3", "dp": "4", "pt": "4", "hgss": "4", "bw": "5", "b2w2": "5", "xy": "6", "oras": "6",
           "sm": "7", "usum": "7", "lgpe": "7b", "sw": "8", "swisle": "8", "swcrown": "8", "la": "8a", "bdsp": "8b",
           "sv": "9", "svmask": "9", "svdisk": "9", "za": "9a", "zadlc": "9a"}
DKEY = {g: (P3_GEN[g] if P3_GEN[g] <= 2 else _MOD_DK[g]) for g in P3_GAMES}   # PKHeX dump of each game
VERSIONS_OF = collections.defaultdict(list)
for _v, _g, _pid in R.VERSIONS:
    VERSIONS_OF[_g].append(_v)
# Japanese Blue: PokeAPI has no wild table for it and PKHeX keeps only part of its tables (blue_jp) → left out of this batch
P3_SKIP = set(os.environ.get("P3_SKIP_VERSIONS", "blue-japan").split(","))
for _g in list(VERSIONS_OF): VERSIONS_OF[_g] = [v for v in VERSIONS_OF[_g] if v not in P3_SKIP]
P3_VERSIONS = [v for g in P3_GAMES for v in VERSIONS_OF[g]]
GAME_OF_VERSION = {v: g for v, g, _ in R.VERSIONS}
PKAPI_VERSION = {pid: v for v, g, pid in R.VERSIONS if pid}
PKXV = {"RD": ["red", "red-japan"], "GN": ["blue", "green-japan"], "BU": ["blue-japan"], "YW": ["yellow"],
        "GD": ["gold"], "SI": ["silver"], "C": ["crystal"]}
PKXV["RB"] = PKXV["RD"] + PKXV["GN"] + PKXV["BU"]
PKXV["RBY"] = PKXV["RB"] + PKXV["YW"]
PKXV["GS"] = PKXV["GD"] + PKXV["SI"]
PKXV["GSC"] = PKXV["GS"] + PKXV["C"]
TIMES = ("morning", "day", "night")

def p3_norm(s):
    s = unicodedata.normalize("NFKC", s or "").casefold().replace("’", "'")
    return re.sub(r"[\s.'\-_,·]", "", s)

# ----------------------------------------------------------------------------- PokeAPI side
pk_loc = {r["id"]: r for r in pcsv("locations")}
pk_loc_by_ident = {r["identifier"]: r for r in pk_loc.values()}
pk_region = {r["id"]: r["identifier"] for r in pcsv("regions")}
pk_area = {r["id"]: r for r in pcsv("location_areas")}
pk_slot = {r["id"]: r for r in pcsv("encounter_slots")}
pk_meth = {r["id"]: r["identifier"] for r in pcsv("encounter_methods")}
pk_cv = {r["id"]: r["identifier"] for r in pcsv("encounter_condition_values")}
pk_cmap = collections.defaultdict(list)
for r in pcsv("encounter_condition_value_map"): pk_cmap[r["encounter_id"]].append(pk_cv[r["encounter_condition_value_id"]])
pk_gi = collections.defaultdict(dict)           # generation -> game index -> location identifier
for r in pcsv("location_game_indices"): pk_gi[int(r["generation_id"])].setdefault(int(r["game_index"]), pk_loc[r["location_id"]]["identifier"])
pk_locnames = collections.defaultdict(dict)    # identifier -> lang -> name
for r in pcsv("location_names"):
    l = PK_LANG.get(pk_lang[r["local_language_id"]])
    if l: pk_locnames[pk_loc[r["location_id"]]["identifier"]][l] = r["name"]
PK2FORM = {}
for et, eid, system, val in out["external_id"][1]:
    if et == "form" and system == "pokeapi-pokemon": PK2FORM.setdefault(int(val), eid)
d_pkenc = pkdoc("encounters")
d_pkloc = pkdoc("location_game_indices")
d_pkln = pkdoc("location_names")
PK_ENC = []   # dicts: version, location, area, method, form, min, max, conds, slot, rarity
for r in pcsv("encounters"):
    v = PKAPI_VERSION.get(int(r["version_id"]))
    if v not in P3_VERSIONS: continue
    s = pk_slot[r["encounter_slot_id"]]
    f = PK2FORM.get(int(r["pokemon_id"]))
    if not f: continue
    a = pk_area[r["location_area_id"]]
    PK_ENC.append(dict(version=v, location=pk_loc[a["location_id"]]["identifier"], area=a["identifier"], method=pk_meth[s["encounter_method_id"]],
                       form=f, min=int(r["min_level"]), max=int(r["max_level"]), conds=tuple(sorted(pk_cmap[r["id"]])), slot=s["slot"], rarity=s["rarity"]))

# ----------------------------------------------------------------------------- PKHeX side
PKX_ENC = {gen: json.load(open(DUMP / f"encounters_{gen}.json", encoding="utf-8")) for gen in sorted({DKEY[g] for g in P3_GAMES}, key=str)}
PKX_LOCN = json.load(open(DUMP / "locations.json", encoding="utf-8"))
d_pkxenc = {gen: doc("pkhex", f"{PKXREV} · Encounters{gen} (encounters_{gen}.json)", PKXREV, file_sha(DUMP / f"encounters_{gen}.json")) for gen in PKX_ENC}
d_pkxloc = doc("pkhex", f"{PKXREV} · GameInfo.Strings, met locations (locations.json)", PKXREV, file_sha(DUMP / "locations.json"))
SLOT_METHOD = {"Grass": "walk", "Surf": "surf", "Old_Rod": "old-rod", "Good_Rod": "good-rod", "Super_Rod": "super-rod",
               "Rock_Smash": "rock-smash", "Headbutt": "headbutt", "HeadbuttSpecial": "headbutt", "BugContest": "bug-contest"}
FAMILY = {"headbutt-rare": "headbutt", "headbutt-low": "headbutt", "headbutt-normal": "headbutt", "headbutt-high": "headbutt",
          "gift": "special", "static": "special", "gift-egg": "special", "roaming": "special", "roaming-grass": "special",
          "pokeflute": "special", "squirt-bottle": "special", "only-one": "special"}
def fam(m): return FAMILY.get(m, m)
def pkx_versions(v):
    if v not in PKXV: return None
    return [x for x in PKXV[v] if x in P3_VERSIONS]
def forms_of(sp, fi, game, random_form=False):
    if random_form:
        return sorted(k for (s, f), k in KEYMAP[game].items() if s == sp and (k, game) in present)
    k = KEYMAP[game].get((sp, fi))
    return [k] if k and (k, game) in present else []
def times_of(t):
    if t in (None, "Any"): return set(TIMES)
    return {x.strip().lower() for x in t.split(",")}

# ---- location identity
LOC_SRC = {}                  # location id -> (generation, kind, detail) : how it was identified
GEN2_LOC = {}                 # PKHeX gen 2 met id -> location identifier
p3_unplaced = collections.Counter()
for gen in PKX_ENC:
    if gen != 2: continue
    for x in PKX_ENC[2]:
        loc = x.get("Location")
        if loc and loc not in (126, 127) and loc not in GEN2_LOC:
            ident = pk_gi[2].get(loc)
            if ident: GEN2_LOC[loc] = ident
# gen 1: PKHeX table number -> PokeAPI location, by identical tables, then elimination
GEN1_LOC = {}
if 1 in PKX_ENC:
    tab = collections.defaultdict(set)
    for x in PKX_ENC[1]:
        a = x.get("_area")
        if not a or a["Type"] in ("Old_Rod", "Good_Rod"): continue   # Old / Good Rod: one table for every water tile
        for v in pkx_versions(a["Version"]) or []:
            tab[(a["Location"], v, SLOT_METHOD[a["Type"]])].add((x["Species"], x["LevelMin"], x["LevelMax"]))
    pkt = collections.defaultdict(set)
    sp_of_form = {r[0]: r[1] for r in form_rows}
    for e in PK_ENC:
        if GAME_OF_VERSION[e["version"]] in ("rb", "y") and e["method"] in ("walk", "surf", "super-rod"):
            pkt[(e["location"], e["version"], e["method"])].add((sp_of_form[e["form"]], e["min"], e["max"]))
    cands = {}
    pk_vm = {(vv, mm) for (l, vv, mm) in pkt}
    for (num, v, m), s in tab.items():
        if (v, m) not in pk_vm: continue          # PokeAPI has no table for this version and method (Japanese Blue)
        c = {l for (l, vv, mm), s2 in pkt.items() if vv == v and mm == m and s2 == s}
        if not c: continue                         # table differs from every PokeAPI table: no evidence either way
        cands[num] = c if num not in cands else cands[num] & c
    changed_ = True
    while changed_:
        changed_ = False
        fixed = {next(iter(c)) for c in cands.values() if len(c) == 1}
        for n, c in cands.items():
            if len(c) > 1 and c & fixed:
                c -= fixed; changed_ = True
    used = collections.Counter(next(iter(c)) for c in cands.values() if len(c) == 1)
    for n, c in cands.items():
        if len(c) == 1 and used[next(iter(c))] == 1: GEN1_LOC[n] = next(iter(c))
    GEN1_AMBIGUOUS = {n: sorted(c) for n, c in cands.items() if n not in GEN1_LOC}

# gen 2, Gold / Silver surfing: these games store no met location, and PKHeX's surfing tables for them sit one place off
# (Crystal's agree with PokeAPI and Bulbapedia). Each Gold / Silver surfing table is placed, like generation 1, at every
# PokeAPI place whose surfing table is identical; the content still comes from the game data.
GS_SURF_LOC = {}
if 2 in PKX_ENC:
    tab2 = collections.defaultdict(set)
    for x in PKX_ENC[2]:
        a = x.get("_area")
        if not a or a["Type"] != "Surf": continue
        for v in pkx_versions(a["Version"]) or []:
            if v in ("gold", "silver"): tab2[(a["Location"], v)].add((x["Species"], x["LevelMin"], x["LevelMax"]))
    sp_of_form2 = {r[0]: r[1] for r in form_rows}
    pks = collections.defaultdict(set)
    for e in PK_ENC:
        if e["version"] in ("gold", "silver") and e["method"] == "surf":
            pks[(e["location"], e["version"])].add((sp_of_form2[e["form"]], e["min"], e["max"]))
    for (num, v), s_ in tab2.items():
        GS_SURF_LOC[(num, v)] = sorted(l for (l, vv), s2 in pks.items() if vv == v and s2 == s_)

# ---- Bulbapedia tables (in-game trades, gifts) for the placement of encounters without a stored location
def wikitable_rows(text):
    """Rows of every wikitable in text, rowspans expanded; cells as raw wikitext."""
    rows_out = []
    for tbl in re.findall(r"\{\|(.*?)\n\|\}", text, re.S):
        pending = {}   # column -> [remaining rows, text]
        for raw in re.split(r"\n\|-[^\n]*", tbl)[1:]:
            cells = []
            for line in raw.strip("\n").split("\n"):
                if line.startswith("!") or not line.startswith("|"): 
                    if cells and not line.startswith(("!", "|")): cells[-1] += "\n" + line
                    continue
                for c in re.split(r"\s*\|\|\s*", line[1:]):
                    cells.append(c)
            row, ci = [], 0
            src = iter(cells)
            while True:
                if ci in pending and pending[ci][0] > 0:
                    row.append(pending[ci][1]); pending[ci][0] -= 1; ci += 1; continue
                try: c = next(src)
                except StopIteration: break
                m = re.match(r'\s*((?:[a-z]+="[^"]*"\s*)+)\|(.*)$', c, re.S)
                attrs, body = (m.group(1), m.group(2)) if m and "[[" not in m.group(1) and "{{" not in m.group(1) else ("", c)
                rs = re.search(r'rowspan="(\d+)"', attrs)
                cs = re.search(r'colspan="(\d+)"', attrs)
                for _ in range(int(cs.group(1)) if cs else 1):
                    if rs: pending[ci] = [int(rs.group(1)) - 1, body.strip()]
                    row.append(body.strip()); ci += 1
            while ci in pending and pending[ci][0] > 0:
                row.append(pending[ci][1]); pending[ci][0] -= 1; ci += 1
            if row: rows_out.append(row)
    return rows_out
def wiki_section(text, start, end):
    i = text.find(start)
    if i < 0: return ""
    j = text.find(end, i + len(start)) if end else -1
    return text[i:j if j > 0 else len(text)]
EN_LOC = {}   # normalised English name -> location identifier (PKHeX gen 2 names + PokeAPI names)
for ident, names in pk_locnames.items():
    if names.get("en"): EN_LOC.setdefault(p3_norm(names["en"]), set()).add(ident)
def wiki_places(cell, region):
    """Location identifiers named in a Bulbapedia cell (route templates and links)."""
    found = set()
    for m in re.finditer(r"\{\{rt\|(\d+)\|(\w+)", cell):
        for pre in (f"{m.group(2).lower()}-route-{m.group(1)}", f"{m.group(2).lower()}-sea-route-{m.group(1)}"):
            if pre in pk_loc_by_ident: found.add(pre)
    for m in re.finditer(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]|\{\{OBP\|([^|}]+)", cell):
        name = m.group(1) or m.group(2)
        for ident in EN_LOC.get(p3_norm(name), ()):
            if pk_region.get(pk_loc_by_ident[ident]["region_id"]) == region or not region: found.add(ident)
    return found
def msp_species(cell):
    m = re.search(r"\{\{MSP/?\d*\|(\d{3,4})\|", cell)
    return int(m.group(1)) if m else None

text_trade, d_btrade = bulba("In-game trade")
text_gift, d_bgift = bulba("Gift Pokémon")
BUL_TRADE = collections.defaultdict(dict)  # (gen, species received) -> {location: {species given}}
BUL_GIFT = collections.defaultdict(set)    # (gen, species) -> {location}
for gen, (s, e), region in [(1, ("===Generation I===", "===Generation II==="), "kanto"), (2, ("===Generation II===", "===Generation III==="), None)]:
    if gen not in PKX_ENC: continue
    for row in wikitable_rows(wiki_section(text_trade, s, e)):
        sps = [msp_species(c) for c in row if msp_species(c)]
        if len(sps) >= 2:
            for l in wiki_places(row[0], region): BUL_TRADE[(gen, sps[1])].setdefault(l, set()).add(sps[0])
for gen, (s, e), region in [(1, ("===[[Generation I]]===", "===[[Generation II]]==="), "kanto"), (2, ("===[[Generation II]]===", "====In Pokémon Stadium 2===="), None)]:
    if gen not in PKX_ENC: continue
    for row in wikitable_rows(wiki_section(text_gift, s, e)):
        sp = msp_species(row[0]) if row else None
        if sp and len(row) >= 5:
            BUL_GIFT[(gen, sp)] |= wiki_places(row[4], region)

# ----------------------------------------------------------------------------- encounters
ENC = collections.defaultdict(lambda: {"times": collections.defaultdict(lambda: [999, 0]), "shiny": set()})
# key: (form, version, location, method) ; times: time -> [min, max] ; non-slot encounters use the time "any"
AVAIL_SRC = collections.defaultdict(set)    # (form, version) -> {"wild", "gift", "npc-trade", "gift-egg", "event"}
PKX_SHINY = collections.defaultdict(list)    # (form, game) -> [Shiny value of every non-event template]
sp_of = {r[0]: r[1] for r in form_rows}
def add_enc(form, v, loc, method, lo, hi, times=("any",), shiny="Random"):
    e = ENC[(form, v, loc, method)]
    for t in times:
        e["times"][t][0] = min(e["times"][t][0], lo); e["times"][t][1] = max(e["times"][t][1], hi)
    e["shiny"].add(shiny or "Random")   # "always" / locked only when every template of the row agrees (Odd Egg: both)
def pk_place(form, v, methods, level=None):
    """Locations where PokeAPI has this form in this version with one of these methods (and this level when given)."""
    return {e["location"] for e in PK_ENC if e["form"] == form and e["version"] == v and e["method"] in methods
            and (level is None or e["min"] <= level <= e["max"])}
p3_trade_unplaced, p3_static_unplaced, p3_unconfirmed = [], [], []
SPECIAL_PK = {"gift": "gift", "gift-egg": "gift-egg", "static": "static", "only-one": "static", "pokeflute": "static", "squirt-bottle": "static"}
exec(open(ROOT / "scripts" / "phases" / "phase3_modern.py", encoding="utf-8").read())
for gen, rows in PKX_ENC.items():
    if not isinstance(gen, int):
        for x in rows: mod_record(x, gen)
        continue
    for x in rows:
        tbl = x["_table"]
        a = x.get("_area")
        vers = pkx_versions(x.get("Version") if not a else a["Version"])
        is_event = "GBEra" in tbl or "VC" in tbl or tbl.endswith("CelebiVC")
        if is_event:
            ev_v = set(pkx_versions(x.get("Version"))) if x.get("Version") in PKXV else None   # "Stadium"…: every version
            for g in P3_GAMES:
                if P3_GEN[g] != gen: continue
                for v in VERSIONS_OF[g]:
                    if ev_v is not None and v not in ev_v: continue
                    for f in forms_of(x["Species"], x.get("Form", 0), g):
                        AVAIL_SRC[(f, v)].add("event")
            continue
        if not vers: continue
        for v in vers:
            g = GAME_OF_VERSION[v]
            fs = forms_of(x["Species"], x.get("Form", 0), g, x.get("IsRandomUnspecificForm", False))
            for f in fs:
                PKX_SHINY[(f, g)].append(x.get("Shiny"))
            if a:   # wild slot
                method = SLOT_METHOD[a["Type"]]
                for f in fs: AVAIL_SRC[(f, v)].add("wild")
                if gen == 1:
                    if a["Type"] in ("Old_Rod", "Good_Rod"):
                        # one table for the whole game (same catch at every fishing spot): the spots are those where
                        # PokeAPI has this rod in this version; the set check below compares the content
                        spots = {e["location"] for e in PK_ENC if e["version"] == v and e["method"] == method}
                        if not spots: p3_unplaced["gen1-old-good-rod"] += 1
                        for l in sorted(spots):
                            for f in fs: add_enc(f, v, l, method, x["LevelMin"], x["LevelMax"]); ENC[(f, v, l, method)]["placement"] = "pokeapi"
                        continue
                    loc = GEN1_LOC.get(a["Location"])
                elif v in ("gold", "silver") and a["Type"] == "Surf":
                    spots = GS_SURF_LOC.get((a["Location"], v), [])
                    if not spots: p3_unplaced["gs-surf-unmatched"] += 1
                    for l in spots:
                        for f in fs:
                            add_enc(f, v, l, method, x["LevelMin"], x["LevelMax"], ["any"], x.get("Shiny")); ENC[(f, v, l, method)]["placement"] = "table-match"
                    continue
                else:
                    loc = GEN2_LOC.get(a["Location"])
                if not loc: p3_unplaced[f"gen{gen}-slot-unplaced"] += 1; continue
                t = sorted(times_of(x.get("EncounterTime"))) if gen == 2 else ["any"]
                for f in fs:
                    add_enc(f, v, loc, method, x["LevelMin"], x["LevelMax"], t, x.get("Shiny"))
                    if gen == 1: ENC[(f, v, loc, method)]["placement"] = "table-match"
            elif x["_type"].startswith("EncounterTrade"):
                lvl = x.get("LevelMinRBY") or x.get("Level") or x["LevelMin"]
                for f in fs:
                    if not pk_place(f, v, {"npc-trade"}): p3_unconfirmed.append((f, v, tbl)); continue   # version labels merged, as above
                    AVAIL_SRC[(f, v)].add("npc-trade")
                    pl = pk_place(f, v, {"npc-trade"}) & set(BUL_TRADE.get((gen, x["Species"]), {}))
                    if len(pl) == 1:
                        l = pl.pop()
                        add_enc(f, v, l, "npc-trade", lvl, lvl, shiny=x.get("Shiny")); ENC[(f, v, l, "npc-trade")]["placement"] = "pokeapi+bulbapedia"
                        # the Pokémon asked in exchange: Bulbapedia's table and PokeAPI's condition must agree
                        pk_give = {c[6:] for e in PK_ENC if e["form"] == f and e["version"] == v and e["method"] == "npc-trade" and e["location"] == l
                                   for c in e["conds"] if c.startswith("trade-")}
                        b_give = BUL_TRADE[(gen, x["Species"])].get(l, set())
                        both = {sp for sp in b_give if p3_norm(en_names[sp]) in {p3_norm(g_) for g_ in pk_give}}
                        if len(both) == 1: ENC[(f, v, l, "npc-trade")]["gives"] = both.pop()
                    else: p3_trade_unplaced.append((f, v))
            else:   # static / gift / egg
                # PKHeX's fixed encounters of these generations are hand-kept legality templates whose version labels are
                # merged ("RBY" for a Red-only Game Corner prize): a version counts only when PokeAPI has the Pokémon in it
                # with a gift / fixed-encounter method; PokeAPI also names the method (gift, static, gift-egg).
                lvl = x.get("Level") or x["LevelMin"]
                egg = bool(x.get("IsEgg") or x.get("EggCycles", 0) > 0)
                for f in fs:
                    if x.get("IsRoaming"):   # roaming: no fixed place in the game data
                        if pk_place(f, v, {"roaming-grass", "roaming-water"}): AVAIL_SRC[(f, v)].add("wild")
                        p3_unplaced["roaming"] += 1; continue
                    recs = [e for e in PK_ENC if e["form"] == f and e["version"] == v and e["method"] in SPECIAL_PK
                            and (e["method"] == "gift-egg") == egg]
                    if not recs: p3_unconfirmed.append((f, v, tbl)); continue
                    labels = {SPECIAL_PK[e["method"]] for e in recs}
                    loc = GEN2_LOC.get(x.get("Location")) if gen == 2 else None
                    placed_by = None
                    if loc:
                        at = {SPECIAL_PK[e["method"]] for e in recs if e["location"] == loc}
                        if not at: p3_static_unplaced.append((f, v, "location-differs")); loc = None
                        else: labels = at
                    else:
                        # no location in the game data: PokeAPI and Bulbapedia (gift table) must name the same place
                        pl = {e["location"] for e in recs} & BUL_GIFT.get((gen, x["Species"]), set())
                        if len(pl) == 1:
                            loc = pl.pop(); labels = {SPECIAL_PK[e["method"]] for e in recs if e["location"] == loc}; placed_by = "pokeapi+bulbapedia"
                        else: p3_static_unplaced.append((f, v, "no-common-place"))
                    method = "gift-egg" if egg else ("gift" if labels == {"gift"} else "static")
                    AVAIL_SRC[(f, v)].add("gift-egg" if egg else "gift" if method == "gift" else "wild")
                    if loc:
                        add_enc(f, v, loc, method, lvl, lvl, shiny=x.get("Shiny"))
                        if placed_by: ENC[(f, v, loc, method)]["placement"] = placed_by

def project(times):
    """time -> [min, max] → list of [min, max, condition] (one row without condition when every time agrees)."""
    if "any" in times: return [[times["any"][0], times["any"][1], None]]
    vals = {t: tuple(times[t]) for t in TIMES if t in times}
    if len(vals) == 3 and len(set(vals.values())) == 1:
        lo, hi = vals["morning"]; return [[lo, hi, None]]
    return [[lo, hi, "time-" + t] for t, (lo, hi) in sorted(vals.items(), key=lambda kv: TIMES.index(kv[0]))]

enc_sets = collections.defaultdict(list)    # (location, version, method) -> [[form, min, max, cond, shiny_locked, extra]]
for (f, v, loc, m), e in ENC.items():
    for lo, hi, cond in project(e["times"]):
        locked = 1 if (e["shiny"] == {"Never"} and GAME_GEN[GAME_OF_VERSION[v]] >= 2) else 0
        ex = {}
        if e["shiny"] == {"Always"}: ex["shiny"] = "always"
        if e.get("gives"): ex["gives_species_id"] = e["gives"]
        if e.get("placement"): ex["placement"] = e["placement"]
        extra = canon(ex) if ex else None
        enc_sets[(loc, v, m)].append([f, lo, hi, cond, locked, extra])
for k_, rows_ in mod_rows().items(): enc_sets[k_].extend(rows_)
MODERN = {g for g in P3_GAMES if P3_GEN[g] >= 3}
GAME_ORDER = {r[0]: int(r[6]) for r in out["game"][1]}
def mfam(g, m):
    """Comparison family of a method (ours or PokeAPI's) in a game."""
    if g not in MODERN: return fam(m)
    if m in ("gift", "gift-egg", "static", "only-one", "pokeflute", "squirt-bottle", "devon-scope", "wailmer-pail", "roaming-grass",
             "roaming-water", "roaming", "pokemon-ranger", "island-scan", "colosseum-bonus-disc-jpn", "colosseum-bonus-disc-us",
             "pokemon-channel-pal", "new-york-pokecenter-wish-eggs", "feebas-tile-fishing", "outbreak", "dynamax-adventure"):
        return "special" if m != "dynamax-adventure" else m
    if m in ("npc-trade", "max-raid"): return m
    if g in ("xy", "oras"):
        if m.endswith("-ambush"): return "ambush"
        return {"yellow-flowers": "walk", "purple-flowers": "walk", "red-flowers": "walk", "rough-terrain": "walk", "seaweed": "walk"}.get(m, m)
    if m == "sos-from-bubbling-spot": return "sos"
    if g in ("sm", "usum"):   # SOS allies: PKHeX and PokeAPI split them differently from the plain wild tables → compared together
        return "special" if m in ("island-scan",) else "wild"
    if g in ("lgpe", "sw", "swisle", "swcrown"):
        return m if m in ("horde", "sos", "friend-safari", "rock-smash") else "wild"
    return {"dark-grass": "walk", "grass-spots": "walk", "cave-spots": "walk", "bridge-spots": "walk", "seaweed": "walk",
            "surf-spots": "surf", "super-rod-spots": "super-rod"}.get(m, fam(m))
FAMILY_WHOLE = {"sm", "usum"}
LEVEL_BOOST = {"sw", "swisle", "swcrown"}   # Wild Area / DLC levels rise with badges
NO_SWARM_CMP = {"bw", "b2w2"}   # PokeAPI has no swarms for Black/White 1–2: swarm rows are left out of the comparison
def mproj(rows, g=None):
    """Projection used to compare with PokeAPI in generations 3+: one (form, min, max) per form, conditions merged."""
    d = {}
    for r in rows:
        if g in NO_SWARM_CMP and r[3] and "swarm-" in r[3]: continue
        lo, hi = d.get(r[0], (999, 0)); d[r[0]] = (min(lo, r[1]), max(hi, r[2]))
    return {(f, lo, hi, None) for f, (lo, hi) in d.items()}
# PokeAPI projection on the same keys (method family, form, min, max, time)
pk_times = collections.defaultdict(lambda: collections.defaultdict(lambda: [999, 0]))
for e in PK_ENC:
    ts = [c[5:] for c in e["conds"] if c in ("time-morning", "time-day", "time-night")]
    g = GAME_OF_VERSION[e["version"]]
    if P3_GEN[g] == 1 or g in MODERN or e["method"] in ("gift", "gift-egg", "static", "npc-trade", "pokeflute", "squirt-bottle", "only-one", "roaming-grass", "roaming-water"):
        ts = ["any"]
    elif not ts: ts = list(TIMES)
    m = "roaming" if e["method"].startswith("roaming") else e["method"]
    lo_, hi_ = e["min"], (e["min"] if e["method"] == "npc-trade" else e["max"])
    for t in ts:
        x = pk_times[(e["location"], e["version"], mfam(g, m), e["form"])][t]
        x[0] = min(x[0], lo_); x[1] = max(x[1], hi_)
pk_sets = collections.defaultdict(set)
for (loc, v, fm, f), times in pk_times.items():
    for lo, hi, cond in project(times):
        pk_sets[(loc, v, fm)].add((f, lo, hi, cond))
pk_present = {(loc, v) for (loc, v, fm) in pk_sets}

def verify_set(table, rk, chosen, obs, gen, proj=None):
    """Set-level verification (convention A). chosen: list of rows; obs: [(source, doc, projected set or None)]."""
    ch = sorted(chosen, key=lambda r: [str(x) for x in r])
    vh = sha256_text(canon(ch))
    parts, dissent = [], []
    citations.append((table, rk, "*", d_pkxenc[gen], canon({"n": len(ch), "sha256": vh}), 1)); parts.append(f"pkhex:{vh}")
    mine = proj(ch) if proj else {(r[0], r[1], r[2], r[3]) for r in ch}
    for s, d, val in obs:
        sh = sha256_text(canon(sorted(val, key=lambda r: [str(x) for x in r])))
        ok = val == mine
        citations.append((table, rk, "*", d, canon({"n": len(val), "sha256": sh}), 1 if ok else 0)); parts.append(f"{s}:{sh}")
        if not ok:
            dissent.append({"source": s, "document_id": d, "missing": sorted([list(x) for x in mine - val], key=str),
                            "extra": sorted([list(x) for x in val - mine], key=str)})
    if dissent:
        discreps.append((table, rk, "*", canon({"n": len(ch), "sha256": vh}), "game-data", canon(dissent), None))
    verifs.append((table, rk, "*", "game-data", vh, sha256_text("|".join(sorted(parts)))))
    return dissent

# group sets by method family for the PokeAPI comparison, publish per exact method
enc_rows = []
fam_sets = collections.defaultdict(set)
fam_raw = collections.defaultdict(list)
for (loc, v, m), rows in enc_sets.items():
    g_ = GAME_OF_VERSION[v]
    for r in (mproj(rows, g_) if g_ in MODERN else rows): fam_sets[(loc, v, mfam(g_, m))].add((r[0], r[1], r[2], r[3]))
    fam_raw[(loc, v, mfam(g_, m))].extend(rows)
p3_agree = collections.Counter()
for (loc, v, m), rows in sorted(enc_sets.items()):
    g = GAME_OF_VERSION[v]; gen = DKEY[g]
    rk = row_key(loc, v, m)
    obs = []
    fm = mfam(g, m)
    if (loc, v) in pk_present or pk_sets.get((loc, v, fm)):
        mine_f = fam_sets[(loc, v, fm)]
        theirs = pk_sets.get((loc, v, fm), set())
        # compare at family level, restricted to this method's forms when the family groups several methods
        if fm != m and not (g in FAMILY_WHOLE and fm == "wild"):   # several published methods share this PokeAPI family: leave out the forms of the other methods
            own_forms = {r[0] for r in rows}
            other_forms = {x[0] for x in mine_f} - own_forms
            theirs = {x for x in theirs if x[0] not in other_forms}
        obs.append(("pokeapi", d_pkenc, theirs))
    if g in FAMILY_WHOLE and fm == "wild":   # the whole family is compared (Sun/Moon: wild + SOS allies)
        fs_ = mproj(fam_raw[(loc, v, fm)], g)
        dis = verify_set("encounter", rk, rows, obs, gen, lambda ch, fs_=fs_: set(fs_))
    else:
        if g in MODERN and fm != m:
            obs = [(s_, d_, {x for x in th if x[0] in {r[0] for r in rows}}) for s_, d_, th in obs]
        if g in LEVEL_BOOST and m not in ("static", "gift", "npc-trade"):   # levels rise with badges (PokeAPI: up to 60): forms only
            obs = [(s_, d_, {(x[0], None, None, None) for x in th}) for s_, d_, th in obs]
            dis = verify_set("encounter", rk, rows, obs, gen, lambda ch, g=g: {(x[0], None, None, None) for x in mproj(ch, g)})
        else:
            dis = verify_set("encounter", rk, rows, obs, gen, (lambda ch, g=g: mproj(ch, g)) if g in MODERN else None)
    p3_agree[(g, m, "sets")] += 1
    if obs: p3_agree[(g, m, "cited")] += 1
    if obs and not dis: p3_agree[(g, m, "agree")] += 1
    for r in rows:
        f, lo, hi, cond, locked, extra = r[:6]
        enc_rows.append([f, v, loc, m, lo, hi, None, r[6] if len(r) > 6 else 0, locked, extra, cond])
# stable ids: same natural key keeps its id
prev_ids = {}
prev_links = collections.defaultdict(list)
for r in read_csv("encounter_condition_link"): prev_links[int(r["encounter_id"])].append(r["condition_id"])
for r in read_csv("encounter"):
    prev_ids[(r["form_id"], r["version_id"], r["area_id"], r["method_id"], ",".join(sorted(prev_links[int(r["id"])])), int(r["is_alpha"] or 0))] = int(r["id"])
next_id = max(list(prev_ids.values()) + [0]) + 1
encounter_rows, link_rows = [], []
for f, v, loc, m, lo, hi, rate, alpha, locked, extra, cond in sorted(enc_rows, key=lambda r: [str(x) for x in r]):
    k = (f, v, loc, m, cond or "", alpha)
    i = prev_ids.get(k)
    if i is None: i = next_id; next_id += 1
    encounter_rows.append([i, f, v, loc, m, lo, hi, rate, alpha, locked, extra])
    for c_ in (cond.split(",") if cond else []): link_rows.append([i, c_])

# ----------------------------------------------------------------------------- locations, areas, names
used_locs = sorted({r[3] for r in encounter_rows})
loc_games = sorted({(r[3], GAME_OF_VERSION[r[2]]) for r in encounter_rows})
location_rows, area_rows = [], []
for l in used_locs:
    p = pk_loc_by_ident.get(l)
    if p is None:   # place created from the game's own location list (PokeAPI does not have it)
        region = MLOC_NEW[l]
        location_rows.append([l, region, None]); area_rows.append([l, l, None])
        rk = row_key(l); val = canon({"id": l, "region": region}); obs_parts = []
        citations.append(("location", rk, "*", d_pkxloc, canon({"met": [[lst, metid, PKX_LOCN[lst]["en"].get(str(metid)), how] for lst, metid, how in sorted(MLOC_SRC[l])]}), 1))
        obs_parts += [f"pkhex:{lst}:{metid}" for lst, metid, how in sorted(MLOC_SRC[l])]
        verifs.append(("location", rk, "*", "game-data", sha256_text(val), sha256_text("|".join(sorted(obs_parts)))))
        verifs.append(("location_area", row_key(l), "*", "game-data", sha256_text(canon({"id": l, "location": l})), sha256_text("|".join(sorted(obs_parts)))))
        citations.append(("location_area", row_key(l), "*", d_pkxloc, canon({"location": l}), 1))
        continue
    location_rows.append([l, pk_region.get(p["region_id"]), int(p["id"])])
    area_rows.append([l, l, None])
    rk = row_key(l)
    # identity: the game's own location index (gen 2) or the identical encounter table (gen 1), and PokeAPI's identifier
    g2 = [i for i, ident in GEN2_LOC.items() if ident == l]
    g1 = [n for n, ident in GEN1_LOC.items() if ident == l]
    val = canon({"id": l, "region": pk_region.get(p["region_id"])})
    obs_parts = []
    if g2:
        _c = {"gen2_index": g2[0], "en": PKX_LOCN["gsc"]["en"].get(str(g2[0]))}
        if MLOC_SRC.get(l):
            _c["met"] = [[lst, metid, PKX_LOCN[lst]["en"].get(str(metid)), how] for lst, metid, how in sorted(MLOC_SRC[l])]
            obs_parts += [f"pkhex:{lst}:{metid}" for lst, metid, how in sorted(MLOC_SRC[l])]
        citations.append(("location", rk, "*", d_pkxloc, canon(_c),
                          1 if p3_norm(PKX_LOCN["gsc"]["en"].get(str(g2[0]))) == p3_norm(pk_locnames[l].get("en")) else 0))
        obs_parts.append(f"pkhex:{g2[0]}")
    if g1:
        citations.append(("location", rk, "*", d_pkxenc[1], canon({"gen1_table": sorted(g1)}), 1)); obs_parts.append(f"pkhex1:{sorted(g1)}")
    if MLOC_SRC.get(l) and not g2:
        citations.append(("location", rk, "*", d_pkxloc, canon({"met": [[lst, metid, PKX_LOCN[lst]["en"].get(str(metid)), how] for lst, metid, how in sorted(MLOC_SRC[l])]}), 1))
        obs_parts += [f"pkhex:{lst}:{metid}" for lst, metid, how in sorted(MLOC_SRC[l])]
    citations.append(("location", rk, "*", d_pkloc, canon({"identifier": l, "region": pk_region.get(p["region_id"])}), 1)); obs_parts.append(f"pokeapi:{l}")
    verifs.append(("location", rk, "*", "game-data", sha256_text(val), sha256_text("|".join(sorted(obs_parts)))))
    verifs.append(("location_area", row_key(l), "*", "game-data", sha256_text(canon({"id": l, "location": l})), sha256_text("|".join(sorted(obs_parts)))))
    citations.append(("location_area", row_key(l), "*", d_pkloc, canon({"location": l}), 1))
for l, g in loc_games:
    verifs.append(("location_game", row_key(l, g), "*", "game-data", sha256_text(canon([l, g])), sha256_text(f"pkhex:{l}:{g}")))
    citations.append(("location_game", row_key(l, g), "*", d_pkxenc[DKEY[g]], canon({"location": l, "game": g}), 1))

# names: per game (gen 2 met-location text), and one name without game from the latest game text that has the place
GL = collections.defaultdict(set)
for g, l, *_ in out["game_language"][1]: GL[g].add(l)
p3_names = collections.Counter()
def add_loc_name(l, lang, game, text_, obs_extra):
    rk = row_key("location", l, "name", lang, game, None)
    obs = [("pkhex", d_pkxloc, text_)] + obs_extra
    v_, st = resolve("translation", rk, "text", obs, lambda x: canon(p3_norm(x)))
    if v_ and st in PUBLISHED:
        tr_rows.append(["location", l, "name", lang, game, None, v_, 1]); p3_names[(game or "-", st)] += 1
LATEST = [("hgss", 4, "hgss"), ("frlg", 3, "rsefrlg"), ("gs", 2, "gsc")]
for l in used_locs:
    g2 = [i for i, ident in GEN2_LOC.items() if ident == l]
    for g in P3_GAMES:
        if P3_GEN[g] != 2 or (l, g) not in set(loc_games) or not g2: continue
        for lang in sorted(GL[g]):
            t = PKX_LOCN["gsc"].get(lang, {}).get(str(g2[0]))
            if not t: continue
            extra_obs = [("pokeapi", d_pkln, pk_locnames[l][lang])] if lang in pk_locnames.get(l, {}) else []
            add_loc_name(l, lang, g, t, extra_obs)
    # generations 3+: the met-location text of each game (PKHeX tags such as "(1)" removed)
    mod_text = {}
    for g in sorted(MODERN, key=lambda g: -GAME_ORDER.get(g, 0)):
        if (l, g) not in set(loc_games): continue
        lst = MOD_LIST[MOD_BASE.get(g, g)]
        ids = sorted({mid for (ls, mid, how) in MLOC_SRC.get(l, ()) if ls == lst})
        if not ids: continue
        for lang in sorted(GL[g]):
            ts = {strip_name(PKX_LOCN[lst].get(lang, {}).get(str(i))) for i in ids} - {""}
            if len(ts) != 1: continue
            t = ts.pop()
            extra_obs = [("pokeapi", d_pkln, pk_locnames[l][lang])] if lang in pk_locnames.get(l, {}) else []
            add_loc_name(l, lang, g, t, extra_obs)
            mod_text.setdefault(g, {})[lang] = (t, extra_obs)
    # generic name (no game): latest published game of generation 3+ that has this place, else the latest game text
    # that has it (HGSS, then FR/LG, then G/S/C), in that game's languages
    if mod_text:
        g = max(mod_text, key=lambda g: GAME_ORDER.get(g, 0))
        for lang, (t, extra_obs) in sorted(mod_text[g].items()): add_loc_name(l, lang, None, t, extra_obs)
        continue
    for g, gen, lst in LATEST:
        idx = [i for i, ident in pk_gi[gen].items() if ident == l]
        if not idx or not PKX_LOCN[lst]["en"].get(str(idx[0])): continue
        for lang in sorted(GL[g]):
            t = PKX_LOCN[lst].get(lang, {}).get(str(idx[0]))
            if not t: continue
            extra_obs = [("pokeapi", d_pkln, pk_locnames[l][lang])] if lang in pk_locnames.get(l, {}) else []
            add_loc_name(l, lang, None, t, extra_obs)
        break

# ----------------------------------------------------------------------------- availability
evo_game = collections.defaultdict(set)      # game -> {(from, to)}
_evo_pairs = {r[0]: (r[1], r[2]) for r in evo_rows}
for r in em_rows:
    if r[0] in _evo_pairs: evo_game[r[1]].add(_evo_pairs[r[0]])
egg_of = collections.defaultdict(set)
for r in out["species_egg_group"][1]: egg_of[int(r[0])].add(r[1])
dex_of_game = collections.defaultdict(set)
for d_ in out["pokedex"][1]: dex_of_game[d_[1]].add(d_[0])
in_dex = collections.defaultdict(set)
for pid, sid, num in out["pokedex_entry"][1]: in_dex[pid].add(int(sid))
# Unown: the letter is drawn at random at each encounter, so every letter shares the default form's sources
for (f_, v_), src_ in list(AVAIL_SRC.items()):
    if f_ == "201" and P3_GEN[GAME_OF_VERSION[v_]] == 2:
        for (ff, gg) in present:
            if ff.startswith("201-") and gg == GAME_OF_VERSION[v_]: AVAIL_SRC[(ff, v_)] |= src_ - {"event"}
avail_rows = []
ST_ALL = {}
p3_avail = collections.Counter()
NATIVE = {"wild", "gift", "npc-trade", "evolve", "breed"}
DLC_BASE = {"swisle": "sw", "swcrown": "sw", "svmask": "sv", "svdisk": "sv", "zadlc": "za"}
DLC_CHAIN = {"swisle": ["sw", "swisle"], "swcrown": ["sw", "swisle", "swcrown"], "svmask": ["sv", "svmask"],
             "svdisk": ["sv", "svmask", "svdisk"], "zadlc": ["za", "zadlc"]}
BASE_VERSION = {dv: bv for (d, bv), dv in DLCV.items()}
def chain_versions(g, v):
    """Versions whose sources count for (g, v): a DLC version has the base game and the earlier DLC (cumulative)."""
    if g not in DLC_CHAIN: return [v]
    bv = BASE_VERSION.get(v, v)
    return [bv if gg == DLC_BASE[g] else DLCV.get((gg, bv)) for gg in DLC_CHAIN[g] if gg in P3_GAMES or gg == DLC_BASE[g]]
def src_of(g, v, f):
    out_ = set()
    for vv in chain_versions(g, v):
        if vv: out_ |= AVAIL_SRC.get((f, vv), set())
    return out_
NO_BREED = {"lgpe", "la", "za", "zadlc"}          # games without breeding (and generation 1)
# forms obtained in a way that cannot evolve: Pikachu in Yellow (the only Pikachu is the starter, which refuses the
# Thunder Stone) → Raichu needs a trade. Checked: partner Pikachu / Eevee of Let's Go and the cap / cosplay Pikachu are
# separate forms with no evolution, the spiky-eared Pichu is an event form.
NO_EVOLVE = {("y", "25")}
LINK = [("rb", "y"), ("gs", "c"), ("rs", "e", "frlg"), ("dp", "pt", "hgss"), ("bw", "b2w2"), ("xy", "oras"), ("sm", "usum")]
def link_group(g): return next((grp for grp in LINK if g in grp), (g,))
# transfers between generations, by receiving game: (method, source games)
TRANSFER_IN = {"dp": [("pal-park", ["rs", "e", "frlg"])], "pt": [("pal-park", ["rs", "e", "frlg"])], "hgss": [("pal-park", ["rs", "e", "frlg"])],
               "bw": [("poke-transfer", ["dp", "pt", "hgss"])], "b2w2": [("poke-transfer", ["dp", "pt", "hgss"])],
               "xy": [("poke-bank", ["bw", "b2w2", "xy", "oras"])], "oras": [("poke-bank", ["bw", "b2w2", "xy", "oras"])],
               "sm": [("poke-bank", ["rb", "y", "gs", "c", "bw", "b2w2", "xy", "oras", "sm", "usum"])],
               "usum": [("poke-bank", ["rb", "y", "gs", "c", "bw", "b2w2", "xy", "oras", "sm", "usum"])]}
_HOME_SRC = ["sm", "usum", "lgpe", "sw", "swisle", "swcrown", "bdsp", "la", "sv", "svmask", "svdisk", "za", "zadlc"]
for _g in ("sw", "swisle", "swcrown", "bdsp", "la", "sv", "svmask", "svdisk", "za", "zadlc"): TRANSFER_IN[_g] = [("home", _HOME_SRC)]
for g in P3_GAMES:
    forms_g = sorted({f for (f, gg) in present if gg == g})
    pre = collections.defaultdict(set)
    for a_, b_ in evo_game[g] | evo_game[DLC_BASE.get(g, g)]: pre[b_].add(a_)
    st = {}
    for v in VERSIONS_OF[g]:
        s = collections.defaultdict(set)
        det_wild = {}
        for f in forms_g:
            src = src_of(g, v, f)
            if "wild" in src: s[f].add("wild")
            elif any(x.startswith("wild:") for x in src):
                s[f].add("wild"); det_wild[f] = ",".join(sorted(x[5:] for x in src if x.startswith("wild:")))
            if src & {"gift", "gift-egg", "gift:pokewalker"}: s[f].add("gift")
            if "npc-trade" in src: s[f].add("npc-trade")
        def obtainable(f): return bool(s[f] & NATIVE)
        def evolvable(f): return obtainable(f) and (g, f) not in NO_EVOLVE
        for _ in range(2):
            ch = True
            while ch:
                ch = False
                for f in forms_g:
                    if "evolve" not in s[f] and any(evolvable(p) for p in pre[f]):
                        s[f].add("evolve"); ch = True
            if P3_GEN[g] >= 2 and g not in NO_BREED:   # breeding: the first stage of a family whose obtainable member can breed
                kids = collections.defaultdict(set)
                for a_, b_ in evo_game[g] | evo_game[DLC_BASE.get(g, g)]: kids[a_].add(b_)
                def family(f):
                    seen, todo = set(), [f]
                    while todo:
                        x = todo.pop()
                        if x in seen: continue
                        seen.add(x); todo += list(kids[x])
                    return seen
                for f in forms_g:
                    if pre[f] or "breed" in s[f]: continue
                    if any(obtainable(x) and "undiscovered" not in egg_of[sp_of[x]] for x in family(f)):
                        s[f].add("breed")
        s["_wild_detail"] = det_wild
        st[v] = s
    ST_ALL[g] = st
def native_any(o, f): return any(ST_ALL[o][ov].get(f, set()) & NATIVE or "event" in src_of(o, ov, f) for ov in VERSIONS_OF[o])
FINAL = {}     # (g, v, f) -> statuses (for the transfer closure)
_fh = out["form"][0]
FORM_INFO = {r[0]: (str(r[_fh.index("is_default")]), str(r[_fh.index("is_battle_only")]), r[_fh.index("base_form_id")] or None) for r in out["form"][1]}
DEFAULT_FORM = {int(r[_fh.index("species_id")]): r[0] for r in out["form"][1] if str(r[_fh.index("is_default")]) == "1"}
p3_formchange = collections.Counter()
FC_CAND = []   # (game, version, form, in_regional_dex): non-default forms with no other way to get them
TRANSFERS = collections.defaultdict(dict)
order = sorted(P3_GAMES, key=lambda g: (P3_GEN[g], GAME_ORDER.get(g, 0)))
for g in order:
    st = ST_ALL[g]
    forms_g = sorted({f for (f, gg) in present if gg == g})
    for v in VERSIONS_OF[g]:
        others = [o for o in VERSIONS_OF[g] if o != v]
        for f in forms_g:
            stats = set(st[v][f])
            details = {}
            if stats & {"wild"} and f in st[v]["_wild_detail"]: details["wild"] = st[v]["_wild_detail"][f]
            if not stats & NATIVE:
                if any(st[o][f] & NATIVE for o in others): stats.add("trade-version-exclusive")
                else:
                    # trade from another game that can trade with this one (Yellow ← Red/Blue, Emerald ← FR/LG…)
                    src_g = sorted(o for o in link_group(g) if o != g and o in P3_GAMES and native_any(o, f))
                    if src_g: stats.add("trade-version-exclusive"); details["trade-version-exclusive"] = "from:" + ",".join(src_g)
                tr = []
                # Time Capsule between generations 1 and 2 (species 1–151 only)
                if sp_of[f] <= 151 and P3_GEN[g] in (1, 2):
                    cap = sorted(o for o in P3_GAMES if P3_GEN[o] in (1, 2) and P3_GEN[o] != P3_GEN[g] and native_any(o, f))
                    if cap: tr.append("time-capsule:" + ",".join(cap))
                for meth, srcs in TRANSFER_IN.get(g, []):
                    ok = [o for o in srcs if o in P3_GAMES and o != g and (native_any(o, f) or any(FINAL.get((o, ov, f), set()) - {"unobtainable"} for ov in VERSIONS_OF[o]))]
                    if ok: tr.append(meth + ":" + ",".join(ok))
                if tr: stats.add("transfer"); details["transfer"] = ";".join(tr)
            if "event" in src_of(g, v, f): stats.add("event")
            if not stats: stats.add("unobtainable")
            FINAL[(g, v, f)] = stats
            if stats == {"unobtainable"} and f in FORM_INFO and FORM_INFO[f][0] == "0":
                # forms reached by a change of form (battle-only forms, Rotom's appliances, Burmy's cloaks…): the schema has
                # no status for them → no row (counted, reported)
                dexes_ = set().union(*(dex_of_game[x] for x in DLC_CHAIN.get(g, [g])))
                FC_CAND.append((g, v, f, 1 if any(sp_of[f] in in_dex[d_] for d_ in dexes_) else 0))
                continue
            dexes = set().union(*(dex_of_game[x] for x in DLC_CHAIN.get(g, [g])))
            dex = 1 if any(sp_of[f] in in_dex[d_] for d_ in dexes) else 0
            for status in sorted(stats):
                detail = None
                if status == "gift":
                    src = src_of(g, v, f)
                    det = sorted({"gift-egg": "gift-egg", "gift:pokewalker": "pokewalker"}[x] for x in src & {"gift-egg", "gift:pokewalker"})
                    if "gift" in src and det: det = ["gift"] + det
                    detail = ",".join(det) or None
                else: detail = details.get(status)
                avail_rows.append([f, v, status, detail, dex])
                rk = row_key(f, v, status)
                val = canon([status, detail, dex])
                citations.append(("availability", rk, "*", d_pkxev if (status == "event" and (f, v) in EV_SRC and not any(
                    "event" in AVAIL_SRC.get((f, vv), set()) and (f, vv) not in EV_SRC for vv in chain_versions(g, v))) else d_pkxenc[DKEY[g]],
                                  canon({"status": status, "detail": detail}), 1))
                verifs.append(("availability", rk, "*", "game-data", sha256_text(val), sha256_text(f"pkhex:{val}")))
                p3_avail[(g, status)] += 1

# ----------------------------------------------------------------------------- form changes (schema 1.3.0, migration 0004)
# A non-default form that no encounter, gift, trade, evolution, breeding, transfer or event gives, in a game whose data
# has the form, reached by changing a form that is obtainable in that version: status 'form-change', detail = kind of
# change (gender, mega, primal, gigantamax, battle, item-or-action). Sources: PKHeX (form in the game's data + base form
# obtainable; Gigantamax: an encounter with the Gigantamax factor), Showdown (form legal in the game's mod, formats-data
# isNonstandard), PokeAPI (pokemon_form_generations lists the game's generation). Published when PKHeX and at least one
# other source agree (2 of 3); a source without the form at all gives no vote.
FC_ITEM_SPECIES = {386, 412, 479, 483, 484, 487, 492, 493, 585, 586, 641, 642, 645, 646, 647, 649, 676, 720, 741, 773,
                   800, 869, 898, 905, 1017}
FC_SEASON_GAMES = {"bw", "b2w2"}   # Deerling / Sawsbuck change with the season only in Black/White 1–2
FC_COSPLAY = {"25-belle", "25-libre", "25-phd", "25-pop-star", "25-rock-star"}   # Cosplay Pikachu's outfits (ORAS)
FC_BASE = {"658-ash": "658-battle-bond", "678-female-mega": "678-female", **{c: "25-cosplay" for c in FC_COSPLAY}}
_fcat = {r[0]: r[_fh.index("category")] for r in out["form"][1]}
_fpk = {r[0]: r[_fh.index("pokeapi_form_id")] for r in out["form"][1]}
def fc_kind(f, g):
    """(kind, base form) when the form is reached by changing another form in game g, else (None, reason)."""
    cat = _fcat.get(f); sp = sp_of[f]
    base = FC_BASE.get(f) or FORM_INFO[f][2] or DEFAULT_FORM.get(sp)
    if cat == "gender": return "gender", DEFAULT_FORM.get(sp)
    if cat in ("mega", "primal", "gigantamax"): return cat, base
    if cat == "totem": return None, "totem"
    if cat == "battle-only": return "battle", base
    if f in FC_COSPLAY: return ("item-or-action", base) if g == "oras" else (None, "cosplay-outside-oras")
    if sp in FC_ITEM_SPECIES:
        if sp in (585, 586) and g not in FC_SEASON_GAMES: return None, "season-fixed"
        if sp == 386 and P3_GEN[g] == 3: return None, "deoxys-form-by-game"
        return "item-or-action", base
    return None, "fixed-at-capture"
# Gigantamax factor: PKHeX encounters that can Gigantamax (raids, gifts, Dynamax Adventures), by version (DLC by place)
GMAX_OK = set()
for x in json.load(open(DUMP / "encounters_8.json", encoding="utf-8")):
    if not x.get("CanGigantamax"): continue
    loc_ = 244 if x.get("_type") == "EncounterStatic8U" else x.get("Location")
    for v0 in {"SW": ["sword"], "SH": ["shield"]}.get(x.get("Version"), ["sword", "shield"]):
        d_ = dlc_of("sw", loc_) if loc_ is not None else None
        vv = DLCV.get((d_, v0)) if d_ else v0
        if vv: GMAX_OK.add((x["Species"], vv))
# Showdown: formats-data of the game's mod (with the mods' inheritance)
_SD_FMT = {}
_SDJ = json.load(open(CACHE / "showdown-species.json", encoding="utf-8"))   # (`sd` is reused by later code)
# our form suffix → Showdown forme (when the names differ; "" = Showdown's base entry)
FC_SD_SUF = {"female-mega": "F-Mega", "male-mega": "M-Mega", "cornerstone-mask": "Cornerstone", "hearthflame-mask": "Hearthflame",
             "wellspring-mask": "Wellspring", "dawn": "Dawn-Wings", "dusk": "Dusk-Mane", "active": "", "amped-gmax": "Gmax",
             "vanilla-cream": ""}
SD_ILLEGAL = {"Past", "Future", "Unobtainable", "CAP", "Custom", "LGPE"}
def sd_formats(mod):
    if mod in _SD_FMT: return _SD_FMT[mod]
    base_dir = CACHE / "showdown/data"
    parent = None
    if mod != "gen9":
        sc = base_dir / f"mods/{mod}/scripts.ts"
        m_ = re.search(r"inherit:\s*['\"](\w+)['\"]", sc.read_text("utf-8")) if sc.exists() else None
        parent = m_.group(1) if m_ else "gen9"
    res = dict(sd_formats(parent)) if parent else {}
    p_ = base_dir / ("formats-data.ts" if mod == "gen9" else f"mods/{mod}/formats-data.ts")
    if p_.exists():
        for m_ in re.finditer(r"^\t(\w+): \{(.*?)^\t\},?", p_.read_text("utf-8"), re.S | re.M):
            body = m_.group(2); ns = re.search(r'isNonstandard:\s*(?:"(\w+)"|null)', body)
            if ns: res[m_.group(1)] = ns.group(1)
            elif "inherit: true" not in body or m_.group(1) not in res: res[m_.group(1)] = None
    _SD_FMT[mod] = res
    return res
def sd_vote(f, g):
    """True / False: Showdown has the form legal / not legal in the game; None: Showdown does not have the form."""
    gb = MOD_BASE.get(g, g); mod = _SDJ["mods"].get(gb)
    if not mod: return None
    fmt = sd_formats(mod); sp = sp_of[f]; suf = f.partition("-")[2]
    if sp == 869: suf = re.sub(r"-[a-z]+-sweet$", "", suf)   # Showdown has the creams, not the sweets
    suf = FC_SD_SUF.get(suf, suf)
    sid = sd_index.get(gb, {}).get((sp, sdid(SD_SUFFIX.get(suf, suf) if suf not in FC_SD_SUF.values() else suf)))
    if sid and sid in fmt: return fmt[sid] not in SD_ILLEGAL
    base_id = sd_index.get(gb, {}).get((sp, ""))
    be = _SDJ["games"].get(gb, {}).get(base_id) if base_id else None
    if be and be.get("formeOrder") and suf and any(sdid(n) == sdid(be["name"] + suf) for n in be["formeOrder"]):
        return fmt.get(base_id) not in SD_ILLEGAL   # cosmetic forme of the species
    return None
_pk_fgen = collections.defaultdict(set)
for r in pcsv("pokemon_form_generations"): _pk_fgen[r["pokemon_form_id"]].add(int(r["generation_id"]))
def pk_vote(f, g):
    gens = _pk_fgen.get(str(_fpk.get(f) or ""))
    if not gens: return None
    return P3_GEN[g] in gens
_FG_DOC = {}
for t_, rk_, col_, d_, obs_, ag_ in citations:
    if t_ == "form_game" and col_ == "*" and rk_ not in _FG_DOC: _FG_DOC[rk_] = d_
d_pkfgen = pkdoc("pokemon_form_generations")
FC_AV = {(v, f) for (g, v, f), st in FINAL.items() if st - {"unobtainable"}}
fc_done, fc_kinds, fc_votes = set(), collections.Counter(), {}
fc_status = collections.Counter()
FC_LEFT = collections.defaultdict(set)   # (form, reason) -> games
_progress = True
while _progress:   # a changed form can be the base of another (Ogerpon's masks → Terastal forms)
    _progress = False
    for g, v, f, dex in FC_CAND:
        if (g, v, f) in fc_done: continue
        kind, base = fc_kind(f, g)
        if not kind or (v, base) not in FC_AV: continue
        if kind == "gigantamax" and not any((sp_of[f], vv) in GMAX_OK for vv in chain_versions(g, v) if vv): continue
        if (f, g) not in fc_votes: fc_votes[(f, g)] = (sd_vote(f, g), pk_vote(f, g))
        sdv, pkv = fc_votes[(f, g)]
        agree = 1 + (sdv is True) + (pkv is True)
        if agree < 2: continue
        fc_done.add((g, v, f)); FC_AV.add((v, f)); _progress = True
        rk = row_key(f, v, "form-change")
        val = canon(["form-change", kind, dex])
        pk_doc = _FG_DOC.get(row_key(f, g)) or d_pkxenc[DKEY[g]]
        citations.append(("availability", rk, "*", pk_doc, canon({"form_in_game_data": True, "from": base, "kind": kind}), 1))
        if kind == "gigantamax":
            citations.append(("availability", rk, "*", d_pkxenc[DKEY["sw"]], canon({"can_gigantamax": True}), 1))
        mod = _SDJ["mods"][MOD_BASE.get(g, g)]
        if sdv is not None: citations.append(("availability", rk, "*", sdmdoc("formats-data", mod), canon({"legal": sdv}), 1 if sdv else 0))
        if pkv is not None: citations.append(("availability", rk, "*", d_pkfgen, canon({"generation": P3_GEN[g], "listed": pkv}), 1 if pkv else 0))
        st_ = "unanimous" if agree == 3 else "majority"
        verifs.append(("availability", rk, "*", st_, sha256_text(val), sha256_text(f"pkhex:true|showdown:{sdv}|pokeapi:{pkv}")))
        if sdv is False or pkv is False:
            alt = [{"source": s_, "value": "absent", "document_id": dd} for s_, vv_, dd in
                   (("showdown", sdv, sdmdoc("formats-data", mod)), ("pokeapi", pkv, d_pkfgen)) if vv_ is False]
            discreps.append(("availability", rk, "*", val, "majority", canon(alt), None))
        avail_rows.append([f, v, "form-change", kind, dex])
        p3_avail[(g, "form-change")] += 1; fc_kinds[kind] += 1; fc_status[st_] += 1
# forms left without availability (reported)
for g, v, f, dex in FC_CAND:
    if (g, v, f) in fc_done: continue
    kind, base = fc_kind(f, g)
    if not kind: reason = base
    elif (v, base) not in FC_AV: reason = "base-unavailable"
    elif kind == "gigantamax" and not any((sp_of[f], vv) in GMAX_OK for vv in chain_versions(g, v) if vv): reason = "no-gigantamax-encounter"
    else:
        sdv, pkv = fc_votes.get((f, g), (sd_vote(f, g), pk_vote(f, g)))
        reason = f"sources:showdown={sdv},pokeapi={pkv}"
        if sdv is False or pkv is False:
            rk = row_key(f, v, "form-change")
            alt = [{"source": s_, "value": "absent", "document_id": dd} for s_, vv_, dd in
                   (("showdown", sdv, sdmdoc("formats-data", _SDJ["mods"][MOD_BASE.get(g, g)])), ("pokeapi", pkv, d_pkfgen)) if vv_ is False]
            if not any(d[1] == rk for d in discreps[-50:]):
                discreps.append(("availability", rk, "*", canon(["form-change", kind, dex]), "open", canon(alt), "unpublished: PKHeX only"))
    FC_LEFT[(f, reason)].add(g)
    p3_formchange[(g, reason)] += 1

# ----------------------------------------------------------------------------- Shiny rules and locks
text_shiny, d_bshiny = bulba("Shiny Pokémon")
_mp = MAN["pokepedia:Pokémon chromatique"]
text_pshiny = (ROOT / _mp["path"]).read_text("utf-8")
d_pshiny = doc("pokepedia", _mp["url"] + f" (oldid {_mp['revision']})", _mp["revision"], _mp["sha256"])
SHINY = {   # game -> [(method, odds, conditions, [(Bulbapedia needle, Poképédia needle)])]
    "gs": [("base", "1/8192", None, [("1/8192", "1/8192")]),
           ("shiny-parent", "1/64", canon({"breeding_parent_shiny": True}), [("1/64", "chance sur 64")])],
    "c": [("base", "1/8192", None, [("1/8192", "1/8192")]),
          ("shiny-parent", "1/64", canon({"breeding_parent_shiny": True}), [("1/64", "chance sur 64")])],
}
# generations 3+: base rate in both wikis; the Shiny Charm only where both give its rate (B2W2). The Masuda method and
# the later Shiny Charm rates are given by Bulbapedia only → not published (reported).
for _g in ("rs", "e", "frlg", "dp", "pt", "hgss", "bw", "b2w2"):
    SHINY[_g] = [("base", "1/8192", None, [("1 roll (1/8192)", "1/8192")])]
SHINY["b2w2"].append(("shiny-charm", "3/8192", canon({"item": "shiny-charm"}), [("3 rolls (~1/2731.00)", "1 sur 2731")]))
for _g in ("xy", "oras", "sm", "usum", "lgpe", "sw", "bdsp", "la", "sv", "za"):
    SHINY[_g] = [("base", "1/4096", None, [("1 roll (1/4096)", "1 chance sur 4096")])]
shiny_rows, lock_rows = [], []
bul_g2 = wiki_section(text_shiny, "==In the core series games==", "==In spin-off") or text_shiny
for g in P3_GAMES:
    for method, odds, cond, needles in SHINY.get(g, []):
        b_ok = all(n[0] in bul_g2 for n in needles); p_ok = all(n[1] in text_pshiny for n in needles)
        rk = row_key(g, method)
        citations.append(("shiny_rule", rk, "*", d_bshiny, canon({"odds": odds, "found": b_ok}), 1 if b_ok else 0))
        citations.append(("shiny_rule", rk, "*", d_pshiny, canon({"odds": odds, "found": p_ok}), 1 if p_ok else 0))
        st_ = "manual" if (b_ok and p_ok) else "disputed"
        verifs.append(("shiny_rule", rk, "*", st_, sha256_text(canon([odds, cond])), sha256_text(f"bulbapedia:{b_ok}|pokepedia:{p_ok}")))
        if st_ in PUBLISHED: shiny_rows.append([g, method, odds, cond])
# locks: every template of the form in the game is Shiny "Never" (its wild / static rows included) and no breeding / evolution path exists
for (f, g), vals in sorted(PKX_SHINY.items()):
    if P3_GEN[g] < 2 or not vals or any(x != "Never" for x in vals): continue
    if any(r[0] == f and GAME_OF_VERSION[r[1]] == g and r[2] in ("evolve", "breed") for r in avail_rows): continue   # wild rows come from these same never-shiny templates
    lock_rows.append([f, g, "npc-trade" if any(r[0] == f and GAME_OF_VERSION[r[1]] == g and r[2] == "npc-trade" for r in avail_rows) else None])
    rk = row_key(f, g)
    citations.append(("shiny_lock", rk, "*", d_pkxenc[DKEY[g]], canon({"shiny": sorted(set(vals))}), 1))
    verifs.append(("shiny_lock", rk, "*", "game-data", sha256_text(canon([f, g])), sha256_text(f"pkhex:{f}:{g}")))

# ----------------------------------------------------------------------------- old Pokédex names (external_id pokedex-legacy)
PDX = ROOT.parent / "pokedex" / "docs" / "data"
legacy = collections.defaultdict(set)
legacy_todo = collections.defaultdict(list)
p3_legacy_unmatched = collections.Counter()
if (PDX / "loc.json").exists():
    pl = json.load(open(PDX / "loc.json", encoding="utf-8"))
    fr_names = collections.defaultdict(set)   # (location) -> normalised French names (any game text)
    for r in tr_rows:
        if r[0] == "location" and r[3] in ("fr", "en"): fr_names[r[1]].add(p3_norm(r[6]))   # English too: "Route 105" (FR "Chenal 105")
    locs_in_game = collections.defaultdict(set)
    for l, g in loc_games: locs_in_game[g].add(l)
    for spf in sorted((PDX / "sp").glob("*.json")):
        spd = json.load(open(spf, encoding="utf-8"))
        for fk, fd in spd.get("f", {}).items():
            for g, lst in (fd.get("en") or {}).items():
                if g not in P3_GAMES: continue
                for e in lst:
                    name = pl["a"][e[0]]
                    base = p3_norm(re.sub(r"\s*\([^)]*\)\s*$", "", name))
                    c = [l for l in locs_in_game[g] if base in fr_names[l]]
                    if len(c) == 1: legacy[c[0]].add(name)
                    else: legacy_todo[name].append((fk, g))
    # names that differ from the game text ("Mont Argenté" for the game's "Grotte Argentée"…): the place where every
    # Pokémon listed under that old name is found in our encounters (at least 80 % of them, single best place)
    enc_at = collections.defaultdict(set)
    for r in encounter_rows: enc_at[(r[1], GAME_OF_VERSION[r[2]])].add(r[3])
    for name, entries in sorted(legacy_todo.items()):
        cnt = collections.Counter(l for fk, g in set(entries) for l in enc_at.get((fk, g), set()))
        best = cnt.most_common(2)
        n_ = len(set(entries))
        if n_ >= 3 and best and best[0][1] >= 0.8 * n_ and (len(best) == 1 or best[1][1] < best[0][1]): legacy[best[0][0]].add(name)
        else: p3_legacy_unmatched[name] += len(entries)
for l, names in sorted(legacy.items()):
    out["external_id"][1].append(["location", l, "pokedex-legacy", canon(sorted(names))])

out["location"] = (["id", "region_id", "pokeapi_id"], location_rows)
out["location_area"] = (["id", "location_id", "pokeapi_id"], area_rows)
out["location_game"] = (["location_id", "game_id"], [list(x) for x in loc_games])
out["encounter_method"] = (["id"], [[m] for m in sorted({r[4] for r in encounter_rows})])
out["encounter_condition"] = (["id"], [[c] for c in sorted({r[1] for r in link_rows})])
out["encounter"] = (["id", "form_id", "version_id", "area_id", "method_id", "min_level", "max_level", "rate_pct", "is_alpha", "shiny_locked", "extra"], encounter_rows)
out["encounter_condition_link"] = (["encounter_id", "condition_id"], link_rows)
out["availability"] = (["form_id", "version_id", "status", "detail", "in_regional_dex"], avail_rows)
out["shiny_rule"] = (["game_id", "method", "odds", "conditions"], shiny_rows)
out["shiny_lock"] = (["form_id", "game_id", "note"], lock_rows)
P3_STATS = dict(games=P3_GAMES, locations=len(location_rows), encounters=len(encounter_rows), encounter_sets=len(enc_sets),
                availability=len(avail_rows), shiny_rules=len(shiny_rows), shiny_locks=len(lock_rows),
                gen1_tables_placed=len(GEN1_LOC), gen1_tables_ambiguous=GEN1_AMBIGUOUS if 1 in PKX_ENC else {},
                unplaced=dict(p3_unplaced), trades_unplaced=sorted(set(p3_trade_unplaced)), statics_unplaced=sorted(set(p3_static_unplaced)),
                unconfirmed_templates=sorted(set(p3_unconfirmed)), skipped_versions=sorted(P3_SKIP),
                names={f"{k[0]}:{k[1]}": n for k, n in sorted(p3_names.items())},
                agreement={f"{g}:{m}": [p3_agree[(g, m, "agree")], p3_agree[(g, m, "cited")], p3_agree[(g, m, "sets")]]
                           for (g, m, k) in sorted(p3_agree) if k == "sets"},
                availability_by_status={f"{g}:{s}": n for (g, s), n in sorted(p3_avail.items())},
                legacy_mapped=len(legacy), legacy_unmatched=dict(p3_legacy_unmatched.most_common()),
                modern_skipped=dict(p3_mod_skip), modern_locations={h: len({l for l, srcs in MLOC_SRC.items() if any(x[2] == h for x in srcs)})
                                                                    for h in ("pokeapi-index", "pokeapi-name", "pokeapi-slug", "created")},
                shiny_lock_list=[f"{f}:{g}" for f, g, _ in lock_rows],
                created_locations=sorted(MLOC_NEW), form_change_left={f"{g}:{k}": n for (g, k), n in sorted(p3_formchange.items())},
                form_change_rows=dict(fc_kinds), form_change_status=dict(fc_status),
                form_change_left_forms={f"{f}|{r}": sorted(gs) for (f, r), gs in sorted(FC_LEFT.items())}, form_skips={f"{a}:{b}:{c}:{d}": n for (a, b, c, d), n in sorted(P3_FORMSKIP.items(), key=str)})
json.dump(P3_STATS, open(ROOT / "reports/phase3-details.json", "w"), ensure_ascii=False, indent=0)
print("phase3", json.dumps({k: v for k, v in P3_STATS.items() if k not in ("agreement", "legacy_unmatched", "trades_unplaced", "statics_unplaced", "unconfirmed_templates", "created_locations", "form_skips")}, ensure_ascii=False))
if os.environ.get("P3_DRY"):
    json.dump([[d_[1], json.loads(d_[5])] for d_ in discreps if d_[0] == "encounter"], open("/tmp/p3disc.json", "w"))
    sys.exit(0)

