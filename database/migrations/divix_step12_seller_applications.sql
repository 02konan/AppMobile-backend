-- ============================================================
-- Migration DIVIX LIVE — étape 12 : candidatures « Devenir vendeur » (KYC)
-- ------------------------------------------------------------
-- Un acheteur soumet une demande (boutique + visuels + pièces d'identité),
-- validée ou refusée par l'administration. À l'approbation, le compte passe
-- acheteur -> commerçant et la boutique est créée.
-- ============================================================

CREATE TABLE IF NOT EXISTS seller_applications (
  id           INT UNSIGNED AUTO_INCREMENT,
  user_id      INT UNSIGNED NOT NULL,
  shop_name    VARCHAR(150) NOT NULL,
  category     VARCHAR(100) NULL,
  city         VARCHAR(100) NULL,
  logo_url     VARCHAR(500) NULL,
  cover_url    VARCHAR(500) NULL,
  id_type      ENUM('cni','passport') NOT NULL,
  id_front_url VARCHAR(500) NULL,
  id_back_url  VARCHAR(500) NULL,
  selfie_url   VARCHAR(500) NULL,
  status       ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  review_note  VARCHAR(500) NULL,
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at  DATETIME     NULL,
  PRIMARY KEY (id),
  KEY idx_seller_apps_status (status),
  KEY idx_seller_apps_user (user_id),
  CONSTRAINT fk_seller_apps_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
