-- ============================================================
-- Migration DIVIX LIVE — étapes 1 & 2
-- ------------------------------------------------------------
-- Additive et non destructive : les données existantes de la
-- boutique en ligne sont conservées.
--   Étape 1 : rôles, connexion par téléphone, boutiques,
--             produits rattachés à une boutique.
--   Étape 2 : lives (sans vidéo) + produits d'un live.
--
-- À exécuter UNE FOIS sur une base déjà installée.
-- Sur alwaysdata : phpMyAdmin -> base -> onglet SQL.
-- ============================================================

-- ------------------------------------------------------------
-- Étape 1.a — Utilisateurs : rôle + connexion par téléphone
-- ------------------------------------------------------------
ALTER TABLE users
  ADD COLUMN role ENUM('buyer','merchant','admin')
    NOT NULL DEFAULT 'buyer' AFTER name;

-- L'e-mail devient facultatif (l'inscription DIVIX se fait au téléphone).
ALTER TABLE users
  MODIFY email VARCHAR(150) NULL;

-- Le téléphone devient l'identifiant de connexion : unique s'il est renseigné
-- (MySQL autorise plusieurs valeurs NULL dans un index unique).
ALTER TABLE users
  ADD UNIQUE KEY uq_users_phone (phone);

-- ------------------------------------------------------------
-- Étape 1.b — Boutiques (une par commerçant)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shops (
  id           INT UNSIGNED AUTO_INCREMENT,
  user_id      INT UNSIGNED NOT NULL,
  name         VARCHAR(150) NOT NULL,
  logo_url     VARCHAR(500) NULL,
  description  TEXT         NULL,
  phone        VARCHAR(30)  NULL,
  whatsapp     VARCHAR(30)  NULL,
  address      VARCHAR(255) NULL,
  commune      VARCHAR(100) NULL,
  hours        VARCHAR(255) NULL,
  category     VARCHAR(100) NULL,
  status       ENUM('pending','validated','suspended')
               NOT NULL DEFAULT 'pending',
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_shops_user (user_id),
  KEY idx_shops_status (status),
  CONSTRAINT fk_shops_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Étape 1.c — Produits rattachés à une boutique
-- ------------------------------------------------------------
ALTER TABLE products
  ADD COLUMN shop_id INT UNSIGNED NULL AFTER id,
  ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1 AFTER is_featured,
  ADD KEY idx_products_shop (shop_id),
  ADD KEY idx_products_active (is_active),
  ADD CONSTRAINT fk_products_shop
    FOREIGN KEY (shop_id) REFERENCES shops (id)
    ON DELETE CASCADE ON UPDATE CASCADE;

-- ------------------------------------------------------------
-- Étape 2.a — Lives
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lives (
  id                  INT UNSIGNED AUTO_INCREMENT,
  shop_id             INT UNSIGNED NOT NULL,
  title               VARCHAR(150) NOT NULL,
  description         TEXT         NULL,
  category            VARCHAR(100) NULL,
  scheduled_at        DATETIME     NULL,
  status              ENUM('scheduled','live','ended')
                      NOT NULL DEFAULT 'scheduled',
  current_product_id  VARCHAR(30)  NULL,
  viewer_count        INT UNSIGNED NOT NULL DEFAULT 0,
  playback_url        VARCHAR(500) NULL,   -- rempli par le service vidéo (étape 3)
  started_at          DATETIME     NULL,
  ended_at            DATETIME     NULL,
  created_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                   ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_lives_shop (shop_id),
  KEY idx_lives_status (status),
  CONSTRAINT fk_lives_shop
    FOREIGN KEY (shop_id) REFERENCES shops (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_lives_current_product
    FOREIGN KEY (current_product_id) REFERENCES products (id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Étape 2.b — Produits sélectionnés pour un live
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS live_products (
  live_id     INT UNSIGNED NOT NULL,
  product_id  VARCHAR(30)  NOT NULL,
  position    INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (live_id, product_id),
  KEY idx_live_products_live (live_id),
  CONSTRAINT fk_live_products_live
    FOREIGN KEY (live_id) REFERENCES lives (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_live_products_product
    FOREIGN KEY (product_id) REFERENCES products (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;
