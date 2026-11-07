"""Task 07 | Employee Payroll Engine"""
from abc import ABC, abstractmethod


def check_number(value, name, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(name + " must be a number that is not negative")
    if maximum is not None and value > maximum:
        raise ValueError(name + " must not be more than " + str(maximum))
    return value


class Employee(ABC):
    """Abstract class: cannot be created directly."""

    def __init__(self, name):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must not be empty")
        self.name = name

    @abstractmethod
    def calculate_pay(self):
        pass


class SalariedEmployee(Employee):
    def __init__(self, name, salary):
        super().__init__(name)
        self.salary = check_number(salary, "salary")

    def calculate_pay(self):
        return self.salary


class HourlyEmployee(Employee):
    def __init__(self, name, hourly_rate, hours):
        super().__init__(name)
        self.hourly_rate = check_number(hourly_rate, "hourly_rate")
        self.hours = check_number(hours, "hours")

    def calculate_pay(self):
        if self.hours <= 40:
            return self.hourly_rate * self.hours
        overtime_hours = self.hours - 40
        return self.hourly_rate * 40 + overtime_hours * self.hourly_rate * 1.5


class CommissionEmployee(Employee):
    def __init__(self, name, base, sales, rate):
        super().__init__(name)
        self.base = check_number(base, "base")
        self.sales = check_number(sales, "sales")
        self.rate = check_number(rate, "rate", maximum=1)

    def calculate_pay(self):
        return self.base + self.sales * self.rate


def payroll_summary(employees):
    """Print-ready summary for any mix of employee types."""
    lines = []
    total = 0
    for emp in employees:
        if not isinstance(emp, Employee):
            raise TypeError("payroll needs Employee objects")
        pay = round(emp.calculate_pay(), 2)       # same call works for every type
        total += pay
        lines.append("%-10s %-20s %10.2f" % (emp.name, type(emp).__name__, pay))
    lines.append("%-31s %10.2f" % ("TOTAL", total))
    return "\n".join(lines)


if __name__ == "__main__":
    staff = [
        SalariedEmployee("Ayesha", 60000),
        HourlyEmployee("Bilal", 20, 45),                # 950
        CommissionEmployee("Chand", 500, 4000, 0.10),   # 900
    ]
    print(payroll_summary(staff))
    try:
        Employee("Nobody")
    except TypeError as error:
        print("Error:", error)
