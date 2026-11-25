# Phase 1b — objets d'évolution, évolutions (méthodes par jeu), Pokédex régionaux, catégories d'espèce, noms de formes.
# Exécuté par scripts/import_data.py dans son espace de noms (provenance : doc/resolve, mêmes règles qu'en phase 1).
EVO = json.load(open(DUMP / "evolutions.json", encoding="utf-8"))
ITEMS_EN = json.load(open(DUMP / "items_en.json", encoding="utf-8"))
NMI = json.load(open(DUMP / "names_moves_items.json", encoding="utf-8"))
d_evo = doc("pkhex", f"{PKXREV} · EvolutionTree (evolutions.json)", PKXREV, file_sha(DUMP / "evolutions.json"))
d_items = doc("pkhex", f"{PKXREV} · GameInfo.Strings.Items (items_en.json)", PKXREV, file_sha(DUMP / "items_en.json"))
d_nmi = doc("pkhex", f"{PKXREV} · GameInfo.Strings moves/items (names_moves_items.json)", PKXREV, file_sha(DUMP / "names_moves_items.json"))
SDM = json.load(open(CACHE / "showdown-more.json", encoding="utf-8"))
def sdmdoc(kind, mod):
    p = CACHE / "showdown/data" / (f"{kind}.ts" if mod == "gen9" else f"mods/{mod}/{kind}.ts")
    if not p.exists(): p = CACHE / f"showdown/data/{kind}.ts"
    return doc("showdown", f"data/{'' if mod == 'gen9' else 'mods/' + mod + '/'}{kind}.ts (mod {mod})@{SDREV[:12]}", SDREV, file_sha(p))

def nname(x): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", (x or "")).encode("ascii", "ignore").decode().lower())
CTX_GAMES = {"gen1": ["rb", "y"], "gen2": ["gs", "c"], "gen3": ["rs", "e", "frlg"], "gen4": ["dp", "pt", "hgss"],
             "gen5": ["bw", "b2w2"], "gen6": ["xy", "oras"], "gen7": ["sm", "usum"], "gen7b": ["lgpe"], "gen8": ["sw"],
             "gen8a": ["la"], "gen8b": ["bdsp"], "gen9": ["sv"], "gen9a": ["za"]}
GAME_CTX = {g: c for c, gs in CTX_GAMES.items() for g in gs}
for _d, _p in DERIVED.items(): GAME_CTX[_d] = GAME_CTX[_p]

# form key per (game, species, form index) — same mapping as the phase 1 personal tables
KEYMAP = collections.defaultdict(dict)
for g in PKHEX_GAMES:
    gid = GAME_OF.get(g, g)
    for r in pkx[g]:
        k = map_form(g, r["species"], r["form"], r["form_name_en"])
        if k and k in form_ids: KEYMAP[gid].setdefault((r["species"], r["form"]), k)
for _d, _p in DERIVED.items(): KEYMAP[_d] = KEYMAP[_p]
present = set(pk_rows.keys())   # (form, game) with a form_game row

# ----------------------------------------------------------------------------- items (only those referenced)
pk_items = {int(r["id"]): r for r in pcsv("items")}
pk_icat = {r["id"]: r["identifier"] for r in pcsv("item_categories")}
pk_item_by_name = collections.defaultdict(list)
pk_item_names = collections.defaultdict(dict)
for r in pcsv("item_names"):
    l = PK_LANG.get(pk_lang[r["local_language_id"]])
    if l: pk_item_names[int(r["item_id"])][l] = r["name"]
    if r["local_language_id"] == "9": pk_item_by_name[nname(r["name"])].append(int(r["item_id"]))
ITEM_FIX = {"upgrade": "upgrade", "blackaugurite": "blackaugurite"}
item_used = {}           # pokeapi id -> (ctx, game index)
item_unmapped = set()
def item_of(ctx, idx):
    if not idx: return None
    lst = ITEMS_EN[ctx]
    if idx >= len(lst): item_unmapped.add((ctx, idx, None)); return None
    c = sorted(i for i in pk_item_by_name.get(nname(lst[idx]), []) if i < 10000) or sorted(pk_item_by_name.get(nname(lst[idx]), []))
    if not c: item_unmapped.add((ctx, idx, lst[idx])); return None
    item_used.setdefault(c[0], (ctx, idx))
    if ctx in ("gen1", "gen2", "gen3"): pass
    else: item_used[c[0]] = item_used[c[0]] if item_used[c[0]][0] not in ("gen1", "gen2", "gen3") else (ctx, idx)
    return c[0]

# ----------------------------------------------------------------------------- evolutions
TIME = {"Morning": "day", "Day": "day", "Night": "night", "Dusk": "dusk"}
LOC = {"LevelUpElectric": "magnetic-field", "LevelUpForest": "moss-rock", "LevelUpCold": "ice-rock",
       "LevelUpSummit": "mount-lanakila", "LevelUpWormhole": "ultra-space", "UseItemWormhole": "ultra-space",
       "LevelUpUnionCircle": "union-circle"}
def method_cols(ctx, r):
    m, a, lvl = r["method"], r["argument"], (r["level"] or None)
    c = dict(trigger="level-up", min_level=None, item_id=None, held_item_id=None, known_move_id=None, known_move_type_id=None,
             location_id=None, time_of_day=None, gender=None, min_friendship=None, min_affection=None, conditions={})
    cond = c["conditions"]
    if r["level_up"] and lvl and m not in ("LevelUpFriendship",): c["min_level"] = lvl
    for k, v in TIME.items():
        if m.endswith(k): c["time_of_day"] = v
    if "Male" in m: c["gender"] = "male"
    if "Female" in m: c["gender"] = "female"
    if m.startswith("UseItem"):
        c["trigger"] = "use-item"; c["item_id"] = item_of(ctx, a); c["min_level"] = None
        if c["item_id"] is None: cond["item_index"] = a
        if m == "UseItemFullMoon": cond["full_moon"] = True
    elif m == "Trade":
        c["trigger"] = "trade"; c["min_level"] = None
    elif m == "TradeHeldItem":
        c["trigger"] = "trade"; c["held_item_id"] = item_of(ctx, a); c["min_level"] = None
    elif m == "TradeShelmetKarrablast":
        c["trigger"] = "trade"; c["min_level"] = None; cond["trade_with_species"] = {588: 616, 616: 588}.get(r["species"])
    elif m.startswith("LevelUpFriendship"):
        cond["high_friendship"] = True
    elif m.startswith("LevelUpHeldItem"):
        c["held_item_id"] = item_of(ctx, a)
    elif m.startswith("LevelUpKnowMove"):
        if "2" in PHASES: c["known_move_id"] = a     # the move table exists from phase 2 on
        else: cond["known_move"] = a
    elif m == "LevelUpMoveType":   # PKHeX method 30: a Dark-type Pokémon in the party (Pancham); the argument is unused
        cond["party_type"] = "dark"
    elif m == "LevelUpAffection50MoveType":
        c["known_move_type_id"] = R.TYPES[a]; cond["affection_points"] = 50
    elif m == "LevelUpBeauty":
        cond["min_beauty"] = a or 170
    elif m == "LevelUpWithTeammate":
        cond["party_species"] = a
    elif m in ("LevelUpATK", "LevelUpDEF", "LevelUpAeqD"):
        cond["relative_stats"] = {"LevelUpATK": "atk>def", "LevelUpDEF": "atk<def", "LevelUpAeqD": "atk=def"}[m]
    elif m in ("LevelUpECl5", "LevelUpECgeq5"):
        cond["personality"] = {"LevelUpECl5": "ec%10<5", "LevelUpECgeq5": "ec%10>=5"}[m]
    elif m == "LevelUpShedinja":
        c["trigger"] = "shed"
    elif m == "LevelUpWeather":
        cond["overworld_rain"] = True
    elif m.startswith("LevelUpVersion"):
        cond["version"] = a
    elif m == "LevelUpInverted":
        cond["upside_down"] = True
    elif m == "LevelUpFormFemale1":
        c["gender"] = "female"
    elif m == "LevelUpCollect999":
        cond["collect"] = 999
    elif m in ("LevelUpNatureAmped", "LevelUpNatureLowKey"):
        cond["nature"] = "amped" if m.endswith("Amped") else "low-key"
    elif m == "LevelUpWalkStepsWith":
        c["trigger"] = "walk"; cond["steps"] = a or 1000
    elif m in ("TowerOfDarkness", "TowerOfWaters"):
        c["trigger"] = "tower"; cond["tower"] = "darkness" if m.endswith("Darkness") else "waters"
    elif m == "CriticalHitsInBattle":
        c["trigger"] = "three-critical-hits"
    elif m == "HitPointsLostInBattle":
        c["trigger"] = "take-damage"; cond["hp_lost"] = a or 49
    elif m.startswith("LevelUpRecoilDamage"):
        c["trigger"] = "recoil-damage"; cond["recoil_hp"] = a or 294
    elif m == "UseMoveAgileStyle":
        c["trigger"] = "agile-style"; cond["use_move"] = a; cond["times"] = 20
    elif m in ("UseMoveStrongStyle", "UseMoveBarbBarrage"):
        c["trigger"] = "strong-style"; cond["use_move"] = a; cond["times"] = 20
    elif m == "LevelUpUseMoveSpecial":
        c["trigger"] = "other"; cond["use_move"] = a; cond["times"] = 20
    elif m == "LevelUpDefeatEquals":
        c["trigger"] = "other"; cond["defeat_same_species_holding_leaders_crest"] = 3
    elif m.startswith("LevelUpInBattle"):
        cond["in_battle"] = True
    elif m == "Spin":
        c["trigger"] = "spin"; cond["spin"] = a
    elif m in LOC:
        pass
    elif m not in ("LevelUp", "LevelUpNinjask", "LevelUpMale", "LevelUpFemale", "LevelUpMorning", "LevelUpNight", "LevelUpDusk"):
        c["trigger"] = "other"; cond["method"] = m; cond["argument"] = a
    if m in LOC: cond["location"] = LOC[m]
    if m.endswith("EC100"): cond["personality"] = "ec%100==0"
    if m.endswith("ECElse"): cond["personality"] = "ec%100!=0"
    if m == "LevelUpNinjask": cond["also_creates"] = None
    cond.pop("also_creates", None)
    return c

prev_evo = {(r["from_form_id"], r["to_form_id"]): int(r["id"]) for r in read_csv("evolution")}
next_evo = max(prev_evo.values(), default=0) + 1
evo_pairs = {}          # (from, to) -> id
evo_methods = collections.defaultdict(list)   # (evo id, game) -> [cols]
skipped_evo = []
for ctx, rows in EVO.items():
    games = CTX_GAMES[ctx] + [d for d, p in DERIVED.items() if p in CTX_GAMES[ctx]]
    for r in rows:
        cols = method_cols(ctx, r)
        for g in games:
            fk = KEYMAP[g].get((r["species"], r["form"])); tk = KEYMAP[g].get((r["to_species"], r["to_form"]))
            if not fk or not tk or (fk, g) not in present or (tk, g) not in present:
                skipped_evo.append((ctx, g, r["species"], r["form"], r["to_species"], r["to_form"], r["method"])); continue
            if (fk, tk) not in evo_pairs:
                evo_pairs[(fk, tk)] = prev_evo.get((fk, tk)) or 0
            lst = evo_methods[((fk, tk), g)]
            if cols not in lst: lst.append(cols)
for k in sorted(evo_pairs):
    if not evo_pairs[k]:
        evo_pairs[k] = next_evo; next_evo += 1

# cross-check (Scarlet/Violet only): Showdown gen9 + PokeAPI pokemon_evolution, simplified signature
pk_evo_rows = collections.defaultdict(list)
for r in pcsv("pokemon_evolution"): pk_evo_rows[int(r["evolved_species_id"])].append(r)
PK_TRIG = {"1": "level-up", "2": "trade", "3": "use-item"}
def sd_key(key):
    sp, _, suf = key.partition("-"); sp = int(sp)
    for c in ([sdid(SD_SUFFIX.get(suf, suf))] if suf else [""]):
        i = sd_index["sv"].get((sp, c))
        if i: return i
    return None
def simple(c):
    t = c["trigger"] if c["trigger"] in ("level-up", "use-item", "trade") else ("level-up" if c["trigger"] == "walk" else "other")
    item = pk_items[c["item_id"]]["identifier"] if c["item_id"] else None
    return canon([t, c["min_level"] if t == "level-up" else None, item if t == "use-item" else None])
d_pkevo = pkdoc("pokemon_evolution"); d_sdevo = sdmdoc("pokedex", "gen9")
pk_item_slug = {int(i): r["identifier"] for i, r in pk_items.items()}
def pokeapi_sigs(to_key):
    u = U.get(to_key)
    if not u: return None
    sp = u["species"]; out_ = set()
    for r in pk_evo_rows.get(sp, []):
        if r["evolved_pokemon_form_id"] and int(r["evolved_pokemon_form_id"]) != u["form_id"]: continue
        if not r["evolved_pokemon_form_id"] and not u["fdef"]: continue
        t = PK_TRIG.get(r["evolution_trigger_id"], "other")
        lvl = int(r["minimum_level"]) if r["minimum_level"] else None
        item = pk_item_slug.get(int(r["trigger_item_id"])) if r["trigger_item_id"] else None
        out_.add(canon([t, lvl if t == "level-up" else None, item if t == "use-item" else None]))
    return out_ or None
SD_T = {"level": "level-up", "levelFriendship": "level-up", "levelExtra": "level-up", "levelHold": "level-up", "levelMove": "level-up",
        "useItem": "use-item", "trade": "trade", "other": "other"}
def showdown_sigs(to_key):
    i = sd_key(to_key)
    e = SDM["evos"]["sv"].get(i) if i else None
    if not e: return None
    t = SD_T.get(e["evoType"], "other")
    return {canon([t, e["evoLevel"] if t == "level-up" else None, norm(e["evoItem"]) if (t == "use-item" and e["evoItem"]) else None])}

evo_rows, em_rows = [], []
for (fk, tk), eid in sorted(evo_pairs.items(), key=lambda x: x[1]):
    evo_rows.append([eid, fk, tk])
    gms = sorted({g for (p, g) in evo_methods if p == (fk, tk)}, key=order_games.index)
    resolve("evolution", row_key(eid), "*", [("pkhex", d_evo, [fk, tk])])
    for g in gms:
        for v, c in enumerate(evo_methods[((fk, tk), g)], 1):
            cond = canon(c["conditions"]) if c["conditions"] else None
            row = [eid, g, v, c["trigger"], c["min_level"], c["item_id"], c["held_item_id"], c["known_move_id"], c["known_move_type_id"],
                   c["location_id"], c["time_of_day"], c["gender"], c["min_friendship"], c["min_affection"], cond]
            em_rows.append(row)
            obs = [("pkhex", d_evo, row[3:])]
            if g == "sv":
                mine = simple(c)
                for src, dd, sigs in (("pokeapi", d_pkevo, pokeapi_sigs(tk)), ("showdown", d_sdevo, showdown_sigs(tk))):
                    if sigs: obs.append((src, dd, row[3:] if mine in sigs else sorted(sigs)))
            resolve("evolution_method", row_key(eid, g, v), "*", obs)
out["evolution"] = (["id", "from_form_id", "to_form_id"], evo_rows)
out["evolution_method"] = (["evolution_id", "game_id", "variant", "trigger", "min_level", "item_id", "held_item_id", "known_move_id",
                            "known_move_type_id", "location_id", "time_of_day", "gender", "min_friendship", "min_affection", "conditions"], em_rows)

# evolution chains: connected species groups from game data, ids from PokeAPI
pk_chain = {int(r["id"]): int(r["evolution_chain_id"]) for r in pk_species.values() if r["evolution_chain_id"]}
parent = {}
def find(x):
    while parent.setdefault(x, x) != x: x = parent[x]
    return x
for (fk, tk) in evo_pairs:
    a, b = int(fk.partition("-")[0]), int(tk.partition("-")[0])
    parent[find(a)] = find(b)
comp = collections.defaultdict(set)
for sid in range(1, 1026): comp[find(sid)].add(sid)
chain_of = {}
d_pkchain = pkdoc("pokemon_species")
chain_rows = {}
by_chain = collections.defaultdict(list)
for members in comp.values():
    ids = collections.Counter(pk_chain.get(s) for s in members if pk_chain.get(s))
    if ids: by_chain[ids.most_common(1)[0][0]].append(sorted(members))
for cid, groups in sorted(by_chain.items()):
    for g in groups:
        for s in g: chain_of[s] = cid
    pk_members = sorted(s for s, c in pk_chain.items() if c == cid and s <= 1025)
    # game data: list of evolution families sharing this PokeAPI chain (Phione/Manaphy, Meltan/Melmetal: two families)
    resolve("evolution_chain", row_key(cid), "*", [("pkhex", d_evo, sorted(groups)), ("pokeapi", d_pkchain, [pk_members])])
    chain_rows[cid] = [cid, None]
out["evolution_chain"] = (["id", "baby_item_id"], [chain_rows[k] for k in sorted(chain_rows)])
for r in sp_rows:
    if r[0] in chain_of:
        r[3] = chain_of[r[0]]
        resolve("species", row_key(r[0]), "evolution_chain_id", [("pkhex", d_evo, chain_of[r[0]]), ("pokeapi", d_pkchain, pk_chain.get(r[0]))])

# items table (evolution items and held items referenced above)
d_pkitems = pkdoc("items")
item_rows, ig_rows = [], []
for iid in sorted(item_used):
    ctx, idx = item_used[iid]
    r = pk_items[iid]
    item_rows.append([iid, r["identifier"], pk_icat.get(r["category_id"]), None])
    resolve("item", row_key(iid), "*", [("pkhex", d_items, nname(ITEMS_EN[ctx][idx])), ("pokeapi", d_pkitems, nname(pk_item_names[iid].get("en")))])
    ext.append(["item", str(iid), "slug", r["identifier"]])
    # game index in the shared item list of Generation IV+ games (names in 10 languages come from it)
    g9 = [i for i, n in enumerate(ITEMS_EN["gen9"]) if nname(n) == nname(ITEMS_EN[ctx][idx])]
    if g9: ext.append(["item", str(iid), "game-index", str(g9[0])])
    for lang in LANGS:
        obs = []
        if g9 and lang in NMI and g9[0] < len(NMI[lang]["items"]) and NMI[lang]["items"][g9[0]]:
            obs.append(("pkhex", d_nmi, NMI[lang]["items"][g9[0]]))
        if lang in pk_item_names[iid]: obs.append(("pokeapi", pkdoc("item_names"), pk_item_names[iid][lang]))
        add_tr("item", iid, "name", lang, obs)
out["item"] = (["id", "slug", "category", "go_template"], item_rows)

# ----------------------------------------------------------------------------- regional Pokédex
def parse_dex(text, alola=False):
    """Returns {national: [regional numbers…]} from a Bulbapedia list (templates + raw multi-form rows)."""
    res = collections.defaultdict(list)
    for m in re.finditer(r"\{\{[Rr]dex(?:/(\w+))?\|([^{}]*)\}\}", text):
        p = m.group(2).split("|")
        try:
            if alola: res[int(p[5])].append(tuple(int(x) if x.strip().isdigit() else None for x in p[:5]))
            else: res[int(p[1])].append(int(p[0]))
        except (ValueError, IndexError): pass
    for blk in re.split(r"\n\|-", text):
        cells = re.findall(r"^\|[^\n|]*\|\s*#(\d+|—|-)\s*$", blk, re.M)
        if len(cells) >= 2 and cells[-1].isdigit():
            nat = int(cells[-1])
            if alola:
                isl = [int(a) if b == "yes" else None for a, b in re.findall(r'data-sort-value="(\d+)"[^\n]*\{\{(yes|no)\}\}', blk)[:4]]
                res[nat].append(tuple([int(cells[0]) if cells[0].isdigit() else None] + isl))
            elif cells[0].isdigit(): res[nat].append(int(cells[0]))
    return res
def section(text, start=None, stop=None):
    i = text.index("==List of Pokémon by")
    t = text[i:]
    j = re.search(r"\n==[^=]", t[5:]); t = t[: j.start() + 5] if j else t
    if start: t = t[t.index(start):]
    if stop and stop in t: t = t[: t.index(stop)]
    return t
B = "List of Pokémon by "
DEX = [  # id, game, region, pokeapi identifier, page, start, stop, island index
    ("rb-kanto", "rb", "kanto", "kanto", B + "Kanto Pokédex number", None, "===Let's Go", None),
    ("y-kanto", "y", "kanto", "kanto", B + "Kanto Pokédex number", None, "===Let's Go", None),
    ("frlg-kanto", "frlg", "kanto", "kanto", B + "Kanto Pokédex number", None, "===Let's Go", None),
    ("lgpe-kanto", "lgpe", "kanto", "letsgo-kanto", B + "Kanto Pokédex number", None, None, None),
    ("gs-johto", "gs", "johto", "original-johto", B + "New Pokédex number", None, None, None),
    ("c-johto", "c", "johto", "original-johto", B + "New Pokédex number", None, None, None),
    ("hgss-johto", "hgss", "johto", "updated-johto", B + "Johto Pokédex number", None, None, None),
    ("rs-hoenn", "rs", "hoenn", "hoenn", B + "Hoenn Pokédex number in Generation III", None, "===Unseen numbers", None),
    ("e-hoenn", "e", "hoenn", "hoenn", B + "Hoenn Pokédex number in Generation III", None, "===Unseen numbers", None),
    ("oras-hoenn", "oras", "hoenn", "updated-hoenn", B + "Hoenn Pokédex number in Generation VI", None, None, None),
    ("dp-sinnoh", "dp", "sinnoh", "original-sinnoh", B + "Sinnoh Pokédex number", None, "===Platinum expansion", None),
    ("pt-sinnoh", "pt", "sinnoh", "extended-sinnoh", B + "Sinnoh Pokédex number", None, None, None),
    ("bdsp-sinnoh", "bdsp", "sinnoh", "original-sinnoh", B + "Sinnoh Pokédex number", None, "===Platinum expansion", None),
    ("bw-unova", "bw", "unova", "original-unova", B + "Unova Pokédex number in Pokémon Black and White", None, None, None),
    ("b2w2-unova", "b2w2", "unova", "updated-unova", B + "Unova Pokédex number in Pokémon Black 2 and White 2", None, None, None),
    ("xy-kalos-central", "xy", "kalos", "kalos-central", B + "Central Kalos Pokédex number", None, None, None),
    ("xy-kalos-coastal", "xy", "kalos", "kalos-coastal", B + "Coastal Kalos Pokédex number", None, None, None),
    ("xy-kalos-mountain", "xy", "kalos", "kalos-mountain", B + "Mountain Kalos Pokédex number", None, None, None),
    ("sm-alola", "sm", "alola", "original-alola", B + "Alola Pokédex number in Pokémon Sun and Moon", None, None, 0),
    ("sm-melemele", "sm", "alola", "original-melemele", B + "Alola Pokédex number in Pokémon Sun and Moon", None, None, 1),
    ("sm-akala", "sm", "alola", "original-akala", B + "Alola Pokédex number in Pokémon Sun and Moon", None, None, 2),
    ("sm-ulaula", "sm", "alola", "original-ulaula", B + "Alola Pokédex number in Pokémon Sun and Moon", None, None, 3),
    ("sm-poni", "sm", "alola", "original-poni", B + "Alola Pokédex number in Pokémon Sun and Moon", None, None, 4),
    ("usum-alola", "usum", "alola", "updated-alola", B + "Alola Pokédex number in Pokémon Ultra Sun and Ultra Moon", None, None, 0),
    ("usum-melemele", "usum", "alola", "updated-melemele", B + "Alola Pokédex number in Pokémon Ultra Sun and Ultra Moon", None, None, 1),
    ("usum-akala", "usum", "alola", "updated-akala", B + "Alola Pokédex number in Pokémon Ultra Sun and Ultra Moon", None, None, 2),
    ("usum-ulaula", "usum", "alola", "updated-ulaula", B + "Alola Pokédex number in Pokémon Ultra Sun and Ultra Moon", None, None, 3),
    ("usum-poni", "usum", "alola", "updated-poni", B + "Alola Pokédex number in Pokémon Ultra Sun and Ultra Moon", None, None, 4),
    ("sw-galar", "sw", "galar", "galar", B + "Galar Pokédex number", None, None, None),
    ("swisle-isle-of-armor", "swisle", "galar", "isle-of-armor", B + "Isle of Armor Pokédex number", None, None, None),
    ("swcrown-crown-tundra", "swcrown", "galar", "crown-tundra", B + "Crown Tundra Pokédex number", None, None, None),
    ("la-hisui", "la", "hisui", "hisui", B + "Hisui Pokédex number", None, None, None),
    ("sv-paldea", "sv", "paldea", "paldea", B + "Paldea Pokédex number", None, None, None),
    ("svmask-kitakami", "svmask", "kitakami", "kitakami", B + "Kitakami Pokédex number", None, None, None),
    ("svdisk-blueberry", "svdisk", "blueberry", "blueberry", B + "Blueberry Pokédex number", None, None, None),
    ("za-lumiose", "za", "kalos", "lumiose-city", B + "Lumiose Pokédex number", None, None, None),
    ("zadlc-hyperspace", "zadlc", "kalos", "hyperspace", B + "Hyperspace Pokédex number", None, None, None),
]
PKX_DEX = {"sw-galar": ("sw", "galar"), "swisle-isle-of-armor": ("sw", "isle-of-armor"), "swcrown-crown-tundra": ("sw", "crown-tundra"),
           "bdsp-sinnoh": ("bdsp", "sinnoh"), "la-hisui": ("la", "hisui"), "sv-paldea": ("sv", "paldea"),
           "svmask-kitakami": ("sv", "kitakami"), "svdisk-blueberry": ("sv", "blueberry"), }
# Z-A: PersonalInfo9ZA.DexIndex is not a Pokédex number for species outside the Lumiose Pokédex (values repeat, e.g. 207 for
# both Voltorb and Pupitar), so it is not used; Z-A Pokédex numbers come from PokeAPI + Bulbapedia.
pk_dexes = {r["identifier"]: int(r["id"]) for r in pcsv("pokedexes")}
pk_dexnum = collections.defaultdict(dict)
for r in pcsv("pokemon_dex_numbers"): pk_dexnum[int(r["pokedex_id"])][int(r["species_id"])] = int(r["pokedex_number"])
d_pkdex = pkdoc("pokemon_dex_numbers")
dex_rows, entry_rows, dex_unpublished = [], [], []
regions = {r[0] for r in R.REGIONS}
for order, (did, game, region, pkident, page, start, stop, island) in enumerate(DEX, 1):
    text, d_b = bulba(page)
    parsed = parse_dex(section(text, start, stop), alola=island is not None)
    bul = {}
    for nat, vals in parsed.items():
        nums = [(list(v) + [None] * 5)[island] for v in vals] if island is not None else vals
        nums = [n for n in nums if n is not None]
        if nums: bul[nat] = min(nums)
    pkid = pk_dexes.get(pkident)
    pkv = pk_dexnum.get(pkid, {}) if pkid else {}
    px = {}
    if did in PKX_DEX:
        g, name = PKX_DEX[did]
        for r in pkx[g]:
            n = (r.get("dex") or {}).get(name)
            if n: px[r["species"]] = min(n, px.get(r["species"], n))
    dex_rows.append([did, game, region if region in regions else None, order, pkid])
    resolve("pokedex", row_key(did), "*", [("pokeapi", pkdoc("pokedexes"), [game, pkident]), ("bulbapedia", d_b, [game, pkident])] if pkid else [("bulbapedia", d_b, [game, pkident])])
    for sid in sorted(set(bul) | set(pkv) | set(px)):
        if sid > 1025: continue
        obs = []
        if sid in px: obs.append(("pkhex", pkxdoc(PKX_DEX[did][0]), px[sid]))   # index 0 = no data, not "absent"
        if pkv: obs.append(("pokeapi", d_pkdex, pkv.get(sid, -1)))
        if bul: obs.append(("bulbapedia", d_b, bul.get(sid, -1)))
        n0 = (len(citations), len(verifs), len(discreps))
        v, st = resolve("pokedex_entry", row_key(did, sid), "number", obs)
        if v == -1:   # majority says "not in this Pokédex": no row, keep the disagreement for the report only
            dex_unpublished.append((did, sid, [(o[0], o[2]) for o in obs]))
            del citations[n0[0]:], verifs[n0[1]:], discreps[n0[2]:]
            continue
        if st in PUBLISHED: entry_rows.append([did, sid, v])
        else: dex_unpublished.append((did, sid, [(o[0], o[2]) for o in obs]))
out["pokedex"] = (["id", "game_id", "region_id", "sort_order", "pokeapi_id"], dex_rows)
out["pokedex_entry"] = (["pokedex_id", "species_id", "number"], entry_rows)

# ----------------------------------------------------------------------------- species categories (genus)
GLANG = ["en", "ja", "fr", "de", "it", "es", "ko", "zh-Hant", "zh-Hans"]
cat_text, d_bcat = bulba("List of categories in other languages")
bul_genus = {}
for line in cat_text.split("\n"):
    m = re.match(r"\|\s*style=\"font-family:monospace,monospace\"\s*\|\s*(\d{4})\s*\|\|(.*)$", line)
    if not m or int(m.group(1)) in bul_genus: continue   # first row = default form (regional forms follow)
    cells = [c.strip() for c in m.group(2).split("||")]
    if len(cells) < 11: continue
    def tt(x): return re.sub(r"\{\{tt\|([^|}]*)\|[^}]*\}\}", r"\1", x)
    def clean(x): return re.sub(r"''.*?''", "", tt(x)).replace("<br>", " ").strip()
    en, ja, _ro, fr, de, it, es, ko, zh = [clean(c) for c in cells[2:11]]
    ko = ko.split(" ")[0] if ko else ko
    zh = re.findall(r"[\u3400-\u9fff]+", cells[10])
    zh_t, zh_s = (zh[0], zh[1]) if len(zh) >= 2 else ((zh[0], zh[0]) if zh else ("", ""))
    vals = dict(en=en, ja=ja, fr=fr, de=de, it=it, es=es, ko=ko, **{"zh-Hant": zh_t, "zh-Hans": zh_s})
    bul_genus[int(m.group(1))] = {k: v for k, v in vals.items() if v and v not in ("—", "-")}
STRIP = re.compile(r"(Pokémon|ポケモン|포켓몬|寶可夢|宝可梦|-|\s|\*)")
def core(x): return STRIP.sub("", nfkc(x or "")).lower().replace("œ", "oe")
def core_de(x): return re.sub(r"(en|es|n|s|e)$", "", core(x))   # German compounds add a linking ending (Drache → Drachen-Pokémon)
pk_genus = collections.defaultdict(dict)
for r in pcsv("pokemon_species_names"):
    l = PK_LANG.get(pk_lang[r["local_language_id"]])
    if l and r["genus"]: pk_genus[int(r["pokemon_species_id"])][l] = r["genus"]
d_pkgen = pkdoc("pokemon_species_names")
for sid in range(1, 1026):
    for lang in GLANG:
        obs = []
        if lang not in pk_genus[sid]: continue   # wiki-only value: never stored
        if lang in pk_genus[sid]: obs.append(("pokeapi", d_pkgen, pk_genus[sid][lang]))
        b = bul_genus.get(sid, {}).get(lang)
        cmp = core_de if lang == "de" else core
        if b:   # the wiki may list several words ("Pez Color / Pez Dorado"): keep the one matching, if any
            alts = [a.strip() for a in b.split(" / ")]
            b = next((a for a in alts if cmp(a) == cmp(pk_genus[sid][lang])), alts[0])
            obs.append(("bulbapedia", d_bcat, b))
        if not obs: continue
        rk = row_key("species", str(sid), "genus", lang, None, None)
        v, st = resolve("translation", rk, "text", obs, cmp)
        if v and st in PUBLISHED:   # stored text = full in-game string (the wiki gives the core word only, used as a check)
            tr_rows.append(["species", str(sid), "genus", lang, None, None, pk_genus[sid][lang], 1])

# ----------------------------------------------------------------------------- form names (published only when game strings and PokeAPI agree)
pk_form_names = collections.defaultdict(dict)
for r in pcsv("pokemon_form_names"):
    l = PK_LANG.get(pk_lang[r["local_language_id"]])
    if l and r["form_name"]: pk_form_names[int(r["pokemon_form_id"])][l] = r["form_name"]
d_pkfn = pkdoc("pokemon_form_names")
form_index = {}
for g in reversed(order_games):
    for (sp, idx), k in KEYMAP.get(g, {}).items(): form_index.setdefault(k, (sp, idx))
fn_stats = collections.Counter()
for key in sorted(form_ids):
    u = U.get(key)
    if not u or key == str(u["species"]) and not u["form_ident"]: continue
    if key not in form_index: continue
    sp, idx = form_index[key]
    for lang in LANGS:
        p = (pkx_names.get(lang, {}).get("forms", {}).get(str(sp)) or [])
        pv = p[idx] if idx < len(p) else None
        av = pk_form_names[u["form_id"]].get(lang)
        if not pv or not av: continue
        rk = row_key("form", key, "form_name", lang, None, None)
        same = nfkc(pv) == nfkc(av)
        # PKHeX form labels are an editorial list (tier 3 for form names, see source note): agreement of both is required
        obs = [("pokeapi", d_pkfn, av), ("pkhex", d_pkx, pv)]
        n0 = (len(citations), len(verifs), len(discreps))
        st = "unanimous" if same else "disputed"
        for s, dd, val in obs: citations.append(("translation", rk, "text", dd, canon(val), 1 if nfkc(val) == nfkc(av) else 0))
        if not same: discreps.append(("translation", rk, "text", canon(av), "open", canon([{"source": "pkhex", "document_id": d_pkx, "value": pv}]), None))
        verifs.append(("translation", rk, "text", "seeded" if not same else "unanimous", sha256_text(canon(av)),
                       sha256_text("|".join(sorted(f"{s}:{sha256_text(canon(val))}" for s, dd, val in obs)))))
        fn_stats[(lang, same)] += 1
        if same: tr_rows.append(["form", key, "form_name", lang, None, None, av, 1])
        else:
            del citations[n0[0]:], verifs[n0[1]:], discreps[n0[2]:]   # not stored, listed in the report

PHASE1B_STATS = dict(evolutions=len(evo_rows), evolution_methods=len(em_rows), chains=len(chain_rows), items=len(item_rows),
                     pokedexes=len(dex_rows), pokedex_entries=len(entry_rows), dex_unpublished=len(dex_unpublished),
                     item_unmapped=sorted(map(str, item_unmapped)), evo_skipped=len(skipped_evo),
                     form_names={f"{l}:{'ok' if s else 'diff'}": n for (l, s), n in sorted(fn_stats.items())})
json.dump(dict(stats=PHASE1B_STATS, dex_unpublished=dex_unpublished, evo_skipped=sorted(set(skipped_evo))),
          open(ROOT / "reports/phase1b-details.json", "w"), ensure_ascii=False, indent=0)
print("phase1b", json.dumps({k: v for k, v in PHASE1B_STATS.items() if k != "item_unmapped"}, ensure_ascii=False), "items unmapped:", len(item_unmapped))
