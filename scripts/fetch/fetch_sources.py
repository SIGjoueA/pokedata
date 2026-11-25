"""Fetch every source into cache/ and record (source, locator, revision, sha256) in cache/manifest.json.

Sources (see plan, section 4):
  pkhex      tier 1  PKHeX.Core personal tables + game text, dumped with scripts/fetch/pkhex_dumper (needs dotnet)
  pokeapi    tier 3  PokeAPI CSV (git, data/v2/csv)
  showdown   tier 3  Pokemon Showdown data (git, data/)
  bulbapedia tier 2  wikitext of selected pages through the MediaWiki API (polite: cached, 1 req/s)
"""
import datetime, json, os, subprocess, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import CACHE, ROOT, load_manifest, save_manifest, sha256_bytes

UA = "pokedata/1.0 (unofficial fan database; https://github.com/SIGjoueA/pokedata)"
NOW = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

BULBA_PAGES = [
    "List of Japanese Pokémon names", "List of French Pokémon names", "List of German Pokémon names",
    "List of Italian Pokémon names", "List of Spanish Pokémon names", "List of Korean Pokémon names",
    "List of Chinese Pokémon names", "List of Pokémon with gender differences", "Gigantamax",
]
POKEPEDIA_CATEGORIES = ["Pokémon légendaire", "Pokémon fabuleux", "Ultra-Chimère", "Pokémon Paradoxe"]
BULBA_CATEGORIES = ["Legendary Pokémon", "Mythical Pokémon", "Ultra Beasts", "Paradox Pokémon", "Baby Pokémon"]


def sh(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def git_source(name, url, sparse):
    d = CACHE / name
    if not d.exists():
        sh(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse", url, str(d)])
        sh(["git", "sparse-checkout", "set", *sparse], cwd=d)
    else:
        sh(["git", "fetch", "-q", "--depth", "1", "origin"], cwd=d)
        sh(["git", "reset", "-q", "--hard", "FETCH_HEAD"], cwd=d)  # local cache only, never pushed
    return sh(["git", "rev-parse", "HEAD"], cwd=d)


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def bulba_api(params):
    params = {**params, "format": "json", "formatversion": "2"}
    url = "https://bulbapedia.bulbagarden.net/w/api.php?" + urllib.parse.urlencode(params)
    time.sleep(1)
    return json.loads(http_get(url))


def main():
    m = load_manifest()
    CACHE.mkdir(parents=True, exist_ok=True)

    # PokeAPI + Showdown (git)
    rev = git_source("pokeapi", "https://github.com/PokeAPI/pokeapi.git", ["data/v2/csv"])
    m["pokeapi"] = {"source_id": "pokeapi", "revision": rev, "retrieved_at": NOW, "path": "cache/pokeapi/data/v2/csv"}
    rev = git_source("showdown", "https://github.com/smogon/pokemon-showdown.git", ["data"])
    m["showdown"] = {"source_id": "showdown", "revision": rev, "retrieved_at": NOW, "path": "cache/showdown/data"}

    # Showdown species per mod, flattened with node (the data files are TypeScript object literals)
    out = CACHE / "showdown-species.json"
    sh(["node", str(ROOT / "scripts/fetch/showdown_species.mjs"), str(CACHE / "showdown/data"), str(out)])
    m["showdown-species"] = {"source_id": "showdown", "revision": m["showdown"]["revision"], "retrieved_at": NOW,
                             "path": "cache/showdown-species.json"}

    sh(["node", str(ROOT / "scripts/fetch/showdown_more.mjs"), str(CACHE / "showdown/data"), str(CACHE / "showdown-more.json")])
    m["showdown-more"] = {"source_id": "showdown", "revision": m["showdown"]["revision"], "retrieved_at": NOW,
                          "path": "cache/showdown-more.json"}

    # PKHeX dump (tier 1)
    dump = CACHE / "pkhex-dump"
    proj = ROOT / "scripts/fetch/pkhex_dumper"
    sh(["dotnet", "run", "-c", "Release", "--project", str(proj), "--", str(dump)])
    ver = [l for l in (proj / "pkhex_dumper.csproj").read_text().splitlines() if "PKHeX.Core" in l][0].split('Version="')[1].split('"')[0]
    m["pkhex"] = {"source_id": "pkhex", "revision": f"PKHeX.Core {ver}", "retrieved_at": NOW, "path": "cache/pkhex-dump"}

    # Bulbapedia pages (wikitext + revision id)
    bdir = CACHE / "bulbapedia"; bdir.mkdir(exist_ok=True)
    for title in BULBA_PAGES:
        j = bulba_api({"action": "query", "prop": "revisions", "rvprop": "content|ids", "rvslots": "main", "titles": title, "redirects": "1"})
        page = j["query"]["pages"][0]
        rv = page["revisions"][0]
        text = rv["slots"]["main"]["content"]
        fn = bdir / (title.replace(" ", "_") + ".wiki")
        fn.write_text(text, "utf-8")
        m["bulbapedia:" + title] = {"source_id": "bulbapedia", "revision": str(rv["revid"]), "retrieved_at": NOW,
                                    "path": str(fn.relative_to(ROOT)),
                                    "url": "https://bulbapedia.bulbagarden.net/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
                                    "sha256": sha256_bytes(text.encode())}
    for cat in BULBA_CATEGORIES:
        members, cont = [], {}
        while True:
            j = bulba_api({"action": "query", "list": "categorymembers", "cmtitle": "Category:" + cat, "cmlimit": "500", "cmnamespace": "0", **cont})
            members += [x["title"] for x in j["query"]["categorymembers"]]
            if "continue" not in j:
                break
            cont = {"cmcontinue": j["continue"]["cmcontinue"]}
        members.sort()
        fn = bdir / ("Category_" + cat.replace(" ", "_") + ".json")
        fn.write_text(json.dumps(members, ensure_ascii=False, indent=0), "utf-8")
        m["bulbapedia:Category:" + cat] = {"source_id": "bulbapedia", "revision": "categorymembers", "retrieved_at": NOW,
                                           "path": str(fn.relative_to(ROOT)),
                                           "url": "https://bulbapedia.bulbagarden.net/wiki/Category:" + urllib.parse.quote(cat.replace(" ", "_")),
                                           "sha256": sha256_bytes(fn.read_bytes())}
    # Poképédia categories (third wiki for species flags)
    pdir = CACHE / "pokepedia"; pdir.mkdir(exist_ok=True)
    for cat in POKEPEDIA_CATEGORIES:
        members, cont = [], {}
        while True:
            url = "https://www.pokepedia.fr/api.php?" + urllib.parse.urlencode({"action": "query", "list": "categorymembers", "cmtitle": "Catégorie:" + cat, "cmlimit": "500", "cmnamespace": "0", "format": "json", **cont})
            time.sleep(1)
            j = json.loads(http_get(url))
            members += [x["title"] for x in j["query"]["categorymembers"]]
            if "continue" not in j:
                break
            cont = {"cmcontinue": j["continue"]["cmcontinue"]}
        members.sort()
        fn = pdir / ("Categorie_" + cat.replace(" ", "_") + ".json")
        fn.write_text(json.dumps(members, ensure_ascii=False, indent=0), "utf-8")
        m["pokepedia:Catégorie:" + cat] = {"source_id": "pokepedia", "revision": "categorymembers", "retrieved_at": NOW,
                                          "path": str(fn.relative_to(ROOT)),
                                          "url": "https://www.pokepedia.fr/Cat%C3%A9gorie:" + urllib.parse.quote(cat.replace(" ", "_")),
                                          "sha256": sha256_bytes(fn.read_bytes())}
    save_manifest(m)
    print(json.dumps({k: v.get("revision") for k, v in m.items()}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
