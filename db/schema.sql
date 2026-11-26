-- =============================================================================
-- pokedata : schéma SQLite v1 (1.1.0 ; 1.0.0 validé le 25/11/2026, 1.1.0 le 26/11/2026)
-- =============================================================================
-- Projet de fans non officiel. Pokémon et tous les noms, textes et données de
-- jeu associés © Nintendo, Creatures Inc., GAME FREAK inc. et The Pokémon
-- Company. Ce schéma (le code) est sous licence MIT.
--
-- Conventions
--   * SQLite >= 3.37 (tables STRICT, json1 intégré). Charger avec
--     PRAGMA foreign_keys = ON.
--   * Capacités et talents : id = id du Pokédex / PokeAPI (option A). L'index
--     interne des jeux (identique jusqu'au talent 298) est rangé dans
--     external_id (system 'game-index').
--   * Identifiants :
--       - entiers « officiels » quand ils existent et sont stables dans les
--         jeux : n° national (espèce), n° de capacité, n° de talent ; ce sont
--         aussi les ids PokeAPI et ceux du Pokédex actuel ;
--       - slugs TEXT lisibles et stables ailleurs : jeu ('sv', 'svmask', 'za'),
--         version ('scarlet'), forme ('6-mega-x', même clé que le Pokédex),
--         type ('fire'), attaque GO ('FIRE_SPIN_FAST', template du GAME_MASTER),
--         langue (BCP 47 : 'fr', 'es-419', 'zh-Hans'…).
--     Ces ids apparaissent tels quels dans les URL de l'API (/api/v1/...) :
--     on ne les renumérote jamais.
--   * Valeurs « par jeu » : une ligne par (entité, jeu). Plus volumineux que des
--     plages de validité, mais explicite, simple à vérifier et à citer, et sans
--     piège pour les jeux hors lignée (Let's Go, Légendes, Champions).
--   * Données GO : elles changent dans le temps et non par jeu ; on utilise des
--     plages de dates valid_from / valid_to (NULL = toujours en vigueur).
--   * Booléens : INTEGER 0/1 avec CHECK. Dates : TEXT ISO 8601 (UTC pour les
--     horodatages, 'YYYY-MM-DD' pour les dates de sortie).
--   * Colonnes extra : TEXT JSON (json_valid) pour les mécaniques propres à un
--     seul jeu (style Rapide/Puissant de Légendes Arceus, recharge de Z-A…).
--   * Provenance : section 13. Chaque ligne d'une table de données est
--     identifiée par (table_name, row_key) où row_key est la clé primaire
--     sérialisée en tableau JSON compact, ex. '["6-mega-x","sv"]'.
--     Exception (1.1.0, migration 0002) : learnset est vérifiée par ensemble,
--     row_key = '[form_id, game_id, method_id]' (voir verification).
--   * Fichiers CSV (1.1.0) : une table = un CSV trié dans db/data/, sauf
--     verification et citation, découpées par table décrite :
--     db/data/verification/<table_name>.csv, db/data/citation/<table_name>.csv.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 0. Métadonnées de la base
-- -----------------------------------------------------------------------------
CREATE TABLE meta (
  key   TEXT PRIMARY KEY,          -- 'schema_version', 'data_version', 'generated_at', 'license_notice'
  value TEXT NOT NULL
) STRICT;

-- Rempli par scripts/build_sqlite.py (schema_version, data_version, generated_at, license_notice).

-- -----------------------------------------------------------------------------
-- 1. Langues (10 langues officielles + 2 écritures auxiliaires du japonais)
-- -----------------------------------------------------------------------------
CREATE TABLE language (
  id          TEXT PRIMARY KEY,    -- code BCP 47
  name_native TEXT NOT NULL,
  is_official INTEGER NOT NULL CHECK (is_official IN (0,1)), -- 1 = langue de jeu officielle
  sort_order  INTEGER NOT NULL,
  pokeapi_id  TEXT,                -- code PokeAPI correspondant (amorçage)
  note        TEXT
) STRICT;

-- Contenu : db/data/language.csv

-- -----------------------------------------------------------------------------
-- 2. Générations, jeux, versions, langues par jeu, Pokédex régionaux
-- -----------------------------------------------------------------------------
CREATE TABLE generation (
  id          INTEGER PRIMARY KEY, -- 1..9
  main_region TEXT                 -- slug de région (FK souple : region défini plus bas)
) STRICT;

CREATE TABLE region (
  id            TEXT PRIMARY KEY,  -- 'kanto', 'hisui', 'paldea', 'kitakami', 'blueberry', 'lumiose'…
  generation_id INTEGER REFERENCES generation(id)
) STRICT;

-- Un « jeu » = un jeu de données cohérent : jeu de base, DLC (cumulatif), remake,
-- service (HOME), jeu mobile (GO) ou jeu dérivé de combat (Champions).
-- Les slugs reprennent ceux du Pokédex actuel (core.json → games[].id).
CREATE TABLE game (
  id             TEXT PRIMARY KEY,  -- 'rb','y','gs',…,'sv','svmask','svdisk','la','za','zadlc','frlgsw','go','home','champions'
  kind           TEXT NOT NULL CHECK (kind IN ('main','remake','legends','dlc','rerelease','service','mobile','battle')),
  generation_id  INTEGER REFERENCES generation(id),  -- NULL pour GO / HOME (hors générations)
  base_game_id   TEXT REFERENCES game(id),           -- DLC → jeu de base ; 'frlgsw' → 'frlg'
  release_date   TEXT,                               -- première sortie mondiale, YYYY-MM-DD
  platform       TEXT,                               -- 'GB','GBA','DS','3DS','Switch','Switch 2','iOS/Android'…
  sort_order     INTEGER NOT NULL,                   -- ordre chronologique
  pokeapi_version_group TEXT,                        -- ex. 'scarlet-violet', 'the-teal-mask'
  is_active_service INTEGER NOT NULL DEFAULT 0 CHECK (is_active_service IN (0,1)), -- GO, HOME, Champions : données évolutives
  note           TEXT
) STRICT;

-- Cartouche / édition jouable (Écarlate, Violet…). ids = ids PokeAPI quand ils existent.
CREATE TABLE version (
  id          TEXT PRIMARY KEY,    -- 'scarlet', 'violet', 'legends-za', 'the-teal-mask-scarlet'…
  game_id     TEXT NOT NULL REFERENCES game(id),
  pokeapi_id  INTEGER UNIQUE,      -- 1..53 (Pokédex actuel : games[].ver[][0])
  sort_order  INTEGER NOT NULL
) STRICT;

-- Langues jouables par jeu (vérifiées : boutique Nintendo, sites officiels, wikis).
-- Répond à « quels jeux ont l'espagnol d'Amérique latine ? ».
CREATE TABLE game_language (
  game_id     TEXT NOT NULL REFERENCES game(id),
  language_id TEXT NOT NULL REFERENCES language(id),
  since_date  TEXT,                -- ajout en cours de vie (ex. HOME 4.0.0, GO 2024)
  since_game_version TEXT,         -- ex. '4.0.0'
  PRIMARY KEY (game_id, language_id)
) STRICT;

-- Mises à jour logicielles des jeux (patchs qui modifient les données).
CREATE TABLE game_patch (
  game_id      TEXT NOT NULL REFERENCES game(id),
  patch        TEXT NOT NULL,      -- '3.0.1', '0.305.0'
  release_date TEXT,
  note         TEXT,
  PRIMARY KEY (game_id, patch)
) STRICT;

-- Pokédex régionaux / listes ('paldea', 'kitakami', 'lumiose', 'hyperspace'…).
CREATE TABLE pokedex (
  id         TEXT PRIMARY KEY,
  game_id    TEXT NOT NULL REFERENCES game(id),
  region_id  TEXT REFERENCES region(id),
  sort_order INTEGER NOT NULL,
  pokeapi_id INTEGER
) STRICT;

-- -----------------------------------------------------------------------------
-- 3. Types et efficacité
-- -----------------------------------------------------------------------------
CREATE TABLE type (
  id            TEXT PRIMARY KEY,  -- 'normal'..'fairy', 'stellar', 'unknown' (???)
  generation_id INTEGER REFERENCES generation(id),
  pokeapi_id    INTEGER,
  go_template   TEXT               -- 'POKEMON_TYPE_FIRE'
) STRICT;

-- Tables d'efficacité : 'gen1', 'gen2-5', 'gen6+', 'go' (multiplicateurs GO 1.6 / 0.625 / 0.390625).
CREATE TABLE type_chart (
  id    TEXT PRIMARY KEY,
  note  TEXT
) STRICT;

CREATE TABLE type_chart_game (      -- quel tableau s'applique à quel jeu
  game_id       TEXT PRIMARY KEY REFERENCES game(id),
  type_chart_id TEXT NOT NULL REFERENCES type_chart(id)
) STRICT;

CREATE TABLE type_efficacy (       -- seules les paires ≠ 1 sont stockées
  type_chart_id  TEXT NOT NULL REFERENCES type_chart(id),
  attacking_type TEXT NOT NULL REFERENCES type(id),
  defending_type TEXT NOT NULL REFERENCES type(id),
  factor         REAL NOT NULL,     -- 0, 0.5, 2 ; GO : 0.390625, 0.625, 1.6
  PRIMARY KEY (type_chart_id, attacking_type, defending_type)
) STRICT;

-- -----------------------------------------------------------------------------
-- 4. Espèces et formes
-- -----------------------------------------------------------------------------
CREATE TABLE growth_rate (
  id      TEXT PRIMARY KEY,         -- 'medium-slow'… (Pokédex : sp.gw)
  formula TEXT
) STRICT;

CREATE TABLE egg_group (
  id TEXT PRIMARY KEY               -- 'monster', 'dragon'…
) STRICT;

CREATE TABLE species (
  id               INTEGER PRIMARY KEY,  -- n° national (Pokédex : core.e[].id, sp/{id}.json)
  slug             TEXT NOT NULL UNIQUE, -- 'pikachu'
  generation_id    INTEGER NOT NULL REFERENCES generation(id),
  evolution_chain_id INTEGER,            -- FK vers evolution_chain (Pokédex : core.chains)
  growth_rate_id   TEXT REFERENCES growth_rate(id),
  gender_rate      INTEGER,              -- -1 asexué, sinon femelles en huitièmes (0..8)
  hatch_cycles     INTEGER,
  is_baby          INTEGER NOT NULL DEFAULT 0 CHECK (is_baby IN (0,1)),
  is_legendary     INTEGER NOT NULL DEFAULT 0 CHECK (is_legendary IN (0,1)),
  is_mythical      INTEGER NOT NULL DEFAULT 0 CHECK (is_mythical IN (0,1)),
  is_ultra_beast   INTEGER NOT NULL DEFAULT 0 CHECK (is_ultra_beast IN (0,1)),
  is_paradox       INTEGER NOT NULL DEFAULT 0 CHECK (is_paradox IN (0,1)),
  has_gender_differences INTEGER NOT NULL DEFAULT 0 CHECK (has_gender_differences IN (0,1))
  -- noms, catégorie (« Pokémon Souris »), étymologies : table translation
) STRICT;

CREATE TABLE species_egg_group (
  species_id   INTEGER NOT NULL REFERENCES species(id),
  egg_group_id TEXT NOT NULL REFERENCES egg_group(id),
  PRIMARY KEY (species_id, egg_group_id)
) STRICT;

CREATE TABLE pokedex_entry (       -- numéros régionaux
  pokedex_id TEXT NOT NULL REFERENCES pokedex(id),
  species_id INTEGER NOT NULL REFERENCES species(id),
  number     INTEGER NOT NULL,
  PRIMARY KEY (pokedex_id, species_id)
) STRICT;

-- Forme = toute variante qui peut différer par ses données OU son apparence.
-- id = clé du Pokédex actuel : '{n° national}' pour la forme par défaut,
-- '{n°}-{suffixe}' sinon ('6-mega-x', '19-alola', '25-partner-cap', '3-gmax',
-- '3-female'). Les costumes GO sont des formes de category 'go-costume'.
CREATE TABLE form (
  id            TEXT PRIMARY KEY,
  species_id    INTEGER NOT NULL REFERENCES species(id),
  slug          TEXT NOT NULL UNIQUE,        -- 'charizard-mega-x'
  category      TEXT NOT NULL CHECK (category IN (
                  'default','regional','mega','primal','gigantamax','alternate',
                  'gender','battle-only','cosmetic','totem','alpha-only','go-costume','event')),
  is_default    INTEGER NOT NULL CHECK (is_default IN (0,1)),
  is_battle_only INTEGER NOT NULL DEFAULT 0 CHECK (is_battle_only IN (0,1)),
  base_form_id  TEXT REFERENCES form(id),    -- méga / gigamax / costume → forme de base (Pokédex : mb)
  introduced_game_id TEXT REFERENCES game(id),
  sort_order    INTEGER NOT NULL,
  pokeapi_pokemon_id INTEGER,                -- ex. 10034 (Pokédex : hs / as)
  pokeapi_form_id    INTEGER,
  note          TEXT
) STRICT;
CREATE INDEX form_species ON form(species_id);

-- Données d'une forme dans un jeu (types, stats, taille…) : une ligne par jeu.
CREATE TABLE form_game (
  form_id       TEXT NOT NULL REFERENCES form(id),
  game_id       TEXT NOT NULL REFERENCES game(id),
  type1_id      TEXT NOT NULL REFERENCES type(id),
  type2_id      TEXT REFERENCES type(id),
  hp            INTEGER, atk INTEGER, def INTEGER,
  spa           INTEGER, spd INTEGER, spe INTEGER,  -- Gén. 1 : spa = spd = Spécial
  height_dm     INTEGER,
  weight_hg     INTEGER,
  base_exp      INTEGER,
  catch_rate    INTEGER,
  base_friendship INTEGER,
  ev_hp INTEGER, ev_atk INTEGER, ev_def INTEGER, ev_spa INTEGER, ev_spd INTEGER, ev_spe INTEGER,
  in_game_data  INTEGER NOT NULL DEFAULT 1 CHECK (in_game_data IN (0,1)), -- présente dans les données du jeu
  extra         TEXT CHECK (extra IS NULL OR json_valid(extra)), -- ex. Légendes : spécimens Baron
  PRIMARY KEY (form_id, game_id)
) STRICT;
CREATE INDEX form_game_game ON form_game(game_id);

-- -----------------------------------------------------------------------------
-- 5. Talents et objets
-- -----------------------------------------------------------------------------
CREATE TABLE ability (
  id            INTEGER PRIMARY KEY, -- id Pokédex/PokeAPI (ref.ab) ; index des jeux dans external_id
  slug          TEXT NOT NULL UNIQUE,
  generation_id INTEGER REFERENCES generation(id)
  -- nom et descriptions par jeu : translation (field 'name', 'flavor', 'effect')
) STRICT;

CREATE TABLE form_ability (
  form_id    TEXT NOT NULL REFERENCES form(id),
  game_id    TEXT NOT NULL REFERENCES game(id),
  slot       TEXT NOT NULL CHECK (slot IN ('1','2','hidden')),
  ability_id INTEGER NOT NULL REFERENCES ability(id),
  PRIMARY KEY (form_id, game_id, slot)
) STRICT;

CREATE TABLE item (
  id           INTEGER PRIMARY KEY,  -- id PokeAPI (les index internes varient selon le jeu → external_id)
  slug         TEXT NOT NULL UNIQUE,
  category     TEXT,                 -- 'mega-stone', 'evolution', 'tm', 'berry', 'held'…
  go_template  TEXT                  -- ex. 'ITEM_SUN_STONE'
) STRICT;

CREATE TABLE item_game (             -- objet présent dans un jeu (+ prix, CT…)
  item_id INTEGER NOT NULL REFERENCES item(id),
  game_id TEXT NOT NULL REFERENCES game(id),
  game_index INTEGER,                -- index interne du jeu
  price   INTEGER,
  extra   TEXT CHECK (extra IS NULL OR json_valid(extra)),
  PRIMARY KEY (item_id, game_id)
) STRICT;

CREATE TABLE form_held_item (        -- objets tenus à l'état sauvage
  form_id    TEXT NOT NULL REFERENCES form(id),
  version_id TEXT NOT NULL REFERENCES version(id),
  item_id    INTEGER NOT NULL REFERENCES item(id),
  rarity_pct INTEGER,
  PRIMARY KEY (form_id, version_id, item_id)
) STRICT;

-- -----------------------------------------------------------------------------
-- 6. Capacités (par jeu) et movesets
-- -----------------------------------------------------------------------------
CREATE TABLE move (
  id            INTEGER PRIMARY KEY,  -- n° officiel (= PokeAPI, Pokédex : moves.json)
  slug          TEXT NOT NULL UNIQUE,
  generation_id INTEGER REFERENCES generation(id),
  kind          TEXT NOT NULL DEFAULT 'normal' CHECK (kind IN ('normal','z','max','gmax','shadow'))
) STRICT;

-- Valeurs d'une capacité dans un jeu (elles changent : Puissance, Précision, PP…).
CREATE TABLE move_game (
  move_id       INTEGER NOT NULL REFERENCES move(id),
  game_id       TEXT NOT NULL REFERENCES game(id),
  type_id       TEXT NOT NULL REFERENCES type(id),
  damage_class  TEXT NOT NULL CHECK (damage_class IN ('physical','special','status')),
  power         INTEGER,            -- NULL = « — » ; 1 = variable
  accuracy      INTEGER,            -- NULL = ne rate jamais
  pp            INTEGER,
  priority      INTEGER NOT NULL DEFAULT 0,
  effect_chance INTEGER,
  target        TEXT,               -- 'selected-pokemon', 'all-opponents'…
  makes_contact INTEGER CHECK (makes_contact IN (0,1)),
  is_usable     INTEGER NOT NULL DEFAULT 1 CHECK (is_usable IN (0,1)), -- 0 = capacité retirée (« ne peut pas être utilisée »)
  flags         TEXT CHECK (flags IS NULL OR json_valid(flags)),  -- ["sound","punch","protect"…]
  extra         TEXT CHECK (extra IS NULL OR json_valid(extra)),  -- Légendes Arceus : styles ; Z-A : recharge, portée…
  PRIMARY KEY (move_id, game_id)
) STRICT;

CREATE TABLE move_effect_stat (     -- variations de stats / altérations infligées, par jeu
  move_id    INTEGER NOT NULL,
  game_id    TEXT NOT NULL,
  target     TEXT NOT NULL CHECK (target IN ('user','target')),
  effect     TEXT NOT NULL,         -- 'atk','def',…,'burn','paralysis','flinch'
  amount     INTEGER,               -- crans (±1..±6) ou NULL pour une altération
  chance_pct INTEGER,
  PRIMARY KEY (move_id, game_id, target, effect),
  FOREIGN KEY (move_id, game_id) REFERENCES move_game(move_id, game_id)
) STRICT;

CREATE TABLE learn_method (
  id TEXT PRIMARY KEY  -- 'level-up','machine','egg','tutor','evolution','reminder','event',
                       -- 'form-change','mastery'(Légendes Arceus),'plus'(Z-A),'stadium-surfing-pikachu'…
) STRICT;

-- CT / CS / DT / CT Z-A : numéro par jeu (Pokédex : tm.json « CT108 »).
CREATE TABLE machine (
  game_id  TEXT NOT NULL REFERENCES game(id),
  label    TEXT NOT NULL,           -- 'TM108', 'TR12', 'HM03' (libellé neutre ; noms localisés via translation)
  move_id  INTEGER NOT NULL REFERENCES move(id),
  item_id  INTEGER REFERENCES item(id),
  PRIMARY KEY (game_id, label)
) STRICT;

CREATE TABLE learnset (
  form_id      TEXT NOT NULL REFERENCES form(id),
  game_id      TEXT NOT NULL REFERENCES game(id),
  move_id      INTEGER NOT NULL REFERENCES move(id),
  method_id    TEXT NOT NULL REFERENCES learn_method(id),
  level        INTEGER NOT NULL DEFAULT 0,  -- 0 si sans objet ; 1 + is_evolution… selon méthode
  version_id   TEXT REFERENCES version(id), -- NULL = toutes les versions du jeu (ex. tuteurs exclusifs)
  sort_order   INTEGER NOT NULL DEFAULT 0,  -- ordre d'apprentissage au même niveau
  extra        TEXT CHECK (extra IS NULL OR json_valid(extra)), -- Légendes : niveau de maîtrise ; Z-A : coût Plus
  PRIMARY KEY (form_id, game_id, move_id, method_id, level)
) STRICT;
CREATE INDEX learnset_move ON learnset(move_id, game_id);

-- -----------------------------------------------------------------------------
-- 7. Évolutions
-- -----------------------------------------------------------------------------
CREATE TABLE evolution_chain (
  id            INTEGER PRIMARY KEY, -- = PokeAPI evolution-chain id (Pokédex : core.chains)
  baby_item_id  INTEGER REFERENCES item(id)
) STRICT;

CREATE TABLE evolution (
  id            INTEGER PRIMARY KEY,
  from_form_id  TEXT NOT NULL REFERENCES form(id),
  to_form_id    TEXT NOT NULL REFERENCES form(id),
  UNIQUE (from_form_id, to_form_id)
) STRICT;

-- Méthode d'évolution, qui peut varier selon le jeu (Pokédex : evo.json, variantes « v »).
CREATE TABLE evolution_method (
  evolution_id  INTEGER NOT NULL REFERENCES evolution(id),
  game_id       TEXT NOT NULL REFERENCES game(id),
  variant       INTEGER NOT NULL DEFAULT 1,  -- plusieurs méthodes possibles dans un même jeu
  trigger       TEXT NOT NULL CHECK (trigger IN ('level-up','use-item','trade','shed','spin','tower','three-critical-hits',
                  'take-damage','agile-style','strong-style','recoil-damage','walk','other','go-candy')),
  min_level     INTEGER,
  item_id       INTEGER REFERENCES item(id),
  held_item_id  INTEGER REFERENCES item(id),
  known_move_id INTEGER REFERENCES move(id),
  known_move_type_id TEXT REFERENCES type(id),
  location_id   TEXT,                        -- FK souple vers location(id)
  time_of_day   TEXT CHECK (time_of_day IN ('day','night','dusk','morning','evening')),
  gender        TEXT CHECK (gender IN ('male','female')),
  min_friendship INTEGER,
  min_affection INTEGER,
  conditions    TEXT CHECK (conditions IS NULL OR json_valid(conditions)), -- météo, stats relatives, console renversée…
  PRIMARY KEY (evolution_id, game_id, variant)
) STRICT;

-- -----------------------------------------------------------------------------
-- 8. Lieux et disponibilité
-- -----------------------------------------------------------------------------
-- Lieu (stable entre jeux : « Route 1 » de Kanto existe dans RB, FRLG, LGPE, HGSS…).
CREATE TABLE location (
  id         TEXT PRIMARY KEY,       -- 'kanto-route-1', 'paldea-south-province-area-one'
  region_id  TEXT REFERENCES region(id),
  pokeapi_id INTEGER
) STRICT;

-- Sous-zone (étage d'une grotte, secteur, antre, zone sauvage de Z-A…).
CREATE TABLE location_area (
  id          TEXT PRIMARY KEY,      -- 'mt-moon-b1f'
  location_id TEXT NOT NULL REFERENCES location(id),
  pokeapi_id  INTEGER
) STRICT;

CREATE TABLE location_game (         -- lieu présent dans un jeu
  location_id TEXT NOT NULL REFERENCES location(id),
  game_id     TEXT NOT NULL REFERENCES game(id),
  PRIMARY KEY (location_id, game_id)
) STRICT;

CREATE TABLE encounter_method (
  id TEXT PRIMARY KEY  -- 'walk','surf','old-rod','headbutt','sos','gift','static','raid-max','raid-tera',
                       -- 'outbreak','alpha','wild-zone','rift'(Z-A),'roaming'… (Pokédex : loc.m)
) STRICT;

CREATE TABLE encounter_condition (
  id TEXT PRIMARY KEY  -- 'time-night','weather-rain','season-winter','radio-off','slot2-firered','post-game'…
                       -- (Pokédex : loc.c)
) STRICT;

CREATE TABLE encounter (
  id            INTEGER PRIMARY KEY,
  form_id       TEXT NOT NULL REFERENCES form(id),
  version_id    TEXT NOT NULL REFERENCES version(id),
  area_id       TEXT NOT NULL REFERENCES location_area(id),
  method_id     TEXT NOT NULL REFERENCES encounter_method(id),
  min_level     INTEGER,
  max_level     INTEGER,
  rate_pct      REAL,                -- taux d'apparition si connu
  is_alpha      INTEGER NOT NULL DEFAULT 0 CHECK (is_alpha IN (0,1)),
  shiny_locked  INTEGER NOT NULL DEFAULT 0 CHECK (shiny_locked IN (0,1)),
  extra         TEXT CHECK (extra IS NULL OR json_valid(extra))
) STRICT;
CREATE INDEX encounter_form ON encounter(form_id, version_id);
CREATE INDEX encounter_area ON encounter(area_id);

CREATE TABLE encounter_condition_link (
  encounter_id INTEGER NOT NULL REFERENCES encounter(id) ON DELETE CASCADE,
  condition_id TEXT NOT NULL REFERENCES encounter_condition(id),
  PRIMARY KEY (encounter_id, condition_id)
) STRICT;

-- Comment obtenir une forme dans un jeu, au-delà des rencontres sauvages
-- (Pokédex : sp.pln, trade.json, « Hors dex »).
CREATE TABLE availability (
  form_id    TEXT NOT NULL REFERENCES form(id),
  version_id TEXT NOT NULL REFERENCES version(id),
  status     TEXT NOT NULL CHECK (status IN ('wild','evolve','breed','gift','trade-version-exclusive',
                'transfer','event','unobtainable','storable-only')),
  detail     TEXT,                   -- clé de texte libre, traduite via translation (entity 'availability')
  in_regional_dex INTEGER CHECK (in_regional_dex IN (0,1)),
  PRIMARY KEY (form_id, version_id, status)
) STRICT;

-- Chromatiques : taux et verrous par jeu (Pokédex : shiny.json).
CREATE TABLE shiny_rule (
  game_id    TEXT NOT NULL REFERENCES game(id),
  method     TEXT NOT NULL,          -- 'base','masuda','charm','outbreak','sandwich-lvl3'…
  odds       TEXT NOT NULL,          -- '1/4096'
  conditions TEXT CHECK (conditions IS NULL OR json_valid(conditions)),
  PRIMARY KEY (game_id, method)
) STRICT;

CREATE TABLE shiny_lock (
  form_id TEXT NOT NULL REFERENCES form(id),
  game_id TEXT NOT NULL REFERENCES game(id),
  note    TEXT,
  PRIMARY KEY (form_id, game_id)
) STRICT;

-- -----------------------------------------------------------------------------
-- 9. Pokémon GO
-- -----------------------------------------------------------------------------
CREATE TABLE go_cp_multiplier (      -- CPM par niveau (1 à 55, demi-niveaux)
  level REAL PRIMARY KEY,
  cpm   REAL NOT NULL
) STRICT;

-- Stats et paramètres GO d'une forme, versionnés dans le temps (ajustements de stats).
CREATE TABLE go_pokemon (
  form_id        TEXT NOT NULL REFERENCES form(id),
  valid_from     TEXT NOT NULL,       -- date d'effet (YYYY-MM-DD)
  valid_to       TEXT,                -- NULL = en vigueur
  template_id    TEXT,                -- 'V0006_POKEMON_CHARIZARD'
  base_atk       INTEGER NOT NULL,
  base_def       INTEGER NOT NULL,
  base_sta       INTEGER NOT NULL,
  type1_id       TEXT NOT NULL REFERENCES type(id),
  type2_id       TEXT REFERENCES type(id),
  buddy_km       REAL,
  candy_to_evolve INTEGER,
  third_move_stardust INTEGER,
  third_move_candy    INTEGER,
  purify_stardust INTEGER,
  purify_candy    INTEGER,
  base_capture_rate REAL,
  base_flee_rate    REAL,
  extra          TEXT CHECK (extra IS NULL OR json_valid(extra)), -- énergie méga, Dynamax…
  PRIMARY KEY (form_id, valid_from)
) STRICT;

-- Sorties GO par variante (normale, chromatique, Obscur, Dynamax, Gigamax, costume…).
CREATE TABLE go_release (
  form_id     TEXT NOT NULL REFERENCES form(id),
  variant     TEXT NOT NULL CHECK (variant IN ('normal','shiny','shadow','shadow-shiny','purified',
                'dynamax','gigantamax','dynamax-shiny','gigantamax-shiny','mega','lucky-only')),
  released_on TEXT,                   -- NULL = pas encore sortie
  methods     TEXT CHECK (methods IS NULL OR json_valid(methods)), -- ["wild","raid","egg","research","rocket"…]
  is_regional INTEGER NOT NULL DEFAULT 0 CHECK (is_regional IN (0,1)),
  region_note TEXT,
  PRIMARY KEY (form_id, variant)
) STRICT;

CREATE TABLE go_move (
  id         TEXT PRIMARY KEY,        -- 'FIRE_SPIN_FAST', 'BLAST_BURN' (Pokédex : go.json moves)
  move_id    INTEGER REFERENCES move(id), -- capacité équivalente de la série principale
  kind       TEXT NOT NULL CHECK (kind IN ('fast','charged','max'))
) STRICT;

-- Valeurs PvE et PvP d'une attaque, versionnées dans le temps (rééquilibrages).
CREATE TABLE go_move_stats (
  go_move_id     TEXT NOT NULL REFERENCES go_move(id),
  valid_from     TEXT NOT NULL,
  valid_to       TEXT,
  type_id        TEXT NOT NULL REFERENCES type(id),
  pve_power      INTEGER,
  pve_energy     INTEGER,             -- gain (rapide) ou coût (chargée, négatif dans le GAME_MASTER)
  pve_duration_ms INTEGER,
  pve_damage_window_start_ms INTEGER,
  pve_damage_window_end_ms   INTEGER,
  pvp_power      INTEGER,
  pvp_energy     INTEGER,
  pvp_turns      INTEGER,             -- attaques rapides : durée en tours
  pvp_buffs      TEXT CHECK (pvp_buffs IS NULL OR json_valid(pvp_buffs)), -- {"chance":0.3,"self_atk":1…}
  PRIMARY KEY (go_move_id, valid_from)
) STRICT;

CREATE TABLE go_learnset (
  form_id    TEXT NOT NULL REFERENCES form(id),
  go_move_id TEXT NOT NULL REFERENCES go_move(id),
  status     TEXT NOT NULL CHECK (status IN ('normal','elite','legacy','shadow-only','purified-only','event')),
  valid_from TEXT NOT NULL DEFAULT '2016-07-06',
  valid_to   TEXT,
  PRIMARY KEY (form_id, go_move_id, valid_from)
) STRICT;

CREATE TABLE go_costume (            -- détails des costumes (la forme est dans form, category 'go-costume')
  form_id     TEXT PRIMARY KEY REFERENCES form(id),
  event_key   TEXT,                   -- 'Fall2019', 'Jan2020' (Pokédex : costumes.json x)
  first_seen  TEXT,
  shiny       INTEGER CHECK (shiny IN (0,1))
) STRICT;

-- -----------------------------------------------------------------------------
-- 10. Combats, raids et formats
-- -----------------------------------------------------------------------------
-- Constantes de combat par jeu (critique, STAB, Téra, météo…).
CREATE TABLE battle_constant (
  game_id TEXT NOT NULL REFERENCES game(id),
  key     TEXT NOT NULL,              -- 'crit_multiplier','stab','stab_tera_same','stage_multipliers','weather_boost_go'…
  value   TEXT NOT NULL,              -- nombre ou JSON
  unit    TEXT,
  note    TEXT,
  PRIMARY KEY (game_id, key)
) STRICT;

-- Effets de terrain : météo, champs, salles, Gravité… et leurs modificateurs.
CREATE TABLE field_effect (
  id   TEXT PRIMARY KEY,              -- 'rain','sun','sandstorm','snow','hail','electric-terrain','gravity','go-weather-windy'…
  kind TEXT NOT NULL CHECK (kind IN ('weather','terrain','room','other','go-weather'))
) STRICT;

CREATE TABLE field_effect_modifier (
  field_effect_id TEXT NOT NULL REFERENCES field_effect(id),
  game_id         TEXT NOT NULL REFERENCES game(id),
  target          TEXT NOT NULL,      -- 'type:fire', 'stat:spd:type:rock', 'move:solar-beam'…
  multiplier      REAL,
  note            TEXT,
  PRIMARY KEY (field_effect_id, game_id, target)
) STRICT;

-- Règles générales d'un palier de raid (étoiles SV, antre É/B, niveau GO, Combat Max GO).
CREATE TABLE raid_tier (
  game_id      TEXT NOT NULL REFERENCES game(id),
  tier         TEXT NOT NULL,         -- '5','6','7' ; GO : '1','3','5','mega','shadow-5','max-6'…
  kind         TEXT NOT NULL CHECK (kind IN ('max-raid','tera-raid','go-raid','go-max-battle','go-shadow-raid')),
  boss_level   INTEGER,
  boss_hp      INTEGER,               -- GO : PV du boss
  boss_cpm     REAL,                  -- GO
  time_limit_s INTEGER,
  rules        TEXT CHECK (rules IS NULL OR json_valid(rules)), -- boucliers, actions spéciales…
  PRIMARY KEY (game_id, tier, kind)
) STRICT;

-- Un boss précis (Pokédex : raids.json, raid-bosses.json, tera7.json).
CREATE TABLE raid_boss (
  id           INTEGER PRIMARY KEY,
  game_id      TEXT NOT NULL,
  tier         TEXT NOT NULL,
  kind         TEXT NOT NULL,
  form_id      TEXT NOT NULL REFERENCES form(id),
  version_id   TEXT REFERENCES version(id),   -- exclusivité de version
  location_id  TEXT REFERENCES location(id),  -- antre / lieu fixe
  tera_type_id TEXT REFERENCES type(id),
  is_gigantamax INTEGER NOT NULL DEFAULT 0 CHECK (is_gigantamax IN (0,1)),
  rate_pct     REAL,
  start_at     TEXT,                  -- événements datés (raids 7★, GO)
  end_at       TEXT,
  shiny_possible INTEGER CHECK (shiny_possible IN (0,1)),
  moves        TEXT CHECK (moves IS NULL OR json_valid(moves)),
  extra        TEXT CHECK (extra IS NULL OR json_valid(extra)), -- actions spéciales, récompenses
  FOREIGN KEY (game_id, tier, kind) REFERENCES raid_tier(game_id, tier, kind)
) STRICT;
CREATE INDEX raid_boss_form ON raid_boss(form_id);

-- Formats / règlements (Champions, séries classées SV, ligues GO).
CREATE TABLE battle_format (
  id         TEXT PRIMARY KEY,        -- 'champions-reg-a','sv-reg-h','go-great-league'
  game_id    TEXT NOT NULL REFERENCES game(id),
  start_date TEXT,
  end_date   TEXT,
  rules      TEXT CHECK (rules IS NULL OR json_valid(rules)) -- plafond PC, clauses, niveau…
) STRICT;

CREATE TABLE battle_format_form (
  format_id TEXT NOT NULL REFERENCES battle_format(id),
  form_id   TEXT NOT NULL REFERENCES form(id),
  allowed   INTEGER NOT NULL CHECK (allowed IN (0,1)),
  PRIMARY KEY (format_id, form_id)
) STRICT;

-- -----------------------------------------------------------------------------
-- 11. Cartes (liens externes et coordonnées, AUCUNE image stockée)
-- -----------------------------------------------------------------------------
CREATE TABLE game_map (
  id          TEXT PRIMARY KEY,       -- 'serebii-sv-paldea', 'pokepedia-za-illumis'
  game_id     TEXT NOT NULL REFERENCES game(id),
  source_id   TEXT NOT NULL,          -- FK vers source(id) (section 13)
  url         TEXT NOT NULL,          -- page de la carte sur le site source (jamais d'image copiée)
  width_px    INTEGER,                -- dimensions de référence de la carte source
  height_px   INTEGER,
  coord_system TEXT NOT NULL DEFAULT 'pixel-top-left' CHECK (coord_system IN ('pixel-top-left','normalized','game-units')),
  retrieved_at TEXT,
  note        TEXT
) STRICT;

CREATE TABLE map_position (
  map_id      TEXT NOT NULL REFERENCES game_map(id),
  location_id TEXT NOT NULL REFERENCES location(id),
  area_id     TEXT REFERENCES location_area(id),
  x           REAL,                   -- point (centre) …
  y           REAL,
  shape       TEXT CHECK (shape IS NULL OR json_valid(shape)), -- … ou polygone [[x,y],…]
  PRIMARY KEY (map_id, location_id, area_id)
) STRICT;

-- -----------------------------------------------------------------------------
-- 12. Traductions (générique) et identifiants externes
-- -----------------------------------------------------------------------------
-- Un texte = (entité, champ, langue[, jeu ou version]).
-- entity_type : 'species','form','move','ability','item','type','location','location_area',
--   'game','version','region','pokedex','nature','go_move','availability','machine'…
-- field : 'name','genus','flavor','effect','short_effect','form_name'…
-- Textes de jeu uniquement : aucune prose rédigée par un wiki (décision du 25/11/2026).
-- Les textes qui varient selon le jeu (descriptions, Pokédex) portent game_id
-- ou version_id ; NULL = texte commun à tous les jeux.
CREATE TABLE translation (
  entity_type TEXT NOT NULL,
  entity_id   TEXT NOT NULL,          -- id sérialisé en texte ('25', '6-mega-x', 'fire')
  field       TEXT NOT NULL,
  language_id TEXT NOT NULL REFERENCES language(id),
  game_id     TEXT REFERENCES game(id),
  version_id  TEXT REFERENCES version(id),
  text        TEXT NOT NULL,
  is_official INTEGER NOT NULL DEFAULT 1 CHECK (is_official IN (0,1)) -- 0 = traduction de fan (ex. jeux jamais sortis dans la langue)
) STRICT;
CREATE UNIQUE INDEX translation_key ON translation(
  entity_type, entity_id, field, language_id, IFNULL(game_id, ''), IFNULL(version_id, ''));
CREATE INDEX translation_search ON translation(language_id, field, text);

CREATE TABLE external_id (
  entity_type TEXT NOT NULL,
  entity_id   TEXT NOT NULL,
  system      TEXT NOT NULL,          -- 'pokeapi','showdown','bulbapedia','serebii','pokepedia','go-template','game-index:sv','pokedex-legacy'
  value       TEXT NOT NULL,
  PRIMARY KEY (entity_type, entity_id, system)
) STRICT;

-- Petites tables de référence complémentaires
CREATE TABLE nature (
  id         TEXT PRIMARY KEY,        -- 'adamant'
  increased  TEXT,                    -- 'atk'
  decreased  TEXT                     -- 'spa'
) STRICT;

-- -----------------------------------------------------------------------------
-- 13. Provenance, vérification, désaccords, journal
-- -----------------------------------------------------------------------------
-- Source = site ou extraction ; tier fixe la règle de résolution :
--   1 = données extraites des jeux (datamines publics, dumps de texte) → font foi
--   2 = encyclopédies de référence (Bulbapedia, Serebii, Poképédia…) → vote 2 sur 3
--   3 = amorçage / agrégateurs (PokeAPI, veekun) → jamais seuls pour « vérifié »
--   4 = officiel non extrait (pokemon.com, boutique Nintendo, communiqués)
CREATE TABLE source (
  id        TEXT PRIMARY KEY,         -- 'game-sv-dump','pokeminers-gm','bulbapedia','serebii','pokepedia','pokeapi'…
  name      TEXT NOT NULL,
  tier      INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 4),
  base_url  TEXT,
  license   TEXT,                     -- 'CC BY-NC-SA 2.5', 'CC BY-NC-SA 3.0 FR', 'BSD-3' …
  note      TEXT
) STRICT;

-- Document précis consulté (page de wiki à une révision, fichier de dump à un commit…).
-- content_sha256 = empreinte du contenu utile : si elle ne change pas, rien n'est revérifié.
CREATE TABLE source_document (
  id             INTEGER PRIMARY KEY,
  source_id      TEXT NOT NULL REFERENCES source(id),
  locator        TEXT NOT NULL,       -- URL ou chemin dans le dump
  revision       TEXT,                -- oldid de wiki, commit git, version du jeu
  retrieved_at   TEXT NOT NULL,
  content_sha256 TEXT NOT NULL,
  UNIQUE (source_id, locator, content_sha256)
) STRICT;
CREATE INDEX source_document_locator ON source_document(source_id, locator, retrieved_at);

-- Citation : telle source dit telle valeur pour telle ligne / colonne.
CREATE TABLE citation (
  id              INTEGER PRIMARY KEY,
  table_name      TEXT NOT NULL,
  row_key         TEXT NOT NULL,      -- clé primaire en JSON : '["6-mega-x","sv"]' ; learnset : '[form,jeu,méthode]'
  column_name     TEXT NOT NULL DEFAULT '*',  -- '*' = la ligne entière (learnset : l'ensemble)
  document_id     INTEGER NOT NULL REFERENCES source_document(id),
  observed_value  TEXT,               -- valeur lue (normalisée) ; learnset : {"n": taille, "sha256": empreinte de l'ensemble lu}
  agrees          INTEGER NOT NULL CHECK (agrees IN (0,1)), -- 1 = conforme à la valeur retenue
  UNIQUE (table_name, row_key, column_name, document_id)
) STRICT;
CREATE INDEX citation_row ON citation(table_name, row_key);

-- Statut de vérification courant d'une donnée.
-- learnset (1.1.0) : une ligne par ensemble (forme × jeu × méthode), row_key = '["25","sv","machine"]',
-- column_name '*', value_sha256 = empreinte de la liste triée [move_id, level, version_id] de l'ensemble.
-- Les capacités en plus / en moins selon chaque source sont dans discrepancy.alternatives (missing / extra).
CREATE TABLE verification (
  table_name     TEXT NOT NULL,
  row_key        TEXT NOT NULL,
  column_name    TEXT NOT NULL DEFAULT '*',
  status         TEXT NOT NULL CHECK (status IN (
                   'seeded',            -- importée d'une amorce, pas encore croisée
                   'game-data',         -- confirmée par extraction des jeux
                   'majority',          -- 2 sources sur 3 concordantes
                   'unanimous',         -- toutes les sources consultées concordent
                   'disputed',          -- désaccord non tranché (voir discrepancy)
                   'single-source',     -- une seule source existe (indiqué dans l'API)
                   'manual')),          -- tranchée à la main, justification dans discrepancy
  value_sha256   TEXT NOT NULL,       -- empreinte de la valeur retenue
  sources_fingerprint TEXT NOT NULL,  -- sha256 des content_sha256 cités (triés) : change ⇒ revérifier
  verified_at    TEXT NOT NULL,
  update_id      INTEGER REFERENCES update_log(id),
  PRIMARY KEY (table_name, row_key, column_name)
) STRICT;
CREATE INDEX verification_status ON verification(status);

-- Désaccords entre sources (gardés même une fois tranchés).
CREATE TABLE discrepancy (
  id            INTEGER PRIMARY KEY,
  table_name    TEXT NOT NULL,
  row_key       TEXT NOT NULL,
  column_name   TEXT NOT NULL DEFAULT '*',
  chosen_value  TEXT,
  rule          TEXT NOT NULL CHECK (rule IN ('game-data','majority','manual','open')),
  alternatives  TEXT NOT NULL CHECK (json_valid(alternatives)), -- [{"source":"serebii","value":"90","document_id":12},…]
  note          TEXT,
  opened_update_id INTEGER REFERENCES update_log(id),
  closed_update_id INTEGER REFERENCES update_log(id)
) STRICT;
CREATE INDEX discrepancy_row ON discrepancy(table_name, row_key);

-- Journal des mises à jour (une entrée par passage du pipeline).
CREATE TABLE update_log (
  id             INTEGER PRIMARY KEY,
  started_at     TEXT NOT NULL,
  finished_at    TEXT,
  kind           TEXT NOT NULL CHECK (kind IN ('weekly','release','correction','schema','initial')),
  trigger        TEXT,                -- 'Légendes Z-A 2.0.0', 'GAME_MASTER 2026-11-24', 'hebdo S48'
  data_version   TEXT NOT NULL,       -- ex. '2026.11.25' (données)
  schema_version TEXT NOT NULL,
  git_commit     TEXT,
  summary        TEXT,                -- résumé lisible (repris dans CHANGELOG.md)
  stats          TEXT CHECK (stats IS NULL OR json_valid(stats)) -- {"inserted":12,"updated":3,"verified":420,"disputed":1}
) STRICT;

CREATE TABLE update_log_item (
  update_id   INTEGER NOT NULL REFERENCES update_log(id),
  table_name  TEXT NOT NULL,
  row_key     TEXT NOT NULL,
  column_name TEXT NOT NULL DEFAULT '*',
  action      TEXT NOT NULL CHECK (action IN ('insert','update','delete','verify','dispute','resolve')),
  old_value   TEXT,
  new_value   TEXT,
  document_ids TEXT CHECK (document_ids IS NULL OR json_valid(document_ids)), -- [12,57]
  PRIMARY KEY (update_id, table_name, row_key, column_name, action)
) STRICT;

-- -----------------------------------------------------------------------------
-- 14. Vues utiles (exports et migration du Pokédex)
-- -----------------------------------------------------------------------------
-- Noms d'espèces dans les 10 langues, une colonne par langue.
CREATE VIEW v_species_names AS
SELECT s.id AS species_id,
  MAX(CASE WHEN t.language_id = 'ja'      THEN t.text END) AS ja,
  MAX(CASE WHEN t.language_id = 'ja-Latn' THEN t.text END) AS ja_latn,
  MAX(CASE WHEN t.language_id = 'en'      THEN t.text END) AS en,
  MAX(CASE WHEN t.language_id = 'fr'      THEN t.text END) AS fr,
  MAX(CASE WHEN t.language_id = 'de'      THEN t.text END) AS de,
  MAX(CASE WHEN t.language_id = 'it'      THEN t.text END) AS it,
  MAX(CASE WHEN t.language_id = 'es'      THEN t.text END) AS es,
  MAX(CASE WHEN t.language_id = 'es-419'  THEN t.text END) AS es_419,
  MAX(CASE WHEN t.language_id = 'ko'      THEN t.text END) AS ko,
  MAX(CASE WHEN t.language_id = 'zh-Hans' THEN t.text END) AS zh_hans,
  MAX(CASE WHEN t.language_id = 'zh-Hant' THEN t.text END) AS zh_hant
FROM species s
LEFT JOIN translation t
  ON t.entity_type = 'species' AND t.entity_id = CAST(s.id AS TEXT)
 AND t.field = 'name' AND t.game_id IS NULL AND t.version_id IS NULL
GROUP BY s.id;

-- Données à revérifier : documents dont l'empreinte a changé depuis la vérification.
-- (Le pipeline calcule le nouveau sources_fingerprint et compare ; cette vue liste
--  les lignes jamais croisées ou en désaccord.)
CREATE VIEW v_needs_review AS
SELECT table_name, row_key, column_name, status, verified_at
FROM verification
WHERE status IN ('seeded','disputed');

-- Résumé de vérification par table (pour le journal et la page « état des données »).
CREATE VIEW v_verification_summary AS
SELECT table_name, status, COUNT(*) AS n
FROM verification
GROUP BY table_name, status;
