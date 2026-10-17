# Q1. List Indexing and Slicing
numbers = [10, 20, 30, 40, 50, 60, 70, 80]
first_three = numbers[:3]
last_two = numbers[-2:]
middle_four = numbers[2:6]
reversed_list = numbers[::-1]
print(first_three)
print(last_two)
print(middle_four)
print(reversed_list)


# Q2. List Modification
data = [5, 10, 15, 20, 25]
data[1] = 99
data.append(30)
data.insert(0, 1)
data.remove(15)
popped_val = data.pop()
print(data)
print(popped_val)


# Q3. List Concatenation & Extension
list1 = [1, 2, 3]
list2 = [4, 5, 6]
combined_plus = list1 + list2
list1.extend(list2)
repeated_list = list2 * 3
print(combined_plus)
print(list1)
print(repeated_list)


# Q4. Basic Aggregations
scores = [45, 88, 92, 67, 100, 54, 88]
max_score = max(scores)
min_score = min(scores)
sum_scores = sum(scores)
len_scores = len(scores)
avg_score = sum_scores / len_scores
count_88 = scores.count(88)
index_100 = scores.index(100)
print(max_score)
print(min_score)
print(sum_scores)
print(avg_score)
print(count_88)
print(index_100)


# Q5. List Sorting & Reversing
vals = [34, 12, 89, 5, 67, 23]
sorted_new = sorted(vals)
sorted_desc = sorted(vals, reverse=True)
vals.sort()
vals.reverse()
print(sorted_new)
print(sorted_desc)
print(vals)


# Q6. Nested List Extraction
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
val_5 = matrix[1][1]
val_9 = matrix[2][2]
row_2 = matrix[1]
col_3 = [matrix[0][2], matrix[1][2], matrix[2][2]]
print(val_5)
print(val_9)
print(row_2)
print(col_3)


# Q7. List Operations Challenge
items = [10, 20, 30, 40, 50, 60]
first_half = items[:len(items)//2]
second_half = items[len(items)//2:]
swapped = second_half + first_half
print(swapped)


# Q8. Element Swapping
arr = [100, 200, 300, 400]
arr[0], arr[-1] = arr[-1], arr[0]
print(arr)


# Q9. Cumulative Calculations
nums = [10, 20, 30, 40]
cum_sum = [
    nums[0],
    nums[0] + nums[1],
    nums[0] + nums[1] + nums[2],
    nums[0] + nums[1] + nums[2] + nums[3]
]
print(cum_sum)


# Q10. Matrix Operations
m = [
    [10, 20, 30],
    [40, 50, 60],
    [70, 80, 90]
]
diag = [m[0][0], m[1][1], m[2][2]]
sum_diag = sum(diag)
row_sums = [sum(m[0]), sum(m[1]), sum(m[2])]
col_sums = [
    m[0][0] + m[1][0] + m[2][0],
    m[0][1] + m[1][1] + m[2][1],
    m[0][2] + m[1][2] + m[2][2]
]
print(diag)
print(sum_diag)
print(row_sums)
print(col_sums)