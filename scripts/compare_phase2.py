"""Compare pokedata phase 2 (moves, values per game, machines) with the current Pokédex data.

Usage: python3 scripts/compare_phase2.py <path to pokedex/docs/data> > reports/compare-moves.md
Read-only on the Pokédex side. Movesets (published from schema 1.1.0) are compared by scripts/compare_learnsets.py.
"""
import collections, csv, json, os, re, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, ROOT

PX = sys.argv[1] if len(sys.argv) > 1 else "/workspace/pokedex/docs/data"
db = sqlite3.connect(BUILD / "pokedata.sqlite"); db.row_factory = sqlite3.Row
q = lambda sql, *a: db.execute(sql, a).fetchall()
L = []; p = L.append
p("# Comparaison pokedata ↔ Pokédex — phase 2 (capacités, CT, movesets)\n")
p("Lecture seule des fichiers du Pokédex (`moves.json`, `tm.json`, `learn-index.json`). Constats, sans correction appliquée.\n")

# ---------------------------------------------------------------- moves
pm = json.load(open(os.path.join(PX, "moves.json"), encoding="utf-8"))
names_fr = {int(r["entity_id"]): r["text"] for r in q("SELECT entity_id, text FROM translation WHERE entity_type='move' AND field='name' AND language_id='fr'")}
moves = {r["id"]: r for r in q("SELECT * FROM move")}
p("## Capacités\n")
p(f"- Capacités : pokedata **{len(moves)}**, Pokédex **{len(pm)}** ; seulement dans pokedata : {len(set(moves) - set(map(int, pm)))} "
  f"(surtout capacités Z et Dynamax), seulement dans le Pokédex : {len(set(map(int, pm)) - set(moves))}.")
nd = [(int(i), v[0], names_fr.get(int(i))) for i, v in pm.items() if int(i) in names_fr and v[0].replace("’", "'") != names_fr[int(i)].replace("’", "'")]
p(f"- Noms français différents : **{len(nd)}**" + (" — " + ", ".join(f"{i} : « {a} » / « {b} »" for i, a, b in nd[:40]) if nd else "") + "\n")
CAT = {"p": "physical", "s": "special", "n": "status", "t": "status"}
latest = {}
for r in q("SELECT mg.*, g.sort_order FROM move_game mg JOIN game g ON g.id=mg.game_id WHERE mg.game_id='sv'"):
    latest[r["move_id"]] = r
vd = []
for i, v in pm.items():
    r = latest.get(int(i))
    if not r: continue
    mine = [r["type_id"], r["damage_class"], r["power"], r["accuracy"], r["pp"]]
    theirs = [v[1], CAT.get(v[2], v[2]), v[3] or None, v[4] or None, v[5]]
    if mine != theirs: vd.append((int(i), theirs, mine))
p(f"- Valeurs actuelles (type, catégorie, puissance, précision, PP) comparées à Écarlate/Violet dans pokedata : "
  f"{len(latest)} capacités comparables, **{len(vd)}** différentes.\n")
if vd:
    p("| Capacité | Pokédex | pokedata (sv) |\n|---|---|---|")
    for i, a, b in sorted(vd)[:120]:
        p(f"| {i} {names_fr.get(i, '')} | {a} | {b} |")
    p("")
cnt = collections.Counter(r["game_id"] for r in q("SELECT game_id FROM move_game"))
p("Lignes capacité × jeu publiées : " + ", ".join(f"{g} {n}" for g, n in sorted(cnt.items(), key=lambda kv: [r['sort_order'] for r in q('SELECT sort_order FROM game WHERE id=?', kv[0])][0])) + ".\n")

# ---------------------------------------------------------------- machines
p("## CT / CS / DT\n")
tm = json.load(open(os.path.join(PX, "tm.json"), encoding="utf-8"))
mine = collections.defaultdict(dict)
for r in q("SELECT * FROM machine"):
    mine[r["game_id"]][r["move_id"]] = r["label"]
def norm_label(x):
    m = re.match(r"(CT|CS|DT|TM|HM|TR)(\d+)", x)
    if not m: return x
    k = {"CT": "TM", "CS": "HM", "DT": "TR"}.get(m.group(1), m.group(1))
    return f"{k}{int(m.group(2))}"
p("| Jeu | Pokédex | pokedata | Identiques | Différentes | Seulement Pokédex | Seulement pokedata |\n|---|---|---|---|---|---|---|")
mdet = []
for g, t in tm.items():
    if g not in mine: 
        p(f"| {g} | {len(t)} | — | | | | |"); continue
    a = {int(k): norm_label(v) for k, v in t.items()}
    b = {k: norm_label(v) for k, v in mine[g].items()}
    same = sum(1 for k in set(a) & set(b) if a[k] == b[k])
    diff = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    p(f"| {g} | {len(a)} | {len(b)} | {same} | {len(diff)} | {len(set(a) - set(b))} | {len(set(b) - set(a))} |")
    if diff or set(a) ^ set(b):
        mdet.append((g, [(k, a[k], b[k]) for k in diff], sorted(set(a) - set(b)), sorted(set(b) - set(a))))
p("")
for g, diff, oa, ob in mdet:
    p(f"- **{g}** : " + "; ".join(x for x in [
        ("différentes (capacité : Pokédex / pokedata) " + ", ".join(f"{k} {a}/{b}" for k, a, b in diff[:20])) if diff else "",
        ("seulement Pokédex " + ", ".join(map(str, oa[:20]))) if oa else "",
        ("seulement pokedata " + ", ".join(map(str, ob[:20]))) if ob else ""] if x))
p("")

# ---------------------------------------------------------------- learnsets: see compare_learnsets.py
p("## Movesets\n")
p("Publiés à partir des données 2026.11.26 (schéma 1.1.0) : comparaison dans `reports/compare-learnsets.md`.\n")
print("\n".join(L))
