"""Phase 1 import: reference tables, species, forms, per-game form data, abilities, names (10 languages),
with cross-checks, citations, verification status, discrepancies and the update log.

Inputs: cache/ (scripts/fetch/fetch_sources.py). Outputs: db/data/*.csv.
Rules (plan.md §5): game extraction (tier 1) wins; otherwise >= 2 agreeing sources incl. one of tier <= 2.
"""
import collections, csv, datetime, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, LANGS, ROOT, canon, load_manifest, read_csv, row_key, sha256_bytes, sha256_text, write_csv
import reference as R

MAN = load_manifest()
NOW = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
DATA_VERSION = os.environ.get("DATA_VERSION", datetime.date.today().strftime("%Y.%m.%d"))
SCHEMA_VERSION = "1.0.0"
TIER = {s[0]: s[2] for s in R.SOURCES}
PK = CACHE / "pokeapi/data/v2/csv"
DUMP = CACHE / "pkhex-dump"
PKHEX_GAMES = ["rb", "y", "gs", "c", "rs", "e", "fr", "lg", "dp", "pt", "hgss", "bw", "b2w2", "xy", "oras",
               "sm", "usum", "lgpe", "sw", "bdsp", "la", "sv", "za"]
GAME_GEN = {g[0]: g[2] for g in R.GAMES}
GAME_GEN["fr"] = GAME_GEN["lg"] = 3

# ----------------------------------------------------------------------------- provenance store
documents = {}   # key -> dict(id, source_id, locator, revision, retrieved_at, content_sha256)
citations = []   # (table, row_key, column, doc_id, observed, agrees)
verifs = []      # (table, row_key, column, status, value_sha, fingerprint)
discreps = []    # (table, row_key, column, chosen, rule, alternatives, note)


def doc(source_id, locator, revision, content_sha):
    key = (source_id, locator)
    if key not in documents:
        documents[key] = dict(id=len(documents) + 1, source_id=source_id, locator=locator, revision=revision,
                              retrieved_at=MAN.get(source_id, {}).get("retrieved_at", NOW), content_sha256=content_sha)
    return documents[key]["id"]


def file_sha(path):
    return sha256_bytes(open(path, "rb").read())


def nfkc(s):
    return unicodedata.normalize("NFKC", s).replace("’", "'").strip() if isinstance(s, str) else s


def resolve(table, rk, column, observations, compare=None):
    """observations: list of (source_id, doc_id, value). Returns (chosen value, status)."""
    compare = compare or (lambda v: canon(v))
    obs = [o for o in observations if o[2] is not None]
    if not obs:
        return None, None
    tier1 = [o for o in obs if TIER[o[0]] == 1]
    if tier1:
        chosen, status, rule = tier1[0][2], "game-data", "game-data"
    else:
        cnt = collections.Counter(compare(o[2]) for o in obs)
        best, n = cnt.most_common(1)[0]
        chosen = next(o[2] for o in obs if compare(o[2]) == best)
        agreeing = [o for o in obs if compare(o[2]) == best]
        tied = len(cnt) > 1 and list(cnt.values()).count(n) > 1
        if len(obs) == 1:
            status = "single-source"
        elif tied or n < 2 or not any(TIER[o[0]] <= 2 for o in agreeing):
            status = "disputed" if len(cnt) > 1 else ("majority" if any(TIER[o[0]] <= 2 for o in agreeing) else "seeded")
        else:
            status = "unanimous" if len(cnt) == 1 else "majority"
        rule = "majority" if status in ("majority", "unanimous") else "open"
    cv = compare(chosen)
    for s, d, v in obs:
        citations.append((table, rk, column, d, canon(v), 1 if compare(v) == cv else 0))
    dissent = [o for o in obs if compare(o[2]) != cv]
    if dissent:
        discreps.append((table, rk, column, canon(chosen), rule,
                         canon([{"source": s, "document_id": d, "value": v} for s, d, v in dissent]), None))
    fp = sha256_text("|".join(sorted(f"{s}:{sha256_text(canon(v))}" for s, d, v in obs)))
    verifs.append((table, rk, column, status, sha256_text(canon(chosen)), fp))
    return chosen, status


# ----------------------------------------------------------------------------- load sources
def pcsv(name):
    with open(PK / f"{name}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


pk_species = {r["id"]: r for r in pcsv("pokemon_species")}
pk_pokemon = {r["id"]: r for r in pcsv("pokemon")}
pk_forms = pcsv("pokemon_forms")
pk_types = {r["id"]: r["identifier"] for r in pcsv("types")}
pk_abil = {r["id"]: r for r in pcsv("abilities")}
pk_lang = {r["id"]: r["identifier"] for r in pcsv("languages")}
_pk_en = {int(r["ability_id"]): r["name"] for r in pcsv("ability_names") if r["local_language_id"] == "9"}
PK_LANG = {"ja-hrkt": "ja", "en": "en", "fr": "fr", "de": "de", "it": "it", "es": "es", "es-419": "es-419",
           "ko": "ko", "zh-hans": "zh-Hans", "zh-hant": "zh-Hant", "ja-roma": "ja-Latn"}
PKREV = MAN["pokeapi"]["revision"]
def pkdoc(name):
    return doc("pokeapi", f"data/v2/csv/{name}.csv@{PKREV[:12]}", PKREV, file_sha(PK / f"{name}.csv"))

sd = json.load(open(CACHE / "showdown-species.json", encoding="utf-8"))
SDREV = MAN["showdown"]["revision"]
def sddoc(game):
    mod = sd["mods"][game]
    p = CACHE / "showdown/data" / ("pokedex.ts" if mod == "gen9" else f"mods/{mod}/pokedex.ts")
    if not p.exists():
        p = CACHE / "showdown/data/pokedex.ts"
    return doc("showdown", f"data/{'' if mod == 'gen9' else 'mods/' + mod + '/'}pokedex.ts (mod {mod})@{SDREV[:12]}", SDREV, file_sha(p))

pkx = {g: json.load(open(DUMP / f"personal_{g}.json", encoding="utf-8")) for g in PKHEX_GAMES}
pkx_names = json.load(open(DUMP / "names.json", encoding="utf-8"))
def _n(x): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", (x or "")).encode("ascii", "ignore").decode().lower())
def strip_variant(x): return re.sub(r"\s*[（(][^()（）]*[)）]\s*$", "", x or "")
_gn = pkx_names["en"]["abilities"]
# Ability ids follow the Pokédex / PokeAPI numbering (option A). Game indices differ from 299 on and the
# four "Embody Aspect" entries of the games collapse into PokeAPI's single id; game indices go to external_id.
G2P = {}
for _gid, _name in enumerate(_gn):
    if not _name or _gid == 0: continue
    if _gid <= 298: G2P[_gid] = _gid; continue
    _c = [p for p, n in _pk_en.items() if p < 10000 and _n(n) == _n(strip_variant(_name))]
    G2P[_gid] = _c[0] if len(_c) == 1 else None
P2G = collections.defaultdict(list)
for _g, _p in G2P.items():
    if _p: P2G[_p].append(_g)
PKXREV = MAN["pkhex"]["revision"]
def pkxdoc(g):
    return doc("pkhex", f"{PKXREV} · PersonalTable.{g.upper()}", PKXREV, file_sha(DUMP / f"personal_{g}.json"))
def pkxnamedoc():
    return doc("pkhex", f"{PKXREV} · GameInfo.Strings (species, abilities, types)", PKXREV, file_sha(DUMP / "names.json"))

def bulba(title):
    m = MAN["bulbapedia:" + title]
    return (ROOT / m["path"]).read_text("utf-8"), doc("bulbapedia", m["url"] + f" (oldid {m['revision']})" if m["revision"].isdigit() else m["url"], m["revision"], m["sha256"])

# ----------------------------------------------------------------------------- form universe (PokeAPI ids, Pokédex keys)
U = {}
for f in pk_forms:
    p = pk_pokemon[f["pokemon_id"]]; s = pk_species[p["species_id"]]
    sid, sident = s["id"], s["identifier"]
    if p["is_default"] == "1" and f["is_default"] == "1":
        key = sid
    else:
        ident = f["identifier"]
        key = f"{sid}-{ident[len(sident) + 1:]}" if ident.startswith(sident + "-") else f"{sid}-{ident}"
    U[key] = dict(key=key, species=int(sid), pokemon_id=int(p["id"]), form_id=int(f["id"]), slug=f["identifier"],
                  form_ident=f["form_identifier"], battle=f["is_battle_only"] == "1", mega=f["is_mega"] == "1",
                  pdef=p["is_default"] == "1", fdef=f["is_default"] == "1", vg=f["introduced_in_version_group_id"],
                  order=int(f["order"] or 0))
BYSP = collections.defaultdict(list)
for k, v in U.items():
    BYSP[v["species"]].append(k)

EXTRA_FORMS = {  # forms present in game data but absent from PokeAPI (ids follow the Pokédex convention)
    "1017-teal-tera": (1017, "ogerpon-teal-tera", "battle-only", "sv"),
    "1017-wellspring-tera": (1017, "ogerpon-wellspring-tera", "battle-only", "sv"),
    "1017-hearthflame-tera": (1017, "ogerpon-hearthflame-tera", "battle-only", "sv"),
    "1017-cornerstone-tera": (1017, "ogerpon-cornerstone-tera", "battle-only", "sv"),
    "59-lord": (59, "arcanine-lord", "totem", "la"), "101-lord": (101, "electrode-lord", "totem", "la"),
    "549-lady": (549, "lilligant-lady", "totem", "la"), "713-lord": (713, "avalugg-lord", "totem", "la"),
    "900-lord": (900, "kleavor-lord", "totem", "la"),
}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("'", "")).strip("-")


# PKHeX English form label (per game context) → suffix of our form id, when names differ
FORM_ALIAS = {
    (20, "large"): "totem-alola", (105, "large"): "totem", (778, "large"): "totem-disguised",
    (25, "ph-d"): "phd", (201, "f"): "f", (201, "m"): "m", (201, ""): "exclamation", (201, "?"): "question",
    (493, ""): "unknown", (555, "galar"): "galar-standard", (555, "galar-zen"): "galar-zen",
    (649, "water"): "douse", (649, "electric"): "shock", (649, "fire"): "burn", (649, "ice"): "chill",
    (658, "active"): "ash", (658, "ash"): "battle-bond", (664, "poke-ball"): "poke-ball", (665, "poke-ball"): "poke-ball", (666, "poke-ball"): "poke-ball",
    (678, "m-mega"): "male-mega", (678, "f-mega"): "female-mega", (710, "jumbo"): "super", (711, "jumbo"): "super",
    (718, "50-c"): "50-power-construct", (718, "10-c"): "10-power-construct", (741, "pau"): "pau", (744, "dusk"): "own-tempo",
    (59, "lord"): "lord", (101, "lord"): "lord", (549, "lady"): "lady", (713, "lord"): "lord", (900, "lord"): "lord",
    (1017, "teal"): "teal-tera", (1017, "wellspring"): "wellspring-tera", (1017, "hearthflame"): "hearthflame-tera",
    (1017, "cornerstone"): "cornerstone-tera",
}
TOTEM_SPECIES = {735, 738, 743, 752, 754, 758, 777, 784}


def fallback_names():
    """Form labels from games where the form is meaningful (megas are labelled 'None' in SV/LA tables)."""
    fb = {}
    for g in ["oras", "usum", "lgpe", "sw", "la", "sv", "za"]:
        for r in pkx[g]:
            if r["form_name_en"] and r["form"] > 0:
                fb.setdefault((r["species"], r["form"]), r["form_name_en"])
    return fb
FB = fallback_names()


def map_form(game, sp, idx, label):
    # version-specific Deoxys forms in Generation III tables
    if sp == 386 and idx == 0:
        return {"fr": "386-attack", "lg": "386-defense", "e": "386-speed"}.get(game, "386")
    lab = label if label not in (None, "None", "") else FB.get((sp, idx))
    n = norm(lab)
    if lab in ("!",): n = ""
    if lab == "?": n = "?"
    if sp == 1017:
        return ["1017", "1017-wellspring-mask", "1017-hearthflame-mask", "1017-cornerstone-mask",
                "1017-teal-tera", "1017-wellspring-tera", "1017-hearthflame-tera", "1017-cornerstone-tera"][idx]
    if sp == 774 and idx > 0:
        color = n.split("-", 1)[1] if "-" in n else n
        return f"774-{color}-meteor" if idx <= 6 else f"774-{color}"
    if sp == 201 and lab == "!": return "201-exclamation"
    if sp == 201 and lab == "?": return "201-question"
    if sp == 493 and lab == "???": return "493-unknown"
    if sp == 869 and idx > 0:
        return f"869-{n}-strawberry-sweet" if f"869-{n}-strawberry-sweet" in U else None
    if sp in TOTEM_SPECIES and n == "large": return f"{sp}-totem"
    if sp == 778 and idx == 3: return "778-totem-busted"
    if (sp, n) in FORM_ALIAS:
        k = f"{sp}-{FORM_ALIAS[(sp, n)]}"
        return k if (k in U or k in EXTRA_FORMS) else None
    keys = BYSP.get(sp, [])
    # the label may name the PokeAPI default form (Vivillon Meadow, Xerneas Neutral, Maushold Four…)
    if str(sp) in U and n and norm(U[str(sp)]["form_ident"]) == n:
        return str(sp)
    if idx == 0:
        for k in keys:
            if k != str(sp) and n and k.split("-", 1)[1] == n:
                return k
        return str(sp)
    for k in keys:
        if k != str(sp) and k.split("-", 1)[1] == n:
            return k
    for alias in ({"f": "female", "m": "male"}.get(n),):
        if alias and f"{sp}-{alias}" in U:
            return f"{sp}-{alias}"
    toks = set(n.split("-")) if n else set()
    c = [k for k in keys if k != str(sp) and toks and toks <= set(k.split("-", 1)[1].split("-"))]
    if len(c) == 1: return c[0]
    c = [k for k in keys if k != str(sp) and toks and set(k.split("-", 1)[1].split("-")) <= toks]
    if len(c) == 1: return c[0]
    return None


def gtype(game, t):
    return R.GB_TYPES.get(t) if GAME_GEN[game] <= 2 else (R.TYPES[t] if t < len(R.TYPES) else None)


# ----------------------------------------------------------------------------- per-game form data from PKHeX (tier 1)
pk_rows = {}      # (form_key, game) -> dict
unmapped = []
skipped_shared = []
form_types_ids = set(r["pokemon_form_id"] for r in pcsv("pokemon_form_types"))
MAPLOG = []
GAME_OF = {"fr": "frlg", "lg": "frlg"}
NO_ABILITY_GAMES = {"lgpe", "la", "za"}  # abilities do not exist in these games' gameplay (placeholder values in data)
for g in PKHEX_GAMES:
    gid = GAME_OF.get(g, g)
    for r in pkx[g]:
        if not r["present"]:
            continue
        key = map_form(g, r["species"], r["form"], r["form_name_en"])
        if key is not None and r["form"] > 0 and r["entry"] == r["base_entry"]:
            # no own entry in this game's data: only cosmetic forms share the base data
            u = U.get(key)
            cosmetic = u and u["pdef"] and not u["fdef"] and not u["battle"] and str(u["form_id"]) not in form_types_ids
            if not (cosmetic or key == str(r["species"])):
                skipped_shared.append((g, key))
                continue
        if key is None:
            unmapped.append((g, r["species"], r["form"], r["form_name_en"]))
            continue
        MAPLOG.append((r["species"], r["form"], r["form_name_en"], key))
        gen = GAME_GEN[gid]
        t1, t2 = gtype(g, r["type1"]), gtype(g, r["type2"])
        ab = [a for a in r["abilities"]]
        slots = {}
        if gen >= 3 and ab and gid not in NO_ABILITY_GAMES:
            ab = [G2P.get(a, a) if a else 0 for a in ab]
            if ab[0]: slots["1"] = ab[0]
            if len(ab) > 1 and ab[1] and ab[1] != ab[0]: slots["2"] = ab[1]
            if gen >= 5 and len(ab) > 2 and ab[2] and ab[2] not in (ab[0], ab[1]): slots["hidden"] = ab[2]
        row = dict(form_id=key, game_id=gid, type1=t1, type2=(t2 if t2 != t1 else None),
                   stats=[r["hp"], r["atk"], r["def"], r["spa"], r["spd"], r["spe"]],
                   height=r["height"] or None, weight=r["weight"] or None, base_exp=r["base_exp"] or None,
                   catch_rate=r["catch_rate"], friendship=(r["friendship"] if gen >= 2 else None),
                   ev=(r["ev"] if gen >= 3 else None), abilities=slots, src_game=g,
                   gender=r["gender"], hatch=r["hatch"], growth=r["growth"], egg=r["egg"], species=r["species"])
        k2 = (key, gid)
        if k2 in pk_rows and g in ("lg",):
            continue
        pk_rows[k2] = row

# derived rows: DLC (same personal table, latest patch), Switch re-release of FR/LG (same ROM data), Gigantamax forms
DERIVED = {"swisle": "sw", "swcrown": "sw", "svmask": "sv", "svdisk": "sv", "zadlc": "za", "frlgsw": "frlg"}
for (key, gid), row in list(pk_rows.items()):
    for child, parent in DERIVED.items():
        if gid == parent:
            pk_rows[(key, child)] = {**row, "game_id": child, "derived_from": parent}
bulba_gmax_text, bulba_gmax_doc = bulba("Gigantamax")
gmax_nums = set(int(x) for x in re.findall(r"#(\d{4})\s*\n\|\s*\{\{p\|", bulba_gmax_text))
for key, u in U.items():
    if key.endswith("-gmax") or key.endswith("-low-key-gmax"):
        base = str(u["species"]) if not key.endswith("-low-key-gmax") else f"{u['species']}-low-key"
        if u["species"] == 892: base = "892-rapid-strike" if "rapid" in key else "892"
        for gid in ("sw", "swisle", "swcrown"):
            if (base, gid) in pk_rows:
                pk_rows[(key, gid)] = {**pk_rows[(base, gid)], "form_id": key, "game_id": gid, "derived_from": f"{base}@{gid}"}

# cosmetic forms the game data does not enumerate (Unown letters before gen 5, gender forms, Alcremie sweets):
# they share the default form's data in every game of their generation onward where the species has data.
VG_GEN = {r["id"]: int(r["generation_id"]) for r in pcsv("version_groups")}
pk_keys_any = {k for (k, g), row in pk_rows.items() if "derived_from" not in row}
COSMETIC_FILLED = []
native = {k for k, row in pk_rows.items() if "derived_from" not in row or row["derived_from"] in DERIVED.values()}
for key, u in U.items():
    if not (u["pdef"] and not u["fdef"] and not u["battle"] and not u["mega"] and str(u["form_id"]) not in form_types_ids):
        continue
    if "gmax" in key or "totem" in key:
        continue
    sp = str(u["species"])
    sibs = [k for k, v in U.items() if v["species"] == u["species"] and k != key and k != sp and not (v["fdef"])]
    for gid in GAME_GEN:
        if GAME_GEN[gid] is None or GAME_GEN[gid] < VG_GEN[u["vg"]] or (sp, gid) not in pk_rows or (key, gid) in pk_rows:
            continue
        if key in pk_keys_any and (not sibs or any((k, gid) in native for k in sibs)):
            continue  # the game enumerates this species' forms and this one is not among them
        base = pk_rows[(sp, gid)]
        pk_rows[(key, gid)] = {**base, "form_id": key, "game_id": gid, "derived_from": f"{sp}@{gid}"}
        COSMETIC_FILLED.append((key, gid))

# ----------------------------------------------------------------------------- PokeAPI per-generation values (tier 3)
STAT_COL = {"1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5}
cur_stats = collections.defaultdict(dict)
for r in pcsv("pokemon_stats"):
    if r["stat_id"] in STAT_COL: cur_stats[r["pokemon_id"]][STAT_COL[r["stat_id"]]] = int(r["base_stat"])
past_stats = collections.defaultdict(list)
for r in pcsv("pokemon_stats_past"):
    past_stats[r["pokemon_id"]].append((int(r["generation_id"]), r["stat_id"], int(r["base_stat"])))
cur_types = collections.defaultdict(dict)
for r in pcsv("pokemon_types"):
    cur_types[r["pokemon_id"]][int(r["slot"])] = pk_types[r["type_id"]]
past_types = collections.defaultdict(list)
for r in pcsv("pokemon_types_past"):
    past_types[r["pokemon_id"]].append((int(r["generation_id"]), int(r["slot"]), pk_types[r["type_id"]]))
form_types = collections.defaultdict(dict)
for r in pcsv("pokemon_form_types"):
    form_types[r["pokemon_form_id"]][int(r["slot"])] = pk_types[r["type_id"]]
cur_ab = collections.defaultdict(dict)
for r in pcsv("pokemon_abilities"):
    cur_ab[r["pokemon_id"]][{"1": "1", "2": "2", "3": "hidden"}[r["slot"]]] = int(r["ability_id"])
past_ab = collections.defaultdict(list)
for r in pcsv("pokemon_abilities_past"):
    past_ab[r["pokemon_id"]].append((int(r["generation_id"]), {"1": "1", "2": "2", "3": "hidden"}[r["slot"]], int(r["ability_id"]) if r["ability_id"] else None))


def pokeapi_values(key, gen):
    u = U.get(key)
    if not u: return None
    pid = str(u["pokemon_id"])
    stats = [cur_stats[pid].get(i) for i in range(6)]
    for col in range(6):
        cands = sorted((g, v) for g, sid, v in past_stats[pid] if g >= gen and (STAT_COL.get(sid) == col or (sid == "9" and col in (3, 4))))
        if cands: stats[col] = cands[0][1]
    types = dict(cur_types[pid])
    if str(u["form_id"]) in form_types: types = dict(form_types[str(u["form_id"])])
    pt = sorted(set(g for g, s, t in past_types[pid] if g >= gen))
    if pt:
        types = {s: t for g, s, t in past_types[pid] if g == pt[0]}
    ab = dict(cur_ab[pid])
    pa = sorted(set(g for g, s, a in past_ab[pid] if g >= gen))
    if pa:
        for g, s, a in past_ab[pid]:
            if g == pa[0]:
                if a is None: ab.pop(s, None)
                else: ab[s] = a
    if gen < 5: ab.pop("hidden", None)
    if ab.get("hidden") in (ab.get("1"), ab.get("2")): ab.pop("hidden", None)
    if gen < 3: ab = {}
    return dict(types=[types.get(1), types.get(2)], stats=stats, abilities=ab)


# ----------------------------------------------------------------------------- Showdown per-game values (tier 3)
ABIL_GEN = {int(i): int(a["generation_id"]) for i, a in pk_abil.items()}
abil_by_name = {norm(n): G2P.get(i) for i, n in enumerate(pkx_names["en"]["abilities"]) if n and i and G2P.get(i)}
SD_SUFFIX = {"female": "f", "male": "m", "galar-standard": "galar", "paldea-combat-breed": "paldeacombat",
             "paldea-blaze-breed": "paldeablaze", "paldea-aqua-breed": "paldeaaqua", "totem-alola": "alolatotem",
             "own-tempo": "dusk", "50-power-construct": "", "10-power-construct": "10", "50": "", "phd": "phd"}


def sdid(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


sd_index = {}
for g, table in sd["games"].items():
    idx = {}
    for i, e in table.items():
        idx.setdefault((e["num"], sdid(e.get("forme") or "")), i)
    sd_index[g] = idx


def showdown_values(key, game):
    sg = {"frlg": "frlg", "frlgsw": "frlg", "swisle": "sw", "swcrown": "sw", "svmask": "sv", "svdisk": "sv", "zadlc": "za"}.get(game, game)
    if sg not in sd["games"]: return None
    sp, _, suf = key.partition("-")
    sp = int(sp)
    cands = [sdid(SD_SUFFIX.get(suf, suf))] if suf else [""]
    if key in ("386-attack", "386-defense", "386-speed"): cands = [suf]
    if sp == 774: cands = ["meteor"] if (not suf or suf.endswith("meteor")) else [""]
    e = None
    for c in cands:
        i = sd_index[sg].get((sp, c))
        if i: e = sd["games"][sg][i]; break
    if not e: return None
    gen = GAME_GEN[game]
    st = e["baseStats"]
    stats = [st["hp"], st["atk"], st["def"], st["spa"], st["spd"], st["spe"]]
    if gen == 1: stats[4] = stats[3]
    types = [t.lower() for t in e["types"]] + [None]
    ab = {}
    if gen >= 3:
        for slot, name in (e.get("abilities") or {}).items():
            s = {"0": "1", "1": "2", "H": "hidden"}.get(str(slot))
            if s and (gen >= 5 or s != "hidden") and norm(name) in abil_by_name and ABIL_GEN.get(abil_by_name[norm(name)], 99) <= gen:
                ab[s] = abil_by_name[norm(name)]
        if ab.get("hidden") in (ab.get("1"), ab.get("2")): ab.pop("hidden", None)
        if "2" in ab and ab["2"] == ab.get("1"): ab.pop("2")
    return dict(types=types[:2], stats=stats, abilities=ab)


# ----------------------------------------------------------------------------- build tables
out = {}

# reference
out["language"] = (["id", "name_native", "is_official", "sort_order", "pokeapi_id", "note"], [list(l) for l in R.LANGUAGES])
out["generation"] = (["id", "main_region"], [list(g) for g in R.GENERATIONS])
out["region"] = (["id", "generation_id"], [list(r) for r in R.REGIONS])
out["game"] = (["id", "kind", "generation_id", "base_game_id", "release_date", "platform", "sort_order",
                "pokeapi_version_group", "is_active_service", "note"],
               [[g[0], g[1], g[2], g[3], g[4], g[5], g[6], g[7], g[8], g[9]] for g in R.GAMES])
vers = []
for i, (vid, gid, pid) in enumerate(R.VERSIONS):
    vers.append([vid, gid, pid, i + 1])
out["version"] = (["id", "game_id", "pokeapi_id", "sort_order"], vers)
gl = []
for g in R.GAMES:
    for l in g[10]:
        since = R.LANG_SINCE.get((g[0], l), (None, None))
        gl.append([g[0], l, since[0], since[1]])
out["game_language"] = (["game_id", "language_id", "since_date", "since_game_version"], gl)
out["source"] = (["id", "name", "tier", "base_url", "license", "note"], [list(s) for s in R.SOURCES])
out["type"] = (["id", "generation_id", "pokeapi_id", "go_template"],
               [[t, R.TYPE_GEN.get(t, 1), i + 1, f"POKEMON_TYPE_{t.upper()}"] for i, t in enumerate(R.TYPES)]
               + [["stellar", 9, 19, None], ["unknown", 2, 10001, None]])
out["growth_rate"] = (["id", "formula"], [[k, R.GROWTH_FORMULA[k]] for k in R.GROWTH.values()])
out["egg_group"] = (["id"], [[e] for e in R.EGG.values()])
for t in ("language", "generation", "region", "game", "version", "game_language", "source", "type", "growth_rate", "egg_group"):
    hdr, rows = out[t]
    for r in rows:
        rk = row_key(*r[:2]) if t == "game_language" else row_key(r[0])
        verifs.append((t, rk, "*", "manual", sha256_text(canon(r)), sha256_text("reference.py:" + canon(r))))

# species
# species-level values (gender, growth, eggs, hatch) come from the most recent game with breeding
BREED_ORDER = ["sv", "bdsp", "sw", "usum", "sm", "oras", "xy", "b2w2", "bw", "hgss", "pt", "dp", "e", "frlg", "rs", "c", "gs", "y", "rb", "za"]
latest = {}
for (key, gid), row in pk_rows.items():
    if row.get("derived_from") or gid not in BREED_ORDER: continue
    sp = row["species"]
    if key == str(sp) and (sp not in latest or BREED_ORDER.index(gid) < BREED_ORDER.index(latest[sp]["game_id"])):
        latest[sp] = row
GENDER = {255: -1, 254: 8, 0: 0, 31: 1, 63: 2, 127: 4, 191: 6, 225: 7}

def bulba_cat(cat):
    m = MAN["bulbapedia:Category:" + cat]
    names = json.load(open(ROOT / m["path"], encoding="utf-8"))
    d = doc("bulbapedia", m["url"], m["revision"] + "@" + m["retrieved_at"][:10], m["sha256"])
    return set(re.sub(r" \(Pokémon\)$", "", n) for n in names), d

en_names = pkx_names["en"]["species"]
fr_names = pkx_names["fr"]["species"]
def ppe_cat(cat):
    m = MAN["pokepedia:Catégorie:" + cat]
    names = set(json.load(open(ROOT / m["path"], encoding="utf-8")))
    return names, doc("pokepedia", m["url"], m["revision"] + "@" + m["retrieved_at"][:10], m["sha256"])
ppe = {"Legendary Pokémon": ppe_cat("Pokémon légendaire"), "Mythical Pokémon": ppe_cat("Pokémon fabuleux"),
       "Ultra Beasts": ppe_cat("Ultra-Chimère"), "Paradox Pokémon": ppe_cat("Pokémon Paradoxe")}
cats = {c: bulba_cat(c) for c in ["Legendary Pokémon", "Mythical Pokémon", "Ultra Beasts", "Paradox Pokémon", "Baby Pokémon"]}
gd_text, gd_doc = bulba("List of Pokémon with gender differences")
gd_nums = set(int(x) for x in re.findall(r"\{\{gendif\|(\d{4})\|", gd_text))
sd_cur = sd["games"]["sv"]
sp_rows, egg_rows = [], []
d_pkspecies = pkdoc("pokemon_species")
d_sv = sddoc("sv")
for sid in range(1, 1026):
    s = pk_species[str(sid)]
    rk = row_key(sid)
    gen = next(g for a, b, g in R.GEN_RANGES if a <= sid <= b)
    lr = latest.get(sid)
    name = en_names[sid]
    sde = sd_cur.get(sdid(name)) or next((e for e in sd_cur.values() if e["num"] == sid and not e.get("forme")), None)
    tags = set(sde["tags"]) if sde else set()
    def flag(col, pk_val, sd_val, cat):
        obs = []
        if pk_val is not None: obs.append(("pokeapi", d_pkspecies, pk_val))
        if sd_val is not None: obs.append(("showdown", d_sv, sd_val))
        if cat: obs.append(("bulbapedia", cats[cat][1], 1 if name in cats[cat][0] else 0))
        if cat in ppe: obs.append(("pokepedia", ppe[cat][1], 1 if fr_names[sid] in ppe[cat][0] else 0))
        return resolve("species", rk, col, obs)[0]
    legendary = flag("is_legendary", int(s["is_legendary"]), 1 if tags & {"Sub-Legendary", "Restricted Legendary"} else 0, "Legendary Pokémon")
    mythical = flag("is_mythical", int(s["is_mythical"]), 1 if "Mythical" in tags else 0, "Mythical Pokémon")
    ub = flag("is_ultra_beast", None, 1 if "Ultra Beast" in tags else 0, "Ultra Beasts")
    paradox = flag("is_paradox", None, 1 if "Paradox" in tags else 0, "Paradox Pokémon")
    baby = flag("is_baby", int(s["is_baby"]), None, "Baby Pokémon")
    gdiff = resolve("species", rk, "has_gender_differences",
                    [("pokeapi", d_pkspecies, int(s["has_gender_differences"])), ("bulbapedia", gd_doc, 1 if sid in gd_nums else 0)])[0]
    d_lr = pkxdoc(lr["src_game"]) if lr else None
    g_val = GENDER.get(lr["gender"]) if lr else None
    if g_val in (0, 8) and f"{sid}-female" in U or f"{sid}-male" in U and g_val in (0, 8):
        g_val = 4  # species split into male/female forms (Meowstic, Indeedee, Basculegion, Oinkologne)
    gender = resolve("species", rk, "gender_rate", [("pkhex", d_lr, g_val),
                                                    ("pokeapi", d_pkspecies, int(s["gender_rate"]))])[0]
    growth = resolve("species", rk, "growth_rate_id", [("pkhex", d_lr, R.GROWTH.get(lr["growth"]) if lr else None),
                                                       ("pokeapi", d_pkspecies, {"1": "slow", "2": "medium-fast", "3": "fast", "4": "medium-slow", "5": "erratic", "6": "fluctuating"}[s["growth_rate_id"]])])[0]
    hatch = resolve("species", rk, "hatch_cycles", [("pkhex", d_lr, lr["hatch"] if lr and lr["hatch"] else None),
                                                    ("pokeapi", d_pkspecies, int(s["hatch_counter"]) if s["hatch_counter"] else None)])[0]
    resolve("species", rk, "generation_id", [("pkhex", d_lr, gen), ("pokeapi", d_pkspecies, int(s["generation_id"]))])
    sp_rows.append([sid, s["identifier"], gen, None, growth, gender, hatch, baby, legendary, mythical, ub, paradox, gdiff])
    if lr:
        eggs = sorted(set(R.EGG[e] for e in lr["egg"] if e in R.EGG))
        for e in eggs:
            egg_rows.append([sid, e])
        resolve("species_egg_group", rk, "*", [("pkhex", d_lr, eggs)])
out["species"] = (["id", "slug", "generation_id", "evolution_chain_id", "growth_rate_id", "gender_rate", "hatch_cycles",
                   "is_baby", "is_legendary", "is_mythical", "is_ultra_beast", "is_paradox", "has_gender_differences"], sp_rows)
out["species_egg_group"] = (["species_id", "egg_group_id"], egg_rows)

# forms
def category(key, u):
    suf = key.partition("-")[2]
    if not suf: return "default"
    if key in EXTRA_FORMS: return EXTRA_FORMS[key][2]
    if u["mega"]: return "mega"
    if "primal" in suf: return "primal"
    if suf.endswith("gmax"): return "gigantamax"
    if "totem" in suf: return "totem"
    if suf in ("female", "male") or suf.endswith("-female") and not u["mega"]: return "gender"
    if u["battle"]: return "battle-only"
    if any(r in suf for r in ("alola", "galar", "hisui", "paldea")): return "regional"
    if u["pdef"] and not u["fdef"]: return "cosmetic"
    return "alternate"

VG_GAME = {}
for r in pcsv("version_groups"):
    VG_GAME[r["id"]] = next((g[0] for g in R.GAMES if g[7] == r["identifier"]), None)
in_games = collections.defaultdict(set)
for (key, gid) in pk_rows: in_games[key].add(gid)
order_games = [g[0] for g in R.GAMES]
form_rows, form_present = [], set()
d_pkforms = pkdoc("pokemon_forms")
all_keys = list(U.keys()) + list(EXTRA_FORMS.keys())
for key in all_keys:
    u = U.get(key)
    if u:
        sp, slug = u["species"], u["slug"]
    else:
        sp, slug = EXTRA_FORMS[key][0], EXTRA_FORMS[key][1]
    cat = category(key, u or {"mega": False, "battle": True, "pdef": False, "fdef": False})
    games = sorted(in_games.get(key, []), key=order_games.index)
    intro = games[0] if games else (VG_GAME.get(u["vg"]) if u else None)
    base = None
    if cat in ("mega", "primal", "gigantamax", "totem", "battle-only", "cosmetic", "gender") and key != str(sp):
        base = str(sp)
        if key.endswith("-low-key-gmax"): base = f"{sp}-low-key"
        if key.startswith("892-") and key.endswith("gmax"): base = "892-rapid-strike" if "rapid" in key else "892"
        if key.startswith("1017-") and key.endswith("-tera"):
            m = key[5:-5]; base = "1017" if m == "teal" else f"1017-{m}-mask"
    rk = row_key(key)
    obs = []
    if games: obs.append(("pkhex", pkxdoc({"frlg": "fr", "frlgsw": "fr"}.get(games[0], games[0]) if games[0] in PKHEX_GAMES + ["frlg"] else "sv"), True))
    if u: obs.append(("pokeapi", d_pkforms, True))
    sdv = showdown_values(key, "sv") or showdown_values(key, "za") or showdown_values(key, "sw") or showdown_values(key, "usum")
    if sdv: obs.append(("showdown", d_sv, True))
    if key.endswith("gmax") and sp in gmax_nums: obs.append(("bulbapedia", bulba_gmax_doc, True))
    resolve("form", rk, "*", obs)
    form_rows.append([key, sp, slug, cat, 1 if key == str(sp) else 0, 1 if (u and u["battle"]) or cat == "battle-only" else 0,
                      base, intro, (u["order"] if u else 9999), (u["pokemon_id"] if u else None), (u["form_id"] if u else None), None])
form_ids = set(r[0] for r in form_rows)
out["form"] = (["id", "species_id", "slug", "category", "is_default", "is_battle_only", "base_form_id", "introduced_game_id",
                "sort_order", "pokeapi_pokemon_id", "pokeapi_form_id", "note"], form_rows)

# form_game + form_ability
fg_rows, fa_rows = [], []
d_pstats, d_ptypes, d_pab = pkdoc("pokemon_stats"), pkdoc("pokemon_types"), pkdoc("pokemon_abilities")
for (key, gid), row in sorted(pk_rows.items()):
    if key not in form_ids: continue
    gen = GAME_GEN[gid]
    rk = row_key(key, gid)
    src_game = row["src_game"]
    d1 = pkxdoc(src_game)
    pv = pokeapi_values(key, gen)
    sv = showdown_values(key, gid)
    d_sd = sddoc({"frlg": "frlg", "frlgsw": "frlg", "swisle": "sw", "swcrown": "sw", "svmask": "sv", "svdisk": "sv", "zadlc": "za"}.get(gid, gid)) if sv else None
    types = [row["type1"], row["type2"]]
    stats = row["stats"]
    def obs3(field, mine):
        o = [("pkhex", d1, mine)]
        if pv: o.append(("pokeapi", d_ptypes if field == "types" else d_pstats if field == "stats" else d_pab, pv[field]))
        if sv: o.append(("showdown", d_sd, sv[field]))
        return o
    def cmp_types(v): return canon([x for x in v if x])
    def cmp_stats(v): return canon(v[:3] + [v[3]] + v[5:] if gen == 1 else v)
    resolve("form_game", rk, "types", obs3("types", types), cmp_types)
    resolve("form_game", rk, "stats", obs3("stats", stats), cmp_stats)
    if gen >= 3 and gid not in NO_ABILITY_GAMES | {"zadlc"}:
        resolve("form_ability", rk, "*", obs3("abilities", row["abilities"]), lambda v: canon({k: int(x) for k, x in v.items()}))
    ev = row["ev"] or [None] * 6
    other = dict(height_dm=row["height"], weight_hg=row["weight"], base_exp=row["base_exp"], catch_rate=row["catch_rate"],
                 base_friendship=row["friendship"], ev=row["ev"])
    resolve("form_game", rk, "*", [("pkhex", d1, other)])
    fg_rows.append([key, gid, types[0], types[1], *stats, row["height"], row["weight"], row["base_exp"], row["catch_rate"],
                    row["friendship"], *ev, 1, canon({"derived_from": row["derived_from"]}) if row.get("derived_from") else None])
    for slot, a in row["abilities"].items():
        fa_rows.append([key, gid, slot, a])
out["form_game"] = (["form_id", "game_id", "type1_id", "type2_id", "hp", "atk", "def", "spa", "spd", "spe", "height_dm",
                     "weight_hg", "base_exp", "catch_rate", "base_friendship", "ev_hp", "ev_atk", "ev_def", "ev_spa", "ev_spd",
                     "ev_spe", "in_game_data", "extra"], fg_rows)
out["form_ability"] = (["form_id", "game_id", "slot", "ability_id"], fa_rows)

# abilities: ids = game index (PKHeX / Showdown numbering); PokeAPI ids differ from 299 on → external_id
sd_ab = {}
_t = open(CACHE / "showdown/data/abilities.ts", encoding="utf-8").read()
for _k, _b in re.findall(r"^\t(\w+): \{\n(.*?)^\t\},", _t, re.M | re.S):
    _n = re.search(r'^\t\tname: "([^"]+)"', _b, re.M); _u = re.search(r"^\t\tnum: (-?\d+)", _b, re.M)
    if _n and _u and int(_u.group(1)) > 0: sd_ab[int(_u.group(1))] = _n.group(1)
d_sdab = doc("showdown", f"data/abilities.ts@{SDREV[:12]}", SDREV, file_sha(CACHE / "showdown/data/abilities.ts"))
pk_ab_en = {}
for r in pcsv("ability_names"):
    if r["local_language_id"] == "9": pk_ab_en[int(r["ability_id"])] = r["name"]
ab_rows = []
d_pkab = pkdoc("ability_names")
gnames = pkx_names["en"]["abilities"]
for pid in sorted(P2G):
    gids = sorted(P2G[pid])
    ab_rows.append([pid, pk_abil[str(pid)]["identifier"], int(pk_abil[str(pid)]["generation_id"])])
    obs = [("pkhex", pkxnamedoc(), strip_variant(gnames[gids[0]]))]
    sdn = [strip_variant(sd_ab[g]) for g in gids if g in sd_ab]
    if sdn: obs.append(("showdown", d_sdab, sdn[0]))
    obs.append(("pokeapi", d_pkab, _pk_en.get(pid)))
    resolve("ability", row_key(pid), "*", obs, lambda v: canon(norm(v)))
out["ability"] = (["id", "slug", "generation_id"], ab_rows)

# ----------------------------------------------------------------------------- translations
tr_rows = []
def add_tr(entity, eid, field, lang, obs, compare=nfkc):
    rk = row_key(entity, str(eid), field, lang, None, None)
    v, st = resolve("translation", rk, "text", obs, lambda x: canon(nfkc(x)))
    if v: tr_rows.append([entity, str(eid), field, lang, None, None, v, 1])

# Bulbapedia name lists
BUL = {}
eng = {}
for lang, title in [("ja", "List of Japanese Pokémon names"), ("fr", "List of French Pokémon names"), ("de", "List of German Pokémon names"),
                    ("ko", "List of Korean Pokémon names"), ("zh", "List of Chinese Pokémon names"), ("it", "List of Italian Pokémon names"),
                    ("es", "List of Spanish Pokémon names")]:
    text, d = bulba(title)
    for m in re.finditer(r"\{\{Lop/foreign\|(\d{4})\|([^|}]*)\|(\w+)\|([^|}]*)(?:\|([^|}]*))?(?:\|([^|}]*))?", text):
        num = int(m.group(1)); eng.setdefault(num, m.group(2))
        def clean(x): return re.sub(r"<ref.*", "", x or "").strip()
        if lang == "zh":
            BUL[(num, "zh-Hant")] = (clean(m.group(4)), d); BUL[(num, "zh-Hans")] = (clean(m.group(5)), d)
        elif lang == "ja":
            BUL[(num, "ja")] = (clean(m.group(4)), d)
            if m.group(6): BUL[(num, "ja-Latn")] = (clean(m.group(6)), d)
        else:
            BUL[(num, lang)] = (clean(m.group(4)), d)
    if lang in ("it", "es"):
        BUL[("doc", lang)] = d
for num, e in eng.items():  # Italian/Spanish lists only record names that differ from English
    for lang in ("it", "es"):
        BUL.setdefault((num, lang), (e, BUL[("doc", lang)]))

pk_names = collections.defaultdict(dict)
for r in pcsv("pokemon_species_names"):
    l = PK_LANG.get(pk_lang[r["local_language_id"]])
    if l: pk_names[int(r["pokemon_species_id"])][l] = r["name"]
d_pknames = pkdoc("pokemon_species_names")
d_pkx = pkxnamedoc()
for sid in range(1, 1026):
    for lang in LANGS + ["ja-Latn"]:
        obs = []
        if lang in pkx_names: obs.append(("pkhex", d_pkx, pkx_names[lang]["species"][sid]))
        if lang in pk_names[sid]: obs.append(("pokeapi", d_pknames, pk_names[sid][lang]))
        b = BUL.get((sid, lang))
        if b and b[0]: obs.append(("bulbapedia", b[1], b[0]))
        add_tr("species", sid, "name", lang, obs)

# types and abilities names
pk_type_names = collections.defaultdict(dict)
for r in pcsv("type_names"):
    l = PK_LANG.get(pk_lang[r["local_language_id"]])
    if l: pk_type_names[int(r["type_id"])][l] = r["name"]
d_ptn = pkdoc("type_names")
for i, t in enumerate(R.TYPES + ["stellar"]):
    for lang in LANGS:
        obs = [("pkhex", d_pkx, pkx_names[lang]["types"][i])] if i < len(pkx_names[lang]["types"]) else []
        tid = i + 1
        if lang in pk_type_names[tid]: obs.append(("pokeapi", d_ptn, pk_type_names[tid][lang]))
        add_tr("type", t, "name", lang, obs)
pk_ab_names = collections.defaultdict(dict)
for r in pcsv("ability_names"):
    l = PK_LANG.get(pk_lang[r["local_language_id"]])
    if l: pk_ab_names[int(r["ability_id"])][l] = r["name"]
d_pan = pkdoc("ability_names")
for aid, slug, gen in ab_rows:
    for lang in LANGS:
        lst = pkx_names[lang]["abilities"]
        g0 = sorted(P2G[aid])[0]
        obs = [("pkhex", d_pkx, strip_variant(lst[g0]))] if g0 < len(lst) and lst[g0] else []
        if lang in pk_ab_names[aid]: obs.append(("pokeapi", d_pan, pk_ab_names[aid][lang]))
        add_tr("ability", aid, "name", lang, obs)
out["translation"] = (["entity_type", "entity_id", "field", "language_id", "game_id", "version_id", "text", "is_official"], tr_rows)

# external ids (aliases: readable slugs, PokeAPI, Showdown)
ext = []
for r in form_rows:
    ext.append(["form", r[0], "slug", r[2]])
    if r[9]: ext.append(["form", r[0], "pokeapi-pokemon", str(r[9])])
    if r[10]: ext.append(["form", r[0], "pokeapi-form", str(r[10])])
for r in sp_rows:
    ext.append(["species", str(r[0]), "slug", r[1]])
    ext.append(["species", str(r[0]), "showdown", sdid(en_names[r[0]])])
for aid, slug, gen in ab_rows:
    ext.append(["ability", str(aid), "game-index", ",".join(str(g) for g in sorted(P2G[aid]))])
    ext.append(["ability", str(aid), "slug", slug])
out["external_id"] = (["entity_type", "entity_id", "system", "value"], ext)

# ----------------------------------------------------------------------------- provenance tables + log
out["source_document"] = (["id", "source_id", "locator", "revision", "retrieved_at", "content_sha256"],
                          [[d["id"], d["source_id"], d["locator"], d["revision"], d["retrieved_at"], d["content_sha256"]] for d in documents.values()])
bad=[c for c in citations if c[3] is None]
if bad: print("BAD", len(bad), bad[:5]); sys.exit(1)
cit_rows = [[i + 1, *c] for i, c in enumerate(sorted(set(citations)))]
out["citation"] = (["id", "table_name", "row_key", "column_name", "document_id", "observed_value", "agrees"], cit_rows)

# keep verified_at / update_id of rows whose fingerprint did not change (no re-verification loop)
prev = {(r["table_name"], r["row_key"], r["column_name"]): r for r in read_csv("verification")}
prev_log = read_csv("update_log")
update_id = (max(int(r["id"]) for r in prev_log) + 1) if prev_log else 1
ver_rows, changed = [], 0
for t, rk, col, st, vh, fp in verifs:
    p = prev.get((t, rk, col))
    if p and p["sources_fingerprint"] == fp and p["value_sha256"] == vh and p["status"] == st:
        ver_rows.append([t, rk, col, st, vh, fp, p["verified_at"], p["update_id"]])
    else:
        changed += 1
        ver_rows.append([t, rk, col, st, vh, fp, NOW, update_id])
out["verification"] = (["table_name", "row_key", "column_name", "status", "value_sha256", "sources_fingerprint", "verified_at", "update_id"], ver_rows)
out["discrepancy"] = (["id", "table_name", "row_key", "column_name", "chosen_value", "rule", "alternatives", "note",
                       "opened_update_id", "closed_update_id"],
                      [[i + 1, *d, update_id, (update_id if d[4] != "open" else None)] for i, d in enumerate(sorted(discreps))])

status_counts = collections.Counter(v[3] for v in verifs)
stats = {"rows": {t: len(r) for t, (h, r) in out.items()}, "verification": dict(status_counts),
         "discrepancies": len(discreps), "reverified": changed, "unmapped_pkhex_rows": len(unmapped), "skipped_shared_entry": len(skipped_shared), "cosmetic_filled": len(COSMETIC_FILLED)}
if changed:
    log = [[int(r["id"]), r["started_at"], r["finished_at"], r["kind"], r["trigger"], r["data_version"], r["schema_version"],
            r["git_commit"], r["summary"], r["stats"]] for r in prev_log]
    log.append([update_id, NOW, NOW, "initial" if not prev_log else "weekly", "Phase 1 — espèces, formes, noms",
                DATA_VERSION, SCHEMA_VERSION, None,
                f"Import et vérification : {len(sp_rows)} espèces, {len(form_rows)} formes, {len(fg_rows)} lignes forme×jeu, "
                f"{len(tr_rows)} traductions ; {len(discreps)} écarts notés ; {changed} données (re)vérifiées.", canon(stats)])
    out["update_log"] = (["id", "started_at", "finished_at", "kind", "trigger", "data_version", "schema_version", "git_commit", "summary", "stats"], log)
    items = [[update_id, t, "*", "*", "verify", None, str(n), None] for t, n in collections.Counter(v[0] for v in verifs).items()]
    prev_items = [[int(r["update_id"]), r["table_name"], r["row_key"], r["column_name"], r["action"], r["old_value"] or None,
                   r["new_value"] or None, r["document_ids"] or None] for r in read_csv("update_log_item")]
    out["update_log_item"] = (["update_id", "table_name", "row_key", "column_name", "action", "old_value", "new_value", "document_ids"], prev_items + items)

for name, (hdr, rows) in out.items():
    write_csv(name, hdr, rows)
json.dump({"mapping": sorted(set(MAPLOG), key=lambda x: (x[0], x[1], str(x[2]))), "unmapped": unmapped, "skipped_shared_entry": sorted(set(skipped_shared))}, open(ROOT / "reports/phase1-unmapped.json", "w"), ensure_ascii=False, indent=0)
print(json.dumps(stats, indent=1, ensure_ascii=False))
