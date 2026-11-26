"""Compare the published movesets (table learnset, schema 1.1.0) with the current Pokédex data (learn-index.json).

Usage: python3 scripts/compare_learnsets.py <path to pokedex/docs/data> > reports/compare-learnsets.md
Read-only on the Pokédex side.
"""
import collections, json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD

PX = sys.argv[1] if len(sys.argv) > 1 else "/workspace/pokedex/docs/data"
db = sqlite3.connect(BUILD / "pokedata.sqlite")
q = lambda sql, *a: db.execute(sql, a).fetchall()
L = []; p = L.append
BIT = {"level-up": 1, "reminder": 1, "mastery": 1, "plus": 1, "machine": 2, "egg": 4, "tutor": 8}
BITNAME = {1: "niveau", 2: "CT", 4: "œuf", 8: "tuteur", 16: "autre (changement de forme…)"}
def bits(b): return " + ".join(n for k, n in BITNAME.items() if b & k) or "—"

li = json.load(open(os.path.join(PX, "learn-index.json"), encoding="utf-8"))
G, K = li["g"], li["k"]
theirs = collections.defaultdict(lambda: collections.defaultdict(int))
for mv, arr in li["L"].items():
    i = 0
    while i < len(arr):
        f, n = arr[i], arr[i + 1]
        for c in arr[i + 2:i + 2 + n]:
            theirs[G[c >> 5]][(K[f], int(mv))] |= c & 31
        i += 2 + n
# DLC: the Pokédex files them under their own game ids, pokedata under the base game (the game data include the DLC)
DLC = {"swisle": "sw", "swcrown": "sw", "svmask": "sv", "svdisk": "sv", "zadlc": "za"}
merged = collections.defaultdict(lambda: collections.defaultdict(int))
for g, d in theirs.items():
    for k, b in d.items():
        merged[DLC.get(g, g)][k] |= b
sw_alone = theirs["sw"]
theirs = merged
ours = collections.defaultdict(lambda: collections.defaultdict(int))
for f, g, mv, m in q("SELECT form_id, game_id, move_id, method_id FROM learnset"):
    ours[g][(f, mv)] |= BIT.get(m, 16)
forms = {r[0] for r in q("SELECT id FROM form")}
present = collections.defaultdict(set)
for f, g in q("SELECT form_id, game_id FROM form_game"):
    present[g].add(f)
games = [r[0] for r in q("SELECT id FROM game ORDER BY sort_order") if r[0] not in DLC]
has_ls = collections.defaultdict(set)
for f, g in q("SELECT DISTINCT form_id, game_id FROM learnset"):
    has_ls[g].add(f)
nrows = q("SELECT COUNT(*) FROM learnset")[0][0]
nsets = q("SELECT COUNT(*) FROM verification WHERE table_name='learnset'")[0][0]
ndisc = q("SELECT COUNT(*) FROM discrepancy WHERE table_name='learnset'")[0][0]

p("# Comparaison pokedata ↔ Pokédex — movesets\n")
p("Lecture seule de `learn-index.json` du Pokédex. Constats, sans correction appliquée.\n")
p(f"pokedata : **{nrows}** lignes `learnset` publiées, **{nsets}** ensembles forme × jeu × méthode vérifiés (statut `game-data`, "
  f"contrôlés avec PokeAPI et, pour les jeux où ses données sont propres au jeu, Showdown) ; **{ndisc}** ensembles où une source de contrôle diffère "
  "(détail dans `discrepancy`, champs `missing` / `extra`).\n")
p("Comparaison sur les couples (forme, capacité) par jeu. Le Pokédex ne couvre qu'une partie des formes dans les anciens jeux : "
  "les couples « seulement pokedata » sont séparés entre formes que le Pokédex couvre dans ce jeu et formes qu'il ne couvre pas. "
  "Les couples « seulement Pokédex » sont classés : forme absente de la table `form` de pokedata ; forme sans ligne `form_game` "
  "dans ce jeu (absente du jeu d'après ses données) ; forme du jeu sans moveset propre dans les données du jeu (variantes cosmétiques "
  "comme les bonbons de Charmilly, formes de combat, Méga-Évolutions : le moveset est celui de l'entrée du jeu, rangé sur la forme "
  "correspondante) ; autres. Les extensions (Isolarmure, Couronneige, Masque Turquoise, Disque Indigo, Méga-Dimension) sont "
  "fusionnées avec leur jeu, comme dans pokedata.\n")
p("| Jeu | Couples Pokédex | Couples pokedata | Communs | Méthode identique | Seulement pokedata (formes couvertes / non couvertes par le Pokédex) | Seulement Pokédex : hors table / hors jeu / sans moveset propre / autres |")
p("|---|---|---|---|---|---|---|")
rest_by_game = {}
for g in games:
    o, t = ours.get(g, {}), theirs.get(g, {})
    if not o and not t:
        continue
    if not t:
        p(f"| {g} | — | {len(o)} | | | | |"); continue
    common = set(o) & set(t)
    same = sum(1 for k in common if (o[k] & 15) == (t[k] & 15))
    tf = {k[0] for k in t}
    only_o = [k for k in o if k not in t]
    only_t = [k for k in t if k not in o]
    a = [k for k in only_t if k[0] not in forms]
    b = [k for k in only_t if k[0] in forms and k[0] not in present[g]]
    nl = [k for k in only_t if k[0] in forms and k[0] in present[g] and k[0] not in has_ls[g]]
    c = [k for k in only_t if k[0] in forms and k[0] in present[g] and k[0] in has_ls[g]]
    rest_by_game[g] = c
    p(f"| {g} | {len(t)} | {len(o)} | {len(common)} | {same} ({100 * same // max(1, len(common))} %) | "
      f"{sum(1 for k in only_o if k[0] in tf)} / {sum(1 for k in only_o if k[0] not in tf)} | {len(a)} / {len(b)} / {len(nl)} / {len(c)} |")

p("\n## Écart d'Épée/Bouclier (sw)\n")
p("Rapport de la phase 2 (movesets calculés, non publiés) : **9 444** couples seulement dans le Pokédex pour `sw`. "
  "Cause principale : les DT (TR01–TR99) étaient lus dans les drapeaux des CT (index 100+) au lieu de leur propre table ; "
  "corrigé dans `scripts/fetch/pkhex_dumper/Learn.cs` (`GetIsLearnTR`).\n")
t, o = sw_alone, ours["sw"]
only_t = [k for k in t if k not in o]
a = sorted({k[0] for k in only_t if k[0] not in forms})
b = sorted({k[0] for k in only_t if k[0] in forms and k[0] not in present["sw"]})
nl = sorted({k[0] for k in only_t if k[0] in forms and k[0] in present["sw"] and k[0] not in has_ls["sw"]})
c = [k for k in only_t if k[0] in forms and k[0] in present["sw"] and k[0] in has_ls["sw"]]
p(f"Même calcul (fichier `sw` du Pokédex seul, sans les extensions) après correction : **{len(only_t)}** couples seulement dans le Pokédex "
  f"(**{len(c)}** une fois écartées les formes sans moveset propre), tous expliqués :\n")
if a:
    p(f"- {sum(1 for k in only_t if k[0] in a)} couples sur {len(a)} formes absentes de la table `form` de pokedata : " + ", ".join(a[:6]) + ";")
p(f"- {sum(1 for k in only_t if k[0] in b)} couples sur des formes absentes d'Épée/Bouclier selon les données du jeu : " + ", ".join(b) + ";")
p(f"- {sum(1 for k in only_t if k[0] in nl)} couples sur {len(nl)} formes sans moveset propre dans les données du jeu "
  f"({len([f for f in nl if f.startswith('869-')])} variantes crème × bonbon de Charmilly, dont le moveset est celui de la forme « bonbon fraise » de la même crème"
  + (", " + ", ".join(f for f in nl if not f.startswith('869-')) if any(not f.startswith('869-') for f in nl) else "") + ");")
grp = collections.defaultdict(list)
for f, mv in sorted(c):
    grp[t[(f, mv)]].append(f"{f}:{mv}")
for bt, lst in sorted(grp.items()):
    p(f"- {len(lst)} couples « {bits(bt)} » côté Pokédex : " + ", ".join(lst[:24]) + ("…" if len(lst) > 24 else "") + ";")
p("")
p("Lecture des « autres » : capacités des formes de Motisma (479-*) apprises au changement de forme (méthode « autre » dans le Pokédex, "
  "pas un moveset des jeux) ; Aire d'Eau (518) et Aire de Feu (519) par tuteur pour Silvallié (773-*), quand les données du jeu (PKHeX) "
  "ne donnent qu'Aire d'Herbe (520) — PokeAPI donne les trois, écart enregistré dans `discrepancy` (18 ensembles) ; capacités d'œuf "
  "que le Pokédex attribue aux formes de combat (778-busted, 845-gulping/gorging, 875-noice, 877-hangry) : les données du jeu n'en "
  "donnent qu'à la forme de base.\n")
p("Autres constats : en Écarlate/Violet et Soleil/Lune/Ultra-Soleil/Ultra-Lune, le Pokédex reporte les capacités d'œuf sur les "
  "évolutions et les Méga-Évolutions (les données du jeu et PokeAPI ne les donnent qu'au premier stade) ; les formes de type de "
  "Silvallié (773-*) n'ont pas de ligne `form_game` dans Soleil/Lune et Ultra-Soleil/Ultra-Lune (phase 1), d'où les couples « hors jeu ».\n")

p("## Écarts restants par jeu (« seulement Pokédex », formes présentes dans le jeu)\n")
for g, c in rest_by_game.items():
    if not c:
        continue
    t = theirs[g]
    cnt = collections.Counter(t[k] for k in c)
    p(f"- **{g}** ({len(c)}) : " + ", ".join(f"{bits(b)} {n}" for b, n in cnt.most_common()) + " — ex. "
      + ", ".join(f"{f}:{mv}" for f, mv in sorted(c)[:12]))
p("")
p("## Écarts entre sources de contrôle (pokedata)\n")
p("Ensembles où PokeAPI ou Showdown diffère des données des jeux, par jeu et méthode (source : ensembles concernés).\n")
cnt = collections.Counter()
for rk, alt in q("SELECT row_key, alternatives FROM discrepancy WHERE table_name='learnset'"):
    f, g, m = json.loads(rk)
    for a in json.loads(alt):
        cnt[(g, m, a["source"])] += 1
p("| Jeu | Méthode | Source | Ensembles |\n|---|---|---|---|")
for (g, m, s), n in sorted(cnt.items(), key=lambda kv: (games.index(kv[0][0]), kv[0][1], kv[0][2])):
    p(f"| {g} | {m} | {s} | {n} |")
p("")
print("\n".join(L))
