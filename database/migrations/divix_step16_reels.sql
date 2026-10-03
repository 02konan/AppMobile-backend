-- DIVIX — étape 16 : ReelShops (vidéos courtes shoppables)
-- Vidéos courtes (≤ 30 s, hébergées sur Cloudinary) publiées par une boutique,
-- avec une sélection de produits présentés en dessous (bouton « Acheter »).

CREATE TABLE reels (
  id                INT UNSIGNED AUTO_INCREMENT,
  shop_id           INT UNSIGNED NOT NULL,
  caption           VARCHAR(300) NULL,
  video_url         VARCHAR(500) NOT NULL,
  thumbnail_url     VARCHAR(500) NULL,
  duration_seconds  INT UNSIGNED NULL,
  view_count        INT UNSIGNED NOT NULL DEFAULT 0,
  is_active         TINYINT(1)   NOT NULL DEFAULT 1,
  created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_reels_shop (shop_id),
  KEY idx_reels_active (is_active, id),
  CONSTRAINT fk_reels_shop
    FOREIGN KEY (shop_id) REFERENCES shops (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Produits sélectionnés pour un reel
CREATE TABLE reel_products (
  reel_id     INT UNSIGNED NOT NULL,
  product_id  VARCHAR(30)  NOT NULL,
  position    INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (reel_id, product_id),
  KEY idx_reel_products_reel (reel_id),
  CONSTRAINT fk_reel_products_reel
    FOREIGN KEY (reel_id) REFERENCES reels (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_reel_products_product
    FOREIGN KEY (product_id) REFERENCES products (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;
