-- ============================================================
-- Migration DIVIX LIVE — étape 5 : chat du live
-- ------------------------------------------------------------
-- Messages de chat pendant un live (persistés côté serveur ; l'app
-- rafraîchit par interrogation. Peut évoluer vers Agora RTM/temps réel).
-- ============================================================

CREATE TABLE IF NOT EXISTS live_messages (
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
