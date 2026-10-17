# Q21. Unique Values
numbers = [10, 20, 10, 30, 40, 20, 50]
unique_set = set(numbers)
unique_count = len(unique_set)
print(unique_set)
print(unique_count)


# Q22. Set Operations
a = {1, 2, 3, 4, 5}
b = {4, 5, 6, 7, 8}
union_result = a | b
intersection_result = a & b
diff_result = a - b
symmetric_diff_result = a ^ b
print(union_result)
print(intersection_result)
print(diff_result)
print(symmetric_diff_result)


# Q23. Add and Remove
skills = {"Python", "SQL", "AWS"}
skills.add("Snowflake")
skills.add("Databricks")
skills.discard("AWS")
print(skills)


# Q24. Common Students
python_students = {"Ali", "Sara", "Ahmed", "Zain"}
sql_students = {"Sara", "Ahmed", "Hamza", "Usman"}
both_courses = python_students & sql_students
exact_one_course = python_students ^ sql_students
print(both_courses)
print(exact_one_course)


# Q25. Subset and Superset
required_skills = {"Python", "SQL"}
candidate_skills = {"Python", "SQL", "AWS", "Snowflake"}
is_subset = required_skills.issubset(candidate_skills)
is_superset = candidate_skills.issuperset(required_skills)
print(is_subset)
print(is_superset)


# Q26. Missing Numbers
numbers = {1, 2, 4, 6, 8, 10}
all_numbers = set(range(1, 11))
missing_numbers = all_numbers - numbers
print(missing_numbers)


# Q27. Three-Set Analysis
python = {"Ali", "Sara", "Ahmed", "Zain"}
sql = {"Sara", "Ahmed", "Hamza"}
aws = {"Ahmed", "Zain", "Hamza"}
in_all_three = python & sql & aws
python_and_sql_not_aws = (python & sql) - aws
at_least_two = (python & sql) | (python & aws) | (sql & aws)
print(in_all_three)
print(python_and_sql_not_aws)
print(at_least_two)


# Q28. Transaction Analysis
day1 = {101, 102, 103, 104}
day2 = {103, 104, 105, 106}
day3 = {104, 106, 107, 108}
all_days = day1 & day2 & day3
exactly_one_day = (day1 ^ day2 ^ day3) - (day1 & day2) - (day2 & day3) - (day1 & day3)
at_least_two_days = (day1 & day2) | (day2 & day3) | (day1 & day3)
print(all_days)
print(exactly_one_day)
print(at_least_two_days)


# Q29. Access Control
required_permissions = {"read", "write", "execute"}
user_permissions = {"read", "write", "delete"}
missing_permissions = required_permissions - user_permissions
extra_permissions = user_permissions - required_permissions
is_fully_authorized = required_permissions.issubset(user_permissions)
print(missing_permissions)
print(extra_permissions)
print(is_fully_authorized)


# Q30. Customer Segmentation
website = {"C1", "C2", "C3", "C4", "C5"}
mobile = {"C3", "C4", "C6", "C7"}
store = {"C2", "C4", "C7", "C8"}
all_three = website & mobile & store
exactly_two = ((website & mobile) - store) | ((website & store) - mobile) | ((mobile & store) - website)
exactly_one = (website ^ mobile ^ store) - exactly_two - all_three
print(all_three)
print(exactly_two)
print(exactly_one)