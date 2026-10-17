# Q31. Dictionary Access
student = {"name": "Ali", "age": 22, "course": "Python", "marks": 85}
student_name = student["name"]
student_marks = student["marks"]
student_city = student.get("city", "Karachi")
print(student_name)
print(student_marks)
print(student_city)


# Q32. Update Dictionary
employee = {"name": "Sara", "salary": 100000, "department": "IT"}
employee["salary"] = employee["salary"] * 1.20
employee["bonus"] = 15000
employee["department"] = "Data Engineering"
print(employee)


# Q33. Dictionary Methods
product = {"id": 101, "name": "Laptop", "price": 120000, "stock": 5}
keys = product.keys()
values = product.values()
items = product.items()
stock_value = product.pop("stock")
print(keys)
print(values)
print(items)
print(stock_value)
print(product)


# Q34. Merge Dictionaries
dict1 = {"a": 10, "b": 20, "c": 30}
dict2 = {"b": 50, "d": 40}
merged_dict = dict1 | dict2
print(merged_dict)


# Q35. Student Marks
marks = {"Ali": 85, "Sara": 92, "Ahmed": 78, "Zain": 88}
score_values = list(marks.values())
highest_score = max(score_values)
lowest_score = min(score_values)
average_score = sum(score_values) / len(score_values)
top_student = max(marks, key=marks.get)
print(highest_score)
print(lowest_score)
print(average_score)
print(top_student)


# Q36. Nested Employee Records
employees = {
    "E101": {"name": "Ali", "salary": 80000},
    "E102": {"name": "Sara", "salary": 120000},
    "E103": {"name": "Ahmed", "salary": 95000}
}
sara_salary = employees["E102"]["salary"]
employees["E101"]["salary"] = employees["E101"]["salary"] * 1.15
total_payroll = employees["E101"]["salary"] + employees["E102"]["salary"] + employees["E103"]["salary"]
print(sara_salary)
print(employees["E101"]["salary"])
print(total_payroll)


# Q37. Dictionary Inversion
data = {"Python": "Ali", "SQL": "Sara", "AWS": "Ahmed"}
keys_list = list(data.keys())
values_list = list(data.values())
inverse_dict = {values_list[0]: keys_list[0], values_list[1]: keys_list[1], values_list[2]: keys_list[2]}
print(inverse_dict)


# Q38. Order Calculation
order = {
    "laptop": {"price": 120000, "quantity": 2},
    "mouse": {"price": 1500, "quantity": 5},
    "keyboard": {"price": 3500, "quantity": 3}
}
subtotal_laptop = order["laptop"]["price"] * order["laptop"]["quantity"]
subtotal_mouse = order["mouse"]["price"] * order["mouse"]["quantity"]
subtotal_keyboard = order["keyboard"]["price"] * order["keyboard"]["quantity"]
grand_total = subtotal_laptop + subtotal_mouse + subtotal_keyboard
discounted_amount = grand_total * 0.90
print(subtotal_laptop, subtotal_mouse, subtotal_keyboard)
print(grand_total)
print(discounted_amount)


# Q39. Employee Performance
employees = {
    "Ali": {"python": 90, "sql": 85, "aws": 88},
    "Sara": {"python": 95, "sql": 92, "aws": 90},
    "Ahmed": {"python": 80, "sql": 87, "aws": 84}
}
ali_avg = (employees["Ali"]["python"] + employees["Ali"]["sql"] + employees["Ali"]["aws"]) / 3
sara_avg = (employees["Sara"]["python"] + employees["Sara"]["sql"] + employees["Sara"]["avg"] if "avg" in employees["Sara"] else employees["Sara"]["aws"]) / 3
ahmed_avg = (employees["Ahmed"]["python"] + employees["Ahmed"]["sql"] + employees["Ahmed"]["aws"]) / 3
top_performer = max(employees, key=lambda x: (employees[x]["python"] + employees[x]["sql"] + employees[x]["aws"]))
highest_sql = max(employees, key=lambda x: employees[x]["sql"])
print(ali_avg, sara_avg, ahmed_avg)
print(top_performer)
print(highest_sql)


# Q40. Inventory Management
inventory = {
    "P101": {"name": "Laptop", "price": 120000, "stock": 5},
    "P102": {"name": "Mouse", "price": 1500, "stock": 20},
    "P103": {"name": "Keyboard", "price": 3500, "stock": 10}
}
total_value = (inventory["P101"]["price"] * inventory["P101"]["stock"]) + (inventory["P102"]["price"] * inventory["P102"]["stock"]) + (inventory["P103"]["price"] * inventory["P103"]["stock"])
most_valuable = max(inventory, key=lambda x: inventory[x]["price"] * inventory[x]["stock"])
inventory["P101"]["stock"] -= 2
inventory["P102"]["stock"] -= 5
print(total_value)
print(most_valuable)
print(inventory["P101"]["stock"])
print(inventory["P102"]["stock"])