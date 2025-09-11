# omr/utils.py
import csv
import os
os.makedirs("results", exist_ok=True)

def check_answers(student_answers, answer_key):
    score = 0
    total = 0
    details = {}
    for q, correct in answer_key.items():
        total += 1
        student_ans = student_answers.get(q, "-")
        details[q] = {"student": student_ans, "correct": correct}
        if student_ans == correct:
            score += 1
    return score, total, details

def export_result(student_id, answers, score, total, file_path="results/results.csv"):
    header_needed = not os.path.exists(file_path)
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header_needed:
            writer.writerow(["student_id", "answers_dict", "score", "total"])
        writer.writerow([student_id, str(answers), score, total])
