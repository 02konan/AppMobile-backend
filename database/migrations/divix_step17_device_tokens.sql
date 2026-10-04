-- DIVIX — étape 17 : notifications push (jetons d'appareils FCM)
-- Chaque appareil enregistre son jeton Firebase Cloud Messaging, rattaché à
-- un utilisateur, pour recevoir les notifications (lives, commandes, reels).

CREATE TABLE device_tokens (
  id          INT UNSIGNED AUTO_INCREMENT,
  user_id     INT UNSIGNED NOT NULL,
  token       VARCHAR(255) NOT NULL,
  platform    VARCHAR(20)  NULL,
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                           ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_device_token (token),
  KEY idx_device_tokens_user (user_id),
  CONSTRAINT fk_device_tokens_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;
