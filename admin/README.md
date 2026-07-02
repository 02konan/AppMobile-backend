# AppMobile Admin — Interface de gestion web

Application Flask de gestion (back-office) pour la boutique Appmobile :
produits, catégories, commandes et utilisateurs. Rendu côté serveur
(Jinja2 + Bootstrap 5), requêtes SQL directes via PyMySQL sur la même base
MySQL que l'API REST (`../database`).

Distincte de l'API REST (`../app`) qui sert l'application mobile : cette
application est une interface web classique destinée à un navigateur, avec
authentification par session.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

La base doit déjà exister (voir `../database/README.md`). Le compte admin
par défaut du `.env.example` est `admin` / `changeme123` — **à changer**
avant tout déploiement (voir les instructions dans `.env.example` pour
générer un nouveau hash de mot de passe).

## Lancer le serveur

```bash
python run.py
```

L'interface est disponible sur `http://localhost:5050`.

## Fonctionnalités

- **Tableau de bord** : statistiques (produits, catégories, commandes,
  clients, chiffre d'affaires, alertes de stock faible), dernières commandes
- **Produits** : liste avec recherche/filtre par catégorie, ajout,
  modification, suppression, gestion des couleurs/tailles
- **Catégories** : liste, ajout, modification, suppression (bloquée si des
  produits y sont encore rattachés) ; l'icône doit être choisie parmi celles
  reconnues par l'application mobile
- **Commandes** : liste filtrable par statut, détail (articles, client,
  adresse), changement de statut (en traitement / expédiée / livrée)
- **Utilisateurs** : liste en lecture seule (nombre de commandes, total
  dépensé)

## Sécurité

- Authentification par session, un seul compte administrateur défini via
  variables d'environnement (`ADMIN_USERNAME` / `ADMIN_PASSWORD_HASH`)
- Toutes les routes de gestion sont protégées par `@login_required`
- Toutes les requêtes SQL utilisent des paramètres liés (`%s`), jamais de
  concaténation de chaînes — protection contre les injections SQL
