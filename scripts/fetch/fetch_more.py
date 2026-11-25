"""Fetch the extra sources of phases 1b and 2 into cache/ and record them in cache/manifest.json.

  bulbapedia  regional Pokédex lists, categories in other languages, priority brackets (wikitext + revid)
  pokepedia   move pages (infobox + in-game descriptions), batched 50 titles per request
  serebii     attackdex lists per type and per game (facts only: type, category, PP, power, accuracy;
              the in-game description column is kept only to cross-check the official text)
Polite: MediaWiki API, 1 request/second, identifiable User-Agent, local cache.
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import CACHE, ROOT, load_manifest, save_manifest, sha256_bytes
from fetch_sources import NOW, UA, http_get

BULBA = ["List of Pokémon by Kanto Pokédex number", "List of Pokémon by New Pokédex number", "List of Pokémon by Johto Pokédex number",
         "List of Pokémon by Hoenn Pokédex number in Generation III", "List of Pokémon by Hoenn Pokédex number in Generation VI",
         "List of Pokémon by Sinnoh Pokédex number", "List of Pokémon by Unova Pokédex number in Pokémon Black and White",
         "List of Pokémon by Unova Pokédex number in Pokémon Black 2 and White 2", "List of Pokémon by Central Kalos Pokédex number",
         "List of Pokémon by Coastal Kalos Pokédex number", "List of Pokémon by Mountain Kalos Pokédex number",
         "List of Pokémon by Alola Pokédex number in Pokémon Sun and Moon", "List of Pokémon by Alola Pokédex number in Pokémon Ultra Sun and Ultra Moon",
         "List of Pokémon by Galar Pokédex number", "List of Pokémon by Isle of Armor Pokédex number", "List of Pokémon by Crown Tundra Pokédex number",
         "List of Pokémon by Hisui Pokédex number", "List of Pokémon by Paldea Pokédex number", "List of Pokémon by Kitakami Pokédex number",
         "List of Pokémon by Blueberry Pokédex number", "List of Pokémon by Lumiose Pokédex number", "List of Pokémon by Hyperspace Pokédex number",
         "List of categories in other languages", "Priority", "List of moves"]
SEREBII = ["rby", "gs", "", "dp", "bw", "xy", "sm", "swsh", "sv"]   # '' = Generation III attackdex
TYPES = ["normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison", "ground", "flying", "psychic", "bug",
         "rock", "ghost", "dragon", "dark", "steel", "fairy"]


def mw_batch(api, titles):
    """Latest revision of up to 50 titles per request; returns {requested title: (final title, revid, text)}."""
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        url = api + "?" + urllib.parse.urlencode({"action": "query", "prop": "revisions", "rvprop": "content|ids", "rvslots": "main",
                                                  "titles": "|".join(chunk), "redirects": "1", "format": "json", "formatversion": "2"})
        time.sleep(1)
        j = json.loads(http_get(url))
        q = j["query"]
        alias = {}
        for k in ("normalized", "redirects"):
            for x in q.get(k, []):
                alias[x["from"]] = x["to"]
        pages = {p["title"]: p for p in q["pages"]}
        for t in chunk:
            f = t
            while f in alias: f = alias[f]
            p = pages.get(f)
            if p and "revisions" in p:
                rv = p["revisions"][0]
                out[t] = (p["title"], str(rv["revid"]), rv["slots"]["main"]["content"])
    return out


def save_wiki(m, site, title, final, rev, text, base):
    d = CACHE / site; d.mkdir(exist_ok=True)
    fn = d / (re.sub(r"[/:]", "_", title.replace(" ", "_")) + ".wiki")
    fn.write_text(text, "utf-8")
    m[f"{site}:{title}"] = {"source_id": site, "revision": rev, "retrieved_at": NOW, "path": str(fn.relative_to(ROOT)),
                            "url": base + urllib.parse.quote(final.replace(" ", "_")), "sha256": sha256_bytes(text.encode())}


def serebii(m):
    d = CACHE / "serebii"; d.mkdir(exist_ok=True)
    for dex in SEREBII:
        base = f"https://www.serebii.net/attackdex{'-' + dex if dex else ''}/"
        time.sleep(1)
        idx = http_get(base).decode("latin-1")
        found = re.findall(r'href="((?:/attackdex%s/)?(?:type/)?(%s)\.shtml)"' % ('-' + dex if dex else '', "|".join(TYPES)), idx)
        links = sorted({(p if p.startswith("/") else base[len("https://www.serebii.net"):] + p, t) for p, t in found})
        rows = []
        for path, t in links:
            time.sleep(1)
            page = http_get("https://www.serebii.net" + path).decode("latin-1")
            for tr in re.findall(r"<tr>(.*?)</tr>", page, re.S):
                tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
                a = re.search(r'<a href="/attackdex[^"]*/([a-z0-9]+)\.shtml">([^<]+)</a>', tds[0]) if tds else None
                if not a or len(tds) < 6:
                    continue
                imgs = [re.search(r'type/([a-z]+)\.(?:gif|png)', x) for x in tds[1:3]]
                cells = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in tds]
                rows.append({"slug": a.group(1), "name": html.unescape(a.group(2)).strip(), "type": imgs[0].group(1) if imgs[0] else None,
                             "category": imgs[1].group(1) if imgs[1] else None, "pp": cells[3], "power": cells[4], "accuracy": cells[5],
                             "text": re.sub(r"\s+", " ", cells[6]).strip() if len(cells) > 6 else None, "list": t})
        rows.sort(key=lambda r: (r["slug"], r["list"]))
        body = json.dumps(rows, ensure_ascii=False, indent=0)
        fn = d / f"attackdex_{dex or 'gen3'}.json"
        fn.write_text(body, "utf-8")
        m[f"serebii:attackdex-{dex or 'gen3'}"] = {"source_id": "serebii", "revision": NOW[:10], "retrieved_at": NOW, "path": str(fn.relative_to(ROOT)),
                                                   "url": base, "sha256": sha256_bytes(body.encode())}
        print("serebii", dex or "gen3", len(links), len(rows))


class Manifest(dict):
    """Re-read the manifest before each save so that concurrent fetch steps do not drop each other's entries."""
    def save(self):
        cur = load_manifest(); cur.update(self); save_manifest(cur)


def main(steps):
    m = Manifest()
    if "bulbapedia" in steps:
        got = mw_batch("https://bulbapedia.bulbagarden.net/w/api.php", BULBA)
        for t in BULBA:
            if t not in got: print("MISSING bulbapedia", t); continue
            save_wiki(m, "bulbapedia", t, *got[t], "https://bulbapedia.bulbagarden.net/wiki/")
        m.save()
    if "pokepedia" in steps:
        names = json.load(open(CACHE / "pkhex-dump/names_moves_items.json", encoding="utf-8"))["fr"]["moves"]
        titles = sorted({n for n in names[1:] if n and n != "—"})
        got = mw_batch("https://www.pokepedia.fr/api.php", titles)
        retry = [t for t in titles if t not in got or "Infobox Capacité" not in got[t][2]]
        got2 = mw_batch("https://www.pokepedia.fr/api.php", [t + " (capacité)" for t in retry])
        for t in retry:
            if t + " (capacité)" in got2 and "Infobox Capacité" in got2[t + " (capacité)"][2]:
                got[t] = got2[t + " (capacité)"]
        moves = {t: {"title": v[0], "revid": v[1], "text": v[2]} for t, v in got.items() if "Infobox Capacité" in v[2]}
        body = json.dumps(moves, ensure_ascii=False, sort_keys=True)
        fn = CACHE / "pokepedia" / "moves.json"; fn.parent.mkdir(exist_ok=True)
        fn.write_text(body, "utf-8")
        m["pokepedia:moves"] = {"source_id": "pokepedia", "revision": "revids in file", "retrieved_at": NOW, "path": str(fn.relative_to(ROOT)),
                                "url": "https://www.pokepedia.fr/", "sha256": sha256_bytes(body.encode())}
        print("pokepedia moves", len(moves), "of", len(titles))
        m.save()
    if "serebii" in steps:
        serebii(m)
        m.save()


if __name__ == "__main__":
    main(sys.argv[1:] or ["bulbapedia", "pokepedia", "serebii"])
