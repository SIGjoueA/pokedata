# Comparaison pokedata ↔ Pokédex — movesets

Lecture seule de `learn-index.json` du Pokédex. Constats, sans correction appliquée.

pokedata : **645613** lignes `learnset` publiées, **34777** ensembles forme × jeu × méthode vérifiés (statut `game-data`, contrôlés avec PokeAPI et, pour les jeux où ses données sont propres au jeu, Showdown) ; **1157** ensembles où une source de contrôle diffère (détail dans `discrepancy`, champs `missing` / `extra`).

Comparaison sur les couples (forme, capacité) par jeu. Le Pokédex ne couvre qu'une partie des formes dans les anciens jeux : les couples « seulement pokedata » sont séparés entre formes que le Pokédex couvre dans ce jeu et formes qu'il ne couvre pas. Les couples « seulement Pokédex » sont classés : forme absente de la table `form` de pokedata ; forme sans ligne `form_game` dans ce jeu (absente du jeu d'après ses données) ; forme du jeu sans moveset propre dans les données du jeu (variantes cosmétiques comme les bonbons de Charmilly, formes de combat, Méga-Évolutions : le moveset est celui de l'entrée du jeu, rangé sur la forme correspondante) ; autres. Les extensions (Isolarmure, Couronneige, Masque Turquoise, Disque Indigo, Méga-Dimension) sont fusionnées avec leur jeu, comme dans pokedata.

| Jeu | Couples Pokédex | Couples pokedata | Communs | Méthode identique | Seulement pokedata (formes couvertes / non couvertes par le Pokédex) | Seulement Pokédex : hors table / hors jeu / sans moveset propre / autres |
|---|---|---|---|---|---|---|
| rb | 3893 | 3849 | 3849 | 3849 (100 %) | 0 / 0 | 43 / 0 / 0 / 1 |
| y | 3925 | 3882 | 3882 | 3882 (100 %) | 0 / 0 | 42 / 0 / 0 / 1 |
| gs | 8725 | 8611 | 8611 | 8611 (100 %) | 0 / 0 | 46 / 36 / 25 / 7 |
| c | 8933 | 8822 | 8822 | 8822 (100 %) | 0 / 0 | 49 / 37 / 25 / 0 |
| rs | 6922 | 13102 | 6794 | 6794 (100 %) | 0 / 6308 | 0 / 128 / 0 / 0 |
| frlg | 6042 | 15308 | 5979 | 5979 (100 %) | 0 / 9329 | 63 / 0 / 0 / 0 |
| e | 9536 | 17953 | 9354 | 9354 (100 %) | 0 / 8599 | 0 / 181 / 0 / 1 |
| dp | 7560 | 24540 | 7453 | 7453 (100 %) | 0 / 17087 | 0 / 79 / 27 / 1 |
| pt | 12478 | 28337 | 12354 | 12354 (100 %) | 0 / 15983 | 0 / 91 / 27 / 6 |
| hgss | 15003 | 29529 | 14878 | 14878 (100 %) | 0 / 14651 | 96 / 0 / 27 / 2 |
| bw | 7940 | 32203 | 7937 | 7937 (100 %) | 0 / 24266 | 0 / 0 / 0 / 3 |
| b2w2 | 18399 | 38669 | 18395 | 18395 (100 %) | 0 / 20274 | 0 / 0 / 0 / 4 |
| xy | 27707 | 42335 | 27527 | 27527 (100 %) | 0 / 14808 | 127 / 47 / 0 / 6 |
| oras | 18366 | 52520 | 18206 | 17839 (97 %) | 0 / 34314 | 102 / 57 / 0 / 1 |
| sm | 22063 | 47937 | 20668 | 20658 (99 %) | 0 / 27269 | 74 / 1152 / 0 / 169 |
| usum | 34019 | 59044 | 32296 | 32256 (99 %) | 0 / 26748 | 99 / 1433 / 0 / 191 |
| lgpe | 5135 | 5135 | 5086 | 5086 (100 %) | 0 / 49 | 49 / 0 / 0 / 0 |
| sw | 38549 | 41657 | 35896 | 35896 (100 %) | 0 / 5761 | 0 / 47 / 2538 / 68 |
| bdsp | 7262 | 25426 | 7217 | 7217 (100 %) | 2 / 18207 | 0 / 41 / 0 / 4 |
| la | 2383 | 5801 | 2367 | 1806 (76 %) | 3022 / 412 | 0 / 16 / 0 / 0 |
| sv | 46937 | 53155 | 43581 | 43174 (99 %) | 158 / 9416 | 0 / 104 / 2538 / 714 |
| za | — | 22836 | | | | |
| frlgsw | 6042 | 0 | 0 | 0 (0 %) | 0 / 0 | 63 / 0 / 5979 / 0 |

## Écart d'Épée/Bouclier (sw)

Rapport de la phase 2 (movesets calculés, non publiés) : **9 444** couples seulement dans le Pokédex pour `sw`. Cause principale : les DT (TR01–TR99) étaient lus dans les drapeaux des CT (index 100+) au lieu de leur propre table ; corrigé dans `scripts/fetch/pkhex_dumper/Learn.cs` (`GetIsLearnTR`).

Même calcul (fichier `sw` du Pokédex seul, sans les extensions) après correction : **2653** couples seulement dans le Pokédex (**68** une fois écartées les formes sans moveset propre), tous expliqués :

- 47 couples sur des formes absentes d'Épée/Bouclier selon les données du jeu : 172-spiky-eared;
- 2538 couples sur 54 formes sans moveset propre dans les données du jeu (54 variantes crème × bonbon de Charmilly, dont le moveset est celui de la forme « bonbon fraise » de la même crème);
- 27 couples « œuf » côté Pokédex : 778-busted:174, 778-busted:194, 778-busted:288, 845-gorging:297, 845-gorging:332, 845-gorging:355, 845-gorging:392, 845-gorging:432, 845-gulping:297, 845-gulping:332, 845-gulping:355, 845-gulping:392, 845-gulping:432, 875-noice:38, 875-noice:187, 875-noice:392, 875-noice:457, 875-noice:487, 875-noice:556, 877-hangry:162, 877-hangry:207, 877-hangry:229, 877-hangry:252, 877-hangry:268…;
- 36 couples « tuteur » côté Pokédex : 773:518, 773:519, 773-bug:518, 773-bug:519, 773-dark:518, 773-dark:519, 773-dragon:518, 773-dragon:519, 773-electric:518, 773-electric:519, 773-fairy:518, 773-fairy:519, 773-fighting:518, 773-fighting:519, 773-fire:518, 773-fire:519, 773-flying:518, 773-flying:519, 773-ghost:518, 773-ghost:519, 773-grass:518, 773-grass:519, 773-ground:518, 773-ground:519…;
- 5 couples « autre (changement de forme…) » côté Pokédex : 479-fan:403, 479-frost:59, 479-heat:315, 479-mow:437, 479-wash:56;

Lecture des « autres » : capacités des formes de Motisma (479-*) apprises au changement de forme (méthode « autre » dans le Pokédex, pas un moveset des jeux) ; Aire d'Eau (518) et Aire de Feu (519) par tuteur pour Silvallié (773-*), quand les données du jeu (PKHeX) ne donnent qu'Aire d'Herbe (520) — PokeAPI donne les trois, écart enregistré dans `discrepancy` (18 ensembles) ; capacités d'œuf que le Pokédex attribue aux formes de combat (778-busted, 845-gulping/gorging, 875-noice, 877-hangry) : les données du jeu n'en donnent qu'à la forme de base.

Autres constats : en Écarlate/Violet et Soleil/Lune/Ultra-Soleil/Ultra-Lune, le Pokédex reporte les capacités d'œuf sur les évolutions et les Méga-Évolutions (les données du jeu et PokeAPI ne les donnent qu'au premier stade) ; les formes de type de Silvallié (773-*) n'ont pas de ligne `form_game` dans Soleil/Lune et Ultra-Soleil/Ultra-Lune (phase 1), d'où les couples « hors jeu ».

## Écarts restants par jeu (« seulement Pokédex », formes présentes dans le jeu)

- **rb** (1) : autre (changement de forme…) 1 — ex. 25:57
- **y** (1) : autre (changement de forme…) 1 — ex. 25:57
- **gs** (7) : œuf 7 — ex. 1:204, 120:48, 120:62, 120:112, 143:204, 238:142, 43:204
- **e** (1) : autre (changement de forme…) 1 — ex. 172:344
- **dp** (1) : autre (changement de forme…) 1 — ex. 172:344
- **pt** (6) : autre (changement de forme…) 6 — ex. 172:344, 479-fan:403, 479-frost:59, 479-heat:315, 479-mow:437, 479-wash:56
- **hgss** (2) : autre (changement de forme…) 2 — ex. 172:344, 172-spiky-eared:344
- **bw** (3) : tuteur 3 — ex. 647:548, 648:547, 648-pirouette:547
- **b2w2** (4) : tuteur 4 — ex. 647:548, 647-resolute:548, 648:547, 648-pirouette:547
- **xy** (6) : autre (changement de forme…) 6 — ex. 172:344, 479-fan:403, 479-frost:59, 479-heat:315, 479-mow:437, 479-wash:56
- **oras** (1) : autre (changement de forme…) 1 — ex. 172:344
- **sm** (169) : œuf 146, autre (changement de forme…) 16, tuteur 7 — ex. 115-mega:23, 115-mega:38, 115-mega:50, 115-mega:68, 115-mega:116, 115-mega:193, 115-mega:253, 115-mega:264, 115-mega:283, 115-mega:306, 115-mega:359, 115-mega:376
- **usum** (191) : œuf 165, autre (changement de forme…) 16, tuteur 10 — ex. 115-mega:23, 115-mega:38, 115-mega:50, 115-mega:68, 115-mega:116, 115-mega:193, 115-mega:306, 115-mega:359, 115-mega:376, 115-mega:509, 127-mega:31, 127-mega:98
- **sw** (68) : tuteur 36, œuf 27, autre (changement de forme…) 5 — ex. 479-fan:403, 479-frost:59, 479-heat:315, 479-mow:437, 479-wash:56, 773:518, 773:519, 773-bug:518, 773-bug:519, 773-dark:518, 773-dark:519, 773-dragon:518
- **bdsp** (4) : CT 4 — ex. 413-trash:89, 413-trash:201, 413-trash:317, 413-trash:523
- **sv** (714) : œuf 675, CT 34, autre (changement de forme…) 5 — ex. 1011:111, 1011:205, 1011:389, 1018:163, 1018:243, 1018:400, 1019:111, 1019:205, 1019:389, 106:68, 106:183, 106:229

## Écarts entre sources de contrôle (pokedata)

Ensembles où PokeAPI ou Showdown diffère des données des jeux, par jeu et méthode (source : ensembles concernés).

| Jeu | Méthode | Source | Ensembles |
|---|---|---|---|
| gs | egg | pokeapi | 4 |
| frlg | level-up | pokeapi | 1 |
| pt | tutor | pokeapi | 3 |
| hgss | egg | pokeapi | 1 |
| hgss | tutor | pokeapi | 1 |
| b2w2 | tutor | pokeapi | 4 |
| oras | tutor | pokeapi | 843 |
| usum | egg | pokeapi | 1 |
| usum | tutor | pokeapi | 13 |
| sw | tutor | pokeapi | 18 |
| bdsp | machine | pokeapi | 1 |
| la | mastery | pokeapi | 19 |
| sv | egg | pokeapi | 2 |
| sv | level-up | pokeapi | 1 |
| sv | machine | pokeapi | 5 |
| sv | machine | showdown | 5 |
| za | level-up | pokeapi | 117 |
| za | plus | pokeapi | 118 |

