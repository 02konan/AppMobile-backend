-- ============================================================
-- Migration DIVIX LIVE — étape 13 : version des conditions vendeur acceptées
-- ------------------------------------------------------------
-- Enregistre la version des Conditions Vendeur acceptée lors de la
-- candidature (traçabilité / conformité).
-- ============================================================

ALTER TABLE seller_applications
  ADD COLUMN terms_version VARCHAR(20) NULL AFTER status;
