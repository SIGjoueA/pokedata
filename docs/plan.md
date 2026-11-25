# pokedata — plan de projet

Base de données Pokémon indépendante et réutilisable, qui deviendra aussi la source unique et vérifiée du Pokédex (sigjouea.github.io/pokedex).
Statut : **validé le 25/11/2026** (plan et schéma 1.0.0). Décisions prises : identifiants du Pokédex dans les adresses de l'API, alias lisibles en plus (option A) ; textes rédigés par les wikis **exclus** de la base. Phase 1 publiée (section 16), phase 1b publiée (section 17), phase 2 publiée sans les movesets (section 18).

---

## 1. Principes

| Principe | Conséquence concrète |
|---|---|
| Les données extraites des jeux font foi | Chaque valeur cite sa source ; une extraction de jeu l'emporte sur les wikis. |
| Sinon, majorité 2 sur 3 | Bulbapedia, Serebii, Poképédia (et d'autres si besoin) ; l'écart est conservé dans `discrepancy`. |
| Pas de revérification en boucle | Une donnée vérifiée garde l'empreinte (sha256) de ses sources ; on ne la recontrôle que si cette empreinte change. |
| Vérifier avant de présenter | Pas de champ « non vérifié » publié quand un croisement est possible ; `single-source` seulement quand une seule source existe. |
| Gratuit, sans serveur | SQLite + JSON statiques sur GitHub Pages ; fichier `.sqlite` en pièce jointe de Release GitHub. |
| Aucun média copié | Ni sprites, ni cartes, ni cris : des liens et des coordonnées seulement. |

## 2. Choix clés (et options écartées)

1. **SQLite comme base, mais la source de vérité dans git est du texte.** `db/data/` contient une table par fichier (CSV trié, UTF-8). Le `.sqlite` et les JSON sont *construits* à partir de là.
   - Pourquoi : un binaire SQLite rend les diffs illisibles et alourdit l'historique à chaque mise à jour. Des CSV triés donnent des diffs relus en une seconde.
   - Écarté : commiter le `.sqlite` (diffs illisibles) ; Postgres/Supabase (il faudrait un serveur, donc des coûts) ; JSON comme source (trop de doublons et pas de contraintes).
2. **Une ligne par (entité, jeu)** pour les stats, types, talents, capacités et movesets.
   - Pourquoi : c'est explicite et simple à citer. Ça évite les pièges des plages « valable à partir de la génération N » avec Let's Go, Légendes Arceus, Z-A ou Champions.
   - Écarté : les plages de validité, plus compactes mais sources d'erreurs. Le volume reste faible : environ 1 500 formes × 30 jeux, soit moins de 50 000 lignes.
   - **Exception : GO.** Ses données changent dans le temps, pas d'un jeu à l'autre. Elles ont donc des dates `valid_from` / `valid_to`.
3. **Identifiants stables, repris de l'existant.**
   - N° national pour les espèces.
   - Ids du Pokédex / PokeAPI pour les capacités et les talents (pour les talents, l'index interne des jeux diverge à partir de 299 : il est rangé dans `external_id`, système `game-index`).
   - Clés du Pokédex actuel pour les formes (`6-mega-x`) et les jeux (`sv`, `za`).
   - Templates du GAME_MASTER pour les attaques GO.
   - Les autres systèmes (PokeAPI, Showdown, wikis, index internes des jeux) sont rangés dans `external_id`.
4. **Une seule table de traductions générique** : entité, champ, langue, avec un jeu ou une version en option. Elle couvre les 10 langues officielles et deux écritures auxiliaires (kanji, rōmaji).
   - Écarté : une colonne par langue dans chaque table (rigide, et la plupart des cellules seraient vides).
5. **Provenance générique.**
   - Chaque donnée est désignée par `(table_name, row_key, column_name)`, où `row_key` est sa clé en JSON.
   - Les tables `citation`, `verification`, `discrepancy` et `update_log` s'appliquent à toutes les données.
   - Écarté : des colonnes de source dans chaque table (insuffisant dès qu'on a 3 sources et un désaccord).
6. **Les calculs restent côté Pokédex.** Classements PvP, simulations de raids et PC max sont *calculés* à partir de la base ; ce ne sont pas des données sources. La base fournit les entrées : stats, CPM, attaques, tables de types.

## 3. Phases (dans l'ordre)

Chaque phase se termine par trois choses :
- un import vérifié ;
- un rapport de comparaison avec les données actuelles du Pokédex (`reports/compare-<domaine>.md`) ;
- une publication de l'API pour ce domaine.

La bascule du Pokédex vers la base, domaine par domaine, est faite côté Pokédex.

| # | Phase | Contenu | Sortie / critère de fin |
|---|---|---|---|
| 0 | Fondations | Validation du schéma, création du dépôt, licence, squelette du pipeline. Référentiels : langues, générations, régions, jeux, versions, `game_language`, types et tables d'efficacité, sources. | `make build` produit une base vide valide et une API d'index ; CI au vert. |
| 1 | Espèces et formes + noms multilingues | `species`, `form`, `form_game` (types, stats, taille, poids, EV, taux de capture), `form_ability`, `ability`, `pokedex`/`pokedex_entry`, `evolution*`, `egg_group`, `item` (de base). Noms, catégories, descriptions de talents et entrées du Pokédex en 10 langues. | 1 025 espèces et toutes leurs formes ; noms vérifiés dans chaque langue où ils existent. |
| 2 | Capacités et movesets | `move`, `move_game` (valeurs par jeu), `move_effect_stat`, `machine`, `learnset` (toutes méthodes, y compris maîtrise dans Légendes Arceus et Plus dans Z-A). Descriptions en 10 langues. | Comparaison avec `learn-index.json`, `moves.json` et `tm.json` du Pokédex. |
| 3 | Lieux et disponibilité | `location`, `location_area`, `encounter` (+ conditions), `availability` (évolution, échange, transfert, événement, hors dex), `form_held_item`, `shiny_rule`, `shiny_lock`. | Comparaison avec `loc.json`, `loc-index.json`, `trade.json`, `shiny.json` et `sp.pln`. |
| 4 | Pokémon GO | `go_pokemon`, `go_move` / `go_move_stats` (PvE et PvP), `go_learnset` (attaques élite et legacy), `go_release` (chromatique, Obscur, Dynamax, Gigamax…), `go_costume`, `go_cp_multiplier`, boss de raid GO. | Comparaison avec `go.json`, `pvp-moves.json`, `costumes.json`, `shadow.json` et `raid-bosses.json`. |
| 5 | Combat et raids | `battle_constant`, `field_effect*`, `raid_tier`, `raid_boss` (Dynamax, Téracristal dont 7★, raids GO, Combats Max), `battle_format` (Champions, séries SV, ligues GO). | Comparaison avec `raids.json`, `tera7.json`, `boss-schedule.json` et la logique météo/terrains de la v60.40. |
| 6 | Cartes | `game_map` (liens vers les cartes de Serebii, Bulbapedia, Poképédia…) et `map_position` (coordonnées ou polygone de chaque lieu, sur la carte de référence). | Au moins une carte référencée par jeu ; tous les lieux de la phase 3 positionnés. |

Les jeux sont tous traités dans chaque phase (de Rouge/Bleu à Champions, plus GO et HOME), en commençant par les plus récents.
Tant que le schéma ne change pas, chaque phase est publiée dès qu'elle est vérifiée.

## 4. Pipeline d'import

```
fetch → normalize → stage → crosscheck → resolve → load → export → publish
```

1. **fetch** (`scripts/fetch/*`) : télécharge chaque source dans `cache/` (non suivi par git), avec l'URL, la révision et le sha256 du contenu (`source_document`). Il est poli avec les wikis : API MediaWiki, cache local, débit limité, User-Agent identifiable.
2. **normalize** : convertit chaque source vers les ids et unités du schéma (dm, hg, slugs). Les tables de correspondance de noms passent par `external_id`.
3. **stage** : une base temporaire par source, avec le même schéma.
4. **crosscheck** : compare les valeurs champ par champ et écrit une `citation` par source consultée.
5. **resolve** : applique les règles de la section 5 et écrit `verification` et, s'il y a lieu, `discrepancy`.
6. **load** : écrit dans `db/data/*.csv` (tri stable), puis construit `build/pokedata.sqlite`.
7. **export** : génère `api/v1/**` (JSON stable : clés triées, sans horodatage dans les fichiers de données) et les index.
8. **publish** : commit, tag et Release (fichier `.sqlite`), déploiement Pages. Seulement pour les ajouts ou corrections vérifiés, ou une fois l'accord obtenu pour une structure ou un gros ajout.

### Sources par rôle

| Rôle (tier) | Sources | Usage |
|---|---|---|
| 1 — extraction des jeux | Datamines publics : tables personnelles, learnsets, rencontres et textes multilingues des jeux Switch/3DS (dumps publiés par la communauté de datamining, données de PKHeX/pkNX consultées comme référence), **GAME_MASTER GO** (PokeMiners), données d'Ultra-Soleil/Lune et d'avant pour l'historique. | Font foi. |
| 2 — encyclopédies | **Bulbapedia** (CC BY-NC-SA 2.5), **Serebii** (tous droits réservés : faits seulement), **Poképédia** (CC BY-NC-SA 3.0 FR) ; en renfort : Pokémon GO Wiki, Pokewiki (DE), WikiDex (ES). | Vote 2 sur 3 quand aucune extraction n'existe ou pour la confirmer. |
| 3 — amorces | **PokeAPI / CSV veekun** (`pokeapi/data/v2/csv`, code BSD-3), **Pokémon Showdown** (MIT) pour les mécaniques. | Remplissage initial et correspondance des ids ; jamais suffisantes seules pour le statut « vérifié ». |
| 4 — officiel | pokemon.com, press.pokemon.com, boutique Nintendo (langues, dates), pokemongo.com (événements). | Dates, langues, annonces. |

**Décision validée : aucun texte rédigé par un wiki (prose, notes, étymologies, distributions) n'entre dans la base**, ni dans une table à part. On n'en tire que des faits (valeurs, appartenance à une catégorie). Les textes (noms, descriptions) viennent uniquement des jeux (`translation` ne contient que des textes de jeu).

## 5. Règles de résolution des conflits

Pour chaque donnée, dans l'ordre :
1. **Une extraction de jeu existe** → elle fait foi (`status = game-data`). Si un wiki dit autre chose, l'écart est noté dans `discrepancy` (`rule = game-data`), sans bloquer.
2. **Sinon, au moins 2 sources concordantes dont une de rang 1–2** → `majority` (ou `unanimous` si toutes concordent ; en pratique « 2 sur 3 » quand 3 sources existent). La valeur minoritaire est conservée dans `discrepancy.alternatives`.
3. **Désaccord total ou égalité** → on cherche une quatrième source. Sinon `disputed` : non publié, signalé dans le journal.
4. **Une seule source existe** (événement récent, donnée confidentielle) → `single-source`, publié avec cette mention.
5. **Arbitrage manuel** (rare) → `manual`, avec justification écrite dans `discrepancy.note`.
6. **Valeurs différentes selon le jeu** : ce n'est pas un conflit. On garde une ligne par jeu, ou par période pour GO.
7. **Normalisation avant comparaison** : unités, arrondis, typographie (apostrophes ’ et ', espaces fines). Une différence purement typographique ne compte pas comme désaccord.

## 6. Vérification, empreintes et journal

- `source_document.content_sha256` = empreinte de la partie utile du document (section de page, ligne de table du dump), pas de la page entière. On ignore ainsi le bruit : publicités, compteurs, mise en page.
- `verification.sources_fingerprint` = sha256 des empreintes citées, triées. Chaque semaine, le pipeline recalcule les empreintes. **Seules les données dont l'empreinte a changé sont recroisées**, plus les nouvelles données et celles en statut `seeded` ou `disputed`.
- `update_log` contient une entrée par passage : date, type (`weekly`, `release`, `correction`, `schema`), déclencheur (ex. « Z-A 2.0.0 »), version des données, commit et statistiques.
- `update_log_item` détaille chaque ajout, modification ou vérification, avec les documents utilisés.
- `CHANGELOG.md` et `api/v1/meta/changelog.json` sont générés depuis `update_log` : ce qui a été vérifié, d'après quelles sources.

## 7. Structure du dépôt `SIGjoueA/pokedata`

```
pokedata/
├── README.md               présentation, usage de l'API, mention légale
├── LICENSE                 MIT (code)
├── NOTICE.md               « Projet de fans non officiel. Pokémon © Nintendo, Creatures, GAME FREAK, The Pokémon Company. »
├── CHANGELOG.md            généré depuis update_log
├── db/
│   ├── schema.sql          schéma (source de vérité de la structure)
│   ├── migrations/         0001_init.sql, 0002_….sql
│   └── data/               une table = un CSV trié (source de vérité des données)
├── scripts/
│   ├── fetch/              fetch_sources.py, showdown_species.mjs, pkhex_dumper/ (C#, .NET 10)
│   ├── common.py, reference.py   utilitaires, référentiels (langues, jeux, versions, sources…)
│   ├── import_data.py      normalisation, croisement, règles de la section 5 → db/data/*.csv
│   ├── build_sqlite.py     CSV → build/pokedata.sqlite
│   ├── export_api.py       SQLite → site/api/v1/**
│   ├── compare_pokedex.py  rapports de comparaison avec le Pokédex
│   └── changelog.py        update_log → CHANGELOG.md
├── tests/                  intégrité (FK, CHECK), échantillons dorés (Pikachu, Dracaufeu, Motisma…)
├── docs/                   page d'accueil et plan ; le site (site/, avec api/) est généré par le workflow
├── reports/                rapports de comparaison et de vérification
└── .github/workflows/      build et déploiement Pages à chaque push sur main (gratuit en dépôt public)
```

`cache/`, `build/` et `site/` ne sont pas suivis par git. Le pipeline est en Python (bibliothèque standard) ; Node.js ne sert qu'à lire les fichiers TypeScript de Showdown.
L'API générée est déployée par le workflow Pages, sans être commitée : cela évite des dizaines de milliers de fichiers modifiés dans l'historique.

## 8. API statique (GitHub Pages)

Base : `https://sigjouea.github.io/pokedata/api/v1/`. GitHub Pages renvoie `Access-Control-Allow-Origin: *` et compresse en gzip.

```
api/v1/
├── index.json                      versions (données, schéma), comptes, liens vers tout le reste
├── meta/{sources,changelog,languages,verification}.json
├── pokemon/index.json              liste légère : id, slug, formes, types, noms ×10
├── pokemon/{id}.json               espèce + formes + données par jeu (types, stats, talents, évolutions, n° régionaux)
├── pokemon/{id}/moves.json         movesets par jeu et méthode
├── pokemon/{id}/locations.json     rencontres et disponibilité par version
├── pokemon/{id}/go.json            stats GO, attaques, sorties, costumes
├── form/{form_id}.json             ex. form/6-mega-x.json
├── move/index.json · move/{id}.json        valeurs par jeu + textes
├── ability/index.json · ability/{id}.json
├── item/index.json · item/{id}.json
├── type/index.json · type/charts.json      tables gen1, gen2-5, gen6+, go
├── game/index.json · game/{game_id}.json   versions, langues, Pokédex régionaux, CT
├── game/{game_id}/pokedex.json             ordre régional + hors dex
├── location/{game_id}.json                 lieux du jeu + rencontres
├── go/{moves,pokemon,raids,cpm}.json
├── raid/{game_id}.json
├── map/{game_id}.json                      liens vers les cartes + coordonnées des lieux
├── search/{lang}.json                      index de recherche prêts : nom normalisé → entité (par langue)
└── download.json                           lien vers le dernier pokedata-<version>.sqlite(.gz) en Release
```

- Le `.sqlite` est publié en **pièce jointe de Release GitHub**, et non dans Pages : la limite est de 2 Go par fichier contre 100 Mo dans git, et le dépôt reste léger.
- `download.json` et `index.json` pointent vers la dernière version.
- Les fichiers de données ne contiennent pas la version : seul `index.json` la porte. Une mise à jour ne modifie ainsi que les fichiers réellement changés, ce qui préserve le cache du service worker du Pokédex.

## 9. Versionnement

- **API** : `/api/v1/` est figée pour sa structure. On n'y fait que des ajouts : nouveaux champs, nouveaux fichiers. Un changement cassant crée `/api/v2/`, et `/api/v1/` reste servie au moins 6 mois.
- **Schéma** : SemVer (`1.0.0`), dans `meta.schema_version`. Toute modification passe par `db/migrations/` et demande un accord (c'est un changement de structure).
- **Données** : version calendaire `AAAA.MM.JJ` (`.n` si plusieurs publications le même jour), avec un tag git `data-AAAA.MM.JJ` et une Release qui contient le `.sqlite`.

## 10. Rythme

- **Chaque semaine** (routine) : `fetch` des sources dont l'empreinte change, recroisement des seules données touchées, publication automatique des ajouts et corrections vérifiés, entrée dans le journal.
- **À chaque sortie** (jeu, DLC, grosse mise à jour, nouveau GAME_MASTER GO avec changement d'équilibrage) : passage `release` dès que les extractions ou les wikis sont à jour. Les gros ajouts (nouveau jeu complet) attendent un accord avant publication.
- **Surveillance** : notes de patch officielles, dépôt GAME_MASTER, journaux de modifications récents des wikis (pages suivies).

## 11. Langues

10 langues officielles : `ja`, `en`, `fr`, `de`, `it`, `es` (Espagne), `es-419` (Amérique latine), `ko`, `zh-Hans`, `zh-Hant`.
Plus deux écritures auxiliaires non officielles :
- `ja-Jpan` : mode kanji des jeux ;
- `ja-Latn` : rōmaji, utilisé par la recherche du Pokédex.

La table `game_language` indique les langues réellement jouables dans chaque jeu. Par exemple, GO n'a pas le chinois simplifié et les vieux jeux n'ont pas le coréen. Un texte n'est donc attendu que là où il existe.

### Espagnol d'Amérique latine : liste vérifiée (au 25/11/2026)

Dans le périmètre (série principale, Légendes, GO, HOME, Champions), seuls ces jeux ont l'espagnol d'Amérique latine comme langue de jeu :

| Jeu | Depuis | Sources |
|---|---|---|
| **Pokémon GO** | v0.305.0 : déploiement à partir du 18 mars 2024 (Mexique), puis le 19 avril 2024 partout ; annonce officielle en mai 2024 | Bulbapedia, « Pokémon in Latin America » et « Pokémon GO » (langues : « Latin American Spanish since May 2024 ») |
| **Légendes Pokémon : Z-A** (Switch et Switch 2) | sortie, 16 oct. 2025 — premier jeu de la série principale avec cette traduction | Communiqué TPCi du 27/02/2025 (press.pokemon.com) ; pokemon.com/el (« el primer título… en español latinoamericano ») ; boutique Nintendo Mexique (`supportedLanguages` : « Latin American Spanish ») ; Bulbapedia |
| **Z-A : Méga-Dimension** (DLC) | 10 déc. 2025 | Hérite des langues de Z-A (contenu additionnel du même jeu). Non vu explicitement sur une fiche : à confirmer à l'extraction des textes. |
| **Pokémon Champions** (Switch, iOS, Android) | sortie : 8 avr. 2026 sur Switch (7 avr. en Amérique), 17 juin 2026 sur mobile | Communiqué TPCi du 27/02/2025 ; Bulbapedia (« playable in ten languages… European and Latin American Spanish ») ; boutique Nintendo Mexique |
| **Pokémon HOME** | version 4.0.0, 2 avr. 2026 | Bulbapedia, « Pokémon HOME » (notes de version : « Compatibility with Latin American Spanish ») ; boutique Nintendo Mexique |

N'ont **pas** l'espagnol d'Amérique latine :
- Écarlate/Violet et ses DLC, Légendes Arceus : la boutique Nintendo liste 9 langues sans lui ;
- Diamant Étincelant/Perle Scintillante, Épée/Bouclier, Let's Go et tous les jeux plus anciens ;
- Rouge Feu/Vert Feuille sur Switch (2026) : ce sont les ROM GBA d'origine, vendues par langue (japonais, anglais, français, espagnol d'Espagne, allemand, italien ; tableau Bulbapedia).

Hors périmètre, pour information : Pokémon UNITE ne l'a pas (Bulbapedia) ; TCG Pocket est exclu.
PokeAPI a désormais un code de langue `es-419`, utilisable comme amorce, mais pas comme preuve.

URL consultées :
- https://press.pokemon.com/en/POKEMON-EXPANDS-ENTERTAINMENT-OFFERINGS-WITH-NEW-WAYS-TO-PLAY-IN-THE-P
- https://www.pokemon.com/el/videojuegos-pokemon/leyendas-pokemon-z-a
- https://www.nintendo.com/es-mx/store/products/pokemon-legends-z-a-switch/ · …/pokemon-champions-switch/ · …/pokemon-home-switch/ · …/pokemon-scarlet-switch/ · …/pokemon-legends-arceus-switch/
- https://bulbapedia.bulbagarden.net/wiki/Pokémon_in_Latin_America · /wiki/Pokémon_HOME · /wiki/Pokémon_Champions · /wiki/Pokémon_GO · /wiki/Pokémon_FireRed_and_LeafGreen_Versions

## 12. Cartes

- `game_map` : une ligne par carte de référence et par site source. On stocke l'URL de la page (pas l'image), les dimensions de référence et le système de coordonnées.
- `map_position` : un point (x, y) ou un polygone par lieu ou sous-zone, mesuré sur la carte de référence.
  - Ainsi, le Pokédex pourra plus tard afficher la carte depuis le site source (lien) ou une carte qu'il dessine lui-même.
  - Les coordonnées restent valables tant que la carte source ne change pas : son empreinte est suivie comme toute autre source.

## 13. Migration du Pokédex : points de correspondance

Analyse de `/workspace/pokedex/docs/data` (v60.40). Le schéma réutilise ses identifiants pour que la bascule se fasse sans table de traduction lourde.

| Pokédex actuel | Contenu | Correspondance pokedata |
|---|---|---|
| `core.e[].id`, `sp/{id}.json` | n° national | `species.id` (identique) |
| `core.e[].k` (`6`, `6-mega-x`, `3-female`, `25-partner-cap`, `3-gmax`) | clé de forme | `form.id` (identique) ; `e[].c` → `form.category` ; `e[].mb` → `form.base_form_id` |
| `core.mg` (`414-sandy` → `414`) | formes cosmétiques regroupées | `form.base_form_id` + `category='cosmetic'` |
| `e[].hs` / `e[].as` (ex. `10034`, `female/3`) | id PokeAPI / chemin du sprite HOME | `form.pokeapi_pokemon_id` ; chemin sprite → `external_id` (system `home-sprite`), aucune image stockée |
| `e[].n`, `en`, `ja`, `ro` | noms FR, EN, JA, rōmaji | `translation` (`fr`, `en`, `ja`, `ja-Latn`) ; `v_species_names` donne le même format à plat |
| `core.types` (`fire`…), `core.charts["1"…]` | types et tables d'efficacité par époque | `type.id` (identique) ; `type_chart` + `type_efficacy` |
| `core.games[].id` (`frlgsw`, `zadlc`, `za`, `svdisk`, `svmask`, `sv`, `la`, `bdsp`, … `rb`) | 28 jeux et DLC cumulatifs | `game.id` (identique) ; `base` → `game.base_game_id` ; `k` → `game.kind` ; `mv` → `game.pokeapi_version_group` ; on ajoute `go`, `home`, `champions` |
| `games[].ver` (`[40,"Écarlate"]`…) | ids PokeAPI des versions (1–53, y compris 50–53 pour les DLC Bouclier/Violet) | `version.pokeapi_id` |
| Listes « Méga-Dex Z-A », « Hors dex É/V », « Hors dex É/B » | listes calculées | non stockées comme jeux : dérivées de `availability` (`in_regional_dex = 0`) et de `form.category='mega'` |
| `dex/{game}.json` (`[espèce, forme, n°]`), `games[].dx` | Pokédex régionaux | `pokedex` + `pokedex_entry` |
| `sp.f[forme].ps` / `pa` / `av` | stats et talents passés, jeux de présence | `form_game` (une ligne par jeu) + `form_ability` |
| `moves.json` (clés 1–919) | capacités : nom FR, type, classe, puissance, précision, PP | `move.id` (identique) + `move_game` ; `desc.json.m` → `translation` (`flavor`) |
| `ref.ab`, `ref.it`, `ref.eg` | talents, objets (ids PokeAPI), groupes Œuf | `ability.id`, `item.id` (identiques), `egg_group.id` (`monster`, `water1`…) |
| `tm.json` (`{"4":"CT108"}` par jeu) | CT par jeu | `machine` (`label` neutre `TM108`, nom localisé dans `translation`) |
| `learn-index.json`, `sp.f.ls` | movesets par jeu | `learnset` (forme, jeu, capacité, méthode, niveau) |
| `evo.json`, `core.chains` | évolutions et variantes par jeu | `evolution` + `evolution_method` (par jeu) ; `evolution_chain.id` = PokeAPI |
| `loc.json` (`a` = noms de lieux FR, `m` = méthodes, `c` = conditions), `sp.f.en` | rencontres | `location` / `location_area` à **slugs stables** (le Pokédex utilise des noms FR, avec des doublons comme « Route 3 ») ; `encounter_method`, `encounter_condition` ; correspondance ancien nom → slug dans `external_id` (system `pokedex-legacy`). **Principal travail de migration.** |
| `loc-index.json`, `learn-index.json` | index inversés pour les filtres | à générer depuis l'API (`search/`, `location/{game}.json`) |
| `sp.pln`, `trade.json` | comment l'obtenir, exclusivités de version | `availability` (`status` + `detail` traduit) |
| `shiny.json` | taux et méthodes de chromatique par jeu, verrous | `shiny_rule`, `shiny_lock` |
| `sp.f.go` (`a/d/s`, `fm/cm`, `fe/ce`, `th`, `shm/pum`, `sh`), `e[].go`, `e[].dmx` | données GO | `go_pokemon`, `go_learnset` (`fe`/`ce` → `elite`), `go_release` (dont `dynamax` à la date `dmx`) |
| `go.json.moves` (`FIRE_SPIN_FAST`…), `pvp-moves.json` | attaques GO PvE et PvP | `go_move.id` (identique) + `go_move_stats` (datée) |
| `costumes.json` (`1-fall2019`…) | costumes GO | `form` (`category='go-costume'`, même id) + `go_costume` ; les URL d'images restent côté Pokédex |
| `shadow.json`, `raid-bosses.json`, `boss-schedule.json`, `mega-energy.json` | Obscur, boss, calendrier, énergie Méga | `go_release`, `raid_boss`, `go_pokemon.extra` |
| `raids.json`, `tera7.json`, `gmax-moves.json` | raids Dynamax et Téracristal | `raid_tier`, `raid_boss`, `move.kind='gmax'` |
| `mega-stones.json` | Méga-Gemmes | `item` (`category='mega-stone'`) + lien vers la forme méga dans `evolution_method` (`conditions`) |
| `sp.ft`, `sp.fv`, `sp.gn` | entrées du Pokédex FR par version, catégorie | `translation` (`flavor`, par `version_id` ; `genus`) |
| `sp.ety`, `sp.evd`, notes de wiki | étymologies et distributions (prose Poképédia) | **hors base** (décision du 25/11/2026) : restent côté Pokédex |
| `rank-*.json`, `pvp.json`, `sim.js` | classements et simulations | restent dans le Pokédex (calculs) |
| `pocket.json`, `cries/`, `img/` | TCG Pocket, cris, images | hors périmètre (TCG Pocket exclu, aucun média) |

Les champs compacts du Pokédex (`gb`, `zb`, `gbk`, bitmasks…) seront recalculés au moment de l'import côté Pokédex, à partir de l'API.

## 14. Décisions prises (25/11/2026)

1. **Identifiants publics de l'API (figés pour toute la v1).**
   - Proposition : garder les clés du Pokédex actuel. Ce sont des n° pour les espèces (`pokemon/25.json`) et `n°-suffixe` pour les formes (`form/6-mega-x.json`), et les slugs courts du Pokédex pour les jeux (`sv`, `za`, `zadlc`).
   - Avantages : migration directe, URL courtes. Inconvénient : moins lisibles que des slugs anglais (`charizard-mega-x`), qui restent disponibles en alias dans `external_id` et dans les fichiers.
   - **Retenu (option A).** Les slugs anglais sont fournis en alias (`aliases` dans les fichiers, `external_id` dans la base).
2. **Prose des wikis (étymologies, notes de distribution).**
   - **Retenu : hors de la base.** Aucune table ne leur est consacrée ; `translation` ne contient que des textes de jeu. Le Pokédex garde ses étymologies de son côté.

Autres choix pris par défaut (modifiables) :
- tous les jeux dès chaque phase ;
- `.sqlite` en Release ;
- API non commitée ;
- rōmaji et kanji comme écritures auxiliaires.

## 15. Licence

- Code (scripts, schéma) : **MIT**.
- Données : projet de fans non officiel. Les noms, textes et données de jeu appartiennent à **Nintendo, Creatures Inc., GAME FREAK inc. et The Pokémon Company**. Cette mention figure dans `NOTICE.md`, `README.md`, `api/v1/index.json` et `meta` de la base.
- Les sources consultées sont créditées dans `meta/sources.json`. Aucune image, aucun son, aucune carte n'est copié.

## 16. Phase 1 : règles appliquées et reports

Règles précisées pendant l'implémentation (sans changement de structure) :
- **Entrée propre** : une forme sans entrée propre dans la table d'un jeu (elle partage celle de la forme de base) n'a pas de ligne pour ce jeu, sauf forme purement cosmétique ou forme par défaut de l'espèce.
- **Formes cosmétiques non énumérées par le jeu** (lettres de Zarbi avant la génération 5, formes femelles, combinaisons de Charmilly) : elles reprennent les données de la forme par défaut dans chaque jeu de leur génération d'introduction ou après, où l'espèce a des données (`extra.derived_from`).
- **Talents** : aucun talent dans Let's Go, Légendes Arceus et Légendes Z-A (le jeu n'en a pas ; les valeurs du fichier sont factices). Talent caché ignoré quand il est identique au talent 1 ou 2.
- **DLC** : les lignes des DLC (`swisle`, `swcrown`, `svmask`, `svdisk`, `zadlc`) et de `frlgsw` sont copiées du dernier patch du jeu de base (`extra.derived_from`) ; la distinction « présent dès le jeu de base / ajouté par le DLC » relève de la disponibilité (phase 3).
- **Gigamax** : copie des données de la forme de base dans Épée/Bouclier et ses DLC.
- **Générations 1–2** : types via la table interne des jeux GB ; EV absents avant la génération 3, bonheur absent en génération 1.
- **Deoxys** : Rouge Feu = Attaque, Vert Feuille = Défense, Émeraude = Vitesse (tables propres à chaque version).
- **Ids de talents** : numérotation Pokédex/PokeAPI ; les 4 variantes « Embody Aspect » du jeu sont fusionnées sous l'id 303 ; index du jeu dans `external_id`.
- **Nouvelles formes (données, pas structure)** : téracristal d'Ogerpon (`1017-*-tera`) et Seigneurs/Dames de Légendes Arceus (`59-lord`, `101-lord`, `549-lady`, `713-lord`, `900-lord`, catégorie `totem`).

Reporté :
- formes propres à GO (Mewtwo armuré, costumes) → phase 4 ; aucune ligne `form_game` pour Champions, HOME et GO (pas d'extraction de rang 1) ;
- noms des formes en 10 langues (seule une source de rang 3 existe) ;
- évolutions et Pokédex régionaux → phase 1b ; catégories (genus) et descriptions de talents → phase 1b ;
- types des formes de combat sans entrée propre dans les anciens jeux (Morphéo en génération 3, Ceriflor en génération 4, Silvallié en génération 7) ;
- forme « Légende » d'Arceus dans Légendes Arceus (non associée à une forme connue) ;
- tables des types → phase 5.

## 17. Phase 1b : règles appliquées et reports

Même structure (schéma 1.0.0), mêmes règles de vérification. Précisions :
- **Évolutions** : méthodes lues dans les arbres d'évolution des jeux (PKHeX, rang 1) par contexte de jeu, appliquées à chaque jeu du contexte où les deux formes ont une ligne `form_game` ; DLC et `frlgsw` reprennent leur jeu de base. Une ligne `evolution_method` par jeu et par variante. Les identifiants `evolution.id` sont stables d'une mise à jour à l'autre (relus dans `evolution.csv`).
  Correspondances : amitié → `conditions.high_friendship` ; lieux (pierre mousse, pierre glacée, champ magnétique, mont Lanakila…) → `conditions.location` (pas de table des lieux avant la phase 3) ; capacité connue → `conditions.known_move` jusqu'à la phase 2 (la table `move` n'existe pas encore), puis `known_move_id` ; Pancham → `conditions.party_type = dark`.
  Contrôle croisé pour Écarlate/Violet avec PokeAPI et Showdown sur une signature simplifiée (déclencheur, niveau, objet) ; les écarts sont notés, la donnée du jeu est retenue.
- **Chaînes** : familles reconstituées depuis les évolutions des jeux ; identifiant = chaîne PokeAPI. Phione/Manaphy et Meltan/Melmetal (évolution GO seulement) : deux familles dans les jeux pour une chaîne PokeAPI, écart noté.
- **Objets** : seuls les objets utilisés par les évolutions sont importés en 1b (id PokeAPI, correspondance par nom anglais du jeu, index du jeu dans `external_id`, noms en 10 langues).
- **Pokédex régionaux** : identifiants `{jeu}-{pokédex}` ; numéros = PKHeX (Épée/Bouclier et DLC, DEPS, Légendes Arceus, Écarlate/Violet et DLC) + PokeAPI + Bulbapedia ; un index 0 dans les tables du jeu signifie « pas de donnée », pas « absent ». Pour Légendes Z-A, l'index des tables (`DexIndex`) se répète entre espèces hors Pokédex : il n'est pas utilisé, les numéros viennent de PokeAPI + Bulbapedia (concordants). Les îles d'Alola ont chacune leur Pokédex.
- **Catégories** : texte complet de PokeAPI (« Pokémon Souris »), contrôlé contre la liste Bulbapedia (mot seul) après retrait de « Pokémon » / ポケモン / 포켓몬 / 寶可夢 / 宝可梦 ; en allemand, la terminaison de composition est ignorée (Drache ↔ Drachen-Pokémon). Le mot de la liste n'est jamais stocké. Les écarts (anciens noms marqués d'un astérisque, coquilles) sont notés et la catégorie n'est pas publiée.
- **Noms de formes** : publiés seulement quand le libellé PKHeX et le nom PokeAPI sont identiques (après normalisation NFKC). Les libellés PKHeX sont souvent abrégés (« Alola » contre « Forme d'Alola ») : la plupart des langues latines ne sont donc pas publiées.

Reporté :
- Pokédex de `frlgsw` (Kanto à 150 entrées dans le Pokédex actuel) et de Champions ;
- catégories en espagnol d'Amérique latine (pas de seconde source) ;
- noms de formes non concordants (≈ 2 750 couples forme × langue ; ≈ 1 200 publiés, surtout japonais, coréen et chinois) ;
- objets hors évolutions, objet d'incubation des bébés (`evolution_chain.baby_item_id`).

## 18. Phase 2 : règles appliquées, reports et décision en attente

Même structure (schéma 1.0.0). Précisions :
- **Capacités** : id = index du jeu (= PokeAPI) ; génération = premier contexte de jeu où la capacité existe (PKHeX, concordant avec PokeAPI) ; `kind` z / max / gmax d'après Showdown. Noms : PKHeX (rang 1) + PokeAPI, suffixes « (P) / (S) » des capacités Z retirés.
- **Valeurs par jeu** (`move_game`), vérifiées par groupes de colonnes :
  - `type_pp` (type, PP) et `is_usable` (capacités retirées) : tables des jeux (PKHeX, rang 1), autres sources citées ;
  - `power` (catégorie, puissance, précision) : Serebii (rang 2, une page par génération), Poképédia (rang 2, valeurs actuelles = Écarlate/Violet), PokeAPI (valeurs actuelles corrigées par `move_changelog`), Showdown (mod du jeu). La ligne n'est publiée que si ce groupe est vérifié ;
  - `priority` : tableau de Bulbapedia par génération (rang 2) + Poképédia + PokeAPI + Showdown ;
  - générations 1 à 3 : la catégorie physique/spéciale dépend du type (statut d'après PokeAPI/Showdown) ; seuls puissance et précision sont comparés. Précisions de la génération 1 en x/256 arrondies (74,6 → 75) ; « 100 » des pages Serebii 1–3 pour une capacité sans test de précision lu comme « — » quand la page de la génération 4 l'indique ;
  - puissance variable ou dégâts fixes = NULL ; `target`, `makes_contact`, `flags`, `effect_chance` laissés vides (seules des sources de rang 3 existent).
- **CT / CS / DT** : listes des jeux (PKHeX) contrôlées par PokeAPI ; libellés à 3 chiffres pour Écarlate/Violet et Légendes Z-A (`TM001`) ; la liste de PKHeX pour Écarlate/Violet commence par un emplacement inutilisé (TM000), ignoré. Légendes Z-A : les 160 CT de la version à jour (DLC compris) sont rattachées à `za`. `item_id` laissé vide (objets CT non importés).
- **Descriptions de jeu** : anglais (PokeAPI + Serebii) et français (PokeAPI + Poképédia, jeux Switch) publiées par jeu seulement si les deux textes sont identiques ; pas de description dans les jeux de génération 1.
- **Évolutions** : `known_move_id` est rempli à partir de cette phase (au lieu de `conditions.known_move`).

Reporté :
- valeurs par jeu pour Let's Go, DEPS, Légendes Arceus et Légendes Z-A (aucune source de rang 2 lue ; PKHeX ne donne que type et PP) ;
- ≈ 160 lignes capacité × jeu où les sources ne concordent pas (dégâts fixes affichés comme puissance, « 100 » contre « — », capacités Z) ;
- descriptions dans les 8 autres langues (une seule source de rang 3, PKHeX n'expose pas ces textes) ;
- `target`, contact, drapeaux, probabilité d'effet ; objets CT.

**Movesets : calculés, non publiés — changement de structure à valider.** L'extraction des jeux donne ≈ 614 000 lignes `learnset` (≈ 14 Mo en CSV, 32 000 ensembles forme × jeu × méthode). Avec la règle actuelle (une ligne de `verification` par ligne de données, citations par source), il faudrait ≈ 125 Mo de `verification.csv` et ≈ 100–150 Mo de `citation.csv`, au-delà de la limite de 100 Mo par fichier de GitHub ; après la phase 2, `verification.csv` fait déjà ≈ 36 Mo et `citation.csv` ≈ 33 Mo (alerte GitHub à 50 Mo). Options :
- **A (recommandée)** : vérification par ensemble — `row_key` = `[form_id, game_id, method_id]`, `column_name = '*'`, `value_sha256` = empreinte de la liste triée (capacité, niveau) ; citations au même niveau avec l'empreinte de l'ensemble observé par chaque source ; les écarts détaillés (capacités en plus ou en moins) dans `discrepancy.alternatives`. ≈ 32 000 vérifications (+7 Mo) et ≈ 100 000 citations (+15 Mo).
- **B** : découper les CSV de provenance par table (`db/data/verification/{table}.csv`, idem pour `citation`) — nécessaire aussi avec A à moyen terme pour rester sous 50 Mo par fichier.
- **C** : garder la provenance des movesets hors du dépôt (seulement dans la base SQLite de la Release).
Proposition : A + B. Défauts connus de l'extraction à corriger avant publication : tuteurs des générations 3 (Émeraude), 6 et 7 non lus (API non publique de PKHeX), DT d'Épée/Bouclier sous-comptés.
