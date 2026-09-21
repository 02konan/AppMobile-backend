-- ============================================================
-- Migration DIVIX LIVE — étape 7 : signalements
-- ------------------------------------------------------------
-- Signalements de contenus abusifs (produit, live, boutique,
-- utilisateur) déposés par les utilisateurs et traités depuis le
-- panneau d'administration.
-- ============================================================

CREATE TABLE IF NOT EXISTS reports (
  id           INT UNSIGNED AUTO_INCREMENT,
  reporter_id  INT UNSIGNED NULL,
  target_type  ENUM('product','live','shop','user') NOT NULL,
  target_id    VARCHAR(30) NOT NULL,
  reason       VARCHAR(100) NOT NULL,
  message      VARCHAR(1000) NULL,
  status       ENUM('open','reviewing','resolved','dismissed') NOT NULL DEFAULT 'open',
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at  DATETIME NULL,
  PRIMARY KEY (id),
  KEY idx_reports_status (status, created_at),
  KEY idx_reports_target (target_type, target_id),
  CONSTRAINT fk_reports_reporter
    FOREIGN KEY (reporter_id) REFERENCES users (id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;
