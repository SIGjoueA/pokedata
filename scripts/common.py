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


def write_csv(name: str, header: list, rows: list) -> int:
    """Write db/data/<name>.csv with a stable sort (by all columns as strings)."""
    DATA.mkdir(parents=True, exist_ok=True)
    def norm(v):
        return "" if v is None else str(v)
    def sort_key(r):
        out = []
        for v in r:
            s = norm(v)
            out.append((0, int(s), "") if s.lstrip("-").isdigit() else (1, 0, s))
        return out
    rows = sorted(rows, key=sort_key)
    with open(DATA / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow([norm(v) for v in r])
    return len(rows)


def read_csv(name: str) -> list:
    p = DATA / f"{name}.csv"
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))
