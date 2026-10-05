-- DIVIX — étape 19 : avis & notes produits
-- Un avis par acheteur et par produit (note 1-5 + commentaire). La note
-- moyenne et le nombre d'avis du produit (products.rating / review_count)
-- sont recalculés côté serveur à chaque écriture.

CREATE TABLE reviews (
  id          INT UNSIGNED AUTO_INCREMENT,
  product_id  VARCHAR(30)  NOT NULL,
  user_id     INT UNSIGNED NOT NULL,
  rating      TINYINT      NOT NULL,
  comment     TEXT         NULL,
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                           ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_review_user (product_id, user_id),
  KEY idx_reviews_product (product_id, id),
  CONSTRAINT fk_reviews_product
    FOREIGN KEY (product_id) REFERENCES products (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_reviews_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;
