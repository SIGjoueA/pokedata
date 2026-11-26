# Comparaison pokedata ↔ Pokédex — phase 3 (lieux, rencontres, disponibilité, chromatiques) : rb, y, gs, c

Lecture seule des fichiers du Pokédex (`sp/*.json` champs `en` et `av`, `loc.json`, `trade.json`, `shiny.json`). Constats, sans correction appliquée. Versions laissées de côté dans ce lot : blue-japan.

## Lieux

- Lieux publiés pour ce lot : **92** ; noms de l’ancien Pokédex rattachés (identifiant externe `pokedex-legacy`) : **151** noms sur **90** lieux.
- Noms du Pokédex sans lieu correspondant dans pokedata (nombre d’occurrences) : « Casino de Céladopole » (24), « Laboratoire (Cramois'Île) » (12), « Repaire Rocket d'Acajou » (8), « Route 4 » (8), « Sillonnant Johto » (5), « Dojo de Combat » (4), « Centre Pokémon (Route 4) » (2), « Centre Pokémon (Route 3) » (2), « Sylphe SARL (6e ét.) » (2), « Toit du manoir Céladon » (2), « Souterrain de Kanto » (2), « Centre Commercial de Doublonville (4e ét.) » (2), « Argenta » (1).
  Cause habituelle : lieu sans rencontre vérifiée dans ce lot (Casino, Laboratoire de Cramois’Île, Route 4 en 1ʳᵉ génération…), ou nom propre au Pokédex (« Sillonnant Johto » pour les Pokémon errants, publiés en disponibilité seulement).
- Noms du Pokédex différents du nom de jeu retenu (24) : « Cramois'Ile » → `cinnabar-island` « Cramois’Ile », « Cave Taupiqueur » → `digletts-cave` « Cave TAUPIQUEUR », « Casino de Doublonville » → `goldenrod-city` « Doublonville », « Route 41 » → `johto-sea-route-41` « Chenal 41 », « Mont Argenté (extérieur) » → `kanto-route-28` « Route 28 », « Route 19 » → `kanto-sea-route-19` « Chenal 19 », « Route 20 » → `kanto-sea-route-20` « Chenal 20 », « Route 21 » → `kanto-sea-route-21` « Chenal 21 », « Route Victoire 1 (1er ét.) » → `kanto-victory-road-1` « Route Victoire (HG/SS) », « Route Victoire 1 (2e ét.) » → `kanto-victory-road-1` « Route Victoire (HG/SS) », « Route Victoire 1 (RdC) » → `kanto-victory-road-1` « Route Victoire (HG/SS) », « Mon Argenté (sommet) » → `mt-silver-cave` « Grotte Argentée », « Mont Argenté (1er étage) » → `mt-silver-cave` « Grotte Argentée », « Mont Argenté (RdC) » → `mt-silver-cave` « Grotte Argentée », « Ruines d'Alpha (extérieur) » → `ruins-of-alph` « Ruines d’Alpha », « Ruines d'Alpha (intérieur A) » → `ruins-of-alph` « Ruines d’Alpha », « Ruines d'Alpha (intérieur B) » → `ruins-of-alph` « Ruines d’Alpha », « Ruines d'Alpha (intérieur C) » → `ruins-of-alph` « Ruines d’Alpha », « Ruines d'Alpha (intérieur D) » → `ruins-of-alph` « Ruines d’Alpha », « Pont de l'Océane » → `vermilion-city` « Carmin sur Mer », « Tourb'Iles (1er s-sol) » → `whirl-islands` « Tourb’Iles », « Tourb'Iles (2e s-sol) » → `whirl-islands` « Tourb’Iles », « Tourb'Iles (3e s-sol) » → `whirl-islands` « Tourb’Iles », « Tourb'Iles (RdC) » → `whirl-islands` « Tourb’Iles ».

## Rencontres (Pokémon × lieu, toutes versions du jeu)

| Jeu | Paires communes | Seulement Pokédex | Seulement pokedata | Niveaux différents |
|---|---|---|---|---|
| rb | 337 | 10 | 3 | 6 |
| y | 314 | 8 | 3 | 7 |
| gs | 690 | 22 | 85 | 41 |
| c | 717 | 12 | 80 | 40 |

### rb

- Seulement dans le Pokédex (10) : 1 @ pallet-town, 101 @ kanto-power-plant, 143 @ kanto-route-12, 143 @ kanto-route-16, 144 @ seafoam-islands, 145 @ kanto-power-plant, 146 @ kanto-victory-road-2, 150 @ cerulean-cave, 4 @ pallet-town, 7 @ pallet-town
- Seulement dans pokedata (3) : 138 @ cinnabar-island, 140 @ cinnabar-island, 142 @ cinnabar-island
- Niveaux (Pokédex → pokedata) (6) : 100 @ kanto-power-plant 21–40 → 21–23, 108 @ kanto-route-18 23–100 → 15–15, 122 @ kanto-route-2 8–100 → 6–6, 124 @ cerulean-city 23–100 → 15–15, 30 @ kanto-route-11 16–100 → 16–16, 83 @ vermilion-city 3–100 → 2–2

### y

- Seulement dans le Pokédex (8) : 101 @ kanto-power-plant, 143 @ kanto-route-12, 143 @ kanto-route-16, 144 @ seafoam-islands, 145 @ kanto-power-plant, 146 @ kanto-victory-road-2, 150 @ cerulean-cave, 25 @ pallet-town
- Seulement dans pokedata (3) : 138 @ cinnabar-island, 140 @ cinnabar-island, 142 @ cinnabar-island
- Niveaux (Pokédex → pokedata) (7) : 1 @ cerulean-city 10–10 → 5–5, 100 @ kanto-power-plant 33–40 → 33–37, 122 @ kanto-route-2 9–100 → 8–8, 4 @ kanto-route-24 10–10 → 5–5, 47 @ kanto-route-18 22–100 → 13–13, 51 @ kanto-route-11 50–100 → 15–15, 7 @ vermilion-city 10–10 → 5–5

### gs

- Seulement dans le Pokédex (22) : 120 @ kanto-route-4, 129 @ kanto-route-4, 19 @ kanto-route-8, 194 @ ruins-of-alph, 195 @ ruins-of-alph, 198 @ kanto-route-18, 21 @ goldenrod-city, 213 @ kanto-route-4, 222 @ kanto-route-4, 54 @ kanto-route-6, 55 @ kanto-route-6, 61 @ kanto-route-22, 72 @ cianwood-city, 72 @ kanto-route-4, 72 @ whirl-islands, 73 @ cianwood-city, 73 @ kanto-route-4, 73 @ whirl-islands, 88 @ celadon-city, 89 @ celadon-city, 98 @ kanto-route-4, 99 @ kanto-route-4
- Seulement dans pokedata (85) : 114 @ mt-silver-cave, 12 @ national-park, 120 @ cerulean-city, 120 @ johto-sea-route-40, 122 @ celadon-city, 123 @ national-park, 127 @ national-park, 129 @ johto-sea-route-40, 129 @ viridian-city, 133 @ celadon-city, 137 @ celadon-city, 15 @ national-park, 170 @ olivine-city, 171 @ olivine-city, 213 @ johto-sea-route-40, 213 @ slowpoke-well, 215 @ mt-silver-cave, 222 @ cerulean-city, 222 @ johto-sea-route-40, 46 @ national-park, 48 @ blackthorn-city, 48 @ cherrygrove-city, 48 @ cianwood-city, 48 @ ecruteak-city, 48 @ goldenrod-city, 48 @ johto-sea-route-40, 48 @ johto-sea-route-41, 48 @ kanto-route-28, 48 @ mahogany-town, 48 @ mt-silver-cave, 48 @ national-park, 48 @ new-bark-town, 48 @ olivine-city, 48 @ violet-city, 49 @ blackthorn-city, 49 @ cherrygrove-city, 49 @ cianwood-city, 49 @ ecruteak-city, 49 @ goldenrod-city, 49 @ johto-sea-route-40, 49 @ johto-sea-route-41, 49 @ kanto-route-28, 49 @ mahogany-town, 49 @ mt-silver-cave, 49 @ new-bark-town, 49 @ olivine-city, 49 @ violet-city, 60 @ mt-silver-cave, 63 @ blackthorn-city, 63 @ cherrygrove-city, 63 @ cianwood-city, 63 @ ecruteak-city, 63 @ johto-sea-route-40, 63 @ johto-sea-route-41, 63 @ kanto-route-28, 63 @ mahogany-town, 63 @ mt-silver-cave, 63 @ new-bark-town, 63 @ olivine-city, 63 @ violet-city …
- Niveaux (Pokédex → pokedata) (41) : 10 @ national-park 10–12 → 7–18, 100 @ olivine-city 5–100 → 5–5, 11 @ national-park 10–10 → 9–18, 112 @ blackthorn-city 30–100 → 10–10, 114 @ kanto-route-28 39–41 → 39–39, 116 @ whirl-islands 15–40 → 20–40, 118 @ cerulean-city 5–40 → 5–14, 118 @ kanto-route-24 4–40 → 10–40, 118 @ kanto-route-25 4–40 → 10–40, 119 @ cerulean-city 10–40 → 10–14, 119 @ kanto-route-24 10–40 → 40–40, 119 @ kanto-route-25 10–40 → 40–40, 119 @ mt-mortar 20–40 → 40–40, 119 @ mt-silver-cave 35–44 → 40–40, 129 @ cerulean-city 10–40 → 10–20, 129 @ johto-route-45 5–40 → 5–24, 13 @ national-park 10–12 → 7–18, 14 @ national-park 10–10 → 9–18, 142 @ kanto-route-14 5–100 → 5–5, 147 @ johto-route-45 20–40 → 10–10, 148 @ johto-route-45 40–40 → 10–10, 183 @ mt-mortar 13–20 → 13–15, 191 @ national-park 12–13 → 11–13, 21 @ kanto-route-9 13–13 → 13–15, 215 @ kanto-route-28 38–42 → 40–40, 217 @ kanto-route-28 40–42 → 40–40, 217 @ mt-silver-cave 44–50 → 42–50, 218 @ kanto-route-17 27–29 → 25–29, 232 @ kanto-route-28 40–42 → 40–40, 232 @ mt-silver-cave 44–50 → 42–50, 60 @ kanto-route-22 4–40 → 10–40, 60 @ viridian-city 5–14 → 5–40, 61 @ kanto-route-28 35–44 → 40–44, 63 @ goldenrod-city 10–10 → 10–15, 72 @ olivine-city 15–24 → 10–24, 73 @ olivine-city 20–24 → 20–40, 77 @ kanto-route-28 40–42 → 40–40, 78 @ kanto-route-28 42–44 → 42–42, 78 @ pewter-city 15–100 → 14–14, 89 @ kanto-route-18 30–30 → 28–30 …

### c

- Seulement dans le Pokédex (12) : 120 @ kanto-route-4, 129 @ kanto-route-4, 195 @ mt-silver-cave, 213 @ kanto-route-4, 222 @ kanto-route-4, 251 @ ilex-forest, 52 @ johto-route-35, 72 @ kanto-route-4, 73 @ kanto-route-4, 85 @ blackthorn-city, 98 @ kanto-route-4, 99 @ kanto-route-4
- Seulement dans pokedata (80) : 11 @ national-park, 114 @ mt-silver-cave, 12 @ national-park, 120 @ cerulean-city, 120 @ johto-sea-route-40, 123 @ national-park, 127 @ national-park, 129 @ johto-sea-route-40, 129 @ viridian-city, 137 @ celadon-city, 14 @ national-park, 15 @ national-park, 164 @ johto-route-43, 166 @ johto-route-37, 170 @ olivine-city, 171 @ olivine-city, 190 @ blackthorn-city, 190 @ cherrygrove-city, 190 @ cianwood-city, 190 @ ecruteak-city, 190 @ goldenrod-city, 190 @ johto-sea-route-40, 190 @ johto-sea-route-41, 190 @ kanto-route-28, 190 @ mahogany-town, 190 @ mt-silver-cave, 190 @ new-bark-town, 190 @ olivine-city, 190 @ violet-city, 21 @ blackthorn-city, 21 @ cherrygrove-city, 21 @ cianwood-city, 21 @ ecruteak-city, 21 @ johto-sea-route-40, 21 @ johto-sea-route-41, 21 @ kanto-route-28, 21 @ mahogany-town, 21 @ mt-silver-cave, 21 @ new-bark-town, 21 @ olivine-city, 21 @ violet-city, 213 @ johto-sea-route-40, 213 @ slowpoke-well, 214 @ blackthorn-city, 214 @ cherrygrove-city, 214 @ cianwood-city, 214 @ ecruteak-city, 214 @ goldenrod-city, 214 @ johto-sea-route-40, 214 @ johto-sea-route-41, 214 @ kanto-route-28, 214 @ mahogany-town, 214 @ mt-silver-cave, 214 @ new-bark-town, 214 @ olivine-city, 214 @ violet-city, 222 @ cerulean-city, 222 @ johto-sea-route-40, 223 @ johto-route-44, 24 @ mt-silver-cave …
- Niveaux (Pokédex → pokedata) (40) : 10 @ johto-route-31 4–5 → 4–4, 10 @ national-park 10–10 → 7–18, 100 @ olivine-city 5–100 → 5–5, 114 @ kanto-route-28 39–41 → 39–39, 118 @ cerulean-city 5–40 → 5–14, 118 @ kanto-route-24 4–40 → 5–40, 118 @ kanto-route-25 4–40 → 5–40, 119 @ cerulean-city 10–40 → 10–14, 125 @ kanto-route-10 16–16 → 16–18, 129 @ cerulean-city 10–40 → 10–20, 129 @ johto-route-45 5–40 → 5–24, 13 @ national-park 10–10 → 7–18, 142 @ kanto-route-14 5–100 → 5–5, 147 @ johto-route-45 20–40 → 10–10, 148 @ johto-route-45 40–40 → 10–10, 163 @ johto-route-43 10–16 → 10–10, 163 @ national-park 12–15 → 13–15, 165 @ johto-route-37 10–10 → 10–13, 195 @ ruins-of-alph 14–24 → 15–24, 20 @ kanto-route-11 15–16 → 13–16, 217 @ dark-cave 20–30 → 25–30, 42 @ kanto-route-28 40–44 → 40–42, 42 @ mt-mortar 13–30 → 13–32, 42 @ mt-silver-cave 45–53 → 40–53, 42 @ whirl-islands 23–28 → 24–28, 47 @ mt-silver-cave 46–48 → 46–52, 48 @ kanto-route-25 12–12 → 10–10, 48 @ national-park 10–10 → 10–16, 52 @ kanto-route-11 15–15 → 13–13, 54 @ johto-route-35 15–24 → 13–24, 55 @ mt-silver-cave 40–48 → 35–48, 60 @ viridian-city 5–14 → 5–40, 61 @ kanto-route-28 35–44 → 40–44, 72 @ cianwood-city 15–29 → 15–24, 72 @ olivine-city 15–24 → 10–24, 73 @ olivine-city 20–24 → 20–40, 77 @ kanto-route-28 40–42 → 40–40, 78 @ kanto-route-28 40–44 → 40–40, 82 @ kanto-power-plant 16–100 → 5–5, 95 @ violet-city 5–100 → 3–3

## Disponibilité par jeu

Pokédex : liste `av` (jeux où la forme est disponible). pokedata : au moins un statut autre que `unobtainable` dans une version du jeu.

| Jeu | Formes disponibles (Pokédex) | (pokedata) | Seulement Pokédex | Seulement pokedata |
|---|---|---|---|---|
| rb | 151 | 151 | 0 | 0 |
| y | 151 | 151 | 0 | 0 |
| gs | 276 | 276 | 0 | 0 |
| c | 276 | 276 | 0 | 0 |


## Exclusivités de version

pokedata : statuts `trade-version-exclusive` (autre version ou autre jeu de la génération) ou `transfer` (Capsule Temporelle) sans autre moyen d’obtention dans au moins une version du jeu (événements exclus). Le Pokédex compte aussi les évolutions par échange (Kadabra → Alakazam…), que pokedata classe en `evolve`.

- rb : Pokédex **30**, pokedata **26** (espèces à faire venir d’une autre version, d’un autre jeu ou par la Capsule Temporelle) ; seulement Pokédex : 65, 68, 76, 94 ; seulement pokedata : —.
- y : Pokédex **18**, pokedata **14** (espèces à faire venir d’une autre version, d’un autre jeu ou par la Capsule Temporelle) ; seulement Pokédex : 26, 65, 68, 76, 94, 122 ; seulement pokedata : 137, 151.
- gs : Pokédex **54**, pokedata **27** (espèces à faire venir d’une autre version, d’un autre jeu ou par la Capsule Temporelle) ; seulement Pokédex : 1, 4, 7, 10, 11, 12, 13, 14, 15, 65, 68, 76, 94, 138, 140, 142, 165, 167, 186, 199, 208, 212, 216, 225, 226, 227, 230, 231, 233 ; seulement pokedata : 151, 251.
- c : Pokédex **38**, pokedata **18** (espèces à faire venir d’une autre version, d’un autre jeu ou par la Capsule Temporelle) ; seulement Pokédex : 3, 6, 9, 65, 68, 76, 94, 142, 144, 145, 146, 150, 186, 199, 208, 212, 223, 224, 230, 233 ; seulement pokedata : —.

## Chromatiques

- rb : taux de base Pokédex — / pokedata — ; règles pokedata : — (pas de chromatiques) ; règles Pokédex : — ; verrous Pokédex : 151, pokedata : —.
- y : taux de base Pokédex — / pokedata — ; règles pokedata : — (pas de chromatiques) ; règles Pokédex : — ; verrous Pokédex : 151, pokedata : —.
- gs : taux de base Pokédex 1/8192 / pokedata 1/8192 ; règles pokedata : base 1/8192, shiny-parent 1/64 ; règles Pokédex : Rencontre normale 1/8192; Reproduction avec un parent chromatique 1/64; Léviator rouge garanti ; verrous Pokédex : 151, pokedata : —.
- c : taux de base Pokédex 1/8192 / pokedata 1/8192 ; règles pokedata : base 1/8192, shiny-parent 1/64 ; règles Pokédex : Rencontre normale 1/8192; Reproduction avec un parent chromatique 1/64; Léviator rouge garanti; Œuf Bizarre 14 % ; verrous Pokédex : 151, pokedata : —.
- Rencontres au chromatique imposé par le jeu (pokedata, `encounter.extra.shiny`) : 130 c (always), 130 gs (always).

