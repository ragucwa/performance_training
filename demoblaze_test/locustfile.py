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
    PRODUCTS_BY_CAT = {
        "phone": products["phones"],
        "notebook": products["laptops"],
        "monitor": products["monitors"],
    }

CATEGORY_WEIGHTS = [("phone", 50), ("notebook", 30), ("monitor", 20)]
ADD_TO_CART_CHANCE = 0.4


def think(min_s=1, max_s=3):
    time.sleep(random.uniform(min_s, max_s))


def pick_category():
    cats, weights = zip(*CATEGORY_WEIGHTS)
    return random.choices(cats, weights=weights, k=1)[0]


class BaseDemoblazeUser(HttpUser):
    abstract = True
    wait_time = between(1, 3)
    host = "https://api.demoblaze.com"

    def on_start(self):
        self.api = APIClient(self.client)
        self.cart_items = 0

    def browse_and_add(self):
        cat = pick_category()
        self.api.get_by_category(cat)
        think(1, 2)

        prod = random.choice(PRODUCTS_BY_CAT[cat])
        self.api.view_product(prod)
        think(1, 3)

        if random.random() < ADD_TO_CART_CHANCE:
            self.api.add_to_cart(prod)
            self.cart_items += 1
            think(1, 2)


class GuestUser(BaseDemoblazeUser):
    weight = 3

    @task
    def guest_flow(self):
        self.api.get_entries()
        think(1, 2)

        for _ in range(random.randint(1, 3)):
            self.browse_and_add()

        if self.cart_items > 0:
            self.api.view_cart()
            think(1, 2)
            self.api.delete_cart()
            self.cart_items = 0


class RegisteredUser(BaseDemoblazeUser):
    weight = 7

    def on_start(self):
        super().on_start()
        self.user, self.pwd = random.choice(USERS)
        self.api.login(self.user, self.pwd)

    @task
    def registered_flow(self):
        self.api.get_entries()
        think(1, 2)

        for _ in range(random.randint(1, 3)):
            self.browse_and_add()

        if self.cart_items > 0:
            self.api.view_cart()
            think(1, 2)
            self.api.checkout()
            self.cart_items = 0
