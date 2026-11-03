"""
Python OOP: Four Pillars Assignment (Q1 to Q8)
Uses only the Python standard library.
"""
from abc import ABC, abstractmethod


# ======================================================================
# Q1. Student Result Manager  |  Pillar: Encapsulation
# ======================================================================

class Student:
    def __init__(self, name, marks=0):
        self.name = name          # public
        self._marks = 0           # protected (convention)
        self.__grade = "F"        # private (name mangling)
        self.set_marks(marks)

    def __calculate_grade(self):
        if self._marks >= 80:
            return "A"
        elif self._marks >= 60:
            return "B"
        elif self._marks >= 40:
            return "C"
        return "F"

    def set_marks(self, marks):
        valid_type = isinstance(marks, (int, float)) and not isinstance(marks, bool)
        if valid_type and 0 <= marks <= 100:
            self._marks = marks
            self.__grade = self.__calculate_grade()
            print(f"{self.name}: marks updated to {marks}")
            return True
        print(f"{self.name}: invalid marks '{marks}' (must be 0 to 100)")
        return False

    def get_marks(self):
        return self._marks

    def get_grade(self):
        return self.__grade


# ======================================================================
# Q2. Secure Bank Account  |  Pillar: Encapsulation
# ======================================================================

class BankAccount:
    def __init__(self, holder_name, initial_balance, pin):
        self.holder_name = holder_name   # public
        self.__balance = initial_balance  # private
        self.__pin = pin                  # private

    def __check_pin(self, pin):
        return pin == self.__pin

    def deposit(self, amount):
        if amount <= 0:
            print("Deposit rejected: amount must be greater than zero.")
            return False
        self.__balance += amount
        print(f"Deposit successful: Rs. {amount}. New balance: Rs. {self.__balance}")
        return True

    def withdraw(self, amount, pin):
        if not self.__check_pin(pin):
            print("Withdrawal rejected: incorrect PIN.")
            return False
        if amount <= 0:
            print("Withdrawal rejected: amount must be greater than zero.")
            return False
        if amount > self.__balance:
            print("Withdrawal rejected: insufficient balance.")
            return False
        self.__balance -= amount
        print(f"Withdrawal successful: Rs. {amount}. New balance: Rs. {self.__balance}")
        return True

    def get_balance(self, pin):
        if not self.__check_pin(pin):
            print("Access denied: incorrect PIN.")
            return None
        return self.__balance


# ======================================================================
# Q3. Employee Roles  |  Pillar: Inheritance
# ======================================================================

class Employee:
    def __init__(self, name, employee_id):
        self.name = name
        self.employee_id = employee_id

    def display_details(self):
        print(f"Name: {self.name}")
        print(f"Employee ID: {self.employee_id}")


class Developer(Employee):
    def __init__(self, name, employee_id, programming_language):
        super().__init__(name, employee_id)
        self.programming_language = programming_language

    def display_details(self):
        super().display_details()
        print("Role: Developer")
        print(f"Programming Language: {self.programming_language}")


class Manager(Employee):
    def __init__(self, name, employee_id, team_size):
        super().__init__(name, employee_id)
        self.team_size = team_size

    def display_details(self):
        super().display_details()
        print("Role: Manager")
        print(f"Team Size: {self.team_size}")


# ======================================================================
# Q4. Vehicle Rental System  |  Pillar: Inheritance
# ======================================================================

class Vehicle:
    def __init__(self, brand, model, daily_rate):
        self.brand = brand
        self.model = model
        self.daily_rate = daily_rate

    def calculate_rent(self, days):
        if days <= 0:
            raise ValueError("Rental duration must be at least 1 day.")
        return self.daily_rate * days


class Car(Vehicle):
    INSURANCE_FEE = 1000

    def calculate_rent(self, days):
        base = super().calculate_rent(days)
        return base + self.INSURANCE_FEE


class Bike(Vehicle):
    DISCOUNT = 0.10

    def calculate_rent(self, days):
        base = super().calculate_rent(days)
        return base - (base * self.DISCOUNT)


# ======================================================================
# Q5. Notification Dispatcher  |  Pillar: Polymorphism
# ======================================================================

class EmailNotification:
    def send(self, message):
        print(f"[EMAIL] Sending email: {message}")


class SMSNotification:
    def send(self, message):
        print(f"[SMS] Sending text message: {message}")


class PushNotification:
    def send(self, message):
        print(f"[PUSH] Sending push alert: {message}")


def notify_all(notifications, message):
    for notification in notifications:
        notification.send(message)   # same call, different behaviour


# Added later - notify_all() is NOT changed
class WhatsAppNotification:
    def send(self, message):
        print(f"[WHATSAPP] Sending WhatsApp message: {message}")


# ======================================================================
# Q6. Checkout Discount Calculator  |  Pillar: Polymorphism
# ======================================================================

class Customer:
    discount_rate = 0.0
    label = "Customer"

    def final_price(self, amount):
        if amount < 0:
            raise ValueError("Bill amount cannot be negative.")
        return amount - (amount * self.discount_rate)


class RegularCustomer(Customer):
    discount_rate = 0.05
    label = "Regular"

    def final_price(self, amount):
        return super().final_price(amount)


class PremiumCustomer(Customer):
    discount_rate = 0.10
    label = "Premium"

    def final_price(self, amount):
        return super().final_price(amount)


class VIPCustomer(Customer):
    discount_rate = 0.20
    label = "VIP"

    def final_price(self, amount):
        return super().final_price(amount)


def print_receipt(customer, amount):
    final = customer.final_price(amount)
    print(f"{customer.label:<8} | Bill: Rs. {amount:,.2f} | "
          f"Discount: {customer.discount_rate * 100:.0f}% | Final: Rs. {final:,.2f}")


# Extension: new type, print_receipt() is NOT modified
class GoldCustomer(Customer):
    discount_rate = 0.15
    label = "Gold"

    def final_price(self, amount):
        return super().final_price(amount)


# ======================================================================
# Q7. Shape Calculator  |  Pillar: Abstraction
# ======================================================================

PI = 3.14159


class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

    @abstractmethod
    def perimeter(self):
        pass


class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return PI * self.radius ** 2

    def perimeter(self):
        return 2 * PI * self.radius


class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)


# ======================================================================
# Q8. Payment Gateway  |  Pillar: Abstraction
# ======================================================================

class PaymentMethod(ABC):
    name = "Payment"

    @staticmethod
    def _validate(amount):
        if amount <= 0:
            raise ValueError("Transaction amount must be positive.")

    @abstractmethod
    def pay(self, amount):
        pass

    @abstractmethod
    def refund(self, amount):
        pass


class CardPayment(PaymentMethod):
    name = "Card"

    def pay(self, amount):
        self._validate(amount)
        print(f"Method: {self.name} | Type: Payment | Amount: Rs. {amount:,.2f}")

    def refund(self, amount):
        self._validate(amount)
        print(f"Method: {self.name} | Type: Refund  | Amount: Rs. {amount:,.2f}")


class WalletPayment(PaymentMethod):
    name = "Wallet"

    def pay(self, amount):
        self._validate(amount)
        print(f"Method: {self.name} | Type: Payment | Amount: Rs. {amount:,.2f}")

    def refund(self, amount):
        self._validate(amount)
        print(f"Method: {self.name} | Type: Refund  | Amount: Rs. {amount:,.2f}")


class BankTransferPayment(PaymentMethod):
    name = "Bank Transfer"

    def pay(self, amount):
        self._validate(amount)
        print(f"Method: {self.name} | Type: Payment | Amount: Rs. {amount:,.2f}")

    def refund(self, amount):
        self._validate(amount)
        print(f"Method: {self.name} | Type: Refund  | Amount: Rs. {amount:,.2f}")


def process_transaction(method, amount):
    method.pay(amount)


# Extension: new method, process_transaction() is NOT modified
class MobileBankingPayment(PaymentMethod):
    name = "Mobile Banking"

    def pay(self, amount):
        self._validate(amount)
        print(f"Method: {self.name} | Type: Payment | Amount: Rs. {amount:,.2f}")

    def refund(self, amount):
        self._validate(amount)
        print(f"Method: {self.name} | Type: Refund  | Amount: Rs. {amount:,.2f}")


def demo_q1():
    print("\n==================== Q1. Student Result Manager ====================")
    s1 = Student("Haseeb", 85)
    s2 = Student("Ali", 55)

    print("\n--- Valid update ---")
    s2.set_marks(72)
    print(f"{s2.name} -> Marks: {s2.get_marks()}, Grade: {s2.get_grade()}")

    print("\n--- Invalid update ---")
    s1.set_marks(150)
    print(f"{s1.name} -> Marks: {s1.get_marks()}, Grade: {s1.get_grade()}")

    print("\n--- Extension: direct access to __grade ---")
    try:
        print(s1.__grade)
    except AttributeError as error:
        print("AttributeError:", error)
    print("Explanation: Python name mangling renames __grade to _Student__grade,")
    print("so s1.__grade is not found. It can still be reached as:", s1._Student__grade)
    print("This is a convention to discourage access, not real security.")


def demo_q2():
    print("\n==================== Q2. Secure Bank Account ====================")
    acc1 = BankAccount("Haseeb", 5000, 1234)
    acc2 = BankAccount("Sara", 2000, 4321)

    print("--- Account 1 ---")
    acc1.deposit(1500)                 # successful deposit
    acc1.withdraw(2000, 1234)          # successful withdrawal
    acc1.deposit(-100)                 # rejected: negative deposit
    acc1.withdraw(500, 9999)           # rejected: wrong PIN
    print("Balance:", acc1.get_balance(1234))

    print("\n--- Account 2 ---")
    acc2.withdraw(10000, 4321)         # rejected: exceeds balance
    print("Balance:", acc2.get_balance(4321))

    print("\n--- Extension: are double underscores real security? ---")
    print("Direct acc1.__balance fails, but name mangling still exposes it:")
    print("acc1._BankAccount__balance =", acc1._BankAccount__balance)
    print("acc1._BankAccount__pin     =", acc1._BankAccount__pin)
    print("Explanation: Python only renames the attribute to _ClassName__attr.")
    print("Anyone who knows this pattern can read or change it, so it prevents")
    print("accidental access only. Real security needs a database, hashing, and")
    print("server-side access control.")


def demo_q3():
    print("\n==================== Q3. Employee Roles ====================")
    dev = Developer("Ahmed Khan", "E101", "Python")
    mgr = Manager("Fatima Ali", "E202", 8)

    print("--- Developer ---")
    dev.display_details()
    print("\n--- Manager ---")
    mgr.display_details()


def demo_q4():
    print("\n==================== Q4. Vehicle Rental System ====================")
    car = Car("Toyota", "Corolla", 3000)
    bike = Bike("Honda", "CD70", 800)

    days = 3
    print(f"Car  ({car.brand} {car.model}) for {days} days: Rs. {car.calculate_rent(days):,.2f}")
    print(f"Bike ({bike.brand} {bike.model}) for {days} days: Rs. {bike.calculate_rent(days):,.2f}")

    print("\n--- Invalid duration ---")
    for vehicle in (car, bike):
        try:
            vehicle.calculate_rent(0)
        except ValueError as error:
            print(f"{vehicle.__class__.__name__}: Error - {error}")


def demo_q5():
    print("\n==================== Q5. Notification Dispatcher ====================")
    print("--- Original channels ---")
    notify_all([EmailNotification(), SMSNotification(), PushNotification()],
               "Your order has been shipped.")

    print("\n--- After adding WhatsAppNotification ---")
    notify_all([EmailNotification(), WhatsAppNotification()],
               "Your payment was received.")

    print("\nWhere polymorphism occurs:")
    print("Inside notify_all(), the line notification.send(message) is one call,")
    print("but the output depends on the object's class (Email, SMS, Push, WhatsApp).")
    print("The function never checks types, so new channels work without edits.")


def demo_q6():
    print("\n==================== Q6. Checkout Discount Calculator ====================")
    bill = 10000
    customers = [RegularCustomer(), PremiumCustomer(), VIPCustomer()]

    print("--- Bill of Rs. 10,000 ---")
    for c in customers:
        print_receipt(c, bill)

    print("\n--- Extension: GoldCustomer ---")
    print_receipt(GoldCustomer(), bill)

    print("\n--- Negative bill ---")
    try:
        print_receipt(RegularCustomer(), -500)
    except ValueError as error:
        print("Error:", error)


def demo_q7():
    print("\n==================== Q7. Shape Calculator ====================")
    shapes = [Circle(5), Rectangle(4, 6)]
    for shape in shapes:
        print(f"{shape.__class__.__name__}: Area = {shape.area():.2f}, "
              f"Perimeter = {shape.perimeter():.2f}")

    print("\n--- Instantiating abstract Shape ---")
    try:
        Shape()
    except TypeError as error:
        print("TypeError:", error)
    print("Explanation: Shape has abstract methods (area, perimeter) with no")
    print("implementation, so Python refuses to create an object of it. Only")
    print("subclasses that implement all abstract methods can be instantiated.")


def demo_q8():
    print("\n==================== Q8. Payment Gateway ====================")
    print("--- Payments ---")
    for m in (CardPayment(), WalletPayment(), BankTransferPayment()):
        process_transaction(m, 2500)

    print("\n--- Refunds ---")
    CardPayment().refund(500)
    WalletPayment().refund(300)

    print("\n--- Extension: MobileBankingPayment ---")
    process_transaction(MobileBankingPayment(), 1800)

    print("\n--- Invalid amount ---")
    try:
        process_transaction(CardPayment(), -100)
    except ValueError as error:
        print("Error:", error)

    print("\n--- Abstract class cannot be instantiated ---")
    try:
        PaymentMethod()
    except TypeError as error:
        print("TypeError:", error)


if __name__ == "__main__":
    demo_q1()
    demo_q2()
    demo_q3()
    demo_q4()
    demo_q5()
    demo_q6()
    demo_q7()
    demo_q8()
