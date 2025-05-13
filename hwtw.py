import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import csv
import json

class DataViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Teamwork group1")
        self.root.geometry("1300x800")

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

        # Get column names
        columns = list(self.current_data[0].keys())

        # Create filter dialog window
        filter_win = tk.Toplevel(self.root)
        filter_win.title("Filter Data")

        tk.Label(filter_win, text="Select column to filter:").pack(pady=(10, 2))
        selected_column = tk.StringVar()
        col_combo = ttk.Combobox(filter_win, textvariable=selected_column, values=columns, state='readonly')
        col_combo.pack(padx=10, pady=5)

        tk.Label(filter_win, text="Select filter type:").pack(pady=(10, 2))
        filter_type = tk.StringVar()
        #filter_type.set("Text Match")
        #ttk.Radiobutton(filter_win, text="Text Match", variable=filter_type, value="text").pack(anchor='w', padx=20)
        ttk.Radiobutton(filter_win, text="Minimum Value", variable=filter_type, value="min").pack(anchor='w', padx=20)
        ttk.Radiobutton(filter_win, text="Maximum Value", variable=filter_type, value="max").pack(anchor='w', padx=20)

        #tk.Label(filter_win, text="Enter filter value (if applicable):").pack(pady=(10, 2))
        value_entry = ttk.Entry(filter_win)
        value_entry.pack(padx=10, pady=5)

        def apply_filter():
            col = selected_column.get()
            f_type = filter_type.get()
            val = value_entry.get()

            if not col:
                messagebox.showwarning("Missing Input", "Please select a column.")
                return

            try:
                if f_type == "text":
                    filtered = [row for row in self.current_data if val.lower() in str(row.get(col, "")).lower()]
                elif f_type == "min":
                    filtered = [row for row in self.current_data if float(row.get(col, float('inf'))) == min(
                        float(r.get(col)) for r in self.current_data if self._is_float(r.get(col)))]
                elif f_type == "max":
                    filtered = [row for row in self.current_data if float(row.get(col, float('-inf'))) == max(
                        float(r.get(col)) for r in self.current_data if self._is_float(r.get(col)))]
                else:
                    filtered = []

                self.display_data(filtered)
                self.current_data = filtered
                filter_win.destroy()

            except Exception as e:
                messagebox.showerror("Filter Error", f"Failed to filter data:\n{e}")

        ttk.Button(filter_win, text="Apply Filter", command=apply_filter).pack(pady=10)

    def _is_float(self, value):
        try:
            float(value)
            return True
        except:
            return False

    def calculus(self):
        if not self.current_data:
            return

        # Identify numeric columns
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

        # Dialog to choose columns
        column_selection = tk.Toplevel(self.root)
        column_selection.title("Select Columns for Calculation")

        tk.Label(column_selection, text="Select one or more numeric columns:").pack(padx=10, pady=5)

        vars = {}
        for col in numeric_cols:
            var = tk.BooleanVar(value=True)  # default all selected
            chk = tk.Checkbutton(column_selection, text=col, variable=var)
            chk.pack(anchor='w', padx=20)
            vars[col] = var

        def on_calculate():
            selected = [col for col, var in vars.items() if var.get()]
            if not selected:
                messagebox.showwarning("No Selection", "Please select at least one column.")
                return

            results = []
            for col in selected:
                nums = numeric_cols[col]
                total = sum(nums)
                avg = total / len(nums) if nums else 0
                # ➕ Add more calculations as needed here
                results.append(f"{col}:\n  Sum = {total:.2f}\n  Avg = {avg:.2f}")

            messagebox.showinfo("Calculation Results", "\n\n".join(results))
            column_selection.destroy()

        ttk.Button(column_selection, text="Calculate", command=on_calculate).pack(pady=10)

    def undo_changes(self):
        self.current_data = self.original_data.copy()
        self.display_data(self.original_data)

if __name__ == "__main__":
    root = tk.Tk()
    app = DataViewerApp(root)
    root.mainloop()
