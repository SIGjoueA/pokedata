-- =============================================================================
-- pokedata : migration 0003 — schéma 1.1.0 → 1.2.0 (26/11/2026)
-- =============================================================================
-- Décision validée : statut de disponibilité dédié aux échanges en jeu.
--
-- availability.status accepte une valeur de plus : 'npc-trade' (la forme est
-- obtenue par un échange avec un personnage du jeu). Ajout seulement : aucune
-- valeur existante n'est retirée, l'API v1 reste compatible (une valeur
-- d'énumération en plus).
--
-- Avant 1.2.0, ces échanges étaient rangés en status 'gift' avec
-- detail = 'npc-trade' (ou une liste contenant 'npc-trade'). Ils sont reclassés :
-- une ligne 'npc-trade' (detail NULL) et, s'il reste un autre moyen de don, la
-- ligne 'gift' garde le reste de sa liste.
--
-- SQLite ne sait pas modifier une contrainte CHECK : la table est reconstruite.

CREATE TABLE availability_new (
  form_id    TEXT NOT NULL REFERENCES form(id),
  version_id TEXT NOT NULL REFERENCES version(id),
  status     TEXT NOT NULL CHECK (status IN ('wild','evolve','breed','gift','npc-trade','trade-version-exclusive',
                'transfer','event','unobtainable','storable-only')),
  detail     TEXT,                   -- clé de texte libre, traduite via translation (entity 'availability')
  in_regional_dex INTEGER CHECK (in_regional_dex IN (0,1)),
  PRIMARY KEY (form_id, version_id, status)
) STRICT;

INSERT INTO availability_new SELECT form_id, version_id, status, detail, in_regional_dex FROM availability;

-- reclassement des échanges en jeu
INSERT OR IGNORE INTO availability_new (form_id, version_id, status, detail, in_regional_dex)
  SELECT form_id, version_id, 'npc-trade', NULL, in_regional_dex FROM availability
  WHERE status = 'gift' AND (',' || detail || ',') LIKE '%,npc-trade,%';
DELETE FROM availability_new WHERE status = 'gift' AND detail = 'npc-trade';
UPDATE availability_new
  SET detail = NULLIF(TRIM(REPLACE(REPLACE(',' || detail || ',', ',npc-trade,', ','), ',gift,', ','), ','), '')
  WHERE status = 'gift' AND (',' || detail || ',') LIKE '%,npc-trade,%';

DROP TABLE availability;
ALTER TABLE availability_new RENAME TO availability;

UPDATE meta SET value = '1.2.0' WHERE key = 'schema_version';
