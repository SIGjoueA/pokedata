# Comparaison pokedata ↔ Pokédex — phase 1b (évolutions, Pokédex régionaux, catégories)

Lecture seule des fichiers du Pokédex (`docs/data/evo.json`, `dex/*.json`, `sp/*.json`). Les écarts listés ici sont des constats, pas des corrections appliquées d'un côté ou de l'autre.

## Évolutions

- Paires (forme → forme) : pokedata **589**, Pokédex **545**, communes **537**.
- Seulement dans le Pokédex : **8** ; seulement dans pokedata : **52**.

Seulement dans le Pokédex (souvent : évolution propre à GO/HOME, ou forme regroupée autrement) :

`412-sandy→414`, `412-trash→414`, `592-female→593-female`, `665→666`, `667→668-female`, `710→711-small`, `744→745-dusk`, `808→809`

Seulement dans pokedata (évolutions lues dans les tables des jeux, par forme) :

`412-sandy→414-sandy`, `412-trash→414-trash`, `664-archipelago→665-archipelago`, `664-continental→665-continental`, `664-elegant→665-elegant`, `664-fancy→665-fancy`, `664-garden→665-garden`, `664-high-plains→665-high-plains`, `664-jungle→665-jungle`, `664-marine→665-marine`, `664-meadow→665-meadow`, `664-modern→665-modern`, `664-monsoon→665-monsoon`, `664-ocean→665-ocean`, `664-poke-ball→665-poke-ball`, `664-polar→665-polar`, `664-river→665-river`, `664-sandstorm→665-sandstorm`, `664-savanna→665-savanna`, `664-sun→665-sun`, `664-tundra→665-tundra`, `665→666-icy-snow`, `665-archipelago→666-archipelago`, `665-continental→666-continental`, `665-elegant→666-elegant`, `665-fancy→666-fancy`, `665-garden→666-garden`, `665-high-plains→666-high-plains`, `665-jungle→666-jungle`, `665-marine→666-marine`, `665-meadow→666`, `665-modern→666-modern`, `665-monsoon→666-monsoon`, `665-ocean→666-ocean`, `665-poke-ball→666-poke-ball`, `665-polar→666-polar`, `665-river→666-river`, `665-sandstorm→666-sandstorm`, `665-savanna→666-savanna`, `665-sun→666-sun`, `665-tundra→666-tundra`, `744-own-tempo→745-dusk`, `854-antique→855-antique`, `868→869-caramel-swirl-strawberry-sweet`, `868→869-lemon-cream-strawberry-sweet`, `868→869-matcha-cream-strawberry-sweet`, `868→869-mint-cream-strawberry-sweet`, `868→869-rainbow-swirl-strawberry-sweet`, `868→869-ruby-cream-strawberry-sweet`, `868→869-ruby-swirl-strawberry-sweet`, `868→869-salted-cream-strawberry-sweet`, `999-roaming→1000`

- Niveau d'évolution (méthode la plus récente) différent : **0**.

Répartition des déclencheurs dans pokedata (toutes lignes jeu × variante) : level-up 6010, use-item 932, trade 473, spin 54, shed 17, tower 16, walk 9, recoil-damage 8, other 8, take-damage 5, three-critical-hits 5, strong-style 3, agile-style 1.

## Pokédex régionaux

| Jeu | Pokédex (Pokédex) | Pokédex (pokedata) | Entrées Pokédex | Entrées pokedata | Numéros différents | Absents d'un côté |
|---|---|---|---|---|---|---|
| b2w2 | Unys amélioré | b2w2-unova | 301 | 301 | 0 | 0 |
| bdsp | Sinnoh initial | bdsp-sinnoh | 151 | 151 | 0 | 0 |
| bw | Unys initial | bw-unova | 156 | 156 | 0 | 0 |
| c | Johto initial | c-johto | 251 | 251 | 0 | 0 |
| dp | Sinnoh initial | dp-sinnoh | 151 | 151 | 0 | 0 |
| e | Hoenn initial | e-hoenn | 202 | 202 | 0 | 0 |
| frlg | Kanto | frlg-kanto | 151 | 151 | 0 | 0 |
| frlgsw | Kanto | — | 150 | 0 | 0 | 150 |
| gs | Johto initial | gs-johto | 251 | 251 | 0 | 0 |
| hgss | Johto amélioré | hgss-johto | 256 | 256 | 0 | 0 |
| la | Hisui | la-hisui | 242 | 242 | 0 | 0 |
| lgpe | Let's Go Kanto | lgpe-kanto | 153 | 153 | 0 | 0 |
| oras | Hoenn amélioré | oras-hoenn | 211 | 211 | 0 | 0 |
| pt | Sinnoh étendu | pt-sinnoh | 210 | 210 | 0 | 0 |
| rb | Kanto | rb-kanto | 151 | 151 | 0 | 0 |
| rs | Hoenn initial | rs-hoenn | 202 | 202 | 0 | 0 |
| sm | Alola original | sm-alola | 302 | 302 | 0 | 0 |
| sv | Paldea | sv-paldea | 400 | 400 | 0 | 0 |
| svdisk | Myrtille | svdisk-blueberry | 243 | 243 | 0 | 0 |
| svmask | Septentria | svmask-kitakami | 200 | 200 | 0 | 0 |
| sw | Galar | sw-galar | 400 | 400 | 0 | 0 |
| swcrown | Couronneige | swcrown-crown-tundra | 210 | 210 | 0 | 0 |
| swisle | Isolarmure | swisle-isle-of-armor | 211 | 211 | 0 | 0 |
| usum | Alola mis à jour | usum-alola | 403 | 403 | 0 | 0 |
| xy | Kalos : Centre | xy-kalos-central | 153 | 153 | 0 | 0 |
| xy | Kalos : Côtes | xy-kalos-coastal | 153 | 153 | 0 | 0 |
| xy | Kalos : Monts | xy-kalos-mountain | 151 | 151 | 0 | 0 |
| y | Kanto | y-kanto | 151 | 151 | 0 | 0 |
| za | Illumis | za-lumiose | 232 | 232 | 0 | 0 |
| zadlc | Extra Illumis | zadlc-hyperspace | 132 | 132 | 0 | 0 |

Pokédex absents du Pokédex actuel mais publiés par pokedata : `sm-melemele`, `sm-akala`, `sm-ulaula`, `sm-poni`, `usum-melemele`, `usum-akala`, `usum-ulaula`, `usum-poni`.

## Catégories (français)

- Espèces avec catégorie française : pokedata **1020** ; identiques au Pokédex : **1020** sur les espèces communes ; différentes : **0** ; absentes de pokedata : **5**.

Absentes de pokedata (catégorie non vérifiée ou en écart entre sources) : 321, 327, 727, 964, 999

