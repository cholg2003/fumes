import sqlite3
from collections import defaultdict
from openpyxl import Workbook

class ExamResultsSystem:
    def __init__(self):
        self.conn = sqlite3.connect('exam_results.db')
        self.create_table()

    def create_table(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS results
                     (name TEXT PRIMARY KEY, english INTEGER, mathematics INTEGER,
                     science INTEGER, cre INTEGER, sst INTEGER)''')
        self.conn.commit()

    def add_result(self, name, english, math, science, cre, sst):
        c = self.conn.cursor()
        try:
            c.execute("INSERT INTO results VALUES (?, ?, ?, ?, ?, ?)", (name, english, math, science, cre, sst))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print("Result for this student already exists. Use Update Result instead.")

    def generate_report_to_excel(self, filename):
        c = self.conn.cursor()
        c.execute("SELECT * FROM results")
        rows = c.fetchall()

        wb = Workbook()
        ws = wb.active
        ws.append(['Name', 'English', 'Mathematics', 'Science', 'C.R.E', 'S.S.T', 'Total Marks', 'Average Marks'])

        for row in rows:
            total_marks = sum(row[1:])
            average_marks = total_marks / 5
            ws.append([row[0], *row[1:], total_marks, average_marks])

        wb.save(filename)
        print(f"Report generated and saved to {filename}")

if __name__ == "__main__":
    app = ExamResultsSystem()
    # Assuming results have already been added to the database
    # Add results using app.add_result(name, english, math, science, cre, sst)
    app.generate_report_to_excel("exam_results.xlsx")
