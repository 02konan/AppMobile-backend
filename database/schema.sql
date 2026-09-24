-- ============================================================
-- Boutique en ligne — schéma MySQL
-- Correspond aux modèles Dart de l'application (lib/models/*)
-- ============================================================

CREATE DATABASE IF NOT EXISTS ecommerce_app
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

SET NAMES utf8mb4;
USE ecommerce_app;

-- ------------------------------------------------------------
-- Catégories (ProductCategory)
-- ------------------------------------------------------------
CREATE TABLE categories (
  id         VARCHAR(30)  NOT NULL,
  name       VARCHAR(100) NOT NULL,
  icon       VARCHAR(50)  NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Produits (Product)
-- ------------------------------------------------------------
-- Note : la clé étrangère products.shop_id -> shops est ajoutée en fin de
-- fichier, car la table shops est déclarée après products.
CREATE TABLE products (
  id            VARCHAR(30)    NOT NULL,
  shop_id       INT UNSIGNED   NULL,
  category_id   VARCHAR(30)    NOT NULL,
  name          VARCHAR(150)   NOT NULL,
  description   TEXT           NOT NULL,
  price         DECIMAL(10,2)  NOT NULL,
  old_price     DECIMAL(10,2)  NULL,
  image_url     VARCHAR(500)   NOT NULL,
  rating        DECIMAL(2,1)   NOT NULL DEFAULT 0.0,
  review_count  INT UNSIGNED   NOT NULL DEFAULT 0,
  stock         INT UNSIGNED   NOT NULL DEFAULT 10,
  is_featured   TINYINT(1)     NOT NULL DEFAULT 0,
  is_active     TINYINT(1)     NOT NULL DEFAULT 1,
  created_at    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                               ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_products_category (category_id),
  KEY idx_products_featured (is_featured),
  KEY idx_products_shop (shop_id),
  KEY idx_products_active (is_active),
  CONSTRAINT fk_products_category
    FOREIGN KEY (category_id) REFERENCES categories (id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Couleurs disponibles pour un produit
CREATE TABLE product_colors (
  id          INT UNSIGNED AUTO_INCREMENT,
  product_id  VARCHAR(30)  NOT NULL,
  color       VARCHAR(50)  NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_product_color (product_id, color),
  CONSTRAINT fk_product_colors_product
    FOREIGN KEY (product_id) REFERENCES products (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Tailles disponibles pour un produit
CREATE TABLE product_sizes (
  id          INT UNSIGNED AUTO_INCREMENT,
  product_id  VARCHAR(30)  NOT NULL,
  size        VARCHAR(20)  NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_product_size (product_id, size),
  CONSTRAINT fk_product_sizes_product
    FOREIGN KEY (product_id) REFERENCES products (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Utilisateurs (AppUser)
-- ------------------------------------------------------------
CREATE TABLE users (
  id             INT UNSIGNED AUTO_INCREMENT,
  name           VARCHAR(150) NOT NULL,
  username       VARCHAR(50)  NULL,
  role           ENUM('buyer','merchant','admin','driver') NOT NULL DEFAULT 'buyer',
  email          VARCHAR(150) NULL,
  password_hash  VARCHAR(255) NOT NULL,
  phone          VARCHAR(30)  NULL,
  phone_verified TINYINT(1)   NOT NULL DEFAULT 0,
  country        VARCHAR(50)  NULL,
  city           VARCHAR(100) NULL,
  address        VARCHAR(255) NULL,
  avatar_url     VARCHAR(500) NULL,
  created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email),
  UNIQUE KEY uq_users_phone (phone),
  UNIQUE KEY uq_users_username (username)
) ENGINE=InnoDB;

-- Codes de vérification SMS (OTP) — DIVIX LIVE
CREATE TABLE phone_otps (
  phone       VARCHAR(30) NOT NULL,
  code        VARCHAR(6)  NOT NULL,
  expires_at  DATETIME    NOT NULL,
  attempts    INT         NOT NULL DEFAULT 0,
  created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (phone)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Boutiques (une par commerçant) — DIVIX LIVE
-- ------------------------------------------------------------
CREATE TABLE shops (
  id           INT UNSIGNED AUTO_INCREMENT,
  user_id      INT UNSIGNED NOT NULL,
  name         VARCHAR(150) NOT NULL,
  logo_url     VARCHAR(500) NULL,
  cover_url    VARCHAR(500) NULL,
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

-- Clé étrangère produits -> boutique (shops existe désormais)
ALTER TABLE products
  ADD CONSTRAINT fk_products_shop
    FOREIGN KEY (shop_id) REFERENCES shops (id)
    ON DELETE CASCADE ON UPDATE CASCADE;

-- ------------------------------------------------------------
-- Favoris (FavoritesProvider)
-- ------------------------------------------------------------
CREATE TABLE favorites (
  user_id     INT UNSIGNED NOT NULL,
  product_id  VARCHAR(30)  NOT NULL,
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, product_id),
  CONSTRAINT fk_favorites_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_favorites_product
    FOREIGN KEY (product_id) REFERENCES products (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Panier (CartProvider / CartItem)
-- ------------------------------------------------------------
CREATE TABLE cart_items (
  id              INT UNSIGNED AUTO_INCREMENT,
  user_id         INT UNSIGNED NOT NULL,
  product_id      VARCHAR(30)  NOT NULL,
  quantity        INT UNSIGNED NOT NULL DEFAULT 1,
  selected_color  VARCHAR(50)  NULL,
  selected_size   VARCHAR(20)  NULL,
  created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cart_line (user_id, product_id, selected_color, selected_size),
  KEY idx_cart_items_user (user_id),
  CONSTRAINT fk_cart_items_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_cart_items_product
    FOREIGN KEY (product_id) REFERENCES products (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Commandes (Order)
-- ------------------------------------------------------------
CREATE TABLE orders (
  id                 INT UNSIGNED AUTO_INCREMENT,
  order_number       VARCHAR(30)    NOT NULL,
  user_id            INT UNSIGNED   NOT NULL,
  shop_id            INT UNSIGNED   NULL,
  live_id            INT UNSIGNED   NULL,   -- FK ajoutée en fin de fichier
  subtotal           DECIMAL(10,2)  NOT NULL,
  shipping_cost      DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
  total              DECIMAL(10,2)  NOT NULL,
  shipping_address   VARCHAR(255)   NOT NULL,
  customer_phone     VARCHAR(30)    NULL,
  payment_method     ENUM('card','paypal','cash','whatsapp')
                     NOT NULL DEFAULT 'whatsapp',
  status             ENUM('pending','confirmed','preparing','ready',
                          'picked_up','delivering','delivered',
                          'refused','cancelled')
                     NOT NULL DEFAULT 'pending',
  created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_orders_number (order_number),
  KEY idx_orders_user (user_id),
  KEY idx_orders_shop (shop_id),
  KEY idx_orders_live (live_id),
  CONSTRAINT fk_orders_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_orders_shop
    FOREIGN KEY (shop_id) REFERENCES shops (id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Lignes de commande (CartItem au moment de la commande)
-- Les valeurs produit sont dupliquées ("snapshot") pour conserver
-- l'historique même si le produit change de prix ou est supprimé.
CREATE TABLE order_items (
  id              INT UNSIGNED AUTO_INCREMENT,
  order_id        INT UNSIGNED  NOT NULL,
  product_id      VARCHAR(30)   NULL,
  product_name    VARCHAR(150)  NOT NULL,
  unit_price      DECIMAL(10,2) NOT NULL,
  quantity        INT UNSIGNED  NOT NULL,
  selected_color  VARCHAR(50)   NULL,
  selected_size   VARCHAR(20)   NULL,
  PRIMARY KEY (id),
  KEY idx_order_items_order (order_id),
  CONSTRAINT fk_order_items_order
    FOREIGN KEY (order_id) REFERENCES orders (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_order_items_product
    FOREIGN KEY (product_id) REFERENCES products (id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Lives (DIVIX LIVE) — la vidéo est gérée par un service externe ;
-- Flask ne stocke que les métadonnées du live.
-- ------------------------------------------------------------
CREATE TABLE lives (
  id                  INT UNSIGNED AUTO_INCREMENT,
  shop_id             INT UNSIGNED NOT NULL,
  title               VARCHAR(150) NOT NULL,
  description         TEXT         NULL,
  category            VARCHAR(100) NULL,
  cover_url    VARCHAR(500) NULL,
  scheduled_at        DATETIME     NULL,
  status              ENUM('scheduled','live','ended')
                      NOT NULL DEFAULT 'scheduled',
  current_product_id  VARCHAR(30)  NULL,
  viewer_count        INT UNSIGNED NOT NULL DEFAULT 0,
  playback_url        VARCHAR(500) NULL,
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

-- Produits sélectionnés pour un live
CREATE TABLE live_products (
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

-- Clé étrangère commandes -> live (lives existe désormais)
ALTER TABLE orders
  ADD CONSTRAINT fk_orders_live
    FOREIGN KEY (live_id) REFERENCES lives (id)
    ON DELETE SET NULL ON UPDATE CASCADE;

-- Messages de chat pendant un live
CREATE TABLE live_messages (
  id          INT UNSIGNED AUTO_INCREMENT,
  live_id     INT UNSIGNED NOT NULL,
  user_id     INT UNSIGNED NULL,
  user_name   VARCHAR(150) NOT NULL,
  message     VARCHAR(500) NOT NULL,
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_live_messages_live (live_id, id),
  CONSTRAINT fk_live_messages_live
    FOREIGN KEY (live_id) REFERENCES lives (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_live_messages_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Présence des spectateurs (compteur de vues par heartbeat)
CREATE TABLE live_viewers (
  id          INT UNSIGNED AUTO_INCREMENT,
  live_id     INT UNSIGNED NOT NULL,
  viewer_key  VARCHAR(80)  NOT NULL,
  last_seen   DATETIME     NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_live_viewer (live_id, viewer_key),
  KEY idx_live_viewers_last_seen (live_id, last_seen),
  CONSTRAINT fk_live_viewers_live
    FOREIGN KEY (live_id) REFERENCES lives (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- DIVIX LIVE — livraisons & signalements
-- ============================================================

-- Livraisons (une par commande, prise en charge par un livreur)
CREATE TABLE deliveries (
  id            INT UNSIGNED AUTO_INCREMENT,
  order_id      INT UNSIGNED NOT NULL,
  driver_id     INT UNSIGNED NULL,
  status        ENUM('unassigned','assigned','picked_up','delivering','delivered','failed')
                NOT NULL DEFAULT 'unassigned',
  fee           DECIMAL(10,2) NOT NULL DEFAULT 0,
  notes         VARCHAR(500) NULL,
  assigned_at   DATETIME NULL,
  picked_up_at  DATETIME NULL,
  delivered_at  DATETIME NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_deliveries_order (order_id),
  KEY idx_deliveries_driver (driver_id, status),
  CONSTRAINT fk_deliveries_order
    FOREIGN KEY (order_id) REFERENCES orders (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_deliveries_driver
    FOREIGN KEY (driver_id) REFERENCES users (id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Signalements de contenus abusifs
CREATE TABLE reports (
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

-- Candidatures « Devenir vendeur » (KYC)
CREATE TABLE seller_applications (
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
  terms_version VARCHAR(20) NULL,
  review_note  VARCHAR(500) NULL,
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at  DATETIME     NULL,
  PRIMARY KEY (id),
  KEY idx_seller_apps_status (status),
  KEY idx_seller_apps_user (user_id),
  CONSTRAINT fk_seller_apps_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Candidatures « Devenir livreur » (KYC)
CREATE TABLE driver_applications (
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
) ENGINE=InnoDB;
