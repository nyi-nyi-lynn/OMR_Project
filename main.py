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

        tk.Label(root, text="Smart OMR System", font=("Arial", 20)).pack(pady=20)

        # Teacher button
        tk.Button(root, text="Create Questions", width=20, command=self.open_teacher_panel).pack(pady=10)

        # Student button
        tk.Button(root, text="OMR Check", width=20, command=self.open_student_panel).pack(pady=10)

    def open_teacher_panel(self):
        self.root.destroy()
        root2 = tk.Tk()
        TeacherPanel(root2, go_back_callback=self.restart_main)
        root2.mainloop()

    def open_student_panel(self):
        self.root.destroy()
        root2 = tk.Tk()
        StudentPanel(root2, go_back_callback=self.restart_main)
        root2.mainloop()

    def restart_main(self):
        root = tk.Tk()
        MainApp(root)
        root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    MainApp(root)
    root.mainloop()
