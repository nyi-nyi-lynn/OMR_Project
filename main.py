# main.py
import tkinter as tk
from tkinter import messagebox
from teacher.panel import TeacherPanel
from student.panel import StudentPanel
import os

# Ensure required directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("results", exist_ok=True)
os.makedirs("assets", exist_ok=True)

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart OMR System")
        self.root.geometry("420x240")

        tk.Label(root, text="Smart OMR System", font=("Arial", 20)).pack(pady=12)
        tk.Label(root, text="Enter Role (teacher / student):").pack()
        self.role_var = tk.StringVar()
        tk.Entry(root, textvariable=self.role_var).pack(pady=6)
        tk.Button(root, text="Login", width=20, command=self.login).pack(pady=10)

    def login(self):
        role = self.role_var.get().strip().lower()
        if role == "teacher":
            self.root.destroy()
            root2 = tk.Tk()
            TeacherPanel(root2)
            root2.mainloop()
        elif role == "student":
            self.root.destroy()
            root2 = tk.Tk()
            StudentPanel(root2)
            root2.mainloop()
        else:
            messagebox.showerror("Error", "Invalid role! Enter 'teacher' or 'student'.")

if __name__ == "__main__":
    root = tk.Tk()
    MainApp(root)
    root.mainloop()
