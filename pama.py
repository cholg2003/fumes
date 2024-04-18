import tkinter as tk
from tkinter import simpledialog, messagebox
import sqlite3
import datetime

class PharmacyManagementSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pharmacy Management System")

        self.conn = sqlite3.connect('pharmacy.db')
        self.create_table()

        self.create_widgets()

    def create_table(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS items
                     (name TEXT PRIMARY KEY, quantity INTEGER, price REAL, sold INTEGER)''')
        self.conn.commit()

    def create_widgets(self):
        # Search Section
        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Search Item:").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=10)
        search_btn = tk.Button(search_frame, text="Search", command=self.search_item)
        search_btn.pack(side=tk.LEFT)

        # Item List Section
        self.item_listbox = tk.Listbox(self.root, width=50)
        self.item_listbox.pack(pady=10)

        # Buttons Section
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack()

        add_btn = tk.Button(buttons_frame, text="Add Item", command=self.add_item)
        add_btn.grid(row=0, column=0, padx=5)

        update_btn = tk.Button(buttons_frame, text="Update Item", command=self.update_item)
        update_btn.grid(row=0, column=1, padx=5)

        delete_btn = tk.Button(buttons_frame, text="Delete Item", command=self.delete_item)
        delete_btn.grid(row=0, column=2, padx=5)

        sell_btn = tk.Button(buttons_frame, text="Sell Item", command=self.sell_item)
        sell_btn.grid(row=0, column=3, padx=5)

        # Daily Report Section
        report_frame = tk.Frame(self.root)
        report_frame.pack()

        self.report_text = tk.Text(report_frame, width=60, height=10)
        self.report_text.pack()

    def search_item(self):
        search_query = self.search_entry.get().lower()
        self.item_listbox.delete(0, tk.END)
        c = self.conn.cursor()
        c.execute("SELECT * FROM items WHERE name LIKE ?", ('%'+search_query+'%',))
        rows = c.fetchall()
        for row in rows:
            self.item_listbox.insert(tk.END, f"{row[0]} - Quantity: {row[1]} - Price: {row[2]}")

    def add_item(self):
        item_name = simpledialog.askstring("Add Item", "Enter item name:")
        if item_name:
            c = self.conn.cursor()
            c.execute("SELECT * FROM items WHERE name=?", (item_name,))
            if c.fetchone():
                messagebox.showerror("Error", "Item already exists!")
            else:
                quantity = simpledialog.askinteger("Add Item", "Enter quantity:")
                price = simpledialog.askfloat("Add Item", "Enter price per quantity:")
                c.execute("INSERT INTO items VALUES (?, ?, ?, 0)", (item_name, quantity, price))
                self.conn.commit()
                self.update_listbox()

    def update_item(self):
        selected_item = self.item_listbox.curselection()
        if selected_item:
            selected_item = self.item_listbox.get(selected_item[0])
            item_name = selected_item.split(" - ")[0]
            new_quantity = simpledialog.askinteger("Update Item", "Enter new quantity:")
            if new_quantity is not None:
                c = self.conn.cursor()
                c.execute("UPDATE items SET quantity=? WHERE name=?", (new_quantity, item_name))
                self.conn.commit()
                self.update_listbox()

    def delete_item(self):
        selected_item = self.item_listbox.curselection()
        if selected_item:
            selected_item = self.item_listbox.get(selected_item[0])
            item_name = selected_item.split(" - ")[0]
            c = self.conn.cursor()
            c.execute("DELETE FROM items WHERE name=?", (item_name,))
            self.conn.commit()
            self.update_listbox()

    def sell_item(self):
        selected_item = self.item_listbox.curselection()
        if selected_item:
            selected_item = self.item_listbox.get(selected_item[0])
            item_name = selected_item.split(" - ")[0]
            quantity_sold = simpledialog.askinteger("Sell Item", "Enter quantity sold:")
            if quantity_sold is not None:
                c = self.conn.cursor()
                c.execute("SELECT quantity FROM items WHERE name=?", (item_name,))
                current_quantity = c.fetchone()[0]
                if quantity_sold <= current_quantity:
                    c.execute("UPDATE items SET quantity=?, sold=sold+? WHERE name=?",
                              (current_quantity - quantity_sold, quantity_sold, item_name))
                    self.conn.commit()
                    self.update_listbox()
                    self.generate_daily_report(item_name, quantity_sold)
                else:
                    messagebox.showerror("Error", "Insufficient quantity available!")

    def generate_daily_report(self, item_name, quantity_sold):
        report_date = datetime.date.today()
        report_text = f"{report_date} - Sold {quantity_sold} units of {item_name}\n"
        self.report_text.insert(tk.END, report_text)

    def update_listbox(self):
        self.search_entry.delete(0, tk.END)
        self.search_item()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PharmacyManagementSystem()
    app.run()
