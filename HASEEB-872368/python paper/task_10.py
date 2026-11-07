"""Task 10 | CSV Inventory Reconciliation"""
import csv


def read_inventory(path):
    """Return {sku: {'name': ..., 'quantity': ...}}."""
    inventory = {}
    with open(path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            sku = row["sku"].strip()
            if sku == "" or sku in inventory:
                raise ValueError("empty or duplicate SKU in inventory: " + repr(sku))
            quantity = int(row["quantity"])          # raises ValueError if not a number
            if quantity < 0:
                raise ValueError("negative quantity for " + sku)
            inventory[sku] = {"name": row["name"].strip(), "quantity": quantity}
    return inventory


def process_movements(inventory, movements_path):
    """Apply movements in order. Returns the list of rejected rows."""
    rejected = []
    with open(movements_path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            sku = row["sku"].strip()
            movement_type = row["type"].strip().upper()
            reason = ""

            try:
                units = int(row["units"])
            except ValueError:
                units = 0
            if sku not in inventory:
                reason = "unknown SKU"
            elif movement_type not in ("IN", "OUT"):
                reason = "invalid movement type"
            elif units <= 0:
                reason = "units must be a positive whole number"
            elif movement_type == "OUT" and units > inventory[sku]["quantity"]:
                reason = "not enough stock"

            if reason != "":
                rejected.append({"sku": sku, "type": row["type"], "units": row["units"], "reason": reason})
                continue                            # keep processing the next rows

            if movement_type == "IN":
                inventory[sku]["quantity"] += units
            else:
                inventory[sku]["quantity"] -= units
    return rejected


def reconcile(inventory_path, movements_path):
    inventory = read_inventory(inventory_path)
    rejected = process_movements(inventory, movements_path)

    with open("updated_inventory.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["sku", "name", "quantity"])
        for sku in inventory:
            writer.writerow([sku, inventory[sku]["name"], inventory[sku]["quantity"]])

    with open("rejected_movements.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["sku", "type", "units", "reason"])
        writer.writeheader()
        writer.writerows(rejected)
    return inventory, rejected


def create_sample_data():
    with open("inventory.csv", "w", encoding="utf-8") as file:
        file.write("sku,name,quantity\nP01,Pen,10\nP02,Notebook,5\n")
    with open("movements.csv", "w", encoding="utf-8") as file:
        file.write("sku,type,units\n"
                   "P01,OUT,4\n"      # ok -> 6
                   "P01,OUT,9\n"      # rejected: not enough stock
                   "P01,IN,2\n"       # ok -> 8
                   "P99,IN,5\n"       # rejected: unknown SKU
                   "P02,MOVE,1\n"     # rejected: invalid type
                   "P02,IN,0\n")      # rejected: zero units


if __name__ == "__main__":
    create_sample_data()
    inventory, rejected = reconcile("inventory.csv", "movements.csv")
    for sku in inventory:
        print(sku, inventory[sku]["quantity"])
    print("Rejected rows:")
    for row in rejected:
        print(" ", row)
