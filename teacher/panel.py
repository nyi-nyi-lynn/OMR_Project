# teacher/panel.py
import tkinter as tk
from tkinter import messagebox
import json
import os
from teacher.generate_sheet import generate_omr_sheet

os.makedirs("data", exist_ok=True)

class TeacherPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Teacher Panel - Setup MCQs")
        self.root.geometry("760x420")
        self.questions = []
        self.q_no = 1

        tk.Label(root, text="Teacher Panel: Add MCQs (All 4 options required)", font=("Arial", 14)).pack(pady=8)

        frame = tk.Frame(root)
        frame.pack(pady=8)

        tk.Label(frame, text="Question:").grid(row=0, column=0, sticky="e")
        self.q_text_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.q_text_var, width=80).grid(row=0, column=1, columnspan=3, padx=6, pady=4)

        self.choice_vars = {}
        for i, c in enumerate(["A","B","C","D"]):
            tk.Label(frame, text=f"{c}:").grid(row=i+1, column=0, sticky="e")
            self.choice_vars[c] = tk.StringVar()
            tk.Entry(frame, textvariable=self.choice_vars[c], width=70).grid(row=i+1, column=1, columnspan=3, padx=6, pady=2)

        tk.Label(frame, text="Correct Option (A/B/C/D):").grid(row=5, column=0, sticky="e")
        self.correct_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.correct_var, width=5).grid(row=5, column=1, sticky="w")

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="Add Question", width=18, command=self.add_question).grid(row=0, column=0, padx=6)
        tk.Button(btn_frame, text="Save Questions", width=18, command=self.save_questions).grid(row=0, column=1, padx=6)
        tk.Button(btn_frame, text="Generate OMR Sheet", width=18, command=self.generate_sheet).grid(row=0, column=2, padx=6)
        tk.Button(btn_frame, text="Load existing questions", width=18, command=self.load_questions).grid(row=0, column=3, padx=6)

        self.listbox = tk.Listbox(root, width=110, height=8)
        self.listbox.pack(pady=6)

        # If data/questions.json exists load it
        if os.path.exists("data/questions.json"):
            self.load_questions()

    def add_question(self):
        q_text = self.q_text_var.get().strip()
        choices = {c: self.choice_vars[c].get().strip() for c in ["A","B","C","D"]}
        correct = self.correct_var.get().strip().upper()
        if not q_text or correct not in ["A","B","C","D"] or any(v == "" for v in choices.values()):
            messagebox.showerror("Error", "Please fill question, all 4 options and correct option (A/B/C/D).")
            return
        item = {"q_no": self.q_no, "text": q_text, "choices": choices, "answer": correct}
        self.questions.append(item)
        self.listbox.insert(tk.END, f"Q{self.q_no}: {q_text} | A:{choices['A']} B:{choices['B']} C:{choices['C']} D:{choices['D']} | Ans:{correct}")
        self.q_no += 1
        self.clear_fields()

    def clear_fields(self):
        self.q_text_var.set("")
        for c in ["A","B","C","D"]:
            self.choice_vars[c].set("")
        self.correct_var.set("")

    def save_questions(self):
        if not self.questions and not os.path.exists("data/questions.json"):
            messagebox.showerror("Error", "No questions to save.")
            return
        # merge existing + new
        existing = []
        if os.path.exists("data/questions.json"):
            with open("data/questions.json", "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except:
                    existing = []
        # if current new ones appended, we append them after existing
        combined = existing + self.questions
        # reassign q_no sequentially
        for idx, q in enumerate(combined, start=1):
            q["q_no"] = idx
        with open("data/questions.json", "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Saved", f"{len(combined)} questions saved to data/questions.json")
        self.questions = []
        self.q_no = len(combined) + 1
        self.refresh_listbox()

    def load_questions(self):
        if not os.path.exists("data/questions.json"):
            messagebox.showinfo("Info", "No saved questions found.")
            return
        with open("data/questions.json", "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
            except:
                messagebox.showerror("Error", "Failed to load questions.json (invalid JSON).")
                return
        self.questions = []  # new ones empty; use loaded for display
        self.q_no = len(loaded) + 1
        self.refresh_listbox(loaded)
        messagebox.showinfo("Loaded", f"{len(loaded)} questions loaded from data/questions.json")

    def refresh_listbox(self, list_data=None):
        self.listbox.delete(0, tk.END)
        if list_data is None:
            if os.path.exists("data/questions.json"):
                with open("data/questions.json", "r", encoding="utf-8") as f:
                    try:
                        list_data = json.load(f)
                    except:
                        list_data = []
            else:
                list_data = []
        for q in list_data:
            choices = q.get("choices", {})
            self.listbox.insert(tk.END, f"Q{q.get('q_no')}: {q.get('text')} | A:{choices.get('A','')} B:{choices.get('B','')} C:{choices.get('C','')} D:{choices.get('D','')} | Ans:{q.get('answer')}")

    def generate_sheet(self):
        # Ensure questions saved
        if not os.path.exists("data/questions.json"):
            messagebox.showerror("Error", "No saved questions. Save questions first.")
            return
        generate_omr_sheet()
        messagebox.showinfo("Generated", "OMR sheet saved to assets/omr_sheet.png and layout to data/layout.json")
