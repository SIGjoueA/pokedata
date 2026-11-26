-- =============================================================================
-- pokedata : migration 0004 — schéma 1.2.0 → 1.3.0 (26/11/2026)
-- =============================================================================
-- Décision validée : statut de disponibilité dédié aux changements de forme.
--
-- availability.status accepte une valeur de plus : 'form-change' (la forme
-- s'obtient en changeant la forme d'un Pokémon obtenable dans la même version :
-- forme femelle distincte, Méga-Évolution, Primo-Résurgence, Gigamax, forme de
-- combat, objet ou action ; le type de changement va dans availability.detail).
--
-- Ajout seulement : aucune valeur retirée, aucune ligne supprimée, aucune table
-- ni colonne renommée ; l'API v1 reste compatible (une valeur d'énumération en
-- plus). La contrainte CHECK est élargie sur place (procédure SQLite pour
-- assouplir une contrainte CHECK : https://www.sqlite.org/lang_altertable.html,
-- section 7), sans reconstruire la table.

PRAGMA writable_schema = ON;
UPDATE sqlite_master
  SET sql = replace(sql, '''unobtainable'',''storable-only'')', '''unobtainable'',''storable-only'',''form-change'')')
  WHERE type = 'table' AND name = 'availability';
PRAGMA writable_schema = RESET;
PRAGMA writable_schema = OFF;

UPDATE meta SET value = '1.3.0' WHERE key = 'schema_version';
