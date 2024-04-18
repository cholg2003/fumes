import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
from collections import defaultdict
from openpyxl import Workbook

class ExamResultsSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Primary Pupil Exam Results System")

        self.conn = sqlite3.connect('exam_results.db')
        self.create_table()

        self.create_widgets()

    def create_table(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS results
                     (name TEXT PRIMARY KEY, english INTEGER, mathematics INTEGER,
                     science INTEGER, cre INTEGER, sst INTEGER)''')
        self.conn.commit()

    def create_widgets(self):
        # Input Section
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Name:").grid(row=0, column=0)
        self.name_entry = tk.Entry(input_frame)
        self.name_entry.grid(row=0, column=1)

        tk.Label(input_frame, text="English:").grid(row=1, column=0)
        self.english_entry = tk.Entry(input_frame)
        self.english_entry.grid(row=1, column=1)

        tk.Label(input_frame, text="Mathematics:").grid(row=2, column=0)
        self.math_entry = tk.Entry(input_frame)
        self.math_entry.grid(row=2, column=1)

        tk.Label(input_frame, text="Science:").grid(row=3, column=0)
        self.science_entry = tk.Entry(input_frame)
        self.science_entry.grid(row=3, column=1)

        tk.Label(input_frame, text="C.R.E:").grid(row=4, column=0)
        self.cre_entry = tk.Entry(input_frame)
        self.cre_entry.grid(row=4, column=1)

        tk.Label(input_frame, text="S.S.T:").grid(row=5, column=0)
        self.sst_entry = tk.Entry(input_frame)
        self.sst_entry.grid(row=5, column=1)

        add_btn = tk.Button(input_frame, text="Add Result", command=self.add_result)
        add_btn.grid(row=6, columnspan=2, pady=5)

        # Report Section
        report_frame = tk.Frame(self.root)
        report_frame.pack()

        self.report_text = tk.Text(report_frame, width=60, height=10)
        self.report_text.pack()

        generate_report_btn = tk.Button(report_frame, text="Generate Report", command=self.generate_report)
        generate_report_btn.pack(pady=5)

        save_excel_btn = tk.Button(report_frame, text="Save as Excel", command=self.save_excel)
        save_excel_btn.pack(pady=5)

    def add_result(self):
        name = self.name_entry.get()
        english = self.validate_marks(self.english_entry.get())
        math = self.validate_marks(self.math_entry.get())
        science = self.validate_marks(self.science_entry.get())
        cre = self.validate_marks(self.cre_entry.get())
        sst = self.validate_marks(self.sst_entry.get())

        if not name or english is None or math is None or science is None or cre is None or sst is None:
            messagebox.showerror("Error", "Please enter valid data for all fields.")
            return

        c = self.conn.cursor()
        try:
            c.execute("INSERT INTO results VALUES (?, ?, ?, ?, ?, ?)", (name, english, math, science, cre, sst))
            self.conn.commit()
            messagebox.showinfo("Success", "Result added successfully!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Result for this student already exists. Use Update Result instead.")

    def validate_marks(self, marks):
        try:
            marks = int(marks)
            if 0 <= marks <= 100:
                return marks
            else:
                return None
        except ValueError:
            return None

    def generate_report(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM results")
        rows = c.fetchall()

        report_dict = defaultdict(list)
        for row in rows:
            total_marks = row[1] + row[2] + row[3] + row[4] + row[5]
            average_marks = total_marks / 5
            report_dict[row[0]].extend([total_marks, average_marks])

        sorted_report = sorted(report_dict.items(), key=lambda x: x[1][1], reverse=True)

        self.report_text.delete(1.0, tk.END)
        position = 1
        for idx, (name, [total_marks, average_marks]) in enumerate(sorted_report):
            self.report_text.insert(tk.END, f"Position {position}: {name}\nTotal Marks: {total_marks}\nAverage Marks: {average_marks:.2f}\n\n")
            if idx < len(sorted_report) - 1 and average_marks != sorted_report[idx + 1][1][1]:
                position = idx + 2

    def save_excel(self):
        wb = Workbook()
        ws = wb.active
        ws.append(["Name", "Total Marks", "Average Marks"])

        c = self.conn.cursor()
        c.execute("SELECT * FROM results")
        rows = c.fetchall()

        for row in rows:
            total_marks = sum(row[1:])
            average_marks = total_marks / 5
            ws.append([row[0], total_marks, average_marks])

        wb.save("exam_results.xlsx")
        messagebox.showinfo("Success", "Excel file saved successfully!")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ExamResultsSystem()
    app.run()
