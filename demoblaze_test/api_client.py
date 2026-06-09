import base64
import uuid


class APIClient:
    def __init__(self, client):
        self.client = client
        self.auth_token = None
        self.guest_cookie = f"user={self._guid()}"
        self.username = None

    @staticmethod
    def _guid():
        return str(uuid.uuid4())

    def _cart_cookie(self):
        return self.auth_token or self.guest_cookie

    def _cart_flag(self):
        return bool(self.auth_token)

    def get_entries(self):
        with self.client.get("/entries", catch_response=True) as r:
            if r.status_code == 200 and r.text:
                items = r.json().get("Items", [])
                if not items:
                    r.failure("No products returned")
            elif r.status_code != 200:
                r.failure(f"GET /entries returned {r.status_code}")
        return r

    def login(self, username, password):
        with self.client.post(
            "/login",
            json={
                "username": username,
                "password": base64.b64encode(password.encode()).decode(),
            },
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                if "Auth_token" in r.text:
                    self.username = username
                    self.auth_token = r.text.split(":")[1].strip().strip('"')
                elif "Wrong" in r.text:
                    r.failure("Login failed: wrong credentials")
            else:
                r.failure(f"POST /login returned {r.status_code}")
        return r

    def get_by_category(self, category):
        with self.client.post(
            "/bycat",
            json={"cat": category},
            name=f"/bycat ({category})",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                items = r.json().get("Items", [])
                if not items:
                    r.failure(f"No products in category: {category}")
            else:
                r.failure(f"POST /bycat returned {r.status_code}")
        return r

    def view_product(self, prod_id):
        with self.client.post("/view", json={"id": prod_id}, catch_response=True) as r:
            if r.status_code == 200:
                data = r.json()
                if "id" not in data:
                    r.failure("Product data missing 'id'")
            else:
                r.failure(f"POST /view returned {r.status_code}")
        return r

    def add_to_cart(self, prod_id):
        with self.client.post(
            "/addtocart",
            json={
                "id": self._guid(),
                "cookie": self._cart_cookie(),
                "prod_id": prod_id,
                "flag": self._cart_flag(),
            },
            catch_response=True,
        ) as r:
            if r.status_code != 200:
                r.failure(f"POST /addtocart returned {r.status_code}")
                return False
            elif "error" in r.text.lower():
                r.failure(f"addtocart failed: {r.text.strip()}")
                return False
        return True

    def view_cart(self):
        with self.client.post(
            "/viewcart",
            json={"cookie": self._cart_cookie(), "flag": self._cart_flag()},
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                items = r.json().get("Items", [])
                if not items:
                    r.failure("Cart is empty")
            else:
                r.failure(f"POST /viewcart returned {r.status_code}")
        return r

    def delete_cart(self):
        with self.client.post(
            "/deletecart", json={"cookie": self._cart_cookie()}, catch_response=True
        ) as r:
            if r.status_code != 200:
                r.failure(f"POST /deletecart returned {r.status_code}")
            elif "error" in r.text.lower():
                r.failure("Failed to delete cart")
        return r

    def checkout(self):
        self.view_cart()
        return self.delete_cart()
