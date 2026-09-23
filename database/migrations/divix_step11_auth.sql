-- ============================================================
-- Migration DIVIX LIVE — étape 11 : authentification enrichie
-- ------------------------------------------------------------
-- - username (@pseudo) unique, pays, ville, téléphone vérifié sur users
-- - table phone_otps : codes de vérification SMS (OTP)
-- ============================================================

ALTER TABLE users
  ADD COLUMN username       VARCHAR(50)  NULL UNIQUE AFTER name,
  ADD COLUMN phone_verified TINYINT(1)   NOT NULL DEFAULT 0 AFTER phone,
  ADD COLUMN country        VARCHAR(50)  NULL AFTER phone_verified,
  ADD COLUMN city           VARCHAR(100) NULL AFTER country;

CREATE TABLE IF NOT EXISTS phone_otps (
  phone       VARCHAR(30) NOT NULL,
  code        VARCHAR(6)  NOT NULL,
  expires_at  DATETIME    NOT NULL,
  attempts    INT         NOT NULL DEFAULT 0,
  created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
