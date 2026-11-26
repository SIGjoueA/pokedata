"""Regenerate CHANGELOG.md from db/data/update_log.csv (the update log is the source of truth)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, read_csv

items = {}
for r in read_csv("update_log_item"):
    items.setdefault(r["update_id"], []).append(r)
out = ["# Journal des mises à jour\n", "Généré depuis `db/data/update_log.csv` par `scripts/changelog.py`. "
       "Le détail ligne à ligne est dans `update_log_item` (base SQLite) et `api/v1/meta/changelog.json`.\n"]
for r in sorted(read_csv("update_log"), key=lambda r: -int(r["id"])):
    st = json.loads(r["stats"]) if r["stats"] else {}
    out.append(f"\n## {r['data_version']} — {r['trigger']}\n")
    out.append(f"- Type : {r['kind']} · schéma {r['schema_version']} · {r['started_at']} → {r['finished_at']} (UTC)")
    out.append(f"- {r['summary']}")
    if st.get("verification"):
        out.append("- Statuts de vérification : " + ", ".join(f"{k} {v}" for k, v in sorted(st["verification"].items())))
    if st.get("rows"):
        keep = ["species", "form", "form_game", "form_ability", "ability", "evolution", "evolution_method", "pokedex_entry", "item",
                "move", "move_game", "machine", "learnset", "location", "encounter", "availability", "shiny_rule", "translation", "discrepancy"]
        out.append("- Lignes : " + ", ".join(f"{k} {st['rows'][k]}" for k in keep if k in st["rows"]))
(ROOT / "CHANGELOG.md").write_text("\n".join(out) + "\n", "utf-8")
print("CHANGELOG.md written")
