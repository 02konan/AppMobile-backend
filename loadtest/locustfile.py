"""Test de charge DIVIX (Locust) — simule des utilisateurs réels.

Parcours simulé (acheteur) :
  - connexion (JWT), puis navigation : produits, catégories, boutiques, lives
  - consultation du panier / des commandes / du profil
  - ajout au panier (écriture)

NB : l'inscription (register) n'est PAS testée en charge : elle exige un vrai
jeton Firebase Phone Auth, non générable en test automatisé. On teste donc la
connexion + la navigation + les écritures panier, qui représentent l'essentiel
du trafic réel.

Utilisation :
  locust -f loadtest/locustfile.py --host http://127.0.0.1:8080
  # ou en ligne de commande (headless) :
  locust -f loadtest/locustfile.py --headless -u 30 -r 5 -t 30s \
         --host http://127.0.0.1:8080 --only-summary

Comptes de test attendus (voir loadtest/seed.py) :
  téléphones +22507000000NN (NN de 01 à 20), mot de passe "motdepasse1".
"""

import random

from locust import HttpUser, between, task


class BuyerUser(HttpUser):
    # Temps de réflexion réaliste entre deux actions.
    wait_time = between(1, 4)

    def on_start(self):
        """Connexion au démarrage de chaque utilisateur virtuel."""
        self.token = None
        n = random.randint(1, 20)
        phone = f"+22507000000{n:02d}"
        with self.client.post(
            "/api/auth/login",
            json={"phone": phone, "password": "motdepasse1"},
            name="POST /auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and "token" in resp.text:
                self.token = resp.json().get("token")
                resp.success()
            else:
                resp.failure(f"login {resp.status_code}")

    @property
    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    # ---------------- Navigation (lecture, gros du trafic) ----------------
    @task(6)
    def browse_products(self):
        self.client.get("/api/products", name="GET /products")

    @task(3)
    def browse_categories(self):
        self.client.get("/api/categories", name="GET /categories")

    @task(4)
    def browse_shops(self):
        self.client.get("/api/shops", name="GET /shops")

    @task(3)
    def browse_lives(self):
        self.client.get("/api/lives", name="GET /lives")

    @task(2)
    def check_username(self):
        u = f"user{random.randint(1000, 9999)}"
        self.client.get(
            "/api/auth/check-username",
            params={"username": u},
            name="GET /auth/check-username",
        )

    # ---------------- Espace connecté ----------------
    @task(2)
    def my_profile(self):
        if self.token:
            self.client.get("/api/auth/me", headers=self._auth, name="GET /auth/me")

    @task(2)
    def my_cart(self):
        if self.token:
            self.client.get("/api/cart", headers=self._auth, name="GET /cart")

    @task(1)
    def my_orders(self):
        if self.token:
            self.client.get("/api/orders", headers=self._auth, name="GET /orders")

    # ---------------- Écriture (ajout panier) ----------------
    @task(1)
    def add_to_cart(self):
        if not self.token:
            return
        pid = f"p{random.randint(1, 10)}"
        self.client.post(
            "/api/cart",
            headers=self._auth,
            json={"productId": pid, "quantity": 1},
            name="POST /cart",
        )
