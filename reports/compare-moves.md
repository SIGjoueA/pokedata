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

## Movesets (calculés localement depuis les données des jeux, non publiés)

Comparaison par jeu sur les couples (forme, capacité), puis par méthode (montée de niveau, CT, œuf, tuteur).

| Jeu | Couples Pokédex | Couples pokedata | Communs | Seulement Pokédex | Seulement pokedata | Méthode identique (communs) |
|---|---|---|---|---|---|---|
| b2w2 | 18399 | 34026 | 15548 | 2851 | 18478 | 14826 (95 %) |
| bdsp | 7262 | 25426 | 7217 | 45 | 18209 | 7217 (100 %) |
| bw | 7940 | 33610 | 7937 | 3 | 25673 | 7937 (100 %) |
| c | 8933 | 8632 | 8632 | 301 | 0 | 8602 (99 %) |
| dp | 7560 | 24863 | 7115 | 445 | 17748 | 7113 (99 %) |
| e | 9536 | 13103 | 6795 | 2741 | 6308 | 6539 (96 %) |
| frlg | 6042 | 13166 | 5155 | 887 | 8011 | 5060 (98 %) |
| gs | 8725 | 8611 | 8611 | 114 | 0 | 8611 (100 %) |
| hgss | 15003 | 30160 | 14272 | 731 | 15888 | 14267 (99 %) |
| la | 2383 | 5801 | 2367 | 16 | 3434 | 1806 (76 %) |
| lgpe | 5135 | 5135 | 5086 | 49 | 49 | 5086 (100 %) |
| oras | 18366 | 46283 | 15442 | 2924 | 30841 | 14895 (96 %) |
| pt | 12478 | 25221 | 10353 | 2125 | 14868 | 10042 (96 %) |
| rb | 3893 | 3849 | 3849 | 44 | 0 | 3849 (100 %) |
| rs | 6922 | 13102 | 6794 | 128 | 6308 | 6794 (100 %) |
| sm | 22063 | 50263 | 21681 | 382 | 28582 | 21671 (99 %) |
| sv | 26923 | 53155 | 26854 | 69 | 26301 | 26801 (99 %) |
| sw | 27707 | 30049 | 18263 | 9444 | 11786 | 16861 (92 %) |
| usum | 34019 | 62005 | 33522 | 497 | 28483 | 33482 (99 %) |
| xy | 27707 | 43721 | 27457 | 250 | 16264 | 27457 (100 %) |
| y | 3925 | 3882 | 3882 | 43 | 0 | 3882 (100 %) |
| za | — | 22836 | | | | |

Les écarts de méthode viennent surtout des tuteurs (listes de tuteurs non lues pour les générations 3, 6 et 7, voir le plan) et des capacités apprises au rappel / à l'évolution.

