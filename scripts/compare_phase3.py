"""Compare pokedata phase 3 (places, encounters, availability, shiny rules) with the current Pokédex data.

Usage: python3 scripts/compare_phase3.py [<path to pokedex/docs/data>] [games] > reports/compare-locations.md
Read-only on the Pokédex side; findings only, nothing is corrected.
"""
import collections, json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, ROOT

PX = sys.argv[1] if len(sys.argv) > 1 else "/workspace/pokedex/docs/data"
GAMES = (sys.argv[2] if len(sys.argv) > 2 else "rb,y,gs,c").split(",")
db = sqlite3.connect(BUILD / "pokedata.sqlite"); db.row_factory = sqlite3.Row
q = lambda sql, *a: db.execute(sql, a).fetchall()
J = lambda f: json.load(open(os.path.join(PX, f), encoding="utf-8"))
L = []; p = L.append
det = json.load(open(ROOT / "reports" / "phase3-details.json", encoding="utf-8"))
p(f"# Comparaison pokedata ↔ Pokédex — phase 3 (lieux, rencontres, disponibilité, chromatiques) : {', '.join(GAMES)}\n")
p("Lecture seule des fichiers du Pokédex (`sp/*.json` champs `en` et `av`, `loc.json`, `trade.json`, `shiny.json`). "
  "Constats, sans correction appliquée. Versions laissées de côté dans ce lot : " + (", ".join(det.get("skipped_versions", [])) or "aucune") + ".\n")

loc = J("loc.json")
fr = {r["entity_id"]: r["text"] for r in q("SELECT entity_id, text FROM translation WHERE entity_type='location' AND field='name' AND language_id='fr' AND game_id IS NULL")}
legacy = collections.defaultdict(set)
for r in q("SELECT entity_id, value FROM external_id WHERE entity_type='location' AND system='pokedex-legacy'"):
    for n in json.loads(r["value"]): legacy[n].add(r["entity_id"])
in_game = collections.defaultdict(set)
for r in q("SELECT location_id, game_id FROM location_game"): in_game[r["game_id"]].add(r["location_id"])
vers = collections.defaultdict(list)
for r in q("SELECT id, game_id FROM version"): vers[r["game_id"]].append(r["id"])

# pokedata: (game, form) -> location -> [min, max]
mine = collections.defaultdict(dict)
for r in q("SELECT e.form_id, v.game_id, a.location_id, MIN(e.min_level) lo, MAX(e.max_level) hi FROM encounter e "
           "JOIN version v ON v.id=e.version_id JOIN location_area a ON a.id=e.area_id GROUP BY 1, 2, 3"):
    if r["game_id"] in GAMES: mine[(r["game_id"], r["form_id"])][r["location_id"]] = (r["lo"], r["hi"])
avail = collections.defaultdict(set); avail_v = collections.defaultdict(set)
for r in q("SELECT a.form_id, v.game_id, a.version_id, a.status FROM availability a JOIN version v ON v.id=a.version_id"):
    avail[(r["game_id"], r["form_id"])].add(r["status"]); avail_v[(r["game_id"], r["version_id"], r["form_id"])].add(r["status"])

theirs = collections.defaultdict(dict); their_av = collections.defaultdict(set); unmapped = collections.Counter()
for f in sorted(os.listdir(os.path.join(PX, "sp"))):
    sp = J(os.path.join("sp", f))
    for fk, fd in sp.get("f", {}).items():
        for g in fd.get("av") or []: their_av[g].add(fk)
        for g, lst in (fd.get("en") or {}).items():
            if g not in GAMES: continue
            for e in lst:
                name = loc["a"][e[0]]
                c = legacy.get(name, set()) & in_game[g]
                if len(c) != 1: unmapped[name] += 1; continue
                l = c.pop(); lo, hi = theirs[(g, fk)].get(l, (999, 0))
                theirs[(g, fk)][l] = (min(lo, e[2]), max(hi, e[3]))

p("## Lieux\n")
p(f"- Lieux publiés pour ce lot : **{len(set().union(*(in_game[g] for g in GAMES)))}** ; noms de l’ancien Pokédex rattachés "
  f"(identifiant externe `pokedex-legacy`) : **{len(legacy)}** noms sur **{det.get('legacy_mapped')}** lieux.")
if unmapped:
    p(f"- Noms du Pokédex sans lieu correspondant dans pokedata (nombre d’occurrences) : "
      + ", ".join(f"« {n} » ({c})" for n, c in unmapped.most_common()) + ".")
    p("  Cause habituelle : lieu sans rencontre vérifiée dans ce lot (Casino, Laboratoire de Cramois’Île, Route 4 en 1ʳᵉ génération…), "
      "ou nom propre au Pokédex (« Sillonnant Johto » pour les Pokémon errants, publiés en disponibilité seulement).")
diffn = [(l, n, fr.get(l)) for n, ls in legacy.items() for l in ls if fr.get(l) and n.split(" (")[0] != fr.get(l)]
if diffn:
    p(f"- Noms du Pokédex différents du nom de jeu retenu ({len(diffn)}) : "
      + ", ".join(f"« {n} » → `{l}` « {t} »" for l, n, t in sorted(diffn)[:40]) + ".")
p("")

p("## Rencontres (Pokémon × lieu, toutes versions du jeu)\n")
p("| Jeu | Paires communes | Seulement Pokédex | Seulement pokedata | Niveaux différents |\n|---|---|---|---|---|")
ex = {}
for g in GAMES:
    a = {(f, l) for (gg, f), d in theirs.items() if gg == g for l in d}
    b = {(f, l) for (gg, f), d in mine.items() if gg == g for l in d}
    lv = [(f, l, theirs[(g, f)][l], mine[(g, f)][l]) for f, l in a & b if tuple(theirs[(g, f)][l]) != tuple(mine[(g, f)][l])]
    p(f"| {g} | {len(a & b)} | {len(a - b)} | {len(b - a)} | {len(lv)} |")
    ex[g] = (sorted(a - b), sorted(b - a), sorted(lv))
p("")
for g in GAMES:
    oa, ob, lv = ex[g]
    if not (oa or ob or lv): continue
    p(f"### {g}\n")
    if oa: p(f"- Seulement dans le Pokédex ({len(oa)}) : " + ", ".join(f"{f} @ {l}" for f, l in oa[:60]) + (" …" if len(oa) > 60 else ""))
    if ob: p(f"- Seulement dans pokedata ({len(ob)}) : " + ", ".join(f"{f} @ {l}" for f, l in ob[:60]) + (" …" if len(ob) > 60 else ""))
    if lv: p(f"- Niveaux (Pokédex → pokedata) ({len(lv)}) : " + ", ".join(f"{f} @ {l} {a[0]}–{a[1]} → {b[0]}–{b[1]}" for f, l, a, b in lv[:40]) + (" …" if len(lv) > 40 else ""))
    p("")

p("## Disponibilité par jeu\n")
p("Pokédex : liste `av` (jeux où la forme est disponible). pokedata : au moins un statut autre que `unobtainable` dans une version du jeu.\n")
p("| Jeu | Formes disponibles (Pokédex) | (pokedata) | Seulement Pokédex | Seulement pokedata |\n|---|---|---|---|---|")
avd = {}
for g in GAMES:
    a = their_av[g]
    b = {f for (gg, f), st in avail.items() if gg == g and st - {"unobtainable"}}
    p(f"| {g} | {len(a)} | {len(b)} | {len(a - b)} | {len(b - a)} |"); avd[g] = (sorted(a - b, key=lambda x: (int(x.split('-')[0]), x)), sorted(b - a, key=lambda x: (int(x.split('-')[0]), x)))
p("")
for g in GAMES:
    oa, ob = avd[g]
    if oa: p(f"- {g}, seulement Pokédex : " + ", ".join(f"{f} ({'/'.join(sorted(avail.get((g, f), {'—'})))})" for f in oa[:50]))
    if ob: p(f"- {g}, seulement pokedata : " + ", ".join(f"{f} ({'/'.join(sorted(avail[(g, f)]))})" for f in ob[:50]))
p("")
tr = J("trade.json")["g"]
p("## Exclusivités de version\n")
p("pokedata : statuts `trade-version-exclusive` (autre version ou autre jeu de la génération) ou `transfer` (Capsule Temporelle) sans autre moyen d’obtention dans au moins une version du jeu (événements exclus). "
  "Le Pokédex compte aussi les évolutions par échange (Kadabra → Alakazam…), que pokedata classe en `evolve`.\n")
for g in GAMES:
    a = {str(s) for s, _ in tr.get(g, [])}
    b = {f.split("-")[0] for (gg, v, f), st in avail_v.items() if gg == g and st & {"trade-version-exclusive", "transfer"}
         and not st & {"wild", "gift", "evolve", "breed", "event"}}
    p(f"- {g} : Pokédex **{len(a)}**, pokedata **{len(b)}** (espèces à faire venir d’une autre version, d’un autre jeu ou par la Capsule Temporelle) ; seulement Pokédex : "
      f"{', '.join(sorted(a - b, key=int)) or '—'} ; seulement pokedata : {', '.join(sorted(b - a, key=int)) or '—'}.")
p("")

sh = J("shiny.json")
p("## Chromatiques\n")
for g in GAMES:
    m = sh["m"].get(g, {})
    rules = {r["method"]: r["odds"] for r in q("SELECT method, odds FROM shiny_rule WHERE game_id=?", g)}
    locks = sorted(r["form_id"] for r in q("SELECT form_id FROM shiny_lock WHERE game_id=?", g))
    their_locks = sorted(k.lstrip("#") for k in (sh["l"].get(g) or {}))
    p(f"- {g} : taux de base Pokédex {m.get('b') or '—'} / pokedata {rules.get('base', '—')} ; règles pokedata : "
      f"{', '.join(f'{k} {v}' for k, v in sorted(rules.items())) or '— (pas de chromatiques)'} ; règles Pokédex : "
      f"{'; '.join(f'{r[0]} {r[2]}' for r in m.get('r', [])) or '—'} ; verrous Pokédex : {', '.join(their_locks) or '—'}, pokedata : {', '.join(locks) or '—'}.")
fixed = q("SELECT DISTINCT e.form_id, v.game_id, json_extract(e.extra,'$.shiny') s FROM encounter e JOIN version v ON v.id=e.version_id WHERE json_extract(e.extra,'$.shiny') IS NOT NULL")
if fixed: p("- Rencontres au chromatique imposé par le jeu (pokedata, `encounter.extra.shiny`) : " + ", ".join(f"{r['form_id']} {r['game_id']} ({r['s']})" for r in fixed) + ".")
p("")
print("\n".join(L))
