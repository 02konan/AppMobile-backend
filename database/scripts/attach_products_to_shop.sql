-- ============================================================
-- Utilitaire DIVIX — rattacher les produits à une boutique
-- ------------------------------------------------------------
-- Un produit doit avoir un shop_id pour être commandable dans l'app
-- (le catalogue affiche tous les produits, mais la commande via WhatsApp
-- exige une boutique). Les anciens produits de démo ont shop_id = NULL.
--
-- Ce script propose 3 opérations. Exécute UNIQUEMENT celles utiles à ton
-- cas, sur la base de production (ex. divix_appmobile sur alwaysdata).
-- ============================================================

-- 1) DIAGNOSTIC — lister les produits sans boutique
SELECT id, name, price, stock
FROM products
WHERE shop_id IS NULL
ORDER BY name;

-- Voir les boutiques disponibles (pour choisir un id ci-dessous)
SELECT id, name, status FROM shops ORDER BY id;


-- 2) RATTACHEMENT CIBLÉ — tous les produits orphelins vers UNE boutique
--    Remplace 1 par l'id de la boutique voulue (voir la requête ci-dessus),
--    puis décommente les 2 lignes.
-- UPDATE products SET shop_id = 1
-- WHERE shop_id IS NULL;


-- 3) RATTACHEMENT AUTOMATIQUE — vers la première boutique validée
--    (pratique s'il n'y a qu'une boutique). Décommente le bloc.
-- UPDATE products
-- SET shop_id = (
--   SELECT id FROM (
--     SELECT id FROM shops
--     ORDER BY (status = 'validated') DESC, id ASC
--     LIMIT 1
--   ) AS first_shop
-- )
-- WHERE shop_id IS NULL;


-- Vérification finale (doit renvoyer 0)
SELECT COUNT(*) AS produits_sans_boutique
FROM products
WHERE shop_id IS NULL;
