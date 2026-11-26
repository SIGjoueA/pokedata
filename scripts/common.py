"""Shared helpers for the pokedata pipeline (stdlib only)."""
import csv, hashlib, json, os, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "db" / "data"
CACHE = ROOT / "cache"
BUILD = ROOT / "build"
SCHEMA = ROOT / "db" / "schema.sql"
MANIFEST = CACHE / "manifest.json"

LANGS = ["ja", "en", "fr", "de", "it", "es", "es-419", "ko", "zh-Hans", "zh-Hant"]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(s: str) -> str:
    return sha256_bytes(s.encode("utf-8"))


def canon(v) -> str:
    """Canonical JSON used for hashing and observed values."""
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def row_key(*parts) -> str:
    return canon(list(parts))


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text("utf-8"))
    return {}


def save_manifest(m: dict) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1, sort_keys=True), "utf-8")


# Provenance tables split by the table they describe (schema 1.1.0): db/data/<name>/<table_name>.csv
SPLIT_BY_TABLE = {"verification", "citation"}


def write_csv(name: str, header: list, rows: list) -> int:
    """Write db/data/<name>.csv with a stable sort (by all columns as strings).
    Tables of SPLIT_BY_TABLE are written as one file per value of their table_name column."""
    DATA.mkdir(parents=True, exist_ok=True)
    if name in SPLIT_BY_TABLE:
        i = header.index("table_name")
        parts = {}
        for r in rows:
            parts.setdefault(r[i], []).append(r)
        d = DATA / name
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.csv"):
            if old.stem not in parts:
                old.unlink()
        legacy = DATA / f"{name}.csv"
        if legacy.exists():
            legacy.unlink()
        return sum(_write_one(d / f"{t}.csv", header, rs) for t, rs in parts.items())
    return _write_one(DATA / f"{name}.csv", header, rows)


def _write_one(path, header: list, rows: list) -> int:
    def norm(v):
        return "" if v is None else str(v)
    def sort_key(r):
        out = []
        for v in r:
            s = norm(v)
            out.append((0, int(s), "") if s.lstrip("-").isdigit() else (1, 0, s))
        return out
    rows = sorted(rows, key=sort_key)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow([norm(v) for v in r])
    return len(rows)


def read_csv(name: str) -> list:
    """Rows of db/data/<name>.csv, or of every db/data/<name>/*.csv (split tables), in file-name order."""
    d = DATA / name
    paths = sorted(d.glob("*.csv")) if d.is_dir() else [DATA / f"{name}.csv"]
    rows = []
    for p in paths:
        if p.exists():
            with open(p, encoding="utf-8") as f:
                rows.extend(csv.DictReader(f))
    return rows


def data_tables() -> set:
    """Names of the tables present in db/data (one CSV, or a directory of CSVs for split tables)."""
    return {p.stem for p in DATA.glob("*.csv")} | {p.name for p in DATA.iterdir() if p.is_dir() and any(p.glob("*.csv"))}
