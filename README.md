# AppMobile Backend — API Flask

API REST Flask servant l'application mobile Flutter
([Appmobile](https://github.com/02konan/Appmobile)), branchée sur une base
MySQL définie dans `database/schema.sql`.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # puis renseigner les identifiants MySQL
```

La base doit déjà exister (voir `database/README.md`) :

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql        # optionnel, données de démo
mysql -u root -p < database/create_user.sql # utilisateur MySQL dédié
```

Redis et RabbitMQ doivent être démarrés pour les fonctionnalités qui utilisent
le cache et les événements asynchrones. Leurs connexions sont configurées avec
`REDIS_URL`, `RABBITMQ_URL` et `RABBITMQ_QUEUE` dans `.env`. L'état de ces deux
dépendances est disponible via `GET /api/health/dependencies`.

Pour démarrer les services localement :

```bash
docker compose up -d redis rabbitmq
```

### Déploiement sur Render

Le fichier `render.yaml` configure le Web Service Flask avec Gunicorn. Après
avoir créé le service, renseigner dans Render les variables `DB_HOST`,
`DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `JWT_SECRET_KEY` et
`FIREBASE_SERVICE_ACCOUNT_JSON`.

Pour `FIREBASE_SERVICE_ACCOUNT_JSON`, coller le contenu JSON de la clé privée
d'un compte de service Firebase Admin. Cette valeur est un secret : la saisir
dans les variables d'environnement Render ou dans le `.env` local, jamais dans
Git ni dans l'application Flutter. Dans Firebase Console, activer
l'authentification par téléphone et configurer les empreintes SHA-1/SHA-256 de
l'application Android.

Pour Redis, créer un service Render Key Value puis copier son URL interne dans
`REDIS_URL`. Pour RabbitMQ, utiliser une instance externe compatible AMQP (par
exemple CloudAMQP) et copier son URL `amqp://...` dans `RABBITMQ_URL`.
`docker-compose.yml` est destiné au développement local et ne doit pas être
utilisé comme commande de démarrage Render.

## Lancer le serveur

```bash
python run.py
```

L'API écoute sur `http://localhost:5000`.

## Authentification

Toutes les routes protégées attendent un header :

```
Authorization: Bearer <token>
```

Le token est renvoyé par `/api/auth/register` et `/api/auth/login`.

## Endpoints

### Santé

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/health` | Vérifie que l'API répond |
| GET | `/api/health/dependencies` | Vérifie Redis et RabbitMQ |

### Authentification

| Méthode | Route | Auth | Corps | Description |
|---|---|---|---|---|
| POST | `/api/auth/register` | – | `{name, phone, password, role, firebaseIdToken}` | Vérifie le numéro avec Firebase puis crée le compte |
| POST | `/api/auth/login` | – | `{phone, password}` | Connexion, renvoie `{token, user}` |
| GET | `/api/auth/me` | ✓ | – | Profil de l'utilisateur connecté |
| PUT | `/api/auth/me` | ✓ | `{name?, address?, phone?}` | Met à jour le profil |

### Catégories

| Méthode | Route | Auth | Description |
|---|---|---|---|
| GET | `/api/categories` | – | Liste des catégories |

### Produits

| Méthode | Route | Auth | Query params | Description |
|---|---|---|---|---|
| GET | `/api/products` | – | `category`, `featured`, `q` | Liste/filtre/recherche de produits |
| GET | `/api/products/<id>` | – | – | Détail d'un produit |

### Favoris

| Méthode | Route | Auth | Corps | Description |
|---|---|---|---|---|
| GET | `/api/favorites` | ✓ | – | Produits favoris de l'utilisateur |
| POST | `/api/favorites` | ✓ | `{productId}` | Ajoute un favori |
| DELETE | `/api/favorites/<productId>` | ✓ | – | Retire un favori |

### Panier

| Méthode | Route | Auth | Corps | Description |
|---|---|---|---|---|
| GET | `/api/cart` | ✓ | – | Contenu du panier + totaux |
| POST | `/api/cart` | ✓ | `{productId, quantity, selectedColor?, selectedSize?}` | Ajoute un article |
| PUT | `/api/cart/<itemId>` | ✓ | `{quantity}` | Modifie la quantité |
| DELETE | `/api/cart/<itemId>` | ✓ | – | Retire un article |
| DELETE | `/api/cart` | ✓ | – | Vide le panier |

### Commandes

| Méthode | Route | Auth | Corps | Description |
|---|---|---|---|---|
| GET | `/api/orders` | ✓ | – | Historique des commandes |
| GET | `/api/orders/<id>` | ✓ | – | Détail d'une commande |
| POST | `/api/orders` | ✓ | `{shippingAddress, paymentMethod}` | Passe commande à partir du panier courant (vide ensuite le panier) |

## Format des réponses

Les clés JSON sont en camelCase pour correspondre directement aux modèles
Dart de l'application (`lib/models/`). Exemple `GET /api/products/p1` :

```json
{
  "id": "p1",
  "categoryId": "clothing",
  "name": "Veste en jean oversize",
  "description": "...",
  "price": 59.99,
  "oldPrice": 79.99,
  "imageUrl": "https://picsum.photos/seed/jacket1/600/600",
  "rating": 4.6,
  "reviewCount": 128,
  "stock": 10,
  "inStock": true,
  "isFeatured": true,
  "colors": ["Bleu", "Noir"],
  "sizes": ["S", "M", "L", "XL"]
}
```

Les erreurs renvoient `{"error": "message"}` avec le code HTTP approprié
(400, 401, 404, 409...).
