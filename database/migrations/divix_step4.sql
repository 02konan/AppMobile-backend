-- ============================================================
-- Migration DIVIX LIVE — étape 4 : commandes depuis un live
-- ------------------------------------------------------------
-- Rattache les commandes à une boutique et à un live, ajoute le
-- workflow de statuts DIVIX et le paiement WhatsApp.
--
-- Suppose qu'il n'y a pas d'anciennes commandes e-commerce à migrer
-- (statuts processing/shipped/delivered). Si c'était le cas, remapper
-- ces valeurs avant le MODIFY ci-dessous.
-- ============================================================

ALTER TABLE orders
  ADD COLUMN shop_id        INT UNSIGNED NULL AFTER user_id,
  ADD COLUMN live_id        INT UNSIGNED NULL AFTER shop_id,
  ADD COLUMN customer_phone VARCHAR(30)  NULL AFTER shipping_address,
  ADD KEY idx_orders_shop (shop_id),
  ADD KEY idx_orders_live (live_id),
  ADD CONSTRAINT fk_orders_shop
    FOREIGN KEY (shop_id) REFERENCES shops (id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT fk_orders_live
    FOREIGN KEY (live_id) REFERENCES lives (id)
    ON DELETE SET NULL ON UPDATE CASCADE;

-- Workflow de statuts DIVIX
ALTER TABLE orders
  MODIFY status ENUM(
    'pending','confirmed','preparing','ready',
    'picked_up','delivering','delivered','refused','cancelled'
  ) NOT NULL DEFAULT 'pending';

-- Paiement WhatsApp (MVP)
ALTER TABLE orders
  MODIFY payment_method ENUM('card','paypal','cash','whatsapp')
    NOT NULL DEFAULT 'whatsapp';
