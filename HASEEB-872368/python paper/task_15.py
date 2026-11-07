"""Task 15 | Integrated Order Fulfillment System

Run demo:   python task_15.py
Run tests:  python task_15.py test
"""
import json
import os
import sys
import tempfile
import unittest
import uuid


class Product:
    def __init__(self, product_id, name, price):
        if price < 0:
            raise ValueError("price must not be negative")
        self.product_id = product_id
        self.name = name
        self.price = price


class Inventory:
    def __init__(self):
        self.products = {}      # product_id -> Product
        self.stock = {}         # product_id -> quantity

    def load_catalog(self, path):
        """Catalog JSON: [{"id": "P1", "name": "Pen", "price": 100, "stock": 5}, ...]"""
        with open(path, "r", encoding="utf-8") as file:
            items = json.load(file)
        for item in items:
            if item["stock"] < 0:
                raise ValueError("stock must not be negative")
            self.products[item["id"]] = Product(item["id"], item["name"], item["price"])
            self.stock[item["id"]] = item["stock"]

    def check_item(self, product_id, quantity):
        if product_id not in self.products:
            raise ValueError("unknown product: " + str(product_id))
        if quantity > self.stock[product_id]:
            raise ValueError("out of stock: " + product_id)


class Cart:
    def __init__(self):
        self.items = {}         # product_id -> quantity
        self.discount_percent = 0

    def add(self, product_id, quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("quantity must be a positive whole number")
        self.items[product_id] = self.items.get(product_id, 0) + quantity

    def set_discount(self, percent):
        if isinstance(percent, bool) or not isinstance(percent, (int, float)) or not 0 <= percent <= 100:
            raise ValueError("discount must be between 0 and 100")
        self.discount_percent = percent

    def total(self, inventory):
        subtotal = 0
        for product_id in self.items:
            subtotal += inventory.products[product_id].price * self.items[product_id]
        return round(subtotal * (100 - self.discount_percent) / 100, 2)


class Order:
    def __init__(self, items, total):
        self.order_id = "ORD-" + uuid.uuid4().hex[:10].upper()     # unique id
        self.items = dict(items)
        self.total = total

    def to_dict(self):
        return {"order_id": self.order_id, "items": self.items, "total": self.total}


def save_order(order, orders_file):
    orders = []
    if os.path.exists(orders_file):
        with open(orders_file, "r", encoding="utf-8") as file:
            orders = json.load(file)
    orders.append(order.to_dict())
    with open(orders_file, "w", encoding="utf-8") as file:
        json.dump(orders, file, indent=2)


def place_order(cart, inventory, orders_file, save_function=save_order):
    if not cart.items:
        raise ValueError("cart is empty")

    # 1) validate ALL items first, before changing any stock
    for product_id in cart.items:
        inventory.check_item(product_id, cart.items[product_id])

    order = Order(cart.items, cart.total(inventory))

    # 2) reduce stock, then save the order; if saving fails, give the stock back
    old_stock = dict(inventory.stock)
    for product_id in cart.items:
        inventory.stock[product_id] -= cart.items[product_id]
    try:
        save_function(order, orders_file)
    except Exception:
        inventory.stock = old_stock
        raise
    return order


# ---------------- unit tests ----------------
class OrderTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        catalog = os.path.join(self.folder, "catalog.json")
        with open(catalog, "w") as file:
            json.dump([{"id": "P1", "name": "Pen", "price": 100, "stock": 5}], file)
        self.inventory = Inventory()
        self.inventory.load_catalog(catalog)
        self.orders_file = os.path.join(self.folder, "orders.json")

    def test_successful_order_with_discount(self):
        cart = Cart()
        cart.add("P1", 2)
        cart.set_discount(10)
        order = place_order(cart, self.inventory, self.orders_file)
        self.assertEqual(order.total, 180)
        self.assertEqual(self.inventory.stock["P1"], 3)

    def test_out_of_stock_changes_nothing(self):
        cart = Cart()
        cart.add("P1", 6)
        with self.assertRaises(ValueError):
            place_order(cart, self.inventory, self.orders_file)
        self.assertEqual(self.inventory.stock["P1"], 5)

    def test_invalid_quantity_rejected(self):
        for bad in (0, -2, 1.5, "3"):
            with self.assertRaises(ValueError):
                Cart().add("P1", bad)

    def test_rollback_when_saving_fails(self):
        def broken_save(order, path):
            raise OSError("disk error")
        cart = Cart()
        cart.add("P1", 2)
        with self.assertRaises(OSError):
            place_order(cart, self.inventory, self.orders_file, save_function=broken_save)
        self.assertEqual(self.inventory.stock["P1"], 5)

    def test_order_ids_are_unique(self):
        ids = set()
        for i in range(3):
            cart = Cart()
            cart.add("P1", 1)
            ids.add(place_order(cart, self.inventory, self.orders_file).order_id)
        self.assertEqual(len(ids), 3)


def main():
    with open("catalog.json", "w", encoding="utf-8") as file:
        json.dump([{"id": "P1", "name": "Pen", "price": 100, "stock": 5}], file)
    inventory = Inventory()
    inventory.load_catalog("catalog.json")

    cart = Cart()
    cart.add("P1", 2)
    cart.set_discount(10)
    order = place_order(cart, inventory, "orders.json")
    print("Order", order.order_id, "total =", order.total, "| stock left =", inventory.stock["P1"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        unittest.main(argv=[sys.argv[0], "-v"])
    else:
        main()
