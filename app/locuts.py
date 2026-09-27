from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def index(self):
        self.client.get("/")

    @task
    def product(self):
        self.client.get("/api/products")

    @task
    def lives(self):
        self.client.get("/api/lives")
    
    @task
    def shops(self):
            self.client.get("/api/shops")

    @task
    def livreur(self):   
            self.client.get("/api/deliveries")            