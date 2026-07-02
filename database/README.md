# Base de données MySQL

Schéma relationnel utilisé par l'API Flask (`../app`) et correspondant aux
modèles de l'application mobile Flutter [Appmobile](https://github.com/02konan/Appmobile) :
catégories, produits (avec couleurs/tailles), utilisateurs, favoris, panier
et commandes.

## Fichiers

- `schema.sql` — création de la base et des tables (DDL)
- `seed.sql` — données de démonstration (6 catégories, 24 produits, 1
  utilisateur de démo)
- `create_user.sql` — utilisateur MySQL dédié `ecommerce_user` (utilisé par
  l'API Flask, voir `../README.md`)

## Installation

Depuis la racine du dépôt :

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
mysql -u root -p < database/create_user.sql
```

Si la connexion en tant que `root` par mot de passe échoue (erreur
« Access denied », fréquent avec l'authentification par socket Unix sur
Linux), lancez plutôt `sudo mysql < database/schema.sql` etc.

## Schéma

| Table | Rôle |
|---|---|
| `categories` | Catégories de produits |
| `products` | Catalogue produits (prix, stock, note, mise en avant...) |
| `product_colors` / `product_sizes` | Variantes couleur/taille par produit |
| `users` | Comptes utilisateurs (mot de passe hashé) |
| `favorites` | Produits favoris par utilisateur |
| `cart_items` | Panier courant par utilisateur |
| `orders` / `order_items` | Commandes passées (les lignes de commande gardent une copie du nom/prix du produit au moment de l'achat) |

## Notes

- Les identifiants produits (`p1`, `p2`, ...) reprennent ceux utilisés côté
  application mobile pour faciliter le branchement de l'API.
- `password_hash` doit être généré côté backend (bcrypt/argon2 via
  `werkzeug.security`) — la valeur du seed est un exemple, pas un hash
  valide.
