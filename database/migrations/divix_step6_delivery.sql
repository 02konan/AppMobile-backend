-- ============================================================
-- Migration DIVIX LIVE — étape 6 : livraisons & rôle livreur
-- ------------------------------------------------------------
-- Ajoute le rôle « driver » aux utilisateurs et la table des
-- livraisons (une livraison par commande, prise en charge par un
-- livreur). Les changements de statut de livraison synchronisent le
-- statut de la commande côté application.
-- ============================================================

-- Rôle livreur.
ALTER TABLE users
  MODIFY role ENUM('buyer','merchant','admin','driver')
  NOT NULL DEFAULT 'buyer';

CREATE TABLE IF NOT EXISTS deliveries (
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
