-- ============================================================
-- Données de démonstration (identiques à lib/data/mock_data.dart)
-- ============================================================

SET NAMES utf8mb4;
USE ecommerce_app;

-- ------------------------------------------------------------
-- Catégories
-- ------------------------------------------------------------
INSERT INTO categories (id, name, icon) VALUES
  ('clothing', 'Vêtements', 'checkroom'),
  ('shoes', 'Chaussures', 'sports_soccer_outlined'),
  ('electronics', 'Électronique', 'headphones'),
  ('accessories', 'Accessoires', 'watch_outlined'),
  ('home', 'Maison', 'chair_outlined'),
  ('beauty', 'Beauté', 'spa_outlined');

-- ------------------------------------------------------------
-- Produits
-- ------------------------------------------------------------
INSERT INTO products (id, category_id, name, description, price, old_price, image_url, rating, review_count, stock, is_featured) VALUES
  ('p1', 'clothing', 'Veste en jean oversize', 'Veste en jean coupe oversize, idéale pour toutes les saisons. Tissu denim résistant et doublure douce pour un confort optimal.', 59.99, 79.99, 'https://picsum.photos/seed/jacket1/600/600', 4.6, 128, 10, 1),
  ('p2', 'clothing', 'T-shirt coton bio col rond', 'T-shirt basique en coton biologique, coupe régulière, doux et respirant.', 19.99, NULL, 'https://picsum.photos/seed/tshirt1/600/600', 4.3, 342, 10, 0),
  ('p3', 'clothing', 'Pantalon cargo', 'Pantalon cargo multipoches, coupe droite, parfait pour un look streetwear.', 44.99, NULL, 'https://picsum.photos/seed/cargo1/600/600', 4.4, 87, 10, 0),
  ('p4', 'clothing', 'Robe d\'été fleurie', 'Robe légère à motif floral, parfaite pour les journées ensoleillées.', 39.99, 54.99, 'https://picsum.photos/seed/dress1/600/600', 4.7, 201, 10, 1),
  ('p5', 'shoes', 'Sneakers running Air Max', 'Chaussures de running légères avec amorti réactif et semelle respirante.', 89.99, 109.99, 'https://picsum.photos/seed/sneaker1/600/600', 4.8, 512, 10, 1),
  ('p6', 'shoes', 'Chaussures de ville en cuir', 'Chaussures habillées en cuir véritable, finition élégante pour toutes occasions.', 99.99, NULL, 'https://picsum.photos/seed/shoe2/600/600', 4.5, 76, 10, 0),
  ('p7', 'shoes', 'Sandales confort été', 'Sandales légères à semelle souple, idéales pour la plage et le quotidien.', 24.99, NULL, 'https://picsum.photos/seed/sandal1/600/600', 4.1, 54, 10, 0),
  ('p8', 'electronics', 'Casque audio sans fil', 'Casque Bluetooth à réduction de bruit active, autonomie 30h, son haute-fidélité.', 129.99, 159.99, 'https://picsum.photos/seed/headphones1/600/600', 4.7, 890, 10, 1),
  ('p9', 'electronics', 'Montre connectée Sport', 'Montre connectée avec suivi cardiaque, GPS intégré et étanchéité 5 ATM.', 149.99, NULL, 'https://picsum.photos/seed/smartwatch1/600/600', 4.5, 431, 10, 1),
  ('p10', 'electronics', 'Enceinte Bluetooth portable', 'Enceinte compacte et résistante à l\'eau avec 12h d\'autonomie et son 360°.', 49.99, NULL, 'https://picsum.photos/seed/speaker1/600/600', 4.4, 267, 10, 0),
  ('p11', 'electronics', 'Écouteurs sans fil Pro', 'Écouteurs intra-auriculaires avec réduction de bruit et boîtier de charge rapide.', 79.99, 99.99, 'https://picsum.photos/seed/earbuds1/600/600', 4.6, 623, 10, 0),
  ('p12', 'accessories', 'Sac à dos urbain', 'Sac à dos avec compartiment ordinateur portable, résistant à l\'eau.', 54.99, NULL, 'https://picsum.photos/seed/backpack1/600/600', 4.5, 198, 10, 1),
  ('p13', 'accessories', 'Lunettes de soleil polarisées', 'Protection UV400, monture légère en acétate, style intemporel.', 34.99, NULL, 'https://picsum.photos/seed/sunglasses1/600/600', 4.2, 143, 10, 0),
  ('p14', 'accessories', 'Ceinture en cuir', 'Ceinture en cuir véritable avec boucle métallique classique.', 29.99, NULL, 'https://picsum.photos/seed/belt1/600/600', 4.3, 65, 10, 0),
  ('p15', 'accessories', 'Montre classique acier', 'Montre à quartz avec bracelet en acier inoxydable et verre saphir.', 119.99, 149.99, 'https://picsum.photos/seed/watch1/600/600', 4.6, 312, 10, 0),
  ('p16', 'home', 'Lampe de bureau LED', 'Lampe LED à intensité réglable avec port USB de charge intégré.', 32.99, NULL, 'https://picsum.photos/seed/lamp1/600/600', 4.4, 156, 10, 0),
  ('p17', 'home', 'Coussin décoratif velours', 'Coussin doux en velours pour canapé ou lit, housse déhoussable.', 17.99, NULL, 'https://picsum.photos/seed/pillow1/600/600', 4.3, 89, 10, 0),
  ('p18', 'home', 'Plante artificielle décorative', 'Plante artificielle réaliste en pot céramique, entretien zéro.', 27.99, NULL, 'https://picsum.photos/seed/plant1/600/600', 4.5, 72, 10, 0),
  ('p19', 'home', 'Set de tasses en céramique', 'Lot de 4 tasses en céramique artisanale, passe au lave-vaisselle.', 22.99, 29.99, 'https://picsum.photos/seed/mugs1/600/600', 4.6, 118, 10, 0),
  ('p20', 'beauty', 'Crème hydratante visage', 'Crème hydratante 24h à l\'acide hyaluronique, pour tous types de peau.', 24.99, NULL, 'https://picsum.photos/seed/cream1/600/600', 4.7, 405, 10, 1),
  ('p21', 'beauty', 'Palette de maquillage', 'Palette 12 teintes fards à paupières, texture soyeuse longue tenue.', 29.99, NULL, 'https://picsum.photos/seed/palette1/600/600', 4.4, 231, 10, 0),
  ('p22', 'beauty', 'Parfum floral 50ml', 'Eau de parfum aux notes florales et boisées, tenue longue durée.', 64.99, 79.99, 'https://picsum.photos/seed/perfume1/600/600', 4.8, 289, 10, 0),
  ('p23', 'beauty', 'Kit de pinceaux maquillage', 'Set de 10 pinceaux professionnels avec pochette de rangement.', 19.99, NULL, 'https://picsum.photos/seed/brushes1/600/600', 4.3, 97, 10, 0),
  ('p24', 'clothing', 'Sweat à capuche unisexe', 'Sweat à capuche molletonné, coupe confortable, poche kangourou.', 42.99, NULL, 'https://picsum.photos/seed/hoodie1/600/600', 4.5, 276, 10, 0);

-- ------------------------------------------------------------
-- Couleurs produits
-- ------------------------------------------------------------
INSERT INTO product_colors (product_id, color) VALUES
  ('p1', 'Bleu'),
  ('p1', 'Noir'),
  ('p2', 'Blanc'),
  ('p2', 'Noir'),
  ('p2', 'Gris'),
  ('p3', 'Kaki'),
  ('p3', 'Noir'),
  ('p4', 'Multicolore'),
  ('p5', 'Blanc'),
  ('p5', 'Noir'),
  ('p5', 'Rouge'),
  ('p6', 'Marron'),
  ('p6', 'Noir'),
  ('p7', 'Beige'),
  ('p7', 'Noir'),
  ('p8', 'Noir'),
  ('p8', 'Blanc'),
  ('p9', 'Noir'),
  ('p9', 'Argent'),
  ('p10', 'Bleu'),
  ('p10', 'Noir'),
  ('p10', 'Rouge'),
  ('p11', 'Blanc'),
  ('p11', 'Noir'),
  ('p12', 'Noir'),
  ('p12', 'Gris'),
  ('p13', 'Noir'),
  ('p13', 'Écaille'),
  ('p14', 'Marron'),
  ('p14', 'Noir'),
  ('p15', 'Argent'),
  ('p15', 'Or rosé'),
  ('p16', 'Blanc'),
  ('p16', 'Noir'),
  ('p17', 'Vert'),
  ('p17', 'Beige'),
  ('p17', 'Bleu nuit'),
  ('p24', 'Gris'),
  ('p24', 'Noir'),
  ('p24', 'Bordeaux');

-- ------------------------------------------------------------
-- Tailles produits
-- ------------------------------------------------------------
INSERT INTO product_sizes (product_id, size) VALUES
  ('p1', 'S'),
  ('p1', 'M'),
  ('p1', 'L'),
  ('p1', 'XL'),
  ('p2', 'XS'),
  ('p2', 'S'),
  ('p2', 'M'),
  ('p2', 'L'),
  ('p2', 'XL'),
  ('p3', 'S'),
  ('p3', 'M'),
  ('p3', 'L'),
  ('p3', 'XL'),
  ('p4', 'XS'),
  ('p4', 'S'),
  ('p4', 'M'),
  ('p4', 'L'),
  ('p5', '38'),
  ('p5', '39'),
  ('p5', '40'),
  ('p5', '41'),
  ('p5', '42'),
  ('p5', '43'),
  ('p5', '44'),
  ('p6', '40'),
  ('p6', '41'),
  ('p6', '42'),
  ('p6', '43'),
  ('p6', '44'),
  ('p7', '36'),
  ('p7', '37'),
  ('p7', '38'),
  ('p7', '39'),
  ('p7', '40'),
  ('p14', 'S'),
  ('p14', 'M'),
  ('p14', 'L'),
  ('p24', 'S'),
  ('p24', 'M'),
  ('p24', 'L'),
  ('p24', 'XL'),
  ('p24', 'XXL');

-- ------------------------------------------------------------
-- Utilisateur de démonstration (mot de passe : password123)
-- Hash bcrypt fourni à titre d'exemple, à régénérer côté backend
-- ------------------------------------------------------------
INSERT INTO users (name, email, password_hash, phone, address) VALUES
  ('Client Démo', 'client@example.com', '$2y$10$examplehashreplacewithrealbcrypthash1234567890abcdef', '+33 6 12 34 56 78', '12 Rue de la Paix, 75002 Paris');

