"""Compare pokedata (species, forms, names, types, stats, abilities) with the current Pokédex data.

Usage: python3 scripts/compare_pokedex.py <path to pokedex/docs/data> > reports/compare-species-forms.md
Read-only on the Pokédex side.
"""
import collections, json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD

PX = sys.argv[1] if len(sys.argv) > 1 else "/workspace/pokedex/docs/data"
db = sqlite3.connect(BUILD / "pokedata.sqlite"); db.row_factory = sqlite3.Row
core = json.load(open(os.path.join(PX, "core.json"), encoding="utf-8"))
order = [r["id"] for r in db.execute("SELECT id FROM game ORDER BY sort_order")]
MAIN_LATEST = ["svdisk", "sv", "za", "zadlc", "swcrown", "sw", "bdsp", "la", "usum", "lgpe"]

forms = {r["id"]: dict(r) for r in db.execute("SELECT * FROM form")}
fg = collections.defaultdict(dict)
for r in db.execute("SELECT * FROM form_game"):
    fg[r["form_id"]][r["game_id"]] = dict(r)
fa = collections.defaultdict(lambda: collections.defaultdict(dict))
for r in db.execute("SELECT * FROM form_ability"):
    fa[r["form_id"]][r["game_id"]][r["slot"]] = r["ability_id"]
names = collections.defaultdict(dict)
for r in db.execute("SELECT entity_id, language_id, text FROM translation WHERE entity_type='species' AND field='name'"):
    names[int(r["entity_id"])][r["language_id"]] = r["text"]

px_keys = {e["k"]: e for e in core["e"]}
mg = core["mg"]
res = collections.OrderedDict()
def add(cat, item):
    res.setdefault(cat, []).append(item)

for k in sorted(set(px_keys) | set(mg), key=lambda k: (int(k.split("-")[0]), k)):
    if k not in forms:
        add("Formes du Pokédex absentes de pokedata", k)
for k in sorted(forms, key=lambda k: (int(k.split("-")[0]), k)):
    if k not in px_keys and k not in mg:
        add("Formes de pokedata absentes du Pokédex", f"{k} ({forms[k]['category']})")

def latest_row(k):
    for g in ["svdisk", "zadlc", "swcrown", "bdsp", "la", "usum", "lgpe", "oras", "b2w2", "hgss", "e", "c", "y"]:
        if g in fg[k]:
            return g, fg[k][g]
    return None, None

n_cmp = collections.Counter()
for k, e in px_keys.items():
    if k not in forms:
        continue
    sid = e["id"]
    if "-" not in k:
        for lang, fld in (("fr", "n"), ("en", "en"), ("ja", "ja"), ("ja-Latn", "ro")):
            if fld in e:
                n_cmp["names"] += 1
                if e[fld] != names[sid].get(lang):
                    add(f"Noms différents ({lang})", f"#{sid} Pokédex « {e[fld]} » ↔ pokedata « {names[sid].get(lang)} »")
    g, row = latest_row(k)
    if not row:
        add("Formes sans données de jeu dans pokedata (GO, HOME, Champions ou formes sans entrée propre)", k)
        continue
    n_cmp["types"] += 1
    t = [x for x in (row["type1_id"], row["type2_id"]) if x]
    if t != e.get("t"):
        add("Types différents (dernier jeu)", f"{k} [{g}] Pokédex {e.get('t')} ↔ pokedata {t}")
    n_cmp["stats"] += 1
    s = [row["hp"], row["atk"], row["def"], row["spa"], row["spd"], row["spe"]]
    if s != e.get("s"):
        add("Stats différentes (dernier jeu)", f"{k} [{g}] Pokédex {e.get('s')} ↔ pokedata {s}")

# per-species files: abilities and game presence
spdir = os.path.join(PX, "sp")
for fn in sorted(os.listdir(spdir), key=lambda x: int(x.split(".")[0])):
    sp = json.load(open(os.path.join(spdir, fn), encoding="utf-8"))
    for k, f in (sp.get("f") or {}).items():
        if k not in forms:
            continue
        g, row = latest_row(k)
        if g and g in fa[k] and f.get("a"):
            n_cmp["abilities"] += 1
            mine = sorted(fa[k][g].values())
            theirs = sorted(a for a, h in f["a"])
            if mine != theirs:
                add("Talents différents (dernier jeu)", f"{k} [{g}] Pokédex {theirs} ↔ pokedata {mine}")
        if f.get("av"):
            n_cmp["presence"] += 1
            have = set(fg[k])
            av = set(f["av"])
            missing = sorted(av - have, key=order.index) if av - have else []
            if missing:
                add("Jeux listés par le Pokédex sans données de cette forme dans pokedata", f"{k}: {', '.join(missing)}")

print("# Comparaison pokedata ↔ Pokédex : espèces, formes, noms, types, stats, talents\n")
print(f"Pokédex : `{PX}` · pokedata : `build/pokedata.sqlite`\n")
print("| Comparaisons | Nombre |\n|---|---|")
for k, v in n_cmp.items():
    print(f"| {k} | {v} |")
print("\n| Écart | Nombre |\n|---|---|")
for k, v in res.items():
    print(f"| {k} | {len(v)} |")
for k, v in res.items():
    print(f"\n## {k} ({len(v)})\n")
    for x in v[:400]:
        print(f"- {x}")
    if len(v) > 400:
        print(f"- … {len(v) - 400} de plus")
