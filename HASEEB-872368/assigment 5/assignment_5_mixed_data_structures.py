# Q41. Student Performance System
students = [
    {"id": 1, "name": "Ali", "marks": (85, 90, 88)},
    {"id": 2, "name": "Sara", "marks": (92, 95, 91)},
    {"id": 3, "name": "Ahmed", "marks": (78, 84, 80)}
]
ali_avg = sum(students[0]["marks"]) / len(students[0]["marks"])
sara_avg = sum(students[1]["marks"]) / len(students[1]["marks"])
ahmed_avg = sum(students[2]["marks"]) / len(students[2]["marks"])
top_student = max(students, key=lambda x: sum(x["marks"]))["name"]
names_tuple = (students[0]["name"], students[1]["name"], students[2]["name"])
unique_marks = set(students[0]["marks"] + students[1]["marks"] + students[2]["marks"])
print(ali_avg, sara_avg, ahmed_avg)
print(top_student)
print(names_tuple)
print(unique_marks)


# Q42. Employee Skills
employees = {
    "Ali": {"Python", "SQL", "AWS"},
    "Sara": {"Python", "Databricks", "SQL"},
    "Ahmed": {"AWS", "Snowflake", "SQL"}
}
common_skills = employees["Ali"] & employees["Sara"] & employees["Ahmed"]
ali_only = employees["Ali"] - employees["Sara"] - employees["Ahmed"]
all_team_skills = employees["Ali"] | employees["Sara"] | employees["Ahmed"]
python_sql_meeting = {name for name, skills in employees.items() if {"Python", "SQL"}.issubset(skills)}
print(common_skills)
print(ali_only)
print(all_team_skills)
print(python_sql_meeting)


# Q43. Sales Data
sales = [
    ("Laptop", 120000, 2),
    ("Mouse", 1500, 5),
    ("Keyboard", 3500, 3)
]
total_revenue = (sales[0][1] * sales[0][2]) + (sales[1][1] * sales[1][2]) + (sales[2][1] * sales[2][2])
top_revenue_product = max(sales, key=lambda x: x[1] * x[2])[0]
name_to_revenue = {sales[0][0]: sales[0][1] * sales[0][2], sales[1][0]: sales[1][1] * sales[1][2], sales[2][0]: sales[2][1] * sales[2][2]}
set_of_prices = {sales[0][1], sales[1][1], sales[2][1]}
print(total_revenue)
print(top_revenue_product)
print(name_to_revenue)
print(set_of_prices)


# Q44. Customer Orders
customers = {
    "C101": {"name": "Ali", "orders": [1200, 2500, 1800]},
    "C102": {"name": "Sara", "orders": [3000, 4500]},
    "C103": {"name": "Ahmed", "orders": [1500, 2000, 1000]}
}
spending_ali = sum(customers["C101"]["orders"])
spending_sara = sum(customers["C102"]["orders"])
spending_ahmed = sum(customers["C103"]["orders"])
top_customer = max(customers, key=lambda x: sum(customers[x]["orders"]))
totals_tuple = (spending_ali, spending_sara, spending_ahmed)
print(spending_ali, spending_sara, spending_ahmed)
print(top_customer)
print(totals_tuple)


# Q45. Course Enrollment
courses = {
    "Python": {"Ali", "Sara", "Ahmed"},
    "SQL": {"Sara", "Ahmed", "Zain"},
    "AWS": {"Ali", "Ahmed", "Zain"}
}
all_students_set = courses["Python"] | courses["SQL"] | courses["AWS"]
in_all_three = courses["Python"] & courses["SQL"] & courses["AWS"]
exactly_two = ((courses["Python"] & courses["SQL"]) - in_all_three) | ((courses["Python"] & courses["AWS"]) - in_all_three) | ((courses["SQL"] & courses["AWS"]) - in_all_three)
exactly_one = (courses["Python"] ^ courses["SQL"] ^ courses["AWS"]) - exactly_two - in_all_three
unique_count = len(all_students_set)
print(exactly_two)
print(in_all_three)
print(exactly_one)
print(unique_count)


# Q46. E-Commerce Transactions
transactions = [
    {"id": 101, "customer": "Ali", "items": [("Laptop", 120000, 1), ("Mouse", 1500, 2)]},
    {"id": 102, "customer": "Sara", "items": [("Keyboard", 3500, 2), ("Mouse", 1500, 1)]},
    {"id": 103, "customer": "Ali", "items": [("Monitor", 45000, 1)]}
]
total_revenue_ecommerce = (transactions[0]["items"][0][1] * transactions[0]["items"][0][2]) + (transactions[0]["items"][1][1] * transactions[0]["items"][1][2]) + (transactions[1]["items"][0][1] * transactions[1]["items"][0][2]) + (transactions[1]["items"][1][1] * transactions[1]["items"][1][2]) + (transactions[2]["items"][0][1] * transactions[2]["items"][0][2])
ali_spending = (transactions[0]["items"][0][1] * transactions[0]["items"][0][2]) + (transactions[0]["items"][1][1] * transactions[0]["items"][1][2]) + (transactions[2]["items"][0][1] * transactions[2]["items"][0][2])
largest_transaction = max(transactions, key=lambda t: sum(item[1] * item[2] for item in t["items"]))["id"]
unique_product_names = {item[0] for t in transactions for item in t["items"]}
print(total_revenue_ecommerce)
print(ali_spending)
print(largest_transaction)
print(unique_product_names)


# Q47. Pipeline Monitoring
pipelines = {
    "pipeline_1": {"status": "success", "records": (1000, 1200, 1100)},
    "pipeline_2": {"status": "failed", "records": (800, 0, 0)},
    "pipeline_3": {"status": "success", "records": (1500, 1600, 1700)}
}
total_processed = sum(pipelines["pipeline_1"]["records"]) + sum(pipelines["pipeline_2"]["records"]) + sum(pipelines["pipeline_3"]["records"])
failed_pipelines = [name for name, data in pipelines.items() if data["status"] == "failed"]
largest_pipeline_total = max(pipelines, key=lambda x: sum(pipelines[x]["records"]))
avg_records_p1 = sum(pipelines["pipeline_1"]["records"]) / len(pipelines["pipeline_1"]["records"])
avg_records_p2 = sum(pipelines["pipeline_2"]["records"]) / len(pipelines["pipeline_2"]["records"])
avg_records_p3 = sum(pipelines["pipeline_3"]["records"]) / len(pipelines["pipeline_3"]["records"])
print(total_processed)
print(failed_pipelines)
print(largest_pipeline_total)
print(avg_records_p1, avg_records_p2, avg_records_p3)


# Q48. Banking Transactions
accounts = {
    "A101": {"holder": "Ali", "transactions": [5000, -2000, 3000, -1000]},
    "A102": {"holder": "Sara", "transactions": [10000, -3000, -2000]},
    "A103": {"holder": "Ahmed", "transactions": [7000, -1500, 2500]}
}
final_balances = {k: sum(v["transactions"]) for k, v in accounts.items()}
highest_balance_account = max(final_balances, key=final_balances.get)
total_withdrawals = sum(-x for acc in accounts.values() for x in acc["transactions"] if x < 0)
largest_single_deposit = max(x for acc in accounts.values() for x in acc["transactions"] if x > 0)
print(final_balances)
print(highest_balance_account)
print(total_withdrawals)
print(largest_single_deposit)


# Q49. Product Recommendations
users = {
    "Ali": {"purchased": {"Laptop", "Mouse"}, "wishlist": {"Keyboard", "Monitor", "Mouse"}},
    "Sara": {"purchased": {"Keyboard", "Monitor"}, "wishlist": {"Laptop", "Mouse"}},
    "Ahmed": {"purchased": {"Laptop", "Keyboard"}, "wishlist": {"Monitor", "Headphones"}}
}
bought_at_least_two = (users["Ali"]["purchased"] & users["Sara"]["purchased"]) | (users["Sara"]["purchased"] & users["Ahmed"]["purchased"]) | (users["Ali"]["purchased"] & users["Ahmed"]["purchased"])
ali_wishlist_minus_purchases = users["Ali"]["wishlist"] - users["Ali"]["purchased"]
shared_wishlist = users["Ali"]["wishlist"] & users["Sara"]["wishlist"] & users["Ahmed"]["wishlist"]
all_products = users["Ali"]["purchased"] | users["Ali"]["wishlist"] | users["Sara"]["purchased"] | users["Sara"]["wishlist"] | users["Ahmed"]["purchased"] | users["Ahmed"]["wishlist"]
print(bought_at_least_two)
print(ali_wishlist_minus_purchases)
print(shared_wishlist)
print(all_products)


# Q50. Final Company Analysis
company = {
    "departments": {
        "Engineering": {
            "employees": [
                ("Ali", 120000, {"Python", "AWS", "SQL"}),
                ("Sara", 150000, {"Python", "Databricks", "SQL"})
            ],
            "budget": 500000
        },
        "Analytics": {
            "employees": [
                ("Ahmed", 100000, {"SQL", "Power BI"}),
                ("Zain", 130000, {"Python", "SQL", "Tableau"})
            ],
            "budget": 400000
        }
    }
}
eng_payroll = sum(emp[1] for emp in company["departments"]["Engineering"]["employees"])
analytics_payroll = sum(emp[1] for emp in company["departments"]["Analytics"]["employees"])
company_payroll = eng_payroll + analytics_payroll
all_emps = company["departments"]["Engineering"]["employees"] + company["departments"]["Analytics"]["employees"]
highest_paid = max(all_emps, key=lambda x: x[1])[0]
eng_skills = company["departments"]["Engineering"]["employees"][0][2] | company["departments"]["Engineering"]["employees"][1][2]
analytics_skills = company["departments"]["Analytics"]["employees"][0][2] | company["departments"]["Analytics"]["employees"][1][2]
skills_shared_by_all = eng_skills & analytics_skills
engineering_only_skills = eng_skills - analytics_skills
remaining_eng_budget = company["departments"]["Engineering"]["budget"] - eng_payroll
remaining_analytics_budget = company["departments"]["Analytics"]["budget"] - analytics_payroll
eng_avg_salary = eng_payroll / len(company["departments"]["Engineering"]["employees"])
analytics_avg_salary = analytics_payroll / len(company["departments"]["Analytics"]["employees"])
higher_avg_dept = "Engineering" if eng_avg_salary > analytics_avg_salary else "Analytics"
name_to_salary = {emp[0]: emp[1] for emp in all_emps}
all_unique_skills = eng_skills | analytics_skills
is_budget_sufficient = company["departments"]["Engineering"]["budget"] + company["departments"]["Analytics"]["budget"] >= company_payroll

print(eng_payroll, analytics_payroll)
print(company_payroll)
print(highest_paid)
print(skills_shared_by_all)
print(engineering_only_skills)
print(remaining_eng_budget, remaining_analytics_budget)
print(higher_avg_dept)
print(name_to_salary)
print(all_unique_skills)
print(is_budget_sufficient)