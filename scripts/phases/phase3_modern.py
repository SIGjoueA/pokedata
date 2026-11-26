import difflib
# Phase 3 — générations 3 à 9 (jeux qui enregistrent le lieu de rencontre), exécuté depuis phase3.py.
#
# Lieux : le lieu de rencontre stocké par le jeu (id PKHeX, liste de lieux du jeu) fait foi. Identifiant : celui de PokeAPI
#   quand PokeAPI a ce lieu (même index de jeu, ou même nom anglais dans la région du jeu), sinon un identifiant créé
#   depuis le nom anglais du jeu (préfixé par la région en cas d'homonymie). Les suffixes ajoutés par PKHeX pour séparer les
#   homonymes (« (1) », « (HG/SS) », « (Kanto) »…) sont retirés des noms.
# DLC : un lieu du DLC (Isle of Armor, Couronneige, Septentria, Myrtille, dimension Méga) range ses rencontres sous la
#   version DLC (the-isle-of-armor-sword…) ; la disponibilité d'une version DLC est celle du jeu avec ce DLC (cumulative).
# Rencontres sans lieu enregistré (échanges : lieu = « échange » ; raids) : placées seulement là où PokeAPI et Bulbapedia
#   concordent (extra.placement), sinon disponibilité seule.

MOD_DUMP = {"rs": "3", "e": "3", "frlg": "3", "dp": "4", "pt": "4", "hgss": "4", "bw": "5", "b2w2": "5", "xy": "6", "oras": "6",
            "sm": "7", "usum": "7", "lgpe": "7b", "sw": "8", "swisle": "8", "swcrown": "8", "la": "8a", "bdsp": "8b",
            "sv": "9", "svmask": "9", "svdisk": "9", "za": "9a", "zadlc": "9a"}
MOD_LIST = {"rs": "rsefrlg", "e": "rsefrlg", "frlg": "rsefrlg", "dp": "hgss", "pt": "hgss", "hgss": "hgss", "bw": "bw2", "b2w2": "bw2",
            "xy": "xy", "oras": "xy", "sm": "sm", "usum": "sm", "lgpe": "gg", "sw": "swsh", "la": "la", "bdsp": "bdsp", "sv": "sv", "za": "za"}
GI_GEN = {"rsefrlg": 3, "hgss": 4, "bw2": 5, "xy": 6, "sm": 7, "swsh": 8, "sv": 9}
MOD_REGIONS = {"rs": ["hoenn"], "e": ["hoenn"], "oras": ["hoenn"], "frlg": ["kanto"], "lgpe": ["kanto"], "dp": ["sinnoh"],
               "pt": ["sinnoh"], "bdsp": ["sinnoh"], "hgss": ["johto", "kanto"], "bw": ["unova"], "b2w2": ["unova"], "xy": ["kalos"],
               "za": ["kalos"], "sm": ["alola"], "usum": ["alola"], "sw": ["galar"], "la": ["hisui"], "sv": ["paldea"],
               "swisle": ["galar"], "swcrown": ["galar"], "svmask": ["kitakami", "paldea"], "svdisk": ["blueberry", "paldea"], "zadlc": ["kalos"]}
MOD_BASE = {"swisle": "sw", "swcrown": "sw", "svmask": "sv", "svdisk": "sv", "zadlc": "za"}
DLC_ORDER = {"sw": ["swisle", "swcrown"], "sv": ["svmask", "svdisk"], "za": ["zadlc"]}
PKXV.update({"R": ["ruby"], "S": ["sapphire"], "E": ["emerald"], "FR": ["firered"], "LG": ["leafgreen"]})
PKXV.update({"RS": PKXV["R"] + PKXV["S"], "FRLG": PKXV["FR"] + PKXV["LG"]})
PKXV.update({"RSE": PKXV["RS"] + PKXV["E"], "EFL": PKXV["E"] + PKXV["FRLG"]})
PKXV["Gen3"] = PKXV["RSE"] + PKXV["FRLG"]
PKXV.update({"D": ["diamond"], "P": ["pearl"], "Pt": ["platinum"], "HG": ["heartgold"], "SS": ["soulsilver"]})
PKXV.update({"DP": PKXV["D"] + PKXV["P"], "HGSS": PKXV["HG"] + PKXV["SS"]}); PKXV["DPPt"] = PKXV["DP"] + PKXV["Pt"]
PKXV.update({"B": ["black"], "W": ["white"], "B2": ["black-2"], "W2": ["white-2"]})
PKXV.update({"BW": PKXV["B"] + PKXV["W"], "B2W2": PKXV["B2"] + PKXV["W2"]}); PKXV["Gen5"] = PKXV["BW"] + PKXV["B2W2"]
PKXV.update({"X": ["x"], "Y": ["y"], "OR": ["omega-ruby"], "AS": ["alpha-sapphire"]})
PKXV.update({"XY": PKXV["X"] + PKXV["Y"], "ORAS": PKXV["OR"] + PKXV["AS"]})
PKXV.update({"SN": ["sun"], "MN": ["moon"], "US": ["ultra-sun"], "UM": ["ultra-moon"], "GP": ["lets-go-pikachu"], "GE": ["lets-go-eevee"]})
PKXV.update({"SM": PKXV["SN"] + PKXV["MN"], "USUM": PKXV["US"] + PKXV["UM"], "GG": PKXV["GP"] + PKXV["GE"]})
PKXV.update({"SW": ["sword"], "SH": ["shield"], "BD": ["brilliant-diamond"], "SP": ["shining-pearl"], "SL": ["scarlet"], "VL": ["violet"]})
PKXV.update({"SWSH": PKXV["SW"] + PKXV["SH"], "BDSP": PKXV["BD"] + PKXV["SP"], "SV": PKXV["SL"] + PKXV["VL"]})
PKXV.update({"PLA": ["legends-arceus"], "ZA": ["legends-za"]})
DUMP_DEFAULT_V = {"8a": "PLA", "9a": "ZA"}
# DLC version of a base version
DLCV = {}
for _v, _g, _pid in R.VERSIONS:
    if _g in MOD_BASE:
        for _bv in VERSIONS_OF.get(MOD_BASE[_g], []) or [v for v, g, p in R.VERSIONS if g == MOD_BASE[_g]]:
            if _bv in _v or MOD_BASE[_g] == "za": DLCV[(_g, _bv)] = _v

def dlc_of(base, metid):
    """DLC game of a met location (None = base game)."""
    if base == "sw":
        if 164 <= metid <= 202: return "swisle"
        if 204 <= metid <= 246: return "swcrown"
    if base == "sv":
        if 132 <= metid <= 170: return "svmask"
        if 172 <= metid <= 200: return "svdisk"
    if base == "za" and 273 <= metid <= 299: return "zadlc"
    return None

PKX_TAG = re.compile(r"\s*\((?:\d+|-|E|FRLG|RSE|RS|Kanto|unused|D/P/Pt|HG/SS|B/W|B2/W2|X/Y|OR/AS)\)\s*$")
def strip_name(s):
    s = (s or "").strip()
    while True:
        t = PKX_TAG.sub("", s)
        if t == s: return s
        s = t
SKIP_LOC = {"mysteryzone", "farawayplace", "", "pokéwalker", "pokewalker", "daycarecouple", "linktradearrive", "linktrademet", "aucun", "none"}
def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("’", "").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

pk_gi_all = collections.defaultdict(lambda: collections.defaultdict(list))   # gen -> index -> [identifiers]
for r in pcsv("location_game_indices"): pk_gi_all[int(r["generation_id"])][int(r["game_index"])].append(pk_loc[r["location_id"]]["identifier"])
pk_by_name = collections.defaultdict(set)   # normalised English name -> identifiers
for ident, names in pk_locnames.items():
    if names.get("en"): pk_by_name[p3_norm(names["en"])].add(ident)
def pk_reg(ident): return pk_region.get(pk_loc_by_ident[ident]["region_id"]) if ident in pk_loc_by_ident else None
MLOC = {}                       # (list, metid) -> identifier
MLOC_NEW = {}                   # created identifier -> region
MLOC_SRC = collections.defaultdict(set)   # identifier -> {(list, metid, how)}
_new_by_name = {}
PK_LOC_V = collections.defaultdict(set)   # PokeAPI location -> versions with encounters
for _e in PK_ENC: PK_LOC_V[_e["location"]].add(_e["version"])
# one met location id whose text depends on the version (Ruby: Team Magma Hideout, Sapphire: Team Aqua Hideout)
LOC_BY_VERSION = {("rsefrlg", 66): {"ruby": "team-magma-hideout", "sapphire": "team-aqua-hideout"}}
def mloc(game, metid, version=None):
    """Location identifier for a met location id of this game (DLC games use the base game's list)."""
    base = MOD_BASE.get(game, game)
    lst = MOD_LIST[base]
    if version and (lst, metid) in LOC_BY_VERSION and version in LOC_BY_VERSION[(lst, metid)]:
        res = LOC_BY_VERSION[(lst, metid)][version]
        MLOC_SRC[res].add((lst, metid, "pokeapi-index-version")); return res
    key = (lst, metid, game)
    if key in MLOC: return MLOC[key]
    raw = PKX_LOCN[lst]["en"].get(str(metid))
    res = None
    if raw and metid < 30000 and not raw.startswith("—") and p3_norm(strip_name(raw)) not in SKIP_LOC:
        name = strip_name(raw)
        regions = MOD_REGIONS.get(game, [])
        how = None
        cands = []
        if lst in GI_GEN:
            for ident in pk_gi_all[GI_GEN[lst]].get(metid, []):
                pn = p3_norm(pk_locnames[ident].get("en"))
                if pk_reg(ident) in regions and pn and (pn == p3_norm(name) or pn in p3_norm(raw) or p3_norm(name) in pn
                                                         or difflib.SequenceMatcher(None, pn, p3_norm(name)).ratio() >= 0.85):   # "Viapos"/"Viapois"
                    cands.append(ident)
            if len(set(cands)) > 1:   # same index for several PokeAPI places: the one PokeAPI uses for this game's versions
                vs_ = set(VERSIONS_OF.get(game, [])) or {v for v, g_, p_ in R.VERSIONS if g_ == game}
                c2 = sorted({c for c in cands if PK_LOC_V[c] & vs_})
                if len(c2) == 1: cands = c2
            if len(set(cands)) == 1: how = "pokeapi-index"
        if not how:
            _nm = (pk_by_name.get(p3_norm(name)) or pk_by_name.get(p3_norm("Team " + name)) or pk_by_name.get(p3_norm(name.replace("Mount ", "Mt. ")))   # "Aqua Hideout" = "Team Aqua Hideout"
                   or set().union(*[pk_by_name.get(p3_norm(r_ + " " + name), set()) for r_ in regions]))   # "Kanto Power Plant"
            cands = sorted(i for i in _nm if pk_reg(i) in regions)
            if len(cands) > 1:   # the one PokeAPI uses for this game's versions
                vs_ = set(VERSIONS_OF.get(game, [])) or {v for v, g_, p_ in R.VERSIONS if g_ == game}
                c2 = sorted(c for c in cands if PK_LOC_V[c] & vs_)
                if len(c2) == 1: cands = c2
            if len(cands) == 1: how = "pokeapi-name"
            elif not cands:   # the same place reached from another region (Navel Rock…): unique English name anywhere
                cands = sorted(_nm)
                if len(cands) == 1: how = "pokeapi-name"
        if not how:   # PokeAPI sub-place identifiers ("hau-oli-city--shopping-district") and sea routes ("kanto-sea-route-19")
            sl = slugify(name)
            want = {sl} | {f"{r_}-sea-{sl}" for r_ in regions} if sl else set()
            cands = sorted(i for i in pk_loc_by_ident if pk_reg(i) in regions and (i.replace("--", "-") in want or i in want))
            if len(cands) == 1: how = "pokeapi-slug"
        if how:
            res = cands[0]
        else:
            region = regions[0] if regions else None
            k2 = (region, p3_norm(name))
            if k2 in _new_by_name: res = _new_by_name[k2]
            else:
                s = slugify(name) or f"{lst}-{metid}"
                if s.startswith("route-") and region: s = f"{region}-{s}"   # routes: always with the region
                if s in pk_loc_by_ident or s in MLOC_NEW: s = f"{region}-{s}" if region else f"{lst}-{s}"
                while s in pk_loc_by_ident or s in MLOC_NEW: s += "-x"
                MLOC_NEW[s] = region; _new_by_name[k2] = s; res = s
            how = "created"
        MLOC_SRC[res].add((lst, metid, how))
    MLOC[key] = res
    return res

def place_version(game_base, v, metid):
    """(game, version) for an encounter at this met location: DLC places go under the DLC version."""
    d = dlc_of(game_base, metid) if metid is not None else None
    if d and (d, v) in DLCV and d in P3_GAMES: return d, DLCV[(d, v)]
    if d: return None, None
    return game_base, v

def mod_versions(dk, code):
    code = code or DUMP_DEFAULT_V.get(dk)
    if code not in PKXV: return []
    return [x for x in PKXV[code] if GAME_OF_VERSION.get(x) in P3_GAMES]

W8 = ["Normal", "Overcast", "Raining", "Thunderstorm", "Intense_Sun", "Snowing", "Snowstorm", "Sandstorm", "Heavy_Fog"]
W8C = {"All": W8, "Stormy": ["Raining", "Thunderstorm"], "Icy": ["Snowing", "Snowstorm"],
       "All_IoA": ["Normal", "Overcast", "Raining", "Thunderstorm", "Intense_Sun", "Sandstorm", "Heavy_Fog"],
       "All_CT": ["Normal", "Overcast", "Raining", "Thunderstorm", "Intense_Sun", "Snowing", "Snowstorm", "Heavy_Fog"],
       "No_Sun_Sand": ["Normal", "Overcast", "Raining", "Thunderstorm", "Snowing", "Snowstorm", "Heavy_Fog"],
       "All_Ballimere": ["Normal", "Overcast", "Raining", "Thunderstorm", "Intense_Sun", "Snowing", "Heavy_Fog"]}
W9C = {"Standard": ["Normal", "Overcast", "Raining", "Thunderstorm"], "Sand": ["Normal", "Overcast", "Raining", "Sandstorm"],
       "Snow": ["Normal", "Overcast", "Snowing", "Snowstorm"], "Inside": ["Normal", "Overcast"]}
W9 = ["Normal", "Overcast", "Raining", "Thunderstorm", "Mist", "Snowing", "Snowstorm", "Sandstorm"]
WCOND = {"Normal": "weather-normal", "Overcast": "weather-overcast", "Raining": "weather-raining", "Thunderstorm": "weather-thunderstorm",
         "Intense_Sun": "weather-intense-sun", "Snowing": "weather-snowing", "Snowstorm": "weather-snowstorm", "Sandstorm": "weather-sandstorm",
         "Heavy_Fog": "weather-fog", "Mist": "weather-fog"}
def weathers(dk, s):
    out_ = set()
    for p in [p.strip() for p in (s or "").split(",") if p.strip()]:
        if dk == "8":
            out_ |= set(W8C.get(p, [p] if p in W8 else []))
        else:
            out_ |= set(W9C.get(p, [p] if p in W9 else []))
    return out_ or set(W8 if dk == "8" else W9)
T9 = [("day", 0), ("night", 1), ("evening", 2), ("morning", 3)]   # PKHeX EncounterSlot9.Time: bit set = time excluded

def mod_slot_method(dk, x, a):
    T = a.get("Type") or x.get("Type")
    if dk == "3":
        return {"Grass": "walk", "Surf": "surf", "Old_Rod": "old-rod", "Good_Rod": "good-rod", "Super_Rod": "super-rod",
                "Rock_Smash": "rock-smash", "SwarmGrass50": "walk", "SwarmFish50": "feebas-tile-fishing"}.get(T)
    if dk == "4":
        T = T.replace("Safari_", "")
        return {"Grass": "walk", "Surf": "surf", "Old_Rod": "old-rod", "Good_Rod": "good-rod", "Super_Rod": "super-rod",
                "Headbutt": "headbutt", "HeadbuttSpecial": "headbutt", "HoneyTree": "honey-tree", "Rock_Smash": "rock-smash",
                "BugContest": "bug-contest"}.get(T)
    if dk == "5":
        return {"Grass": "walk", "Surf": "surf", "Super_Rod": "super-rod", "Swarm": "walk", "HiddenGrotto": "hidden-grotto"}.get(T)
    if dk == "6":
        # "Standard" tables hold several methods, by slot position (game table layout):
        # X/Y: 0–59 grass, flowers, rough terrain · 60–64 Surf · 65–69 Rock Smash · 70–72 / 73–75 / 76–78 Old / Good / Super Rod
        # OR/AS: 0–23 grass, long grass · 24–26 DexNav-only Pokémon · 27–31 Surf · 32–34 / 35–37 / 38–40 Old / Good / Super Rod
        if T == "Standard":
            i = x.get("_slot_index", 0)
            if x["_type"] == "EncounterSlot6AO":
                return "walk" if i < 24 else "dexnav" if i < 27 else "surf" if i < 32 else "old-rod" if i < 35 else "good-rod" if i < 38 else "super-rod"
            return ("walk" if i < 60 else "surf" if i < 65 else "rock-smash" if i < 70 else "old-rod" if i < 73 else "good-rod" if i < 76
                    else "super-rod" if i < 79 else "walk")
        return {"Rock_Smash": "rock-smash", "Horde": "horde", "Grass": "ambush", "FriendSafari": "friend-safari"}.get(T)
    if dk == "7":
        return {"Standard": "wild", "SOS": "sos"}.get(T)
    if dk == "7b": return "wild"
    if dk == "8":
        w = x.get("Weather") or ""
        if "Fishing" in w: return "fishing"
        if "Shaking_Trees" in w: return "berry-trees"
        if T.startswith(("Symbol", "Sky", "Ground", "Surfing", "Sharpedo")): return "overworld"
        return "walk"
    if dk == "8a":
        return {"Standard": "wild", "Distortion": "distortion", "MassOutbreakRegular": "outbreak",
                "MassOutbreakMassive": "massive-outbreak", "Landmark": "landmark"}.get(T)
    if dk == "8b":
        if x.get("IsUnderground"): return "grand-underground"
        return {"Grass": "walk", "Surf": "surf", "Old_Rod": "old-rod", "Good_Rod": "good-rod", "Super_Rod": "super-rod",
                "HoneyTree": "honey-tree"}.get(T)
    if dk in ("9", "9a"): return "wild"
    return None
def mod_slot_conds(dk, x, a):
    """List of labels (tuples of (dimension, value)) under which this slot appears."""
    T = a.get("Type") or x.get("Type")
    if (dk == "3" and T == "SwarmGrass50") or (dk == "5" and T == "Swarm"): return [(("swarm", "yes"),)]
    if dk == "8":
        return [(("weather", WCOND[w]),) for w in sorted(weathers("8", x.get("Weather")))]
    if dk == "9":
        ts = [t for t, b in T9 if not (int(x.get("Time") or 0) >> b) & 1] or [t for t, b in T9]
        ws = sorted({WCOND[w] for w in weathers("9", x.get("Weather"))})
        return [(("time", "time-" + t), ("weather", w)) for t in ts for w in ws]
    return [()]

MENC = collections.defaultdict(lambda: {"labels": collections.defaultdict(lambda: [999, 0]), "shiny": set(), "extra": {}})
def madd(f, v, loc, m, lo, hi, labels=((),), shiny="Random", alpha=False, extra=None):
    e = MENC[(f, v, loc, m, bool(alpha))]
    for lab in labels:
        r_ = e["labels"][tuple(lab)]; r_[0] = min(r_[0], lo); r_[1] = max(r_[1], hi)
    e["shiny"].add(shiny or "Random")
    if extra: e["extra"].update(extra)

def mforms(sp, fi, game, rnd=False):
    if rnd:
        return sorted(k for (s, f), k in KEYMAP[game].items() if s == sp and (k, game) in present)
    k = KEYMAP[game].get((sp, fi))
    if not k or (k, game) not in present:   # form index known from another game (Unown letters, Deoxys forms of gen 3)
        ks = {KEYMAP[g_].get((sp, fi)) for g_ in KEYMAP} - {None}
        ks = {x for x in ks if (x, game) in present}
        k = ks.pop() if len(ks) == 1 else None
    return [k] if k and (k, game) in present else []

PK_IDX = collections.defaultdict(list)   # (form, version) -> PokeAPI records
for e in PK_ENC: PK_IDX[(e["form"], e["version"])].append(e)
def pk_places(f, v, methods):
    return {e["location"] for e in PK_IDX.get((f, v), []) if e["method"] in methods}

# Bulbapedia in-game trades, generations 3 to 9: (generation, species received) -> {location}
BUL_TRADE_M = collections.defaultdict(set)
_gen_sections = [(3, "===Generation III===", "===Generation IV==="), (4, "===Generation IV===", "===Generation V==="),
                 (5, "===Generation V===", "===Generation VI==="), (6, "===Generation VI===", "===Generation VII==="),
                 (7, "===Generation VII===", "===Generation VIII==="), (8, "===Generation VIII===", "===Generation IX==="),
                 (9, "===Generation IX===", "==See also")]
def all_place_names():
    m = collections.defaultdict(set)
    for ident, names in pk_locnames.items():
        if names.get("en"): m[p3_norm(names["en"])].add(ident)
    return m
def wiki_places_m(cell):
    found = set()
    for mm in re.finditer(r"\{\{rt\|(\d+)\|(\w+)", cell):
        for pre in (f"{mm.group(2).lower()}-route-{mm.group(1)}", f"{mm.group(2).lower()}-sea-route-{mm.group(1)}"):
            if pre in pk_loc_by_ident: found.add(pre)
    for mm in re.finditer(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]|\{\{OBP\|([^|}]+)", cell):
        nm = mm.group(1) or mm.group(2)
        found |= pk_by_name.get(p3_norm(nm), set())
    return found
for gen_, s_, e_ in _gen_sections:
    for row in wikitable_rows(wiki_section(text_trade, s_, e_)):
        sps = [msp_species(c) for c in row if msp_species(c)]
        if len(sps) >= 2:
            for cell in row:
                for l in wiki_places_m(cell): BUL_TRADE_M[(gen_, sps[1])].add(l)

p3_mod_skip = collections.Counter()
P3_FORMSKIP = collections.Counter()
# places reached only with a distributed item that PKHeX does not mark: Newmoon Island (Member Card), Sinjoh Ruins
# (event Arceus), Liberty Garden (Liberty Pass)
EVENT_ITEM_LOC = {("hgss", 79), ("hgss", 231), ("bw2", 62)}
def mod_record(x, dk):
    tbl = x["_table"]; t = x["_type"]; a = x.get("_area")
    if "Colo" in tbl or "XD" in tbl or (x.get("Version") in ("COLO", "XD", "CXD")): return
    code = (a or {}).get("Version") or x.get("Version")
    vers = mod_versions(dk, code)
    if not vers: p3_mod_skip[f"{dk}:version:{code}"] += 1; return
    gen_ = int(dk[0])
    sp, fi = x["Species"], x.get("Form", 0)
    if sp == 0: return
    is_event = (tbl.startswith("EncountersWC3") or t in ("EncounterTrade4RanchGift", "EncounterStatic8ND", "EncounterStatic8NC",
                "EncounterDist9", "EncounterMight9", "EncounterStatic5Entree", "EncounterStatic5Radar"))
    for v0 in vers:
        g0 = GAME_OF_VERSION[v0]
        if is_event:
            if g0 in P3_GAMES and v0 in P3_VERSIONS:
                for f in mforms(sp, fi, g0, x.get("IsRandomUnspecificForm", False)): AVAIL_SRC[(f, v0)].add("event")
            continue
        if a:   # wild slot
            metid = x.get("Location") if x.get("Location") is not None else a.get("Location")
            g, v = place_version(g0, v0, metid)
            if not g or g not in P3_GAMES: continue
            m = mod_slot_method(dk, x, a)
            if not m: p3_mod_skip[f"{dk}:slot-type:{a.get('Type') or x.get('Type')}"] += 1; continue
            fs = mforms(sp, fi, g, x.get("IsRandomUnspecificForm", False))
            if not fs: p3_mod_skip[f"{dk}:form"] += 1; P3_FORMSKIP[(dk, sp, fi, g)] += 1; continue
            loc = mloc(g, metid, v)
            for f in fs:
                AVAIL_SRC[(f, v)].add("wild"); PKX_SHINY[(f, g)].append(x.get("Shiny"))
                if loc: madd(f, v, loc, m, x["LevelMin"], x["LevelMax"], mod_slot_conds(dk, x, a), x.get("Shiny"), x.get("IsAlpha"))
            if not loc: p3_mod_skip[f"{dk}:slot-no-place"] += 1
            continue
        lo_, hi_ = x.get("LevelMin") or x.get("Level"), x.get("LevelMax") or x.get("Level")
        if t == "EncounterStatic4Pokewalker":
            for f in mforms(sp, fi, g0): AVAIL_SRC[(f, v0)].add("gift:pokewalker")
            continue
        if t == "EncounterStatic8N":   # Max Raid dens: the den's place is not stored; the version comes from PokeAPI
            for f in mforms(sp, fi, g0, x.get("IsRandomUnspecificForm", False)):
                for vv in [v0] + [DLCV[(d, v0)] for d in DLC_ORDER.get(g0, []) if (d, v0) in DLCV]:
                    if vv in P3_VERSIONS and pk_places(f, vv, {"max-raid"}): AVAIL_SRC[(f, vv)].add("wild:max-raid")
            continue
        if t == "EncounterTera9":
            d = {"Encounters9.TeraDLC1": "svmask", "Encounters9.TeraDLC2": "svdisk"}.get(tbl)
            hosts = [vv for vv in vers if (vv == "scarlet" and x.get("IsAvailableHostScarlet", True)) or (vv == "violet" and x.get("IsAvailableHostViolet", True))]
            if v0 not in hosts: continue
            vv = DLCV.get((d, v0)) if d else v0
            gg = d or g0
            if vv in P3_VERSIONS:
                for f in mforms(sp, fi, gg, x.get("IsRandomUnspecificForm", False)): AVAIL_SRC[(f, vv)].add("wild:tera-raid")
            continue
        if t.startswith("EncounterTrade"):
            dlcs = [d for d in DLC_ORDER.get(g0, []) if (d, v0) in DLCV and d in P3_GAMES]
            for f in mforms(sp, fi, g0):
                placed = False
                for gg, vv in [(g0, v0)] + [(d, DLCV[(d, v0)]) for d in dlcs]:
                    pl = pk_places(f, vv, {"npc-trade"}) & BUL_TRADE_M.get((gen_, sp), set())
                    if len(pl) == 1 and gg in P3_GAMES and vv in P3_VERSIONS:
                        AVAIL_SRC[(f, vv)].add("npc-trade"); PKX_SHINY[(f, gg)].append(x.get("Shiny"))
                        madd(f, vv, pl.pop(), "npc-trade", lo_, lo_, shiny=x.get("Shiny"), extra={"placement": "pokeapi+bulbapedia"})
                        placed = True; break
                if not placed and g0 in P3_GAMES and v0 in P3_VERSIONS:
                    AVAIL_SRC[(f, v0)].add("npc-trade"); PKX_SHINY[(f, g0)].append(x.get("Shiny")); p3_mod_skip[f"{dk}:trade-unplaced"] += 1
            continue
        if x.get("IsRoaming"):
            if g0 in P3_GAMES and v0 in P3_VERSIONS:
                for f in mforms(sp, fi, g0): AVAIL_SRC[(f, v0)].add("wild:roaming"); PKX_SHINY[(f, g0)].append(x.get("Shiny"))
            continue
        egg = bool(x.get("IsEgg") or (x.get("EggLocation") not in (None, 0, 65535) and gen_ >= 4 and t.startswith("EncounterStatic")))
        metid = x.get("Location")
        if t == "EncounterStatic8U": metid = 244   # Dynamax Adventures: met at the Max Lair
        if egg: metid = x.get("EggLocation") if x.get("EggLocation") not in (None, 0, 65535) else None
        g, v = place_version(g0, v0, metid) if metid is not None else (g0, v0)
        if dk == "8" and sp in (144, 145, 146) and fi == 1 and g == "sw":   # Galarian birds roam base-game places after the Crown Tundra quest
            g, v = ("swcrown", DLCV.get(("swcrown", v0))) if "swcrown" in P3_GAMES else (None, None)
        if not g or g not in P3_GAMES or v not in P3_VERSIONS: continue
        gift = bool(x.get("Gift") or (x.get("FixedBall") not in (None, "None") and t not in ("EncounterStatic8U",)))
        m = ("gift-egg" if egg else "dynamax-adventure" if t == "EncounterStatic8U" else "outbreak" if t == "EncounterOutbreak9"
             else "gift" if gift else "static")
        tag = {"gift-egg": "gift-egg", "gift": "gift"}.get(m, "wild")
        # places reached only with a distributed item (Eon / Aurora / Mystic / Old Sea Map tickets, Member Card, Oak's
        # Letter, Azure Flute, Liberty Pass): PKHeX marks those encounters "fateful" (generations 3–5); in Ruby/Sapphire the
        # Southern Island (Eon Ticket) is not marked → listed here
        ext = None
        if ((gen_ <= 5 and x.get("FatefulEncounter")) or (dk == "3" and metid == 73 and set(vers) <= {"ruby", "sapphire"})
                or (MOD_LIST.get(MOD_BASE.get(g, g)), metid) in EVENT_ITEM_LOC):
            tag = "event"; ext = {"access": "event-item"}
        fs = mforms(sp, fi, g, x.get("IsRandomUnspecificForm", False))
        if not fs: p3_mod_skip[f"{dk}:form"] += 1; P3_FORMSKIP[(dk, sp, fi, g)] += 1; continue
        loc = mloc(g, metid, v) if metid is not None else None
        for f in fs:
            AVAIL_SRC[(f, v)].add(tag if m != "dynamax-adventure" else "wild:dynamax-adventure"); PKX_SHINY[(f, g)].append(x.get("Shiny"))
            if loc: madd(f, v, loc, m, lo_, hi_, shiny=x.get("Shiny"), alpha=x.get("IsAlpha"), extra=ext)
        if not loc: p3_mod_skip[f"{dk}:static-no-place"] += 1

# Mystery Gift database of PKHeX (generations 4+): an event for every version of the games of the card's generation,
# narrowed to the versions PKHeX names when it names some of that generation
EV_CTX = {"Gen4": ["dp", "pt", "hgss"], "Gen5": ["bw", "b2w2"], "Gen6": ["xy", "oras"], "Gen7": ["sm", "usum"], "Gen7b": ["lgpe"],
          "Gen8": ["sw"], "Gen8b": ["bdsp"], "Gen8a": ["la"], "Gen9": ["sv"], "Gen9a": ["za"]}
EV_SRC = set()
_evf = DUMP / "events.json"
d_pkxev = doc("pkhex", f"{PKXREV} · EncounterEvent MGDB (events.json)", PKXREV, file_sha(_evf)) if _evf.exists() else None
for x in (json.load(open(_evf, encoding="utf-8")) if _evf.exists() else []):
    sp, fi = x.get("Species", 0), x.get("Form", 0)
    games = [g for g in EV_CTX.get(x.get("Context"), []) if g in P3_GAMES]
    if not sp or not games: continue
    allv = [v for g in games for v in VERSIONS_OF[g]]
    named = [v for v in PKXV.get(x.get("Version") or "", []) if v in allv] if x.get("_type") != "PCD" else []
    if x.get("_type") == "WC8" and x.get("RestrictVersion") in (1, 2): named = [["sword"], ["shield"]][x["RestrictVersion"] - 1]
    for v in (named or allv):
        for f in mforms(sp, fi, GAME_OF_VERSION[v], False):
            AVAIL_SRC[(f, v)].add("event"); EV_SRC.add((f, v))

COLLAPSIBLE = {"weather", "time"}
def collapse(entries, universe):
    """entries: label(tuple of (dim, value)) -> [lo, hi]. Drop a dimension when every value of the set appears with the same levels."""
    entries = {tuple(sorted(k)): tuple(v) for k, v in entries.items()}
    for dim in sorted(d for d in universe if d in COLLAPSIBLE):
        groups = collections.defaultdict(dict)
        for lab, rng in entries.items():
            rest = tuple(p for p in lab if p[0] != dim); val = [p[1] for p in lab if p[0] == dim]
            if not val: groups[rest][None] = rng; continue
            groups[rest][val[0]] = rng
        ok = all(None not in gr and set(gr) == universe[dim] and len(set(gr.values())) == 1 for gr in groups.values())
        if ok:
            entries = {rest: next(iter(gr.values())) for rest, gr in groups.items()}
    return entries

def mod_rows():
    """MENC → enc_sets rows [form, min, max, cond, shiny_locked, extra, alpha]."""
    uni = collections.defaultdict(lambda: collections.defaultdict(set))
    for (f, v, loc, m, al), e in MENC.items():
        for lab in e["labels"]:
            for dim, val in lab: uni[(loc, v, m)][dim].add(val)
    out_rows = collections.defaultdict(list)
    for (f, v, loc, m, al), e in sorted(MENC.items()):
        for lab, (lo, hi) in sorted(collapse(e["labels"], uni[(loc, v, m)]).items()):
            cond = ",".join(sorted(("swarm-" + val) if dim == "swarm" else val for dim, val in lab)) or None
            ex = dict(e["extra"])
            if e["shiny"] == {"Always"}: ex["shiny"] = "always"
            locked = 1 if e["shiny"] == {"Never"} else 0
            row = [f, lo, hi, cond, locked, canon(ex) if ex else None]
            if al: row.append(1)
            out_rows[(loc, v, m)].append(row)
    return out_rows
