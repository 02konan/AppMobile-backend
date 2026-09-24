-- ============================================================
-- Migration DIVIX LIVE — étape 14 : candidatures « Devenir livreur » (KYC)
-- ------------------------------------------------------------
-- Un utilisateur soumet une demande (zone + véhicule : immatriculation moto,
-- vignette, assurance + pièces d'identité), validée par l'administration.
-- À l'approbation, le compte passe livreur.
-- ============================================================

CREATE TABLE IF NOT EXISTS driver_applications (
  id            INT UNSIGNED AUTO_INCREMENT,
  user_id       INT UNSIGNED NOT NULL,
  city          VARCHAR(100) NULL,
  plate_number  VARCHAR(30)  NOT NULL,
  vignette_url  VARCHAR(500) NULL,
  insurance_url VARCHAR(500) NULL,
  id_type       ENUM('cni','passport') NOT NULL,
  id_front_url  VARCHAR(500) NULL,
  id_back_url   VARCHAR(500) NULL,
  selfie_url    VARCHAR(500) NULL,
  status        ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  terms_version VARCHAR(20)  NULL,
  review_note   VARCHAR(500) NULL,
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at   DATETIME     NULL,
  PRIMARY KEY (id),
  KEY idx_driver_apps_status (status),
  KEY idx_driver_apps_user (user_id),
  CONSTRAINT fk_driver_apps_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
