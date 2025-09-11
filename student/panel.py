# student/panel.py
import tkinter as tk
from tkinter import messagebox, filedialog
import json, os
from omr.processor import realtime_scan, scan_image
from omr.utils import check_answers, export_result

os.makedirs("data", exist_ok=True)

class StudentPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Panel - Take Test")
        self.root.geometry("720x480")

        tk.Label(root, text="Student Panel", font=("Arial", 16)).pack(pady=8)

        form = tk.Frame(root)
        form.pack(pady=6)
        tk.Label(form, text="Student ID:").grid(row=0, column=0, sticky="e")
        self.student_id_var = tk.StringVar()
        tk.Entry(form, textvariable=self.student_id_var, width=30).grid(row=0, column=1, padx=8)

        tk.Button(root, text="Show Printed Questions (from sheet)", width=28, command=self.show_printed_questions).pack(pady=8)
        tk.Button(root, text="Start Camera Scan (press 's' to capture)", width=28, command=self.start_camera_scan).pack(pady=6)
        tk.Button(root, text="Scan Image File", width=28, command=self.scan_image_file).pack(pady=6)

        self.result_label = tk.Label(root, text="", font=("Arial", 12), justify="left")
        self.result_label.pack(pady=12)

    def _load_questions_and_layout(self):
        if not os.path.exists("data/questions.json") or not os.path.exists("data/layout.json"):
            messagebox.showerror("Error", "Missing questions.json or layout.json. Teacher must generate the sheet first.")
            return None, None
        with open("data/questions.json", "r", encoding="utf-8") as f:
            questions = json.load(f)
        with open("data/layout.json", "r", encoding="utf-8") as f:
            layout = json.load(f)
        # Build printed order mapping from layout: printed_index -> original_q_no
        printed_map = {entry["printed_index"]: entry["original_q_no"] for entry in layout}
        # Build a printed-ordered list of questions (use original q_no to find question)
        q_by_no = {q["q_no"]: q for q in questions}
        printed_questions = []
        for printed_idx in sorted(printed_map.keys()):
            orig = printed_map[printed_idx]
            q = q_by_no.get(orig, None)
            if q:
                printed_questions.append(q)
        return printed_questions, printed_map

    def show_printed_questions(self):
        printed_questions, _ = self._load_questions_and_layout()
        if printed_questions is None:
            return
        txt = ""
        for q in printed_questions:
            choices = q.get("choices", {})
            txt += f"Q{q['q_no']}: {q['text']}\n A:{choices.get('A','')}  B:{choices.get('B','')}  C:{choices.get('C','')}  D:{choices.get('D','')}\n\n"
        # show in messagebox (may be long)
        messagebox.showinfo("Printed Questions (order on the sheet)", txt[:10000])

    def start_camera_scan(self):
        student_id = self.student_id_var.get().strip() or "Unknown"
        printed_questions, printed_map = self._load_questions_and_layout()
        if printed_questions is None:
            return
        # Build answer_key mapping original_q_no -> correct answer from questions.json
        answer_key = {}
        for q in printed_questions:
            answer_key[q["q_no"]] = q["answer"]
        try:
            answers, score = realtime_scan(student_id, answer_key)
        except Exception as e:
            messagebox.showerror("Camera Error", str(e))
            return
        total = len(answer_key)
        export_result(student_id, answers, score, total)
        # prepare result text
        s = f"Student ID: {student_id}\nScore: {score}/{total}\n\n"
        for q_no, correct in answer_key.items():
            s += f"Q{q_no}: detected={answers.get(q_no,'-')} correct={correct}\n"
        self.result_label.config(text=s)

    def scan_image_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files","*.png;*.jpg;*.jpeg")])
        if not file_path:
            return
        student_id = self.student_id_var.get().strip() or "Unknown"
        answers, _ = scan_image(file_path)
        # we need answer_key to compute score
        printed_questions, _ = self._load_questions_and_layout()
        if printed_questions is None:
            return
        answer_key = {q["q_no"]: q["answer"] for q in printed_questions}
        score, total, details = check_answers(answers, answer_key)
        export_result(student_id, answers, score, total)
        s = f"Student ID: {student_id}\nScore: {score}/{total}\n\n"
        for q_no, det in details.items():
            s += f"Q{q_no}: detected={det['student']} correct={det['correct']}\n"
        self.result_label.config(text=s)
