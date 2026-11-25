"""Build build/pokedata.sqlite from db/schema.sql + db/data/*.csv (the CSVs are the source of truth)."""
import csv, datetime, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, DATA, SCHEMA, read_csv

ORDER = ["language", "generation", "region", "game", "version", "game_language", "game_patch", "pokedex", "type",
         "type_chart", "type_chart_game", "type_efficacy", "growth_rate", "egg_group", "evolution_chain", "species",
         "species_egg_group", "pokedex_entry", "form", "form_game", "ability", "form_ability", "item", "item_game",
         "form_held_item", "move", "move_game", "move_effect_stat", "learn_method", "machine", "learnset", "evolution",
         "evolution_method", "location", "location_area", "location_game", "encounter_method", "encounter_condition",
         "encounter", "encounter_condition_link", "availability", "shiny_rule", "shiny_lock", "go_cp_multiplier",
         "go_pokemon", "go_release", "go_move", "go_move_stats", "go_learnset", "go_costume", "battle_constant",
         "field_effect", "field_effect_modifier", "raid_tier", "raid_boss", "battle_format", "battle_format_form",
         "source", "game_map", "map_position", "translation", "external_id", "nature", "update_log",
         "source_document", "citation", "verification", "discrepancy", "update_log_item"]


def main(out=None):
    out = out or BUILD / "pokedata.sqlite"
    BUILD.mkdir(parents=True, exist_ok=True)
    if os.path.exists(out):
        os.remove(out)
    db = sqlite3.connect(out)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(open(SCHEMA, encoding="utf-8").read())
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    present = {p.stem for p in DATA.glob("*.csv")}
    unknown = present - tables
    if unknown:
        raise SystemExit(f"CSV without table: {sorted(unknown)}")
    counts = {}
    for t in ORDER:
        if t not in present:
            continue
        cols = {r[1]: r[2].upper() for r in db.execute(f"PRAGMA table_info({t})")}
        rows = read_csv(t)
        if not rows:
            continue
        hdr = list(rows[0].keys())
        def conv(c, v):
            if v == "":
                return None
            ty = cols[c]
            if ty == "INTEGER":
                return int(v)
            if ty == "REAL":
                return float(v)
            return v
        db.executemany(f"INSERT INTO {t} ({','.join(hdr)}) VALUES ({','.join('?' * len(hdr))})",
                       [[conv(c, r[c]) for c in hdr] for r in rows])
        counts[t] = len(rows)
    log = read_csv("update_log")
    last = log[-1] if log else {}
    meta = {"schema_version": last.get("schema_version", "1.0.0"), "data_version": last.get("data_version", ""),
            "api_version": "v1", "license_code": "MIT",
            "license_notice": "Unofficial fan project. Pokémon and all related names, texts and game data © Nintendo, Creatures Inc., GAME FREAK inc., The Pokémon Company. Not affiliated with or endorsed by them.",
            "generated_at": last.get("finished_at", "")}
    db.executemany("INSERT INTO meta(key, value) VALUES (?, ?)", meta.items())
    db.commit()
    bad = db.execute("PRAGMA foreign_key_check").fetchall()
    if bad:
        raise SystemExit(f"foreign key violations: {bad[:10]} (+{len(bad) - 10 if len(bad) > 10 else 0})")
    ok = db.execute("PRAGMA integrity_check").fetchone()[0]
    if ok != "ok":
        raise SystemExit(ok)
    db.execute("VACUUM")
    db.close()
    print(f"{out}: {sum(counts.values())} rows in {len(counts)} tables, {os.path.getsize(out) // 1024} KiB")


if __name__ == "__main__":
    main()
