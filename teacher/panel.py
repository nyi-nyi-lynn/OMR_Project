# teacher/panel.py
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
import pandas as pd  # for Excel reading
from teacher.generate_sheet import generate_omr_sheet

os.makedirs("data", exist_ok=True)

class TeacherPanel:
    def __init__(self, root, go_back_callback=None):
        self.root = root
        self.go_back_callback = go_back_callback
        self.root.title("Create Questions Panel - Setup MCQs")
        self.root.geometry("850x600")
        self.questions = []
        self.q_no = 1
        self.loaded_questions = []

        tk.Label(
            root,
            text="Create Questions Panel: Add MCQs (All 5 options required)",
            font=("Arial", 14)
        ).pack(pady=8)

        frame = tk.Frame(root)
        frame.pack(pady=8)

        # Question Entry
        tk.Label(frame, text="Question:").grid(row=0, column=0, sticky="e")
        self.q_text_var = tk.StringVar()
        self.q_entry = tk.Entry(frame, textvariable=self.q_text_var, width=80)
        self.q_entry.grid(row=0, column=1, columnspan=3, padx=6, pady=4)
        self.q_entry.focus_set()

        # Choices Entries
        self.choice_vars = {}
        for i, c in enumerate(["A", "B", "C", "D", "E"]):
            tk.Label(frame, text=f"{c}:").grid(row=i + 1, column=0, sticky="e")
            self.choice_vars[c] = tk.StringVar()
            tk.Entry(frame, textvariable=self.choice_vars[c], width=70).grid(
                row=i + 1, column=1, columnspan=3, padx=6, pady=2
            )

        # Correct Option
        tk.Label(frame, text="Correct Option (A/B/C/D/E):").grid(row=6, column=0, sticky="e")
        self.correct_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.correct_var, width=5).grid(row=6, column=1, sticky="w")

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="Add Question", width=18, command=self.add_question).grid(row=0, column=0, padx=6)
        tk.Button(btn_frame, text="Save Questions", width=18, command=self.save_questions).grid(row=0, column=1, padx=6)
        tk.Button(btn_frame, text="Load existing questions", width=20, command=self.load_questions).grid(row=0, column=2, padx=6)
        tk.Button(btn_frame, text="Upload from Excel", width=18, command=self.upload_excel).grid(row=0, column=3, padx=6)
        tk.Button(btn_frame, text="Back To Main", width=18, command=self.back).grid(row=1, column=0, columnspan=6, pady=10)
        tk.Button(btn_frame, text="Delete All Questions", width=20, command=self.delete_all_questions).grid(row=0, column=4, padx=6)

        # Text widget for showing questions
        self.questions_frame = tk.Frame(root)
        self.questions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text_widget = tk.Text(self.questions_frame, wrap="word", font=("Courier New", 11), height=20, width=100)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y = tk.Scrollbar(self.questions_frame, orient="vertical", command=self.text_widget.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.config(yscrollcommand=scroll_y.set, state=tk.DISABLED)

        # Bind Enter key to add_question
        self.root.bind("<Return>", lambda event: self.add_question())

    # ---- Functions ----
    def add_question(self):
        q_text = self.q_text_var.get().strip()
        choices = {c: self.choice_vars[c].get().strip() for c in ["A", "B", "C", "D", "E"]}
        correct = self.correct_var.get().strip().upper()

        if not q_text or correct not in ["A", "B", "C", "D", "E"] or any(v == "" for v in choices.values()):
            messagebox.showerror("Error", "Please fill question, all 5 options and correct option (A/B/C/D/E).")
            return

        item = {"q_no": self.q_no, "text": q_text, "choices": choices, "answer": correct}
        self.questions.append(item)
        self.q_no += 1

        self.clear_fields()
        self.q_entry.focus_set()
        self.refresh_text(self.loaded_questions + self.questions)

    def clear_fields(self):
        self.q_text_var.set("")
        for c in ["A", "B", "C", "D", "E"]:
            self.choice_vars[c].set("")
        self.correct_var.set("")

    def save_questions(self):
        if not self.questions and not os.path.exists("data/questions.json"):
            messagebox.showerror("Error", "No questions to save.")
            return
        existing = []
        if os.path.exists("data/questions.json"):
            with open("data/questions.json", "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except:
                    existing = []
        combined = existing + self.questions
        for idx, q in enumerate(combined, start=1):
            q["q_no"] = idx
        with open("data/questions.json", "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("Saved", f"{len(combined)} questions saved.")
        self.questions = []
        self.q_no = len(combined) + 1
        self.loaded_questions = combined
        self.refresh_text(combined)

    def load_questions(self):
        if not os.path.exists("data/questions.json"):
            messagebox.showinfo("Info", "No saved questions found.")
            return

        with open("data/questions.json", "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
            except:
                messagebox.showerror("Error", "Invalid JSON file.")
                return

        self.loaded_questions = loaded
        self.questions = []
        self.q_no = len(loaded) + 1
        self.refresh_text(loaded)
        messagebox.showinfo("Loaded", f"{len(loaded)} questions loaded.")

    def refresh_text(self, questions):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)

        for q in questions:
            q_text = f"Q{q.get('q_no')}: {q.get('text')}\n"
            choices = "\n".join([f"   {c}. {q['choices'].get(c,'')}" for c in ["A","B","C","D","E"]])
            ans = f"   ✅ Correct Answer: {q.get('answer')}\n"
            self.text_widget.insert(tk.END, q_text + choices + "\n" + ans + "\n" + "-"*70 + "\n")

        self.text_widget.config(state=tk.DISABLED)

    def upload_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if not file_path:
            return
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel file: {e}")
            return

        required_cols = ["Question", "A", "B", "C", "D", "E", "Answer"]
        if not all(col in df.columns for col in required_cols):
            messagebox.showerror("Error", f"Excel must have columns: {', '.join(required_cols)}")
            return

        added_count = 0
        for _, row in df.iterrows():
            q_text = str(row["Question"]).strip()
            choices = {c: str(row[c]).strip() for c in ["A", "B", "C", "D", "E"]}
            correct = str(row["Answer"]).strip().upper()
            if q_text and correct in ["A", "B", "C", "D", "E"] and all(choices.values()):
                item = {"q_no": self.q_no, "text": q_text, "choices": choices, "answer": correct}
                self.questions.append(item)
                self.q_no += 1
                added_count += 1

        self.refresh_text(self.loaded_questions + self.questions)
        messagebox.showinfo("Excel Upload", f"{added_count} questions added.")

    def generate_sheet(self):
        if not os.path.exists("data/questions.json"):
            messagebox.showerror("Error", "No saved questions.")
            return
        generate_omr_sheet()
        messagebox.showinfo("Generated", "OMR sheet saved.")

    def back(self):
        self.root.destroy()
        if self.go_back_callback:
            self.go_back_callback()


    def delete_all_questions(self):
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete ALL questions?")
        if not confirm:
            return

        # Clear JSON file
        if os.path.exists("data/questions.json"):
            try:
                with open("data/questions.json", "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2, ensure_ascii=False)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear file: {e}")
                return

        # Clear memory and UI
        self.questions = []
        self.loaded_questions = []
        self.q_no = 1
        self.refresh_text([])
        messagebox.showinfo("Deleted", "All questions have been deleted.")

