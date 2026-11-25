"""Export the static API (site/api/v1/**) from build/pokedata.sqlite.

Only verified data is exported (status game-data, unanimous, majority, manual; single-source is exported
and flagged). Data files carry no version or timestamp: only api/v1/index.json does, so a weekly update
only changes the files whose data really changed.
"""
import collections, json, os, shutil, sqlite3, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, ROOT

SITE = ROOT / "site"
API = SITE / "api" / "v1"
REPO = os.environ.get("GITHUB_REPOSITORY", "SIGjoueA/pokedata")
PAGES = f"https://{REPO.split('/')[0].lower()}.github.io/{REPO.split('/')[1]}"
OK = {"game-data", "unanimous", "majority", "manual", "single-source"}
LANGS = ["ja", "en", "fr", "de", "it", "es", "es-419", "ko", "zh-Hans", "zh-Hant"]


def write(rel, obj):
    p = API / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")), "utf-8")


def fold(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def main():
    db = sqlite3.connect(BUILD / "pokedata.sqlite")
    db.row_factory = sqlite3.Row
    q = lambda sql, *a: db.execute(sql, a).fetchall()
    if API.exists():
        shutil.rmtree(API)
    meta = {r["key"]: r["value"] for r in q("SELECT * FROM meta")}

    ver = collections.defaultdict(dict)
    for r in q("SELECT table_name, row_key, column_name, status FROM verification"):
        ver[(r["table_name"], r["row_key"])][r["column_name"]] = r["status"]
    def status(table, rk, col="*"):
        return ver.get((table, rk), {}).get(col)
    def okv(table, rk, col="*"):
        return status(table, rk, col) in OK
    rk = lambda *parts: json.dumps(list(parts), ensure_ascii=False, separators=(",", ":"))

    names = collections.defaultdict(dict)
    for r in q("SELECT entity_type, entity_id, language_id, text FROM translation WHERE field='name' AND game_id IS NULL AND version_id IS NULL"):
        if okv("translation", rk(r["entity_type"], r["entity_id"], "name", r["language_id"], None, None), "text"):
            names[(r["entity_type"], r["entity_id"])][r["language_id"]] = r["text"]
    aliases = collections.defaultdict(dict)
    for r in q("SELECT * FROM external_id"):
        aliases[(r["entity_type"], r["entity_id"])][r["system"]] = r["value"]
    games = [dict(r) for r in q("SELECT * FROM game ORDER BY sort_order")]
    game_order = [g["id"] for g in games]
    versions = collections.defaultdict(list)
    for r in q("SELECT * FROM version ORDER BY sort_order"):
        versions[r["game_id"]].append({"id": r["id"], "pokeapi_id": r["pokeapi_id"]})
    glang = collections.defaultdict(list)
    for r in q("SELECT * FROM game_language"):
        glang[r["game_id"]].append({"language": r["language_id"], "since": r["since_date"], "since_version": r["since_game_version"]})

    abil = collections.defaultdict(dict)
    for r in q("SELECT * FROM form_ability"):
        if okv("form_ability", rk(r["form_id"], r["game_id"])):
            abil[(r["form_id"], r["game_id"])][r["slot"]] = r["ability_id"]
    fgame = collections.defaultdict(dict)
    for r in q("SELECT * FROM form_game"):
        key = rk(r["form_id"], r["game_id"])
        if not (okv("form_game", key, "types") and okv("form_game", key, "stats")):
            continue
        e = {"types": [t for t in (r["type1_id"], r["type2_id"]) if t],
             "stats": {"hp": r["hp"], "atk": r["atk"], "def": r["def"], "spa": r["spa"], "spd": r["spd"], "spe": r["spe"]},
             "height_dm": r["height_dm"], "weight_hg": r["weight_hg"], "base_exp": r["base_exp"], "catch_rate": r["catch_rate"],
             "base_friendship": r["base_friendship"]}
        if r["ev_hp"] is not None:
            e["ev_yield"] = {"hp": r["ev_hp"], "atk": r["ev_atk"], "def": r["ev_def"], "spa": r["ev_spa"], "spd": r["ev_spd"], "spe": r["ev_spe"]}
        if (r["form_id"], r["game_id"]) in abil:
            e["abilities"] = abil[(r["form_id"], r["game_id"])]
        if r["extra"]:
            e["note"] = json.loads(r["extra"])
        fgame[r["form_id"]][r["game_id"]] = {k: v for k, v in e.items() if v is not None}

    disc = collections.defaultdict(list)
    for r in q("SELECT * FROM discrepancy"):
        disc[r["row_key"]].append({"table": r["table_name"], "column": r["column_name"], "chosen": json.loads(r["chosen_value"]) if r["chosen_value"] else None,
                                   "rule": r["rule"], "others": [{"source": a["source"], "value": a["value"]} for a in json.loads(r["alternatives"])]})

    forms_by_sp = collections.defaultdict(list)
    form_objs = {}
    for r in q("SELECT * FROM form ORDER BY species_id, sort_order, id"):
        if not okv("form", rk(r["id"])):
            continue
        gd = dict(sorted(fgame.get(r["id"], {}).items(), key=lambda kv: game_order.index(kv[0])))
        fdisc = [d for k, v in disc.items() if k.startswith(f'["{r["id"]}",') or k == rk(r["id"]) for d in v]
        o = {"id": r["id"], "species": r["species_id"], "slug": r["slug"], "category": r["category"], "is_default": bool(r["is_default"]),
             "is_battle_only": bool(r["is_battle_only"]), "base_form": r["base_form_id"], "introduced_in": r["introduced_game_id"],
             "aliases": {k: v for k, v in aliases[("form", r["id"])].items()}, "games": gd,
             "verification": status("form", rk(r["id"]))}
        if fdisc:
            o["discrepancies"] = fdisc
        form_objs[r["id"]] = o
        forms_by_sp[r["species_id"]].append(o)

    eggs = collections.defaultdict(list)
    for r in q("SELECT * FROM species_egg_group"):
        eggs[r["species_id"]].append(r["egg_group_id"])
    index = []
    search = collections.defaultdict(list)
    flags = ["is_baby", "is_legendary", "is_mythical", "is_ultra_beast", "is_paradox", "has_gender_differences"]
    for s in q("SELECT * FROM species ORDER BY id"):
        sid = s["id"]
        key = rk(sid)
        nm = names[("species", str(sid))]
        fl = {f: (bool(s[f]) if okv("species", key, f) else None) for f in flags}
        forms = forms_by_sp[sid]
        default = next((f for f in forms if f["is_default"]), None)
        latest = None
        if default and default["games"]:
            lg = list(default["games"])[-1]
            latest = {"game": lg, "types": default["games"][lg]["types"]}
        obj = {"id": sid, "slug": s["slug"], "generation": s["generation_id"], "names": nm,
               "growth_rate": s["growth_rate_id"] if okv("species", key, "growth_rate_id") else None,
               "gender_rate": s["gender_rate"] if okv("species", key, "gender_rate") else None,
               "hatch_cycles": s["hatch_cycles"] if okv("species", key, "hatch_cycles") else None,
               "egg_groups": sorted(eggs[sid]), **fl, "forms": forms,
               "aliases": aliases[("species", str(sid))]}
        sdisc = disc.get(key)
        if sdisc:
            obj["discrepancies"] = sdisc
        write(f"pokemon/{sid}.json", obj)
        index.append({"id": sid, "slug": s["slug"], "generation": s["generation_id"], "names": nm,
                      "forms": [f["id"] for f in forms], "latest": latest})
        for l, n in nm.items():
            search[l].append([fold(n), n, sid])
    write("pokemon/index.json", index)
    for fid, o in form_objs.items():
        write(f"form/{fid}.json", o)
    for l, lst in search.items():
        write(f"search/{l}.json", sorted(lst))

    # abilities
    holders = collections.defaultdict(lambda: collections.defaultdict(list))
    for (fid, gid), slots in abil.items():
        for slot, a in slots.items():
            holders[a][gid].append([fid, slot])
    alist = []
    for a in q("SELECT * FROM ability ORDER BY id"):
        if not okv("ability", rk(a["id"])):
            continue
        nm = names[("ability", str(a["id"]))]
        h = {g: sorted(v) for g, v in sorted(holders[a["id"]].items(), key=lambda kv: game_order.index(kv[0]))}
        write(f"ability/{a['id']}.json", {"id": a["id"], "slug": a["slug"], "generation": a["generation_id"], "names": nm,
                                          "aliases": aliases[("ability", str(a["id"]))], "holders": h})
        alist.append({"id": a["id"], "slug": a["slug"], "names": nm})
    write("ability/index.json", alist)

    write("type/index.json", [{"id": t["id"], "generation": t["generation_id"], "names": names[("type", t["id"])]}
                              for t in q("SELECT * FROM type ORDER BY pokeapi_id")])
    glist = []
    present = collections.defaultdict(list)
    for fid, o in form_objs.items():
        for g in o["games"]:
            present[g].append(fid)
    for g in games:
        o = {**{k: g[k] for k in ("id", "kind", "generation_id", "base_game_id", "release_date", "platform", "pokeapi_version_group", "note")},
             "versions": versions[g["id"]], "languages": sorted(glang[g["id"]], key=lambda x: LANGS.index(x["language"]) if x["language"] in LANGS else 99),
             "forms_in_data": len(present[g["id"]])}
        glist.append(o)
        write(f"game/{g['id']}.json", {**o, "forms": sorted(present[g["id"]], key=lambda f: (int(f.split('-')[0]), f))})
    write("game/index.json", glist)

    write("meta/languages.json", [dict(r) for r in q("SELECT * FROM language ORDER BY sort_order")])
    srcs = [dict(r) for r in q("SELECT * FROM source ORDER BY tier, id")]
    docs = [dict(r) for r in q("SELECT * FROM source_document ORDER BY id")]
    write("meta/sources.json", {"sources": srcs, "documents": docs})
    log = [dict(r) for r in q("SELECT * FROM update_log ORDER BY id DESC")]
    for e in log:
        e["stats"] = json.loads(e["stats"]) if e["stats"] else None
    write("meta/changelog.json", log)
    summ = collections.defaultdict(dict)
    for r in q("SELECT table_name, status, n FROM v_verification_summary"):
        summ[r["table_name"]][r["status"]] = r["n"]
    write("meta/verification.json", {"by_table": summ, "discrepancies": db.execute("SELECT COUNT(*) FROM discrepancy").fetchone()[0],
                                     "statuses": {"game-data": "confirmé par extraction des jeux", "unanimous": "toutes les sources concordent",
                                                  "majority": "au moins 2 sources concordantes dont une de rang 1–2",
                                                  "single-source": "une seule source existe", "manual": "référentiel saisi et sourcé à la main"}})
    dv = meta["data_version"]
    asset = f"pokedata-{dv}.sqlite.gz"
    dl = {"data_version": dv, "url": f"https://github.com/{REPO}/releases/download/data-{dv}/{asset}",
          "release": f"https://github.com/{REPO}/releases/tag/data-{dv}"}
    write("download.json", dl)
    counts = {"species": len(index), "forms": len(form_objs), "abilities": len(alist), "games": len(glist),
              "translations": db.execute("SELECT COUNT(*) FROM translation").fetchone()[0]}
    write("index.json", {"api_version": "v1", "schema_version": meta["schema_version"], "data_version": dv,
                         "generated_at": meta["generated_at"], "license": {"code": "MIT", "notice": meta["license_notice"]},
                         "counts": counts, "download": dl,
                         "endpoints": {k: f"{PAGES}/api/v1/{v}" for k, v in {
                             "pokemon_index": "pokemon/index.json", "pokemon": "pokemon/{id}.json", "form": "form/{form_id}.json",
                             "ability_index": "ability/index.json", "ability": "ability/{id}.json", "types": "type/index.json",
                             "game_index": "game/index.json", "game": "game/{game_id}.json", "search": "search/{lang}.json",
                             "sources": "meta/sources.json", "changelog": "meta/changelog.json", "verification": "meta/verification.json",
                             "languages": "meta/languages.json", "download": "download.json"}.items()}})
    if (ROOT / "docs").exists():
        for p in (ROOT / "docs").iterdir():
            if p.is_file():
                shutil.copy(p, SITE / p.name)
    n = sum(1 for _ in API.rglob("*.json"))
    print(f"{API}: {n} files, {sum(p.stat().st_size for p in API.rglob('*.json')) // 1024} KiB")


if __name__ == "__main__":
    main()
