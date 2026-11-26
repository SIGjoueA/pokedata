# pokedata

> **Projet de fans non officiel.** Données © Nintendo / Creatures Inc. / GAME FREAK inc. / The Pokémon Company. Ni affilié, ni approuvé par eux. Voir [NOTICE.md](NOTICE.md).

Base de données Pokémon ouverte, vérifiée et multilingue (ja, en, fr, de, it, es, es-419, ko, zh-Hans, zh-Hant + romaji), publiée sous forme de :

- **API statique JSON** : <https://sigjouea.github.io/pokedata/api/v1/index.json>
- **base SQLite** téléchargeable à chaque version de données (Releases `data-AAAA.MM.JJ`)
- **CSV** triés dans [`db/data/`](db/data), qui sont la source de vérité (diffs lisibles d'une mise à jour à l'autre) ; la provenance est découpée par table décrite : `db/data/verification/{table}.csv`, `db/data/citation/{table}.csv`

## Contenu

Espèces (1025) et formes (1588) pour chaque jeu du périmètre (Rouge/Bleu → Légendes Z-A et leurs DLC), avec types, statistiques, talents, taille, poids, taux de capture, EV, groupes d'œufs, sexe, croissance, et les noms officiels dans chaque langue où le jeu est sorti (`game_language`). Évolutions, Pokédex régionaux, catégories ; capacités (valeurs par jeu, CT/CS/DT, noms et descriptions de jeu) ; movesets par jeu et par méthode ; lieux, rencontres, disponibilité par version et règles de chromatiques (phase 3, publiée par lots : générations 1 à 9).

Prévu ensuite : objets, GO, tables des types, combats. Voir [`docs/plan.md`](docs/plan.md).

## Vérification

Chaque valeur a une provenance (`citation` → `source_document`, avec empreinte sha256 du fichier ou de la révision de page) et un statut (`verification`) :

| Statut | Règle |
|---|---|
| `game-data` | confirmé par extraction des données des jeux |
| `unanimous` | toutes les sources disponibles concordent |
| `majority` | au moins 2 sources concordantes, dont une de rang 1–2 |
| `single-source` | une seule source existe (signalé dans l'API) |
| `manual` | référentiel saisi à la main et sourcé |

Les movesets (`learnset`) sont vérifiés par ensemble forme × jeu × méthode (schéma 1.1.0) : une ligne de `verification` par ensemble, avec l'empreinte de la liste ; les capacités en plus ou en moins selon chaque source de contrôle sont dans `discrepancy`.

Les rencontres (`encounter`) suivent la même convention, par ensemble zone × version × méthode ; la disponibilité (`availability`) et les lieux sont vérifiés ligne par ligne. À partir de la génération 3, le lieu enregistré par le jeu fait foi ; la provenance du placement est citée. Schéma 1.2.0 (migration 0003) : statut de disponibilité `npc-trade` pour les échanges en jeu.

Les désaccords entre sources sont conservés dans `discrepancy` (et dans l'API, champ `discrepancies`). Une valeur déjà vérifiée n'est re-vérifiée que si son empreinte change. Aucun texte rédigé par un wiki n'est stocké : uniquement des faits et des textes officiels des jeux.

## API

Adresses = identifiants du Pokédex (numéro national, `{numéro}-{forme}` pour les formes) ; les slugs lisibles sont fournis en alias.

| Point d'accès | Contenu |
|---|---|
| `api/v1/index.json` | versions, compteurs, liste des points d'accès |
| `api/v1/pokemon/index.json` | toutes les espèces (noms, formes, types actuels) |
| `api/v1/pokemon/{id}.json` | une espèce, ses formes et leurs données par jeu |
| `api/v1/form/{form_id}.json` | une forme (ex. `6-mega-x`, `37-alola`) |
| `api/v1/ability/{id}.json` | un talent, ses noms et ses porteurs par jeu |
| `api/v1/evolution/{chain_id}.json` | une famille d'évolution : paires de formes et méthodes par jeu (id de chaîne PokeAPI, donné par `pokemon/{id}.json`) |
| `api/v1/pokedex/index.json`, `pokedex/{pokedex_id}.json` | Pokédex régionaux par jeu (ex. `sv-paldea`, `xy-kalos-coastal`) et leurs numéros |
| `api/v1/item/{id}.json` | objets utilisés par les évolutions (noms en 10 langues) |
| `api/v1/move/index.json`, `move/{id}.json` | capacités : noms en 10 langues, valeurs par jeu (type, catégorie, puissance, précision, PP, priorité), CT/CS/DT, descriptions de jeu (anglais, français) |
| `api/v1/machine/{game_id}.json` | liste des CT/CS/DT d'un jeu `[libellé, id de capacité]` |
| `api/v1/learnset/{form_id}.json` | movesets d'une forme par jeu et par méthode (`level-up`, `egg`, `machine`, `tutor`, `reminder`, `mastery`, `plus`) : `[id de capacité, niveau]`, plus l'id de version si la capacité n'existe que dans une version ; écarts des sources de contrôle dans `discrepancies` |
| `api/v1/location/index.json`, `location/{game_id}.json` | lieux d'un jeu : identifiant stable (`kanto-route-3` ≠ `hoenn-route-3`), région, noms de jeu dans les langues du jeu, anciens noms du Pokédex (`aliases.pokedex-legacy`), rencontres par version (méthode, niveaux, conditions), écarts des sources de contrôle |
| `api/v1/pokemon/{id}/locations.json` | pour chaque forme et version : disponibilité (`wild`, `gift`, `npc-trade`, `evolve`, `breed`, `trade-version-exclusive`, `transfer`, `event`, `unobtainable`, avec `detail`), rencontres avec leur lieu (`placement` / `access` quand le lieu ne vient pas du jeu ou demande un objet distribué) et, pour une version DLC, `arrives_with` (jeu de base ou DLC qui apporte la forme) |
| `api/v1/type/index.json`, `game/index.json`, `game/{id}.json` | référentiels (`game/{id}.json` : règles et verrous de chromatiques) |
| `api/v1/search/{lang}.json` | index de recherche `[nom normalisé, nom, id]` |
| `api/v1/meta/{sources,changelog,verification,languages}.json` | provenance, journal, statuts |
| `api/v1/download.json` | lien vers la base SQLite de la version courante |

Les fichiers de données ne contiennent ni date ni numéro de version (seul `index.json` en a), pour que chaque mise à jour ne modifie que ce qui a réellement changé.

## Construire localement

```sh
python3 scripts/build_sqlite.py      # db/data/**/*.csv + db/schema.sql -> build/pokedata.sqlite
python3 scripts/export_api.py        # -> site/api/v1/**
python3 -m unittest discover tests
```

Réimporter depuis les sources (nécessite git, Node.js et .NET 10) :

```sh
python3 scripts/fetch/fetch_sources.py   # cache/ : PokeAPI, Showdown, extraction PKHeX, pages Bulbapedia/Poképédia
python3 scripts/fetch/fetch_more.py bulbapedia pokepedia serebii phase3   # pages des phases 1b, 2 et 3 (Pokédex régionaux, catégories, capacités)
python3 scripts/import_data.py         # -> db/data/*.csv + reports/
python3 scripts/changelog.py             # -> CHANGELOG.md
python3 scripts/compare_learnsets.py > reports/compare-learnsets.md   # comparaison avec le Pokédex (lecture seule)
python3 scripts/compare_phase3.py > reports/compare-locations.md     # lieux et rencontres ↔ Pokédex (lecture seule)
```

## Journal

Voir [CHANGELOG.md](CHANGELOG.md) (généré depuis la table `update_log`).

## Licence

Code et structure : [MIT](LICENSE). Les noms, textes et données Pokémon restent la propriété de leurs ayants droit ([NOTICE.md](NOTICE.md)).
