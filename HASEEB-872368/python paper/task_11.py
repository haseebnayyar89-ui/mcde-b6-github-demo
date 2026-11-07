"""Task 11 | Multi-File Student Gradebook"""
import csv


def get_grade(average):
    if average >= 85:
        return "A"
    if average >= 70:
        return "B"
    if average >= 55:
        return "C"
    if average >= 40:
        return "D"
    return "F"


def read_students(path):
    students = {}                                   # student_id -> name
    with open(path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            student_id = row["student_id"].strip()
            if student_id == "" or student_id in students:
                raise ValueError("empty or duplicate student id: " + repr(student_id))
            students[student_id] = row["name"].strip()
    return students


def read_scores(path, students):
    """Return ({student_id: {subject: marks}}, rejected_rows)."""
    scores = {}
    rejected = []
    with open(path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            student_id = row["student_id"].strip()
            subject = row["subject"].strip()
            reason = ""

            try:
                marks = float(row["marks"])
            except ValueError:
                marks = -1
            if student_id not in students:
                reason = "unknown student id"
            elif subject == "":
                reason = "subject is empty"
            elif not 0 <= marks <= 100:
                reason = "marks must be a number from 0 to 100"
            elif subject in scores.get(student_id, {}):
                reason = "duplicate student-subject entry"

            if reason != "":
                rejected.append({"student_id": student_id, "subject": subject,
                                 "marks": row["marks"], "reason": reason})
                continue
            scores.setdefault(student_id, {})[subject] = marks
    return scores, rejected


def build_report(students, scores):
    rows = []
    for student_id in students:
        if student_id in scores:
            marks_list = list(scores[student_id].values())
            average = sum(marks_list) / len(marks_list)
            rows.append({"student_id": student_id, "name": students[student_id],
                         "average": round(average, 2), "grade": get_grade(average)})
    # rank by average (high first), then by student id
    rows.sort(key=lambda r: (-r["average"], r["student_id"]))
    for index, row in enumerate(rows):
        row["rank"] = index + 1
    return rows


def generate_report(students_path, scores_path, output_path="report.csv"):
    students = read_students(students_path)
    scores, rejected = read_scores(scores_path, students)
    rows = build_report(students, scores)
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["rank", "student_id", "name", "average", "grade"])
        writer.writeheader()
        writer.writerows(rows)
    return rows, rejected


def create_sample_data():
    with open("students.csv", "w", encoding="utf-8") as file:
        file.write("student_id,name\n101,Ayesha\n102,Bilal\n103,Chand\n")
    with open("scores.csv", "w", encoding="utf-8") as file:
        file.write("student_id,subject,marks\n"
                   "101,Math,90\n101,Physics,80\n101,English,85\n"   # average 85.0 -> A
                   "102,Math,60\n102,Physics,72\n"
                   "103,Math,30\n103,Math,99\n"                       # duplicate -> rejected
                   "999,Math,50\n"                                    # unknown id -> rejected
                   "102,English,150\n")                               # out of range -> rejected


if __name__ == "__main__":
    create_sample_data()
    report, rejected = generate_report("students.csv", "scores.csv")
    for row in report:
        print(row)
    print("Rejected rows:")
    for row in rejected:
        print(" ", row)
