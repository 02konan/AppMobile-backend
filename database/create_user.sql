-- Utilisateur dédié pour le backend Flask (évite de dépendre de root,
-- notamment sur les installations où root utilise l'authentification
-- par socket Unix et refuse les connexions par mot de passe).

CREATE USER IF NOT EXISTS 'ecommerce_user'@'localhost' IDENTIFIED BY 'ecommerce_pass';
CREATE USER IF NOT EXISTS 'ecommerce_user'@'%' IDENTIFIED BY 'ecommerce_pass';

GRANT ALL PRIVILEGES ON ecommerce_app.* TO 'ecommerce_user'@'localhost';
GRANT ALL PRIVILEGES ON ecommerce_app.* TO 'ecommerce_user'@'%';

FLUSH PRIVILEGES;
