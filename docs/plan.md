# pokedata — plan de projet

Base de données Pokémon indépendante et réutilisable, qui deviendra aussi la source unique et vérifiée du Pokédex (sigjouea.github.io/pokedex).
Statut : **validé le 25/11/2026** (plan et schéma 1.0.0) ; schéma **1.1.0** validé le 26/11/2026 (options A + B de la section 18, migration 0002) ; schéma **1.2.0** validé le 26/11/2026 (statut de disponibilité `npc-trade`, migration 0003, section 21). Décisions prises : identifiants du Pokédex dans les adresses de l'API, alias lisibles en plus (option A) ; textes rédigés par les wikis **exclus** de la base. Phase 1 publiée (section 16), phase 1b publiée (section 17), phase 2 publiée sans les movesets (section 18), movesets publiés en phase 2b (section 19).

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

- Une ligne de `verification` par ligne de données (ou par groupe de colonnes), sauf `learnset` (schéma 1.1.0) : une ligne par ensemble forme × jeu × méthode (section 19).
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
│   └── data/               une table = un CSV trié (source de vérité des données) ;
│                           verification/ et citation/ : un CSV par table décrite (schéma 1.1.0)
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

## 18. Phase 2 : règles appliquées, reports et décision sur les movesets

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

**Movesets : décision prise le 26/11/2026 — options A + B retenues, publiés en phase 2b (section 19).** Constat d'origine : L'extraction des jeux donne ≈ 614 000 lignes `learnset` (≈ 14 Mo en CSV, 32 000 ensembles forme × jeu × méthode). Avec la règle actuelle (une ligne de `verification` par ligne de données, citations par source), il faudrait ≈ 125 Mo de `verification.csv` et ≈ 100–150 Mo de `citation.csv`, au-delà de la limite de 100 Mo par fichier de GitHub ; après la phase 2, `verification.csv` fait déjà ≈ 36 Mo et `citation.csv` ≈ 33 Mo (alerte GitHub à 50 Mo). Options :
- **A (recommandée)** : vérification par ensemble — `row_key` = `[form_id, game_id, method_id]`, `column_name = '*'`, `value_sha256` = empreinte de la liste triée (capacité, niveau) ; citations au même niveau avec l'empreinte de l'ensemble observé par chaque source ; les écarts détaillés (capacités en plus ou en moins) dans `discrepancy.alternatives`. ≈ 32 000 vérifications (+7 Mo) et ≈ 100 000 citations (+15 Mo).
- **B** : découper les CSV de provenance par table (`db/data/verification/{table}.csv`, idem pour `citation`) — nécessaire aussi avec A à moyen terme pour rester sous 50 Mo par fichier.
- **C** : garder la provenance des movesets hors du dépôt (seulement dans la base SQLite de la Release).
Proposition : A + B. Défauts connus de l'extraction à corriger avant publication : tuteurs des générations 3 (Émeraude), 6 et 7 non lus (API non publique de PKHeX), DT d'Épée/Bouclier sous-comptés.

## 19. Phase 2b : movesets (schéma 1.1.0)

Changement de structure validé (options A + B de la section 18), migration `db/migrations/0002_learnset_set_verification.sql` : aucune table ni colonne modifiée ; seules changent les conventions suivantes et la version du schéma (1.1.0).
- **A — vérification par ensemble** pour `learnset` : `row_key` = `[form_id, game_id, method_id]`, `column_name = '*'`, `value_sha256` = sha256 de la liste triée `[move_id, level, version_id]`. Une citation par document : `observed_value` = `{"n": taille, "sha256": empreinte de l'ensemble lu}`. Les capacités en plus / en moins d'une source sont dans `discrepancy.alternatives` (`missing` = dans les données du jeu mais pas dans la source, `extra` = l'inverse).
- **B — provenance découpée par table** : `db/data/verification/{table}.csv` et `db/data/citation/{table}.csv` (contenu et ids inchangés par rapport aux fichiers uniques de la version 1.0.0). Les autres CSV restent un fichier par table.
- Les ids de `source_document`, `citation` et `discrepancy` déjà publiés sont conservés d'une version à l'autre (un document identique — même source, adresse et empreinte — garde son id et sa date de lecture) ; les nouvelles lignes prennent les ids suivants.

Règles appliquées :
- **Données** : extraction des jeux (PKHeX, rang 1) pour les 22 jeux de Rouge/Bleu à Légendes Z-A, DLC inclus (rangées sous le jeu de base, comme les valeurs par jeu). Méthodes : `level-up` (niveau ; 0 = à l'évolution ; attaques de départ de la génération 1 au niveau 1), `egg`, `machine` (CT, CS, DT), `tutor`, `reminder` (Écarlate/Violet), `mastery` (Légendes Arceus, niveau de maîtrise dans `level`), `plus` (Légendes Z-A, niveau dans `level`). `sort_order` = ordre des données du jeu au même niveau. `version_id` rempli quand une capacité n'existe que dans une version (Deoxys dans Rouge Feu / Vert Feuille).
- **Corrections de l'extraction** (avant publication) : DT d'Épée/Bouclier lues dans leur propre table (elles étaient lues dans les drapeaux des CT) ; CS de la génération 4 ; tuteurs de Cristal, Émeraude, Rouge Feu / Vert Feuille (les 15 tuteurs communs avec Émeraude + attaques ultimes), Diamant/Perle (tuteurs spéciaux), Platine (38 premiers tuteurs de la table commune avec HeartGold/SoulSilver, d'après l'ordre des données), HeartGold/SoulSilver (+ tuteurs spéciaux), Noir 2/Blanc 2, X/Y, Rubis Oméga/Saphir Alpha, Soleil/Lune et Ultra-Soleil/Ultra-Lune (tuteurs de type et spéciaux de PKHeX). Rubis/Saphir n'ont pas de tuteur (les tuteurs Colosseum/XD de PKHeX sont exclus).
- **Contrôles** : PokeAPI (`pokemon_moves.csv`, groupes de versions du jeu et de ses DLC ; maîtrise et Plus = `enhancement_level`) pour toutes les formes que PokeAPI a dans le jeu ; Showdown pour machine, tuteur et œuf seulement, et seulement là où ses données sont propres au jeu (Écarlate/Violet, Épée/Bouclier, DEPS, Légendes Arceus, Let's Go, Légendes Z-A) — ses listes par génération fusionnent les versions et ses niveaux mélangent les jeux d'une génération.
- Statut `game-data` pour chaque ensemble ; les écarts des sources de contrôle sont notés (`reports/compare-learnsets.md`).

Reporté :
- capacités apprises au changement de forme (Motisma, méthode `form-change`), capacités signature enseignées par des personnages (Lame Sainte de Keldeo, Chant Antique de Meloetta en Noir/Blanc et Noir 2/Blanc 2) ;
- movesets des variantes cosmétiques sans entrée propre dans les données du jeu (bonbons de Charmilly…) : le moveset est sur la forme de l'entrée du jeu ;
- écarts à examiner : tuteur Blabla Dodo (Sleep Talk) de Rubis Oméga/Saphir Alpha donné par PKHeX mais pas par PokeAPI ni Showdown (843 ensembles) ; capacités au niveau 0 de Légendes Z-A absentes de PokeAPI (117 ensembles) ; Aires d'Eau/de Feu de Silvallié dans Épée/Bouclier (PokeAPI).


## 20. Phase 3, lot 1 : lieux, rencontres, disponibilité, chromatiques (générations 1 et 2)

Aucune table ni colonne modifiée (schéma 1.1.0). La vérification par ensemble (convention A de la section 19) est appliquée à `encounter` : `row_key` = `[area_id, version_id, method_id]`, empreinte de la liste triée `[form_id, min_level, max_level, condition, shiny_locked, extra]` ; PokeAPI est cité avec l'empreinte de son ensemble projeté sur (forme, niveau min, niveau max, condition d'heure) et ses écarts sont notés (`missing` / `extra`). Provenance découpée par table (convention B).

Règles appliquées :
- **Lieux** : identifiants PokeAPI (`kanto-route-3`, `hoenn-route-3` : deux lieux distincts), une zone par lieu (`location_area.id` = `location.id`) dans ce lot. Noms de jeu par jeu pour Or/Argent et Cristal (textes du jeu extraits par PKHeX, contrôlés par PokeAPI), dans les langues de `game_language` ; nom générique (`game_id` vide) tiré du jeu le plus récent qui contient le lieu (HeartGold/SoulSilver, Rouge Feu/Vert Feuille, Or/Argent) dans les langues de ce jeu. Rouge/Bleu/Jaune n'ayant pas de texte de lieu extractible, ils utilisent ces noms génériques.
- **Ancien nom du Pokédex** : `external_id` système `pokedex-legacy` (liste JSON), rattaché par nom français identique dans le jeu, sinon par co-présence des Pokémon (au moins 3 Pokémon, 80 % d'entre eux trouvés au même lieu unique dans nos rencontres). Les noms homonymes (« Route 3 ») sont rattachés dans le contexte du jeu.
- **Rencontres sauvages** : tables extraites des jeux (PKHeX). Génération 2 : lieu = id de lieu de PKHeX ↔ index de jeu PokeAPI, sauf le Surf d'Or/Argent (ces jeux ne stockent pas le lieu de capture ; les tables de Surf de PKHeX y sont décalées d'un lieu — Cristal concorde avec PokeAPI et Bulbapedia) : chaque table est placée là où PokeAPI a une table identique. Génération 1 : numéro de table PKHeX ↔ lieu PokeAPI par tables identiques puis élimination ; Canne et Super Canne de la génération 1 (une table pour tout le jeu) placées à chaque point de pêche que PokeAPI connaît. Heure (Or/Argent/Cristal) : une ligne sans condition si les trois moments concordent, sinon `time-morning` / `time-day` / `time-night`. Coup d'Boule rare/fréquent fusionnés en `headbutt`. Taux (`rate_pct`) laissés vides.
- **Rencontres fixes, cadeaux, œufs, échanges** : les modèles de PKHeX pour ces générations sont des modèles de légalité aux versions fusionnées (un lot « RBY » pour un lot propre à Rouge) : une version n'est retenue que si PokeAPI y a le Pokémon avec une méthode de cadeau / rencontre fixe / échange ; méthode (gift, static, gift-egg) selon PokeAPI ; niveau selon PKHeX ; lieu : celui de PKHeX en génération 2 s'il concorde avec PokeAPI, sinon le lieu commun à PokeAPI et Bulbapedia (« In-game trade », « Gift Pokémon »), sinon disponibilité seule. Échanges : Pokémon demandé (`extra.gives_species_id`) quand Bulbapedia et PokeAPI concordent. Pokémon errants : disponibilité seule.
- **Disponibilité** (par forme et version) : `wild`, `gift` (`detail` : `gift-egg`), `npc-trade` (échange en jeu, schéma 1.2.0 ; avant : `gift` + `detail = npc-trade`), `evolve` (une pré-évolution est obtenable), `breed` (premier stade d'une famille dont un membre obtenable peut se reproduire), `trade-version-exclusive` (autre version du jeu, ou autre jeu de la génération : `detail` = `from:rb`…), `transfer` (Capsule Temporelle entre générations 1 et 2, espèces 1–151 : `detail` = `time-capsule:gs,c`…), `event` (distributions GB de PKHeX, par version quand PKHeX la précise), `unobtainable`. Zarbi : toutes les lettres partagent la disponibilité de la forme par défaut (lettre tirée à chaque rencontre).
- **Chromatiques** : règles (`shiny_rule`) en `manual` quand Bulbapedia (« Shiny Pokémon ») et Poképédia (« Pokémon chromatique ») donnent le même taux : Or/Argent/Cristal 1/8192, 1/64 avec un parent chromatique. Rencontres au chromatique imposé par le jeu : `encounter.extra.shiny = "always"` (Léviator du Lac Colère). Verrous (`shiny_lock`) : aucun dans ce lot (chaque Pokémon a un moyen chromatique : sauvage, reproduction ou Capsule Temporelle).
- **DLC** : sans objet pour ce lot.

Reporté (lot 1) :
- Bleu japonais (`blue-japan`) : PokeAPI n'a pas ses tables sauvages et PKHeX n'en garde qu'une partie : version laissée hors de ce lot.
- Taux d'apparition et sous-zones (étages, intérieur / extérieur) : PokeAPI seul les fournit (rang 3) ; à reprendre avec une deuxième source (pages de lieux Bulbapedia).
- Tables sans correspondance : Route 4 de la génération 1, Surf d'Or/Argent sans table identique dans PokeAPI (78 lignes de tables), 66 lignes de tables de la génération 1 ; prix du Casino et cadeaux sans lieu commun aux deux sources (disponibilité seule) ; lots de Porygon et d'autres prix écartés par PKHeX comme doublons de légalité.
- Œuf Bizarre de Cristal (14 % de chromatiques) : pas de règle publiée dans ce lot.
- ~~Statut de disponibilité propre aux échanges en jeu~~ : statut `npc-trade` ajouté par le schéma 1.2.0 (section 21), lignes reclassées.
- Raichu dans Jaune : corrigé au lot 2 (le Pikachu de départ refuse la Pierre Foudre → `trade-version-exclusive` `from:rb` et Capsule Temporelle).

## 21. Phase 3, lots 2 et suivants : générations 3 à 9, Légendes, DLC (schéma 1.2.0)

Changement de structure validé (26/11/2026), migration `db/migrations/0003_availability_npc_trade.sql` : `availability.status` accepte `npc-trade` (échange avec un personnage du jeu). Ajout seulement, API v1 compatible (une valeur d'énumération en plus) ; les lignes `gift` + `detail = npc-trade` du lot 1 sont reclassées (une ligne `npc-trade`, la ligne `gift` garde le reste de sa liste).

Publication par lots : lot 2 génération 3 (Rubis/Saphir, Émeraude, Rouge Feu/Vert Feuille), puis génération 4, 5, 6, 7 (+ Let's Go), 8 (Épée/Bouclier + DLC, DEPS, Légendes Arceus), 9 (Écarlate/Violet + DLC, Légendes Z-A + DLC).

Règles appliquées (générations 3 et suivantes, `scripts/phases/phase3_modern.py`) :
- **Lieux** : ces jeux enregistrent le lieu de rencontre ; l'id de lieu du jeu (liste de lieux du jeu extraite par PKHeX) fait foi. Identifiant : celui de PokeAPI quand PokeAPI a ce lieu au même index de jeu (nom proche dans la région du jeu ; plusieurs lieux PokeAPI au même index : celui que PokeAPI utilise pour ces versions), sinon par nom anglais identique, sinon un identifiant créé depuis le nom anglais du jeu (`pokeapi_id` vide, préfixe de région en cas d'homonymie). La provenance du placement est citée (`citation.observed_value.met` : liste, id, nom, méthode `pokeapi-index` / `pokeapi-name` / `created`). Un id dont le texte dépend de la version (index 66 de Rubis/Saphir : Planque Magma / Planque Aqua) est placé par version. Suffixes de PKHeX (« (1) », « (HG/SS) »…) retirés des noms.
- **Placement sans lieu enregistré** (échanges en jeu : le jeu note « échange » ; raids) : lieu commun à PokeAPI et Bulbapedia, noté `encounter.extra.placement = "pokeapi+bulbapedia"`, sinon disponibilité seule. Lot 1, même convention rétroactive : `extra.placement` = `table-match` (tables de la génération 1 et Surf d'Or/Argent placés par table identique), `pokeapi` (points de pêche de la génération 1), `pokeapi+bulbapedia` (cadeaux, fixes et échanges placés par les deux sources).
- **Rencontres** : méthodes du jeu (walk, surf, old-rod, good-rod, super-rod, rock-smash, headbutt, honey-tree, bug-contest, hidden-grotto, horde, friend-safari, sos, wild, overworld, fishing, berry-trees, distortion, outbreak, massive-outbreak, landmark, grand-underground, feebas-tile-fishing…), conditions : essaim (`swarm-yes`), météo (`weather-*`), moment (`time-*`) ; une dimension de condition disparaît quand toutes ses valeurs de l'ensemble donnent les mêmes niveaux. Comparaison avec PokeAPI par ensemble, sur (forme, niveau min, niveau max), méthodes regroupées par famille (variantes PokeAPI « dark-grass », « surf-spots »… ; générations 6–8 : toutes les rencontres sauvages ensemble). Alpha de Légendes : `is_alpha`.
- **Essaims de Noir/Blanc 1–2** : publiés avec la condition `swarm-yes` ; PokeAPI ne les a pas → laissés hors de la comparaison. Saisons de N/B : formes de Vivaldaim / Haydaim publiées selon le jeu (PokeAPI n'a que la forme par défaut).
- **Génération 6** : les tables « Standard » de PKHeX regroupent plusieurs méthodes, séparées par position dans la table (X/Y : herbes et fleurs, Surf, Éclate-Roc, cannes ; ROSA : herbes, Pokémon seulement visibles au PokéNav (`dexnav`), Surf, cannes) ; embuscades de X/Y : `ambush` (PokeAPI : ceiling-, ground-, sky-, trash-can-, rustling-bush-ambush). Les tables ROSA de PokeAPI sont incomplètes (Surf, cannes, nombreuses grottes absentes) : écarts `missing` sans valeur contraire.
- **Génération 7** : Soleil/Lune, USUL : rencontres « Standard » → `wild`, alliés appelés → `sos` ; PokeAPI réunit les deux et ne sépare pas les zones d'un même lieu → comparaison par famille entière (`wild` + `sos`), écarts dus aux sous-zones et aux niveaux. Lieux d'Ultra-Brèches (Ultra-Désert, Ultra-Jungle…) : identifiants créés depuis le nom du jeu (PokeAPI n'a qu'« ultra-space-wilds »). Sous-lieux PokeAPI (`hau-oli-city--shopping-district`) et routes maritimes (`kanto-sea-route-19`) reconnus par identifiant (`pokeapi-slug`). Let's Go : rencontres visibles → `wild`.
- **Génération 8** : Épée/Bouclier : les niveaux des rencontres de la Zone Sauvage et des DLC montent avec les badges (PKHeX et PokeAPI : jusqu'au niveau 60, bornes différentes) → comparaison avec PokeAPI sur les formes seulement pour ces jeux (rencontres fixes, cadeaux et échanges : niveaux comparés). Oiseaux légendaires de Galar : rencontrés dans des lieux du jeu de base mais après la quête de la Couronne Neigeuse → rangés sous la version DLC `the-crown-tundra-*`. DEPS et Légendes Arceus : PokeAPI n'a pas de rencontres pour ces jeux → données du jeu seules (sans comparaison) ; zones de Hisui et cavernes du Grand Souterrain : identifiants créés depuis le nom du jeu. « Mount Coronet » (DEPS) = `mt-coronet`.
- **Génération 9** : Écarlate/Violet et Légendes Z-A : PokeAPI n'a pas de rencontres pour ces jeux → données du jeu seules (sans comparaison avec PokeAPI) ; lieux de Paldea / Septentria repris de PokeAPI (index et nom), lieux de Z-A (zones sauvages, secteurs, Ultra-Dimension du DLC) créés depuis le nom anglais du jeu. Jeu de base / DLC par lieu (Septentria → Le Masque Turquoise, Myrtille → Le Disque Indigo, Ultra-Dimension → Méga-Dimension) ; exception : rencontres fixes placées dans des lieux du jeu de base ou de Septentria mais débloquées par Le Disque Indigo (légendaires d'Amaury, Feu-Perçant / Ire-Foudre / Roc-de-Fer / Chef-de-Fer, Pêchaminus) → version `the-indigo-disk-*`.
- **Accès par objet distribué** (tickets Éon / Aurora / Mystique / Vieille Carte, Carte Membre, Lettre du Prof, Flûte Azur, Pass Liberté : PKHeX marque ces rencontres « fateful » ; Île du Sud de Rubis/Saphir, Île Nouvellune, Ruines Sinjoh et Jardin Libertà ajoutés, non marqués par PKHeX) : rencontre publiée au lieu du jeu avec `extra.access = "event-item"`, disponibilité `event`.
- **Disponibilité** : `wild` (`detail` quand la seule voie sauvage est spéciale : `max-raid`, `tera-raid`, `roaming`, `dynamax-adventure`), `gift` (`detail` : `gift-egg`, `pokewalker`), `npc-trade`, `evolve`, `breed` (pas de reproduction dans Let's Go, Légendes Arceus, Légendes Z-A), `trade-version-exclusive` (autre version, ou jeu relié par échange : `from:` limité aux groupes R/B/J, O/A/C, Rubis/Saphir/Émeraude/RF/VF, Diamant/Perle/Platine/HG/SS, N/B/N2/B2, X/Y/ROSA, S/L/USUL), `transfer` (`detail` : `time-capsule:`, `pal-park:` (génération 4 ← 3), `poke-transfer:` (5 ← 4), `poke-bank:` (X/Y, ROSA ← 5–6 ; S/L, USUL ← 1, 2, 5–7), `home:` (Épée/Bouclier, DEPS, Légendes, Écarlate/Violet ← jeux reliés à HOME), sources transitives), `event`. Pas de mouvement du jeu vers lui-même.
- **DLC** : rencontres des lieux du DLC rangées sous la version DLC (`the-isle-of-armor-sword`…) ; la disponibilité d'une version DLC est celle du jeu avec le DLC (cumulative : jeu de base + DLC précédents + ce DLC). L'API ajoute `arrives_with` (jeu de base ou DLC qui apporte la forme) dans `pokemon/{id}/locations.json` pour chaque version DLC.
- **Évolution impossible** : le Pikachu de départ de Jaune (refuse la Pierre Foudre) ne compte pas pour `evolve` ; cas voisins vérifiés : Pikachu / Évoli partenaires de Let's Go, Pikachu Casquette et Pikachu Cosplay, Pichu Troizépi sont des formes à part sans évolution.
- **Événements des générations 4+** : base de cadeaux mystère de PKHeX (`EncounterEvent.MGDB_*`, extraite dans `events.json` par `scripts/fetch/pkhex_dumper`, argument `events`) : statut `event` pour chaque version des jeux de la génération de la carte (restreint aux versions que PKHeX nomme, Épée ou Bouclier pour les WC8 limités). Ranch Pokémon (DP) compté en `event`.
- **Changements de forme** (formes de combat, Motisma, capes de Cheniti, Shaymin Céleste…) : le schéma n'a pas de statut pour « obtenue en changeant de forme » → pas de ligne de disponibilité pour une forme non par défaut qui n'est obtenable que de cette façon (comptées dans `reports/phase3-details.json`, `form_change_omitted`). Un statut dédié demanderait une migration (proposition à valider).
- **Chromatiques** : taux de base des deux wikis (1/8192 générations 3–5, 1/4096 ensuite) ; Charme Chroma de N2/B2 (3/8192) ; méthode Masuda et Charme Chroma des générations 6+ : un seul des deux wikis donne le taux → non publiés. Verrou : tous les modèles hors événement de la forme dans le jeu « jamais chromatique » (rencontres fixes comprises) et aucune voie par reproduction ou évolution ; depuis le lot 6, une rencontre fixe verrouillée ne lève plus le verrou (lots 4–5 : Reshiram, Zekrom, Kyurem… manquaient).

Reporté (lots 2+) :
- Rouge Feu / Vert Feuille sur Switch (`frlgsw`) : pas de données propres extraites.
- Colosseum / XD (Pokémon obscurs, cadeaux) : jeux hors du référentiel ; leurs rencontres ne sont pas publiées.
- Lot 6 : Poké Loisirs (Poké Pelago, id 30016) sans lieu publié (disponibilité seule) ; lieux croisés de Let's Go (Parc Go) non placés ; Îles Scan d'USUL publiées en `special` sans condition de jour.
- Lot 7 : contenu de raids Dynamax ajouté par les DLC dans la Zone Sauvage non séparé du jeu de base (antres rangés selon leur lieu) ; alphas de Légendes Arceus : seulement ceux que PKHeX marque ; lieux précis des Pokémon des sous-zones de Hisui (camps, points de repère) ramenés à la zone.
- Lot 8 : raids Téracristal (7 étoiles, événements de raids) : disponibilité seulement quand PKHeX les donne ; points d'apparition de Paldea (coordonnées) non publiés ; rencontres fixes de Z-A débloquées par le DLC dans des lieux du jeu de base : non distinguées faute de source structurée.
- Taux d'apparition et sous-zones (comme au lot 1) ; conditions de la génération 4–5 non stockées par PKHeX (radio, saison, Poké Radar, essaims de DP).
