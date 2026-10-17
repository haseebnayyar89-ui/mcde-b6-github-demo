# Q11. Tuple Indexing
colors = ("red", "green", "blue", "yellow", "purple")
second_color = colors[1]
last_color = colors[-1]
middle_three = colors[1:4]
print(second_color)
print(last_color)
print(middle_three)


# Q12. Tuple Unpacking
employee = ("Ali", 28, "Data Engineer", 150000)
name, age, designation, salary = employee
print(name)
print(salary)


# Q13. Tuple Concatenation
tuple1 = (10, 20, 30)
tuple2 = (40, 50, 60)
combined_tuple = tuple1 + tuple2
reversed_tuple = combined_tuple[::-1]
print(combined_tuple)
print(reversed_tuple)


# Q14. Count and Locate
numbers = (10, 20, 30, 20, 40, 20, 50)
count_twenty = numbers.count(20)
first_index_twenty = numbers.index(20)
print(count_twenty)
print(first_index_twenty)


# Q15. Extended Tuple Unpacking
data = (100, 200, 300, 400, 500, 600)
first, second, *remaining, last = data
remaining_list = list(remaining)
print(first, second, last)
print(remaining_list)


# Q16. Modify an Immutable Tuple
numbers = (10, 20, 30, 40, 50)
modified_tuple = numbers[:2] + (300,) + numbers[3:]
print(modified_tuple)


# Q17. Nested Tuple Access
students = (
    ("Ali", (85, 90, 88)),
    ("Sara", (92, 87, 95)),
    ("Ahmed", (78, 84, 80))
)
sara_second_score = students[1][1][1]
ali_average = sum(students[0][1]) / len(students[0][1])
ahmed_highest_score = max(students[2][1])
print(sara_second_score)
print(ali_average)
print(ahmed_highest_score)


# Q18. Tuple Sorting
employees = (
    ("Ali", 80000),
    ("Sara", 120000),
    ("Ahmed", 95000)
)
sorted_employees = tuple(sorted(employees, key=lambda x: x[1], reverse=True))
print(sorted_employees)


# Q19. Tuple Matrix
matrix = ((2, 4, 6), (8, 10, 12), (14, 16, 18))
diagonal = (matrix[0][0], matrix[1][1], matrix[2][2])
product_diagonal = diagonal[0] * diagonal[1] * diagonal[2]
row_sums = (sum(matrix[0]), sum(matrix[1]), sum(matrix[2]))
print(diagonal)
print(product_diagonal)
print(row_sums)


# Q20. Inventory Tuple Challenge
records = (
    ("Laptop", 120000, 5),
    ("Mouse", 1500, 20),
    ("Keyboard", 3500, 10)
)
inventory_value = (records[0][1] * records[0][2]) + (records[1][1] * records[1][2]) + (records[2][1] * records[2][2])
most_expensive = max(records, key=lambda x: x[1])[0]
names_reversed = (records[2][0], records[1][0], records[0][0])
print(inventory_value)
print(most_expensive)
print(names_reversed)