import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import csv
import json

class DataViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Teamwork group1")
        self.root.geometry("1200x900")

        self.original_data = []  # For undo
        self.current_data = []   # What is currently displayed

        self.create_widgets()

    def create_widgets(self):
        # Button Frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        # Buttons
        ttk.Button(button_frame, text="Load CSV or JSON", command=self.load_file).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Filter", command=self.filter_data).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Calculate", command=self.calculus).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Undo", command=self.undo_changes).pack(side='left', padx=5)

        # Treeview Widget
        self.tree = ttk.Treeview(self.root, show="headings")
        self.tree.pack(expand=True, fill='both')

        # Scrollbars
        vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')

        # ✅ Add Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w')
        self.status_bar.pack(side='bottom', fill='x')
    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV or JSON file",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            def read_file_with_encoding(path, encoding):
                with open(path, newline='', encoding=encoding) as f:
                    if path.endswith('.csv'):
                        return list(csv.DictReader(f))
                    elif path.endswith('.json'):
                        data = json.load(f)
                        return [data] if isinstance(data, dict) else data

            try:
                data = read_file_with_encoding(file_path, 'utf-8')
            except UnicodeDecodeError:
                data = read_file_with_encoding(file_path, 'iso-8859-1')

            if data:
                self.original_data = data.copy()
                self.current_data = data.copy()
                self.display_data(data)
            else:
                messagebox.showinfo("No Data", "File loaded but contains no data.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def display_data(self, data):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []

        if not data:
            return

        columns = list(data[0].keys())
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='w')

        for row in data:
            values = [row.get(col, "") for col in columns]
            self.tree.insert("", "end", values=values)

    def filter_data(self):
        if not self.current_data:
            return
        keyword = simpledialog.askstring("Filter", "Enter keyword to filter rows:")
        if not keyword:
            return
        filtered = [row for row in self.current_data if any(keyword.lower() in str(value).lower() for value in row.values())]
        self.display_data(filtered)
        self.current_data = filtered

    def calculus(self):
        if not self.current_data:
            return

        numeric_cols = {}
        for row in self.current_data:
            for key, value in row.items():
                try:
                    num = float(value)
                    numeric_cols.setdefault(key, []).append(num)
                except (ValueError, TypeError):
                    continue

        if not numeric_cols:
            messagebox.showinfo("Calculus", "No numeric data to calculate.")
            return

        results = []
        for col, nums in numeric_cols.items():
            total = sum(nums)
            avg = total / len(nums) if nums else 0
            results.append(f"{col}: Sum = {total:.2f}, Avg = {avg:.2f}")

        messagebox.showinfo("Calculus Results", "\n".join(results))

    def undo_changes(self):
        self.current_data = self.original_data.copy()
        self.display_data(self.original_data)

if __name__ == "__main__":
    root = tk.Tk()
    app = DataViewerApp(root)
    root.mainloop()
