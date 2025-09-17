# student/panel.py
import csv
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk, messagebox
import json, os
from omr.processor import realtime_scan, scan_image
from omr.utlis import check_answers, export_result
import pandas as pd

os.makedirs("data", exist_ok=True)

class StudentPanel:
    def __init__(self, root,go_back_callback=None):
        self.root = root
        self.go_back_callback = go_back_callback
        self.root.title("OMR Check Panel")
        self.root.geometry("720x480")

        tk.Label(root, text="OMR Check Panel", font=("Arial", 16)).pack(pady=8)

        form = tk.Frame(root)
        form.pack(pady=6)
        tk.Label(form, text="Student  Name:").grid(row=0, column=0, sticky="e")
        self.student_id_var = tk.StringVar()
        tk.Entry(form, textvariable=self.student_id_var, width=30).grid(row=0, column=1, padx=8)

        tk.Button(root, text="Show  Questions", width=28, command=self.show_printed_questions).pack(pady=8)
        tk.Button(root, text="Scan ", width=28, command=self.start_camera_scan).pack(pady=6)
        # tk.Button(root, text="Scan Image File", width=28, command=self.scan_image_file).pack(pady=6)\
        tk.Button(root, text="Show Records", width=28, command=self.open_excel).pack(pady=6)
        tk.Button(root, text="Back To Main Panel", width=28, command=self.back).pack(pady=6)

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

        # Create a new window
        win = tk.Toplevel(self.root)
        win.title("Printed Questions")
        win.geometry("700x400")

        # Create a scrollable Text widget
        text_widget = tk.Text(win, wrap="word")
        text_widget.pack(fill="both", expand=True, side="left")

        scrollbar = tk.Scrollbar(win, command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)

        # Build the text
        txt = ""
        for q in printed_questions:
            choices = q.get("choices", {})
            txt += f"Q{q['q_no']}: {q['text']}\n"
            txt += f"  A: {choices.get('A', '')}\n"
            txt += f"  B: {choices.get('B', '')}\n"
            txt += f"  C: {choices.get('C', '')}\n"
            txt += f"  D: {choices.get('D', '')}\n"
            txt += f"  E: {choices.get('E', '')}\n\n"

        text_widget.insert("1.0", txt)
        text_widget.config(state="disabled")  # make it read-only

    def start_camera_scan(self):
        student_id = self.student_id_var.get().strip() or "Unknown"
        printed_questions, printed_map = self._load_questions_and_layout()
        if printed_questions is None:
            return

        # Build answer_key mapping original_q_no -> correct answer from questions.json
        # Letter → Number mapping
        letter_to_index = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
        answer_key = {}

        for q in printed_questions:
            mapped_value = letter_to_index.get(q["answer"], -1)
            answer_key[q["q_no"]] = mapped_value
            print("answer keys " , answer_key)
        try:
            answers, score = realtime_scan(student_id, answer_key)
        except Exception as e:
            messagebox.showerror("Camera Error", str(e))
            return
        total = len(answer_key)
        if score != -1 :
            export_result(student_id, answers, score, total)
        else :
            score = 0


        # Number → Letter mapping for display
        index_to_letter = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E"}

        # prepare result text
        s = f"Student Name: {student_id}\nScore: {score}/{total}\n\n"
        for q_no, correct_idx in answer_key.items():
            detected = answers.get(q_no, "-")
            correct_letter = index_to_letter.get(correct_idx, "-")  # convert number back to letter
            s += f"Q{q_no}: detected={detected} correct={correct_letter}\n"

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
        s = f"Student Name: {student_id}\nScore: {score}/{total}\n\n"
        for q_no, det in details.items():
            s += f"Q{q_no}: detected={det['student']} correct={det['correct']}\n"
        self.result_label.config(text=s)

    def back(self):
        self.root.destroy()
        if self.go_back_callback:
            self.go_back_callback()

    def open_excel(self, file_path="results/results.csv"):
        # Check if file exists
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found: {file_path}")
            return None

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading CSV file: {e}")
            return None

        # Create a new window
        win = tk.Toplevel(self.root)
        win.title("Student's Answers Records")
        win.geometry("800x500")

        # Treeview widget
        tree = tk.ttk.Treeview(win, columns=list(df.columns), show="headings")
        tree.pack(fill="both", expand=True)

        # Define headings
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        # Function to load/reload data
        def load_data():
            try:
                df_new = pd.read_csv(file_path)

                # Clear old rows
                for item in tree.get_children():
                    tree.delete(item)

                # Insert updated rows
                for _, row in df_new.iterrows():
                    tree.insert("", "end", values=list(row))
            except Exception as e:
                messagebox.showerror("Error", f"Error refreshing data: {e}")

        # Initial load
        load_data()

        # Clear records function
        def clear_records():
            if messagebox.askyesno("Confirm", "Are you sure you want to clear all records?"):
                try:
                    header = list(df.columns)
                    with open(file_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(header)

                    load_data()
                    messagebox.showinfo("Cleared", "All records cleared (header preserved).")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to clear records: {e}")

        # Delete selected row(s) function
        def delete_selected():
            selected_items = tree.selection()
            if not selected_items:
                messagebox.showwarning("Warning", "No row selected.")
                return

            if not messagebox.askyesno("Confirm", "Delete selected record(s)?"):
                return

            try:
                # Remove from tree
                for item in selected_items:
                    tree.delete(item)

                # Save back to CSV (keep header + remaining rows)
                rows = [tree.item(child)["values"] for child in tree.get_children()]
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(df.columns)  # header
                    writer.writerows(rows)

                messagebox.showinfo("Deleted", "Selected record(s) deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete record(s): {e}")

        # Buttons
        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Refresh", command=load_data).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Clear All Records", command=clear_records).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=delete_selected).pack(side="left", padx=5)

