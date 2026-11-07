"""Task 06 | Banking Ledger with OOP"""
from collections import namedtuple

# namedtuple is immutable, so a transaction record can never be changed
Transaction = namedtuple("Transaction", ["transaction_id", "action", "amount", "balance"])


def check_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("amount must be a number greater than zero")


class Account:
    def __init__(self, account_id, owner, opening_balance=0):
        if not account_id or not owner:
            raise ValueError("account_id and owner are required")
        if isinstance(opening_balance, bool) or not isinstance(opening_balance, (int, float)) or opening_balance < 0:
            raise ValueError("opening balance must be zero or more")
        self._account_id = account_id
        self._owner = owner
        self._balance = 0
        self._transactions = []
        if opening_balance > 0:
            self._add("open", opening_balance)

    @property
    def account_id(self):
        return self._account_id

    @property
    def balance(self):
        return self._balance

    @property
    def transactions(self):
        return tuple(self._transactions)     # copy, so outside code cannot edit the list

    def _add(self, action, amount):
        """Change the balance and save a transaction record."""
        if action in ("withdrawal", "transfer_out"):
            self._balance -= amount
        else:
            self._balance += amount
        record = Transaction(len(self._transactions) + 1, action, amount, self._balance)
        self._transactions.append(record)

    def deposit(self, amount):
        check_amount(amount)
        self._add("deposit", amount)

    def withdraw(self, amount):
        check_amount(amount)
        if amount > self._balance:
            raise ValueError("insufficient funds")
        self._add("withdrawal", amount)

    def statement(self):
        lines = ["Statement for " + self._owner + " (" + self._account_id + ")"]
        for t in self._transactions:
            lines.append("#%d  %-12s %10.2f  balance %10.2f" % (t.transaction_id, t.action, t.amount, t.balance))
        return "\n".join(lines)


class Bank:
    def __init__(self):
        self._accounts = {}

    def open_account(self, account_id, owner, opening_balance=0):
        if account_id in self._accounts:
            raise ValueError("account already exists: " + str(account_id))
        self._accounts[account_id] = Account(account_id, owner, opening_balance)
        return self._accounts[account_id]

    def get_account(self, account_id):
        if account_id not in self._accounts:
            raise ValueError("account does not exist: " + str(account_id))
        return self._accounts[account_id]

    def transfer(self, from_id, to_id, amount):
        # 1) check everything first, 2) only then change both accounts
        check_amount(amount)
        source = self.get_account(from_id)
        target = self.get_account(to_id)
        if source is target:
            raise ValueError("cannot transfer to the same account")
        if amount > source.balance:
            raise ValueError("insufficient funds")
        source._add("transfer_out", amount)
        target._add("transfer_in", amount)


if __name__ == "__main__":
    bank = Bank()
    bank.open_account("A", "Ali", 1000)
    bank.open_account("B", "Sara", 200)
    bank.transfer("A", "B", 350)
    print("A =", bank.get_account("A").balance, " B =", bank.get_account("B").balance)

    for from_id, to_id, amount in [("A", "B", 99999), ("A", "ZZZ", 10), ("A", "B", -5)]:
        try:
            bank.transfer(from_id, to_id, amount)
        except ValueError as error:
            print("Rejected:", error)
    print("After rejected transfers: A =", bank.get_account("A").balance, " B =", bank.get_account("B").balance)
    print(bank.get_account("A").statement())
