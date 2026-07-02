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
CREATE TABLE products (
  id            VARCHAR(30)    NOT NULL,
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
  created_at    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                               ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_products_category (category_id),
  KEY idx_products_featured (is_featured),
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
  email          VARCHAR(150) NOT NULL,
  password_hash  VARCHAR(255) NOT NULL,
  phone          VARCHAR(30)  NULL,
  address        VARCHAR(255) NULL,
  avatar_url     VARCHAR(500) NULL,
  created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

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
  subtotal           DECIMAL(10,2)  NOT NULL,
  shipping_cost      DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
  total              DECIMAL(10,2)  NOT NULL,
  shipping_address   VARCHAR(255)   NOT NULL,
  payment_method     ENUM('card','paypal','cash') NOT NULL DEFAULT 'card',
  status             ENUM('processing','shipped','delivered')
                     NOT NULL DEFAULT 'processing',
  created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_orders_number (order_number),
  KEY idx_orders_user (user_id),
  CONSTRAINT fk_orders_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE ON UPDATE CASCADE
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
