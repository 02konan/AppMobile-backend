-- ============================================================
-- Migration DIVIX LIVE — étape 9 : présence des spectateurs (compteur de vues)
-- ------------------------------------------------------------
-- Table de présence : chaque spectateur (connecté ou anonyme, identifié par
-- une clé stable) signale régulièrement sa présence (heartbeat). Le nombre de
-- vues d'un live = nombre de spectateurs vus dans une fenêtre récente.
-- Les lignes périmées sont purgées côté application à chaque battement.
--
-- NB : live_id doit être INT UNSIGNED pour correspondre au type de lives.id
-- (sinon MySQL refuse la clé étrangère avec l'erreur #1005 / errno 150).
-- ============================================================

CREATE TABLE IF NOT EXISTS live_viewers (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  live_id     INT UNSIGNED NOT NULL,
  viewer_key  VARCHAR(80)  NOT NULL,
  last_seen   DATETIME     NOT NULL,
  CONSTRAINT uq_live_viewer UNIQUE (live_id, viewer_key),
  CONSTRAINT fk_live_viewers_live FOREIGN KEY (live_id)
    REFERENCES lives (id) ON DELETE CASCADE,
  KEY idx_live_viewers_last_seen (live_id, last_seen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
