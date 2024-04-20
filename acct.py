import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
import pandas as pd

class SchoolAccountingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("School Accounting System")

        # Connect to the database
        self.conn = sqlite3.connect('school_accounting.db')
        self.create_tables()

        # Create tabs for different sections
        self.tab_control = ttk.Notebook(root)
        self.record_payments_tab = ttk.Frame(self.tab_control)
        self.search_students_tab = ttk.Frame(self.tab_control)
        self.generate_reports_tab = ttk.Frame(self.tab_control)

        # Add tabs to the tab control
        self.tab_control.add(self.record_payments_tab, text='Record Payments')
        self.tab_control.add(self.search_students_tab, text='Search Students')
        self.tab_control.add(self.generate_reports_tab, text='Generate Reports')

        self.tab_control.pack(expand=1, fill="both")

        # Initialize UI elements for record payments tab
        self.init_record_payments_tab()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                class TEXT NOT NULL,
                fees_paid INTEGER DEFAULT 0,
                total_fees INTEGER NOT NULL
            )
        ''')
        self.conn.commit()

    def init_record_payments_tab(self):
        self.record_payments_frame = ttk.LabelFrame(self.record_payments_tab, text="Record Payment")
        self.record_payments_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Initialize UI elements
        self.name_label = ttk.Label(self.record_payments_frame, text="Student Name:")
        self.name_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ttk.Entry(self.record_payments_frame)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        self.class_label = ttk.Label(self.record_payments_frame, text="Class:")
        self.class_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.class_entry = ttk.Entry(self.record_payments_frame)
        self.class_entry.grid(row=1, column=1, padx=5, pady=5)

        self.amount_label = ttk.Label(self.record_payments_frame, text="Amount Paid:")
        self.amount_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.amount_entry = ttk.Entry(self.record_payments_frame)
        self.amount_entry.grid(row=2, column=1, padx=5, pady=5)

        self.record_button = ttk.Button(self.record_payments_frame, text="Record Payment", command=self.record_payment)
        self.record_button.grid(row=3, columnspan=2, padx=5, pady=5)

    def record_payment(self):
        name = self.name_entry.get().strip()
        class_ = self.class_entry.get().strip()
        amount = int(self.amount_entry.get().strip())

        cursor = self.conn.cursor()
        cursor.execute("SELECT total_fees, fees_paid FROM students WHERE name=? AND class=?", (name, class_))
        result = cursor.fetchone()
        if result:
            total_fees, fees_paid = result
            fees_paid += amount
            cursor.execute("UPDATE students SET fees_paid=? WHERE name=? AND class=?", (fees_paid, name, class_))
            self.conn.commit()
            messagebox.showinfo("Success", "Payment recorded successfully.")
        else:
            messagebox.showerror("Error", "Student not found.")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = SchoolAccountingApp(root)
    app.run()
