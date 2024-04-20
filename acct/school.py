import tkinter as tk
import sqlite3
import pandas as pd

def initialize_database():
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Students (
                        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        class TEXT,
                        total_fees REAL,
                        fees_paid REAL
                    )''')
    conn.commit()
    conn.close()

initialize_database()

def add_student():
    name = name_entry.get()
    class_ = class_entry.get()
    total_fees = total_fees_entry.get()
    fees_paid = fees_paid_entry.get()
    
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Students (name, class, total_fees, fees_paid) VALUES (?, ?, ?, ?)",
                   (name, class_, total_fees, fees_paid))
    conn.commit()
    conn.close()
    
    clear_entries()

def search_student():
    query = search_entry.get()
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Students WHERE name LIKE ? OR class LIKE ?", ('%' + query + '%', '%' + query + '%'))
    results = cursor.fetchall()
    conn.close()
    
    display_search_results(results)

def display_search_results(results):
    for widget in search_result_frame.winfo_children():
        widget.destroy()

    for i, result in enumerate(results):
        for j, value in enumerate(result):
            label = tk.Label(search_result_frame, text=value)
            label.grid(row=i, column=j)

def edit_student():
    try:
        selected_id = int(edit_id_entry.get())
    except ValueError:
        # Handle the case where the ID is not a valid integer
        # For example, display an error message to the user
        return

    new_name = edit_name_entry.get()
    new_class = edit_class_entry.get()
    new_total_fees = edit_total_fees_entry.get()
    new_fees_paid = edit_fees_paid_entry.get()
    
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE Students SET name=?, class=?, total_fees=?, fees_paid=? WHERE student_id=?",
                   (new_name, new_class, new_total_fees, new_fees_paid, selected_id))
    conn.commit()
    conn.close()

    clear_edit_entries()
    search_student() 

def clear_entries():
    name_entry.delete(0, tk.END)
    class_entry.delete(0, tk.END)
    total_fees_entry.delete(0, tk.END)
    fees_paid_entry.delete(0, tk.END)

def clear_edit_entries():
    edit_id_entry.delete(0, tk.END)
    edit_name_entry.delete(0, tk.END)
    edit_class_entry.delete(0, tk.END)
    edit_total_fees_entry.delete(0, tk.END)
    edit_fees_paid_entry.delete(0, tk.END)

def generate_class_report():
    class_name = class_report_entry.get()
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Students WHERE class=?", (class_name,))
    results = cursor.fetchall()
    conn.close()
    
    # Display the report in a separate window or save to a file

def generate_fee_payment_report():
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Students")
    results = cursor.fetchall()
    conn.close()
    
    # Process and display fee payment report

def export_to_excel():
    conn = sqlite3.connect('school.db')
    df = pd.read_sql_query("SELECT * FROM Students", conn)
    conn.close()
    
    df.to_excel("students_report.xlsx", index=False)

root = tk.Tk()
root.title("School Management System")

# Add widgets for adding students
name_label = tk.Label(root, text="Name:")
name_label.grid(row=0, column=0)
name_entry = tk.Entry(root)
name_entry.grid(row=0, column=1)

class_label = tk.Label(root, text="Class:")
class_label.grid(row=1, column=0)
class_entry = tk.Entry(root)
class_entry.grid(row=1, column=1)

total_fees_label = tk.Label(root, text="Total Fees:")
total_fees_label.grid(row=2, column=0)
total_fees_entry = tk.Entry(root)
total_fees_entry.grid(row=2, column=1)

fees_paid_label = tk.Label(root, text="Fees Paid:")
fees_paid_label.grid(row=3, column=0)
fees_paid_entry = tk.Entry(root)
fees_paid_entry.grid(row=3, column=1)

add_button = tk.Button(root, text="Add Student", command=add_student)
add_button.grid(row=4, columnspan=2)

# Add widgets for searching
search_entry = tk.Entry(root)
search_entry.grid(row=5, column=0)
search_button = tk.Button(root, text="Search", command=search_student)
search_button.grid(row=5, column=1)

search_result_frame = tk.Frame(root)
search_result_frame.grid(row=6, columnspan=2)

# Add widgets for editing
edit_id_entry = tk.Entry(root)
edit_id_entry.grid(row=7, column=0)
edit_name_entry = tk.Entry(root)
edit_name_entry.grid(row=7, column=1)
edit_class_entry = tk.Entry(root)
edit_class_entry.grid(row=8, column=0)
edit_total_fees_entry = tk.Entry(root)
edit_total_fees_entry.grid(row=8, column=1)
edit_fees_paid_entry = tk.Entry(root)
edit_fees_paid_entry.grid(row=9, column=0)
edit_button = tk.Button(root, text="Edit", command=edit_student)
edit_button.grid(row=9, column=1)

# Add widgets for generating reports
class_report_entry = tk.Entry(root)
class_report_entry.grid(row=10, column=0)
class_report_button = tk.Button(root, text="Generate Class Report", command=generate_class_report)
class_report_button.grid(row=10, column=1)

fee_payment_report_button = tk.Button(root, text="Generate Fee Payment Report", command=generate_fee_payment_report)
fee_payment_report_button.grid(row=11, columnspan=2)

export_button = tk.Button(root, text="Export to Excel", command=export_to_excel)
export_button.grid(row=12, columnspan=2)

root.mainloop()
