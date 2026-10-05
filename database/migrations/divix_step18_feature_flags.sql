-- DIVIX — étape 18 : feature flags
-- Permet d'activer/désactiver des fonctionnalités sans nouvelle version de
-- l'app. Seules les surcharges sont stockées ; le reste suit les valeurs par
-- défaut définies côté serveur (app/features.py).

CREATE TABLE feature_flags (
  `key`      VARCHAR(60)  NOT NULL,
  enabled    TINYINT(1)   NOT NULL DEFAULT 1,
  updated_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB;
