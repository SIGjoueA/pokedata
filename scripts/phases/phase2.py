# Phase 2 — capacités (valeurs par jeu), CT/CS/DT, noms et descriptions ; movesets calculés localement (non publiés).
# Exécuté par scripts/import_data.py après la phase 1b, dans le même espace de noms.
import base64, urllib.parse
MI = json.load(open(DUMP / "moveinfo.json", encoding="utf-8"))
MI_T = {c: list(base64.b64decode(v["types"])) for c, v in MI.items()}
MI_PP = {c: list(base64.b64decode(v["pp"])) for c, v in MI.items()}
MI_DUMMY = {c: set(v["dummied"]) for c, v in MI.items()}
MACH = json.load(open(DUMP / "machines.json", encoding="utf-8"))
d_mi = doc("pkhex", f"{PKXREV} · MoveInfo (types, PP, dummied moves: moveinfo.json)", PKXREV, file_sha(DUMP / "moveinfo.json"))
d_mach = doc("pkhex", f"{PKXREV} · machine move lists (machines.json)", PKXREV, file_sha(DUMP / "machines.json"))
CTX_GEN = {"gen1": 1, "gen2": 2, "gen3": 3, "gen4": 4, "gen5": 5, "gen6": 6, "gen7": 7, "gen7b": 7, "gen8": 8, "gen8a": 8, "gen8b": 8, "gen9": 9, "gen9a": 9}
MOVE_GAMES = ["rb", "y", "gs", "c", "rs", "e", "frlg", "dp", "pt", "hgss", "bw", "b2w2", "xy", "oras", "sm", "usum", "lgpe",
              "sw", "bdsp", "la", "sv", "za"]
EN_MOVES = NMI["en"]["moves"]
NMOVES = len(EN_MOVES) - 1
def strip_ps(x): return re.sub(r"\s*\((P|S)\)$", "", x or "")
_cnt = collections.Counter(nname(strip_ps(n)) for n in EN_MOVES[1:] if n)
move_by_name = {nname(strip_ps(n)): i for i, n in enumerate(EN_MOVES) if i and n and _cnt[nname(strip_ps(n))] == 1}   # Z-move (P)/(S) pairs: ambiguous
move_by_name.update({"vicegrip": 11, "hijumpkick": 136, "faintattack": 185, "smellingsalt": 265})

pk_moves = {int(r["id"]): r for r in pcsv("moves")}
pk_vg = {r["id"]: (r["identifier"], int(r["order"])) for r in pcsv("version_groups")}
VG_ORDER = {ident: o for ident, o in pk_vg.values()}
VG_ID = {ident: int(i) for i, (ident, o) in pk_vg.items()}
pk_chg = collections.defaultdict(list)
for r in pcsv("move_changelog"): pk_chg[int(r["move_id"])].append(r)
PK_DC = {"1": "status", "2": "physical", "3": "special"}
def pokeapi_move(mid, game):
    """Values of a move in a game from PokeAPI (current values, rolled back with move_changelog)."""
    r = pk_moves.get(mid)
    if not r: return None
    vg = next(x[7] for x in R.GAMES if x[0] == game)
    o = VG_ORDER.get(vg)
    v = {"type": pk_types.get(r["type_id"]), "power": r["power"], "pp": r["pp"], "accuracy": r["accuracy"], "priority": r["priority"]}
    for f in ("type", "power", "pp", "accuracy", "priority"):
        later = sorted((c for c in pk_chg[mid] if VG_ORDER[pk_vg[c["changed_in_version_group_id"]][0]] > o and c[f + "_id" if f == "type" else f]),
                       key=lambda c: VG_ORDER[pk_vg[c["changed_in_version_group_id"]][0]])
        if later:
            v[f] = pk_types.get(later[0]["type_id"]) if f == "type" else later[0][f]
    to_i = lambda x: int(x) if x not in (None, "") else None
    return {"type": v["type"], "power": to_i(v["power"]) or None, "pp": to_i(v["pp"]), "accuracy": to_i(v["accuracy"]),
            "priority": to_i(v["priority"]) or 0, "damage_class": PK_DC.get(r["damage_class_id"])}
SD_BY_NUM = {g: {m["num"]: m for m in mv.values()} for g, mv in SDM["moves"].items()}
def showdown_move(mid, game):
    e = SD_BY_NUM.get(game, {}).get(mid)
    if not e: return None
    return {"type": (e["type"] or "").lower(), "power": e["basePower"] or None, "pp": e["pp"],
            "accuracy": None if e["accuracy"] is True else e["accuracy"], "priority": e["priority"] or 0,
            "damage_class": (e["category"] or "").lower(), "nonstandard": e["isNonstandard"]}

# Serebii attackdex (tier 2) per generation
SEREBII_OF = {"rb": "rby", "y": "rby", "gs": "gs", "c": "gs", "rs": "gen3", "e": "gen3", "frlg": "gen3", "dp": "dp", "pt": "dp", "hgss": "dp",
              "bw": "bw", "b2w2": "bw", "xy": "xy", "oras": "xy", "sm": "sm", "usum": "sm", "sw": "swsh", "sv": "sv"}
SER, SER_DOC = {}, {}
for dex in sorted(set(SEREBII_OF.values())):
    m = MAN.get(f"serebii:attackdex-{dex}")
    if not m: continue
    rows = json.load(open(ROOT / m["path"], encoding="utf-8"))
    SER_DOC[dex] = doc("serebii", m["url"] + f" ({m['revision']})", m["revision"], m["sha256"])
    t = {}
    for r in rows:
        mid = move_by_name.get(nname(r["name"]))
        if mid: t.setdefault(mid, r)
    SER[dex] = t
def num(x):
    x = (x or "").strip().rstrip("%")
    if re.fullmatch(r"\d+\.\d+", x): return int(float(x) + 0.5)   # Generation I pages give x/256 accuracies (74.6 → 75)
    return int(x) if x.isdigit() else None
def serebii_move(mid, game):
    dex = SEREBII_OF.get(game)
    r = SER.get(dex, {}).get(mid) if dex else None
    if not r: return None
    acc = num(r["accuracy"])
    if dex in ("rby", "gs", "gen3") and acc == 100 and num(r["power"]) is None:
        later = SER.get("dp", {}).get(mid)   # Gen I–III pages print 100 for moves without accuracy check ("--" from Gen IV on)
        if later and num(later["accuracy"]) in (None, 101): acc = None
    return {"type": r["type"], "power": num(r["power"]) or None, "pp": num(r["pp"]), "accuracy": None if acc in (None, 101) else acc,
            "damage_class": {"other": "status"}.get(r["category"], r["category"]), "text": r.get("text")}

# Poképédia infobox (tier 2): current values = Scarlet/Violet
ppm = MAN.get("pokepedia:moves")
PPE = json.load(open(ROOT / ppm["path"], encoding="utf-8")) if ppm else {}
FR_MOVES = NMI["fr"]["moves"]
PPE_CAT = {"Physique": "physical", "Spécial": "special", "Spéciale": "special", "Statut": "status"}
FR_TYPE = {nname(n): R.TYPES[i] for i, n in enumerate(pkx_names["fr"]["types"][:18])}
def ppe_doc(title):
    e = PPE[title]
    return doc("pokepedia", f"https://www.pokepedia.fr/{urllib.parse.quote(e['title'].replace(' ', '_'))} (oldid {e['revid']})", str(e["revid"]), sha256_text(e["text"]))
def pokepedia_move(mid):
    title = FR_MOVES[mid] if mid < len(FR_MOVES) else None
    e = PPE.get(title)
    if not e: return None
    box = {}
    head = e["text"].split("\n" + "'" * 3, 1)[0]   # infobox = everything before the first bold title line
    for k, v in re.findall(r"^\|\s*([\wéè-]+)\s*=\s*(.*?)\s*$", head, re.M): box.setdefault(k, v)
    acc = num(box.get("précision")); pw = num(box.get("puissance"))
    pr = box.get("priorité", "").replace("+", "").strip()
    return {"type": FR_TYPE.get(nname(box.get("type"))), "power": pw or None, "pp": num(box.get("pp")), "accuracy": acc or None,
            "damage_class": PPE_CAT.get(box.get("catégorie")), "priority": int(pr) if re.fullmatch(r"-?\d+", pr) else None,
            "doc": ppe_doc(title), "text": e["text"]}

# Bulbapedia priority tables (tier 2)
prio_text, d_prio = bulba("Priority")
PRIO_SECTIONS = {"Generation IX": ["sv"], "Generation VIII": ["sw", "bdsp", "la"], "Let's Go": ["lgpe"], "Sun, Moon": ["sm", "usum"],
                 "Generation VI": ["xy", "oras"], "Generation V": ["bw", "b2w2"], "Generation IV": ["dp", "pt", "hgss"],
                 "Generation III": ["rs", "e", "frlg"], "Generation II": ["gs", "c"], "Generation I": ["rb", "y"]}
PRIO = {}
body = prio_text[prio_text.index("==Move priority=="):]
body = body[: body.index("==In animation==")]
for sec in re.split(r"\n(?====)", body):
    head = sec.split("\n", 1)[0]
    games = next((g for k, g in PRIO_SECTIONS.items() if k in head and not (k == "Generation VII" )), None)
    if head.startswith("===Generation VII===") or not games or "{|" not in sec: continue
    t = {}
    for val, cell in re.findall(r"\|\s*style=\"text-align:center\"\s*\|\s*([+-]?\d+)\s*\n\|([^\n]*)", sec):
        for mname in re.findall(r"\{\{m\|([^|}]+)", cell):
            mid = move_by_name.get(nname(mname))
            if mid: t[mid] = int(val)
    for g in games: PRIO.setdefault(g, t)

PHYS = {"normal", "fighting", "flying", "poison", "ground", "rock", "bug", "ghost", "steel"}
d_pkmoves = pkdoc("moves")
def mdoc_sd(game): return sdmdoc("moves", SDM["mods"][game])

# ----------------------------------------------------------------------------- move table + names
move_rows, mg_rows = [], []
first_gen = {}
for c, pp in MI_PP.items():
    for i in range(1, len(pp)): first_gen[i] = min(first_gen.get(i, 99), CTX_GEN[c])
def kind_of(mid):
    e = SD_BY_NUM["sv"].get(mid) or SD_BY_NUM["usum"].get(mid) or SD_BY_NUM["sw"].get(mid)
    if not e: return "normal"
    if e.get("isZ"): return "z"
    if e.get("isMax"): return "gmax" if isinstance(e["isMax"], str) else "max"
    return "normal"
move_ids = [i for i in range(1, NMOVES + 1) if EN_MOVES[i] and i in pk_moves]
for mid in move_ids:
    r = pk_moves[mid]
    resolve("move", row_key(mid), "*", [("pkhex", d_mi, first_gen.get(mid)), ("pokeapi", d_pkmoves, int(r["generation_id"]))])
    move_rows.append([mid, r["identifier"], first_gen.get(mid) or int(r["generation_id"]), kind_of(mid)])
    ext.append(["move", str(mid), "slug", r["identifier"]])
    ext.append(["move", str(mid), "showdown", nname(strip_ps(EN_MOVES[mid]))])
out["move"] = (["id", "slug", "generation_id", "kind"], move_rows)
pk_move_names = collections.defaultdict(dict)
for r in pcsv("move_names"):
    l = PK_LANG.get(pk_lang[r["local_language_id"]])
    if l: pk_move_names[int(r["move_id"])][l] = r["name"]
d_pmn = pkdoc("move_names")
for mid in move_ids:
    for lang in LANGS:
        lst = NMI[lang]["moves"]
        obs = [("pkhex", d_nmi, strip_ps(lst[mid]))] if mid < len(lst) and lst[mid] else []
        if lang in pk_move_names[mid]: obs.append(("pokeapi", d_pmn, pk_move_names[mid][lang]))
        add_tr("move", mid, "name", lang, obs)

# ----------------------------------------------------------------------------- move values per game
mg_unpublished = collections.Counter()
mg_unpub_list = []
mg_noserebii = collections.Counter()
for g in MOVE_GAMES:
    c = GAME_CTX[g]; gen = CTX_GEN[c]
    pp_t, ty_t = MI_PP[c], MI_T[c]
    for mid in move_ids:
        if mid >= len(pp_t): continue
        dummied = mid in MI_DUMMY[c]
        if dummied and g in ("lgpe",): continue
        ptype = R.TYPES[ty_t[mid]] if ty_t[mid] < 18 else None
        pk = pokeapi_move(mid, g) if VG_ORDER.get(next(x[7] for x in R.GAMES if x[0] == g)) else None
        sd = showdown_move(mid, g); se = serebii_move(mid, g)
        pp_ = pokepedia_move(mid) if g == "sv" else None
        rk = row_key(mid, g)
        # values that need a tier ≤ 2 source besides tier-3 seeds: damage class, power, accuracy
        def pa(v):
            if v is None: return None
            if gen <= 3: return [v["power"], v["accuracy"]]
            return [v["damage_class"], v["power"], v["accuracy"]]
        obs = []
        if se: obs.append(("serebii", SER_DOC[SEREBII_OF[g]], pa(se)))
        if pp_: obs.append(("pokepedia", pp_["doc"], pa(pp_)))
        if pk: obs.append(("pokeapi", d_pkmoves, pa(pk)))
        if sd: obs.append(("showdown", mdoc_sd(g), pa(sd)))
        if not se and not pp_:
            mg_noserebii[g] += 1; continue          # no tier-2 source for this game: row deferred
        n0 = (len(citations), len(verifs), len(discreps))
        chosen, st = resolve("move_game", rk, "power", obs)
        if st not in PUBLISHED or chosen is None:
            mg_unpublished[g] += 1; mg_unpub_list.append((mid, g, [(o[0], o[2]) for o in obs]))
            del citations[n0[0]:], verifs[n0[1]:], discreps[n0[2]:]
            continue
        if gen <= 3:
            status_move = (pk or sd or {}).get("damage_class") == "status"
            dclass = "status" if status_move else ("physical" if ptype in PHYS else "special")
            power, acc = chosen
        else:
            dclass, power, acc = chosen
        if not dclass:
            del citations[n0[0]:], verifs[n0[1]:], discreps[n0[2]:]; mg_unpublished[g] += 1; continue
        # type + PP: game data (tier 1), other sources cited
        tobs = [("pkhex", d_mi, [ptype, pp_t[mid]])]
        for s_, dd, v in (("serebii", SER_DOC.get(SEREBII_OF.get(g)), se), ("pokepedia", pp_ and pp_["doc"], pp_), ("pokeapi", d_pkmoves, pk), ("showdown", mdoc_sd(g), sd)):
            if v and v.get("type") and v.get("pp"): tobs.append((s_, dd, [v["type"], v["pp"]]))
        resolve("move_game", rk, "type_pp", tobs)
        usable = 0 if dummied else 1
        resolve("move_game", rk, "is_usable", [("pkhex", d_mi, usable)])
        pobs = []
        if g in PRIO: pobs.append(("bulbapedia", d_prio, PRIO[g].get(mid, 0)))
        if pp_ and pp_["priority"] is not None: pobs.append(("pokepedia", pp_["doc"], pp_["priority"]))
        if pk: pobs.append(("pokeapi", d_pkmoves, pk["priority"]))
        if sd: pobs.append(("showdown", mdoc_sd(g), sd["priority"]))
        prio, pst = resolve("move_game", rk, "priority", pobs)
        mg_rows.append([mid, g, ptype, dclass, power, acc, pp_t[mid], prio if prio is not None else 0, None, None, None, usable, None, None])
out["move_game"] = (["move_id", "game_id", "type_id", "damage_class", "power", "accuracy", "pp", "priority", "effect_chance", "target",
                     "makes_contact", "is_usable", "flags", "extra"], mg_rows)

# ----------------------------------------------------------------------------- machines
pk_items_ident = {int(i): r["identifier"] for i, r in pk_items.items()}
pk_mach = collections.defaultdict(dict)
for r in pcsv("machines"):
    ident = pk_items_ident.get(int(r["item_id"]), "")
    if re.fullmatch(r"(tm|hm|tr)\d+", ident):
        pk_mach[int(r["version_group_id"])][ident.upper()] = int(r["move_id"])
d_pkmach = pkdoc("machines")
mach_rows = []
move_set = set(move_ids)
for g, lst in MACH.items():
    vg = VG_ID.get(next(x[7] for x in R.GAMES if x[0] == g))
    pmap = pk_mach.get(vg, {})
    for e in lst:
        label, mid = e["label"], e["move"]
        if g in ("sv", "za") and label.startswith("TM"):
            n_ = int(label[2:]) - (1 if g == "sv" else 0)   # PKHeX's SV list starts with an unused slot (TM000)
            if n_ <= 0: continue
            label = f"TM{n_:03d}"
        if not mid or mid not in move_set: continue
        obs = [("pkhex", d_mach, mid)]
        alt = pmap.get(label) or pmap.get(re.sub(r"(\D+)0*(\d)", r"\g<1>\2", label)) or pmap.get(label[:2] + label[2:].zfill(3))
        if alt: obs.append(("pokeapi", d_pkmach, alt))
        resolve("machine", row_key(g, label), "*", obs)
        mach_rows.append([g, label, mid, None])
out["machine"] = (["game_id", "label", "move_id", "item_id"], mach_rows)

# ----------------------------------------------------------------------------- in-game descriptions (en, fr), per game
def clean_flavor(t):
    t = (t or "").replace("\u00ad\n", "").replace("-\n", "-").replace("\u00ad", "")
    return re.sub(r"\s+", " ", t.replace("\f", " ")).strip()
pk_flavor = collections.defaultdict(dict)
LID = {v: k for k, v in pk_lang.items()}
for r in pcsv("move_flavor_text"):
    l = PK_LANG.get(pk_lang[r["language_id"]])
    if l in ("en", "fr"):
        pk_flavor[(int(r["move_id"]), int(r["version_group_id"]))][l] = clean_flavor(r["flavor_text"])
d_pkfl = pkdoc("move_flavor_text")
PPE_GAMES = {"EB": ["sw"], "DEPS": ["bdsp"], "LPA": ["la"], "EV": ["sv"], "LPZA": ["za"]}
def ppe_desc(mid):
    title = FR_MOVES[mid] if mid < len(FR_MOVES) else None
    e = PPE.get(title)
    if not e or "=== Descriptions ===" not in e["text"]: return {}
    sec = e["text"].split("=== Descriptions ===", 1)[1].split("\n==", 1)[0]
    res = {}
    for games, txt in re.findall(r"^;(.*?)\n:(.*?)$", sec, re.M):
        for code in re.findall(r"\{\{Jeu\|([^}|]+)\}\}", games):
            for g in PPE_GAMES.get(code, []): res[g] = clean_flavor(re.sub(r"<[^>]+>", "", txt))
    return res
def fnorm(x): return nfkc(x).replace("\u202f", " ").replace("\u00a0", " ").replace("’", "'").replace("  ", " ")
fl_stats = collections.Counter()
mg_keys = {(r[0], r[1]) for r in mg_rows}
for mid in move_ids:
    pdesc = ppe_desc(mid)
    for g in MOVE_GAMES:
        if g in ("rb", "y"): continue                          # no move descriptions in Generation I games
        vg = VG_ID.get(next(x[7] for x in R.GAMES if x[0] == g))
        pk = pk_flavor.get((mid, vg), {})
        for lang in ("en", "fr"):
            if lang not in pk: continue
            obs = [("pokeapi", d_pkfl, pk[lang])]
            if lang == "en":
                se = serebii_move(mid, g)
                if se and se.get("text"): obs.append(("serebii", SER_DOC[SEREBII_OF[g]], clean_flavor(se["text"])))
            elif g in pdesc:
                obs.append(("pokepedia", ppe_doc(FR_MOVES[mid]), pdesc[g]))
            if len(obs) < 2:
                fl_stats[(lang, "one-source")] += 1; continue   # a single tier-3 source: not stored
            rk = row_key("move", str(mid), "flavor", lang, g, None)
            n0 = (len(citations), len(verifs), len(discreps))
            v, st = resolve("translation", rk, "text", obs, lambda x: canon(fnorm(x)))
            if st in PUBLISHED:
                tr_rows.append(["move", str(mid), "flavor", lang, g, None, pk[lang], 1]); fl_stats[(lang, "ok")] += 1
            else:   # descriptions differ between games of a generation: keep the gap for the report only
                del citations[n0[0]:], verifs[n0[1]:], discreps[n0[2]:]; fl_stats[(lang, "differ")] += 1

# Lucario etc.: evolution conditions that name a known move now point to the move table
# (done in phase 1b when PHASES contains "2")

# Movesets : voir phase2b.py (publiés à partir du schéma 1.1.0).

PHASE2_STATS = dict(moves=len(move_rows), move_game=len(mg_rows), machines=len(mach_rows), move_game_unpublished=dict(mg_unpublished),
                    move_game_no_tier2=dict(mg_noserebii), flavor={f"{l}:{k}": n for (l, k), n in sorted(fl_stats.items())},
                    )
json.dump(dict(stats=PHASE2_STATS, move_game_unpublished=mg_unpub_list), open(ROOT / "reports/phase2-details.json", "w"), ensure_ascii=False, indent=0)
print("phase2", json.dumps(PHASE2_STATS, ensure_ascii=False))
