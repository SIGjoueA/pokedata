# Comparaison pokedata ↔ Pokédex — phase 2 (capacités, CT, movesets)

Lecture seule des fichiers du Pokédex (`moves.json`, `tm.json`, `learn-index.json`). Constats, sans correction appliquée.

## Capacités

- Capacités : pokedata **920**, Pokédex **819** ; seulement dans pokedata : 101 (surtout capacités Z et Dynamax), seulement dans le Pokédex : 0.
- Noms français différents : **2** — 508 : « Chgt Vitesse » / « Change-Vitesse », 521 : « Change Éclair » / « Change-Éclair »

- Valeurs actuelles (type, catégorie, puissance, précision, PP) comparées à Écarlate/Violet dans pokedata : 870 capacités comparables, **3** différentes.

| Capacité | Pokédex | pokedata (sv) |
|---|---|---|
| 850 Extravaillance | ['psychic', 'status', None, None, 10] | ['psychic', 'status', None, None, 15] |
| 877 Cataclysme | ['dark', 'special', 1, 90, 10] | ['dark', 'special', None, 90, 10] |
| 894 Vindicte | ['dark', 'physical', 1, 100, 10] | ['dark', 'physical', None, 100, 10] |

Lignes capacité × jeu publiées : rb 152, y 152, gs 230, c 230, rs 317, frlg 317, e 317, dp 416, pt 416, hgss 416, bw 496, b2w2 496, xy 548, oras 548, sm 607, usum 607, sw 682, sv 870.

## CT / CS / DT

| Jeu | Pokédex | pokedata | Identiques | Différentes | Seulement Pokédex | Seulement pokedata |
|---|---|---|---|---|---|---|
| zadlc | 160 | — | | | | |
| za | 107 | 160 | 107 | 0 | 0 | 53 |
| svdisk | 229 | — | | | | |
| svmask | 229 | — | | | | |
| sv | 229 | 229 | 229 | 0 | 0 | 0 |
| bdsp | 17 | 100 | 9 | 8 | 0 | 83 |
| swcrown | 200 | — | | | | |
| swisle | 200 | — | | | | |
| sw | 200 | 200 | 200 | 0 | 0 | 0 |
| lgpe | 60 | 60 | 60 | 0 | 0 | 0 |
| usum | 100 | 100 | 100 | 0 | 0 | 0 |
| sm | 100 | 100 | 100 | 0 | 0 | 0 |
| oras | 107 | 107 | 107 | 0 | 0 | 0 |
| xy | 105 | 105 | 105 | 0 | 0 | 0 |
| b2w2 | 101 | 101 | 101 | 0 | 0 | 0 |
| bw | 101 | 101 | 101 | 0 | 0 | 0 |
| hgss | 100 | 100 | 100 | 0 | 0 | 0 |
| pt | 100 | 100 | 100 | 0 | 0 | 0 |
| dp | 100 | 100 | 100 | 0 | 0 | 0 |
| e | 58 | 58 | 58 | 0 | 0 | 0 |
| frlg | 58 | 58 | 58 | 0 | 0 | 0 |
| rs | 58 | 58 | 58 | 0 | 0 | 0 |
| c | 57 | 57 | 57 | 0 | 0 | 0 |
| gs | 57 | 57 | 57 | 0 | 0 | 0 |
| y | 55 | 55 | 55 | 0 | 0 | 0 |
| rb | 55 | 55 | 55 | 0 | 0 | 0 |
| frlgsw | 58 | — | | | | |

- **za** : seulement pokedata 4, 6, 13, 47, 80, 90, 102, 130, 138, 143, 161, 206, 207, 246, 252, 259, 263, 299, 305, 307
- **bdsp** : différentes (capacité : Pokédex / pokedata) 15 HM1/TM93, 19 HM2/TM94, 57 HM3/TM95, 70 HM4/TM96, 127 HM7/TM99, 249 HM6/TM98, 431 HM8/TM100, 432 HM5/TM97; seulement pokedata 14, 46, 53, 58, 59, 63, 76, 85, 86, 87, 89, 91, 92, 94, 104, 113, 115, 126, 138, 148

## Movesets

Publiés à partir des données 2026.11.26 (schéma 1.1.0) : comparaison dans `reports/compare-learnsets.md`.

