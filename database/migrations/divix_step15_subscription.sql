-- ============================================================
-- Migration DIVIX LIVE — étape 15 : abonnement vendeur
-- ------------------------------------------------------------
-- Champs d'abonnement sur la boutique + table des paiements d'abonnement
-- (préparée pour un fournisseur mobile money). Aucune restriction appliquée
-- pour l'instant : la boutique est "abonnée" si subscription_expires_at > now.
-- ============================================================

ALTER TABLE shops
  ADD COLUMN subscription_plan       VARCHAR(30) NULL AFTER status,
  ADD COLUMN subscription_expires_at DATETIME    NULL AFTER subscription_plan;

CREATE TABLE IF NOT EXISTS subscription_payments (
  id         INT UNSIGNED AUTO_INCREMENT,
  shop_id    INT UNSIGNED NOT NULL,
  plan       VARCHAR(30)  NOT NULL,
  amount     DECIMAL(10,2) NOT NULL DEFAULT 0,
  provider   VARCHAR(30)  NULL,
  reference  VARCHAR(100) NULL,
  status     ENUM('pending','success','failed','cancelled') NOT NULL DEFAULT 'pending',
  days       INT          NOT NULL DEFAULT 30,
  created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  paid_at    DATETIME     NULL,
  PRIMARY KEY (id),
  KEY idx_subpay_shop (shop_id, status),
  CONSTRAINT fk_subpay_shop
    FOREIGN KEY (shop_id) REFERENCES shops (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
