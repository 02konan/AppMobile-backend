-- ============================================================
-- Migration DIVIX LIVE — étape 10 : image de couverture des boutiques
-- ------------------------------------------------------------
-- Ajoute une bannière (URL) affichée en haut de la vitrine d'une boutique,
-- en complément du logo.
-- ============================================================

ALTER TABLE shops
  ADD COLUMN cover_url VARCHAR(500) NULL AFTER logo_url;
