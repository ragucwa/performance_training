import json
import random
import time
from pathlib import Path

from locust import HttpUser, between, task

from api_client import APIClient

DATA_DIR = Path(__file__).parent / "data"

with open(DATA_DIR / "users.json") as f:
    USERS = [tuple(u) for u in json.load(f)["users"]]

with open(DATA_DIR / "products.json") as f:
    products = json.load(f)
    PHONES = products["phones"]
    LAPTOPS = products["laptops"]


def think(min_s=1, max_s=3):
    time.sleep(random.uniform(min_s, max_s))


class DemoblazeUser(HttpUser):
    wait_time = between(1, 3)
    host = "https://api.demoblaze.com"

    def on_start(self):
        self.api = APIClient(self.client)
        self.user, self.pwd = random.choice(USERS)

    @task
    def shopping_flow(self):
        self.api.get_entries()
        think(1, 2)

        self.api.login(self.user, self.pwd)
        think(1, 2)

        self.api.get_by_category("phone")
        think(1, 2)
        phone = random.choice(PHONES)
        self.api.view_product(phone)
        think(1, 3)
        self.api.add_to_cart(phone)
        think(1, 2)

        self.api.get_by_category("notebook")
        think(1, 2)
        laptop = random.choice(LAPTOPS)
        self.api.view_product(laptop)
        think(1, 3)
        self.api.add_to_cart(laptop)
        think(1, 2)

        self.api.checkout()
