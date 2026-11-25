"""Compare pokedata phase 1b (evolutions, regional Pokédex, categories) with the current Pokédex data.

Usage: python3 scripts/compare_phase1b.py <path to pokedex/docs/data> > reports/compare-evolutions-dex.md
Read-only on the Pokédex side.
"""
import collections, json, os, re, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD

PX = sys.argv[1] if len(sys.argv) > 1 else "/workspace/pokedex/docs/data"
db = sqlite3.connect(BUILD / "pokedata.sqlite"); db.row_factory = sqlite3.Row
q = lambda sql, *a: db.execute(sql, a).fetchall()
OK = ("game-data", "unanimous", "majority", "manual", "single-source")
ver = {(r[0], r[1]): r[2] for r in q("SELECT table_name, row_key, status FROM verification WHERE column_name IN ('*','number','text')")}
rk = lambda *p: json.dumps(list(p), ensure_ascii=False, separators=(",", ":"))
L = []
p = L.append

p("# Comparaison pokedata ↔ Pokédex — phase 1b (évolutions, Pokédex régionaux, catégories)\n")
p("Lecture seule des fichiers du Pokédex (`docs/data/evo.json`, `dex/*.json`, `sp/*.json`). "
  "Les écarts listés ici sont des constats, pas des corrections appliquées d'un côté ou de l'autre.\n")

# ---------------------------------------------------------------- evolutions
evo = json.load(open(os.path.join(PX, "evo.json"), encoding="utf-8"))
px_pairs = {(a, b): v for a, b, v, *_ in evo}
ours = {}
for r in q("SELECT e.id, e.from_form_id, e.to_form_id FROM evolution e"):
    if ver.get(("evolution", rk(r["id"]))) in OK:
        ours[(r["from_form_id"], r["to_form_id"])] = r["id"]
latest = {}
for r in q("""SELECT m.*, g.sort_order FROM evolution_method m JOIN game g ON g.id=m.game_id ORDER BY g.sort_order"""):
    latest[r["evolution_id"]] = r   # last game wins
only_px = sorted(set(px_pairs) - set(ours), key=lambda x: (int(x[0].split("-")[0]), x))
only_us = sorted(set(ours) - set(px_pairs), key=lambda x: (int(x[0].split("-")[0]), x))
p("## Évolutions\n")
p(f"- Paires (forme → forme) : pokedata **{len(ours)}**, Pokédex **{len(px_pairs)}**, communes **{len(set(ours) & set(px_pairs))}**.")
p(f"- Seulement dans le Pokédex : **{len(only_px)}** ; seulement dans pokedata : **{len(only_us)}**.\n")
def show(lst, n=60):
    return ", ".join(f"`{a}→{b}`" for a, b in lst[:n]) + (" …" if len(lst) > n else "")
if only_px:
    p("Seulement dans le Pokédex (souvent : évolution propre à GO/HOME, ou forme regroupée autrement) :\n")
    p(show(only_px) + "\n")
if only_us:
    p("Seulement dans pokedata (évolutions lues dans les tables des jeux, par forme) :\n")
    p(show(only_us) + "\n")
# level of the most recent method
lvl_diff = []
for pair, eid in ours.items():
    if pair not in px_pairs: continue
    v = [x for x in px_pairs[pair] if x.get("df")] or px_pairs[pair]
    m = re.search(r"Niv\. (\d+)", " ".join(v[-1].get("x", [])))
    r = latest.get(eid)
    if m and r is not None and r["min_level"] and int(m.group(1)) != r["min_level"]:
        lvl_diff.append((pair, int(m.group(1)), r["min_level"], r["game_id"]))
p(f"- Niveau d'évolution (méthode la plus récente) différent : **{len(lvl_diff)}**.\n")
if lvl_diff:
    p("| Évolution | Pokédex | pokedata | jeu pokedata |\n|---|---|---|---|")
    for (a, b), x, y, g in sorted(lvl_diff, key=lambda t: int(t[0][0].split("-")[0]))[:80]:
        p(f"| {a}→{b} | Niv. {x} | Niv. {y} | {g} |")
    p("")
trig = collections.Counter(r["trigger"] for r in q("SELECT trigger FROM evolution_method"))
p("Répartition des déclencheurs dans pokedata (toutes lignes jeu × variante) : " + ", ".join(f"{k} {v}" for k, v in trig.most_common()) + ".\n")

# ---------------------------------------------------------------- regional dex
p("## Pokédex régionaux\n")
dexes = collections.defaultdict(list)
for d in q("SELECT * FROM pokedex ORDER BY sort_order"):
    dexes[d["game_id"]].append(d["id"])
entries = collections.defaultdict(dict)
for r in q("SELECT * FROM pokedex_entry"):
    if ver.get(("pokedex_entry", rk(r["pokedex_id"], r["species_id"]))) in OK:
        entries[r["pokedex_id"]][r["species_id"]] = r["number"]
ISLANDS = {"sm": ["sm-alola"], "usum": ["usum-alola"]}
p("| Jeu | Pokédex (Pokédex) | Pokédex (pokedata) | Entrées Pokédex | Entrées pokedata | Numéros différents | Absents d'un côté |\n|---|---|---|---|---|---|---|")
details = []
for f in sorted(os.listdir(os.path.join(PX, "dex"))):
    g = f[:-5]
    d = json.load(open(os.path.join(PX, "dex", f), encoding="utf-8"))
    if not d["e"]:
        continue
    mine = ISLANDS.get(g, dexes.get(g, []))
    for i, name in enumerate(d["dx"]):
        px = {sp: n for sp, di, n in d["e"] if di == i}
        did = mine[i] if i < len(mine) else None
        us = entries.get(did, {}) if did else {}
        diff = sorted(sp for sp in set(px) & set(us) if px[sp] != us[sp])
        miss = sorted(set(px) ^ set(us))
        p(f"| {g} | {name} | {did or '—'} | {len(px)} | {len(us)} | {len(diff)} | {len(miss)} |")
        if (diff or miss) and did:
            details.append((g, name, did, [(sp, px[sp], us[sp]) for sp in diff], [(sp, px.get(sp), us.get(sp)) for sp in miss]))
p("")
for g, name, did, diff, miss in details:
    p(f"### {g} — {name} (`{did}`)\n")
    if diff:
        p("Numéros différents (espèce : Pokédex / pokedata) : " + ", ".join(f"{sp} : {a}/{b}" for sp, a, b in diff[:60]) + (" …" if len(diff) > 60 else "") + "\n")
    if miss:
        p("Présents d'un seul côté (espèce : Pokédex / pokedata) : " + ", ".join(f"{sp} : {a if a is not None else '—'}/{b if b is not None else '—'}" for sp, a, b in miss[:60]) + (" …" if len(miss) > 60 else "") + "\n")
p("Pokédex absents du Pokédex actuel mais publiés par pokedata : " + ", ".join(f"`{x}`" for g, l in dexes.items() for x in l
  if g not in [f[:-5] for f in os.listdir(os.path.join(PX, 'dex'))] or x not in ISLANDS.get(g, dexes[g])[:len(json.load(open(os.path.join(PX, 'dex', g + '.json'), encoding='utf-8'))['dx'])] ) + ".\n")

# ---------------------------------------------------------------- genus
p("## Catégories (français)\n")
gen_fr = {int(r["entity_id"]): r["text"] for r in q("SELECT entity_id, text FROM translation WHERE entity_type='species' AND field='genus' AND language_id='fr'")}
diffs, missing = [], []
for sid in range(1, 1026):
    path = os.path.join(PX, "sp", f"{sid}.json")
    if not os.path.exists(path): continue
    gn = json.load(open(path, encoding="utf-8")).get("gn")
    if not gn: continue
    if sid not in gen_fr: missing.append(sid); continue
    if gn.strip() != gen_fr[sid].strip(): diffs.append((sid, gn, gen_fr[sid]))
p(f"- Espèces avec catégorie française : pokedata **{len(gen_fr)}** ; identiques au Pokédex : **{len(gen_fr) - len(diffs) - 0}** sur les espèces communes ; différentes : **{len(diffs)}** ; absentes de pokedata : **{len(missing)}**.\n")
if diffs:
    p("| Espèce | Pokédex | pokedata |\n|---|---|---|")
    for sid, a, b in diffs[:150]:
        p(f"| {sid} | {a} | {b} |")
    if len(diffs) > 150: p(f"| … | {len(diffs) - 150} de plus | |")
    p("")
if missing:
    p("Absentes de pokedata (catégorie non vérifiée ou en écart entre sources) : " + ", ".join(map(str, missing[:100])) + "\n")
print("\n".join(L))
