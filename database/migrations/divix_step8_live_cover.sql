-- ============================================================
-- Migration DIVIX LIVE — étape 8 : image de couverture des lives
-- ------------------------------------------------------------
-- Ajoute une image de couverture (URL) affichée sur les cartes de lives
-- et en fond de l'écran de live avant le direct (façon Kaable).
-- ============================================================

ALTER TABLE lives
  ADD COLUMN cover_url VARCHAR(500) NULL AFTER category;
