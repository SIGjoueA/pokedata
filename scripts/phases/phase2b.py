# Phase 2b — movesets (table learnset), vérifiés par ensemble (forme × jeu × méthode) : schéma 1.1.0, option A.
# Exécuté par scripts/import_data.py après la phase 2, dans le même espace de noms.
# Données : extraction des jeux (PKHeX, rang 1). Contrôles : PokeAPI (pokemon_moves.csv) et Showdown (learnsets.ts du mod du jeu).
# Une ligne de verification par ensemble : row_key = [form_id, game_id, method_id], column_name '*',
# value_sha256 = empreinte de la liste triée [move_id, level, version_id] ; une citation par source avec l'empreinte et
# la taille de l'ensemble observé ; les capacités en plus / en moins d'une source vont dans discrepancy.alternatives.
LS_METHODS = ["level-up", "egg", "machine", "tutor", "reminder", "mastery", "plus"]
LEVELED = {"level-up", "mastery", "plus"}
LS_GAMES = {"rb": ["rb"], "y": ["y"], "gs": ["gs"], "c": ["c"], "rs": ["rs"], "e": ["e"], "frlg": ["fr", "lg"], "dp": ["dp"], "pt": ["pt"],
            "hgss": ["hgss"], "bw": ["bw"], "b2w2": ["b2w2"], "xy": ["xy"], "oras": ["oras"], "sm": ["sm"], "usum": ["usum"], "lgpe": ["lgpe"],
            "sw": ["sw"], "bdsp": ["bdsp"], "la": ["la"], "sv": ["sv"], "za": ["za"]}
LS_VERSION = {"fr": "firered", "lg": "leafgreen"}
MOVE_IDS = {r[0] for r in move_rows}

# ---------------------------------------------------------------- game data (tier 1)
ls_rows = {}                                  # (form, game, move, method, level) -> [version set, sort_order]
ls_docs = collections.defaultdict(set)        # game -> pkhex doc ids
ls_drop = collections.Counter()
for g, files in LS_GAMES.items():
    for f in files:
        p = DUMP / f"learnset_{f}.json"
        if not p.exists(): continue
        d = doc("pkhex", f"{PKXREV} · Learnset {f.upper()} (learnset_{f}.json)", PKXREV, file_sha(p))
        ls_docs[g].add(d)
        order = collections.Counter()
        for sp, fi, meth, mv, lvl in json.load(open(p, encoding="utf-8")):
            k = KEYMAP[g].get((sp, fi))
            if not k: ls_drop["form-unmapped"] += 1; continue
            if (k, g) not in present: ls_drop["form-not-in-game"] += 1; continue
            if mv not in MOVE_IDS: ls_drop["move-unknown"] += 1; continue
            method = "level-up" if meth == "level-up-1" else meth
            level = 1 if meth == "level-up-1" else (lvl if method in LEVELED else 0)
            key = (k, g, mv, method, level)
            if key not in ls_rows:
                so = order[(k, method, level)] if method in LEVELED else 0
                order[(k, method, level)] += 1
                ls_rows[key] = [set(), so]
            ls_rows[key][0].add(f)
nfiles = {g: len(fs) for g, fs in LS_GAMES.items()}
learnset_rows = []
SETS = collections.defaultdict(list)          # (form, game, method) -> [[move, level, version]]
for (k, g, mv, method, level), (vs, so) in ls_rows.items():
    ver = None if len(vs) == nfiles[g] else LS_VERSION[next(iter(vs))]
    learnset_rows.append([k, g, mv, method, level, ver, so, None])
    SETS[(k, g, method)].append([mv, level, ver])

# ---------------------------------------------------------------- PokeAPI (tier 3)
VG_OF = {x[0]: x[7] for x in R.GAMES if x[7]}
LS_VGS = {g: {VG_ID[VG_OF[g]]} | {VG_ID[VG_OF[d]] for d, p in DERIVED.items() if p == g and d in VG_OF} for g in LS_GAMES}
VG2G = {vg: g for g, vgs in LS_VGS.items() for vg in vgs}
PKP2FORMS = collections.defaultdict(list)
for et, eid, system, val in out["external_id"][1]:
    if et == "form" and system == "pokeapi-pokemon": PKP2FORMS[int(val)].append(eid)
PK_METHOD = {"1": "level-up", "2": "egg", "3": "tutor", "4": "machine", "13": "reminder"}
pk_ls = collections.defaultdict(set)          # (form, game, method) -> {(move, level)}
with open(PK / "pokemon_moves.csv", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        g = VG2G.get(int(r["version_group_id"]))
        m = PK_METHOD.get(r["pokemon_move_method_id"])
        if not g or not m: continue
        mv, lvl = int(r["move_id"]), int(r["level"] or 0)
        for k in PKP2FORMS.get(int(r["pokemon_id"]), ()):
            if m == "level-up":
                if g == "la" and r["enhancement_level"]: pk_ls[(k, g, "mastery")].add((mv, int(r["enhancement_level"])))
                if g == "za" and r["enhancement_level"]: pk_ls[(k, g, "plus")].add((mv, int(r["enhancement_level"])))
                pk_ls[(k, g, m)].add((mv, lvl))
            else:
                pk_ls[(k, g, m)].add((mv, 0))
pk_ls_forms = {(k, g) for (k, g, _) in pk_ls}            # PokeAPI has this form in this game: absent sets mean "not learnt"
pk_rem_games = {g for (_, g, m) in pk_ls if m == "reminder"}
d_pkls = pkdoc("pokemon_moves")

# ---------------------------------------------------------------- Showdown (tier 3), only where the mod data is per game
# Showdown codes are per generation; they are per game only where the generation has one game in Showdown's main data
# (Sword/Shield, Scarlet/Violet) or a mod of its own (BDSP, Legends: Arceus, Let's Go, Legends: Z-A). Level-up lists merge
# the levels of every release of the generation: only machine, tutor and egg lists are compared.
SD_LS = {"sv": ("gen9", "9"), "sw": ("gen9", "8"), "bdsp": ("gen8bdsp", "8"), "la": ("gen8legends", "8"), "lgpe": ("gen7letsgo", "7"),
         "za": ("gen9legends", "9")}
SD_CODE = {"M": "machine", "T": "tutor", "E": "egg"}
SD_MOVE = {}
for et, eid, system, val in out["external_id"][1]:
    if et == "move" and system == "showdown": SD_MOVE[val] = int(eid)
def sd_species_id(key, game):
    sg = game
    if sg not in sd_index: return None
    sp, _, suf = key.partition("-")
    sp = int(sp)
    cands = [sdid(SD_SUFFIX.get(suf, suf))] if suf else [""]
    if key in ("386-attack", "386-defense", "386-speed"): cands = [suf]
    if sp == 774: cands = ["meteor"] if (not suf or suf.endswith("meteor")) else [""]
    for c in cands:
        i = sd_index[sg].get((sp, c))
        if i: return i
    return None
def sd_learnset(key, game):
    mod, gen = SD_LS[game]
    i = sd_species_id(key, game)
    if not i: return None, None
    src_mod = mod
    ls = SDM["learnsets"].get(mod, {}).get(i)
    if not ls: return None, None
    res = collections.defaultdict(set)
    for mvid, codes in ls.items():
        mv = SD_MOVE.get(mvid)
        if mv is None: continue
        for c in codes:
            if not c.startswith(gen) or len(c) < 2: continue
            m = SD_CODE.get(c[1])
            if not m: continue
            res[m].add((mv, 0))
    return res, src_mod

# ---------------------------------------------------------------- set-level verification
def set_obs(s):
    return canon(sorted(s))
def resolve_set(rk, game, chosen, obs):
    """chosen: list of [move, level, version] (game data); obs: list of (source, doc, set of (move, level)) to compare."""
    mine = {(m, l) for m, l, v in chosen}
    chosen_c = sorted(chosen, key=lambda x: (x[0], x[1], x[2] or ""))
    vh = sha256_text(canon(chosen_c))
    allobs = [("pkhex", d, None) for d in sorted(ls_docs[game])] + obs
    parts = []
    dissent = []
    for s, d, val in allobs:
        if val is None:
            citations.append(("learnset", rk, "*", d, canon({"n": len(chosen_c), "sha256": vh}), 1)); parts.append(f"{s}:{vh}"); continue
        sh = sha256_text(set_obs(val))
        ok = val == mine
        citations.append(("learnset", rk, "*", d, canon({"n": len(val), "sha256": sh}), 1 if ok else 0)); parts.append(f"{s}:{sh}")
        if not ok:
            dissent.append({"source": s, "document_id": d, "missing": sorted(mine - val), "extra": sorted(val - mine)})
    if dissent:
        discreps.append(("learnset", rk, "*", canon({"n": len(chosen_c), "sha256": vh}), "game-data", canon(dissent), None))
    verifs.append(("learnset", rk, "*", "game-data", vh, sha256_text("|".join(sorted(parts)))))
    return dissent

ls_stats = collections.Counter()
ls_agree = collections.Counter()
sd_cache = {}
for (k, g, method), chosen in sorted(SETS.items()):
    rk = row_key(k, g, method)
    obs = []
    if (k, g) in pk_ls_forms and (method != "reminder" or g in pk_rem_games):
        obs.append(("pokeapi", d_pkls, pk_ls.get((k, g, method), set())))
    if g in SD_LS and method in ("machine", "tutor", "egg"):
        if (k, g) not in sd_cache: sd_cache[(k, g)] = sd_learnset(k, g)
        res, src_mod = sd_cache[(k, g)]
        if res:   # Showdown has this form for this generation
            obs.append(("showdown", sdmdoc("learnsets", src_mod), res.get(method, set())))
    dis = resolve_set(rk, g, chosen, obs)
    ls_stats[(g, method, "sets")] += 1
    for s, d, val in obs:
        ls_agree[(g, method, s, "cited")] += 1
        if not any(x["source"] == s for x in dis): ls_agree[(g, method, s, "agree")] += 1

out["learn_method"] = (["id"], [[m] for m in LS_METHODS])
out["learnset"] = (["form_id", "game_id", "move_id", "method_id", "level", "version_id", "sort_order", "extra"], learnset_rows)
LS_STATS = dict(rows=len(learnset_rows), sets=len(SETS), dropped=dict(ls_drop),
                by_game={g: sum(1 for r in learnset_rows if r[1] == g) for g in LS_GAMES},
                agreement={f"{g}:{m}:{s}": [ls_agree[(g, m, s, "agree")], ls_agree[(g, m, s, "cited")]]
                           for (g, m, s, kind) in sorted(ls_agree) if kind == "cited"})
json.dump(LS_STATS, open(ROOT / "reports/phase2b-details.json", "w"), ensure_ascii=False, indent=0)
print("phase2b", json.dumps({k: v for k, v in LS_STATS.items() if k != "agreement"}, ensure_ascii=False))
