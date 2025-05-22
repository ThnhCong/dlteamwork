import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import csv
import json

class DataViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Teamwork group1")
        self.root.geometry("1300x800")

        self.original_data = []
        self.current_data = []
        self.extra_column = None
        self.deleted_columns = {}

        self.create_widgets()

    def create_widgets(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.load_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.close_app)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Remove", command=self.clear_result_column)  # Gắn chức năng Clear sang Remove
        edit_menu.add_command(label="Filter", command=self.filter_data)
        edit_menu.add_command(label="Add")
        edit_menu.add_separator()
        edit_menu.add_command(label="Undo", command=self.undo_last_action)  # Đổi tên và gán hàm undo

        calculate_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Calculate", menu=calculate_menu)
        calculate_menu.add_command(label="Sum", command=self.calculate_sum)
        calculate_menu.add_command(label="Mean", command=self.calculate_mean)
        calculate_menu.add_command(label="Min", command=self.calculate_min)
        calculate_menu.add_command(label="Max", command=self.calculate_max)

        sort_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sort", menu=sort_menu)
        sort_menu.add_command(label="Sort A -> Z", command=lambda: self.sort_column(ascending=True))
        sort_menu.add_command(label="Sort Z -> A", command=lambda: self.sort_column(ascending=False))

        self.tree = ttk.Treeview(self.root, show="headings")
        self.tree.pack(expand=True, fill='both')

        self.status_var = tk.StringVar()
        self.status_var.set("Baby IT")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w')
        self.status_bar.pack(side='bottom', fill='x')

        self.undo_button = tk.Button(self.root, text="Undo", command=self.undo_last_action)
        self.undo_button.pack(side="right", padx=5, pady=5)

    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV or JSON file",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")])
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

    def calculate_sum(self):
        col_name = simpledialog.askstring("Select Column", "Enter the column name to calculate sum:")
        if not col_name:
            return
        try:
            total = sum(float(row.get(col_name, 0)) for row in self.current_data if row.get(col_name))
            self.extra_column = f"{col_name}_sum"
            for idx, row in enumerate(self.current_data):
                row[self.extra_column] = total if idx == 0 else ""
            self.display_data(self.current_data)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate sum: {e}")

    def calculate_mean(self):
        col_name = simpledialog.askstring("Select Column", "Enter the column name to calculate mean:")
        if not col_name:
            return
        try:
            values = [float(row[col_name]) for row in self.current_data if row.get(col_name)]
            if not values:
                raise ValueError("No valid numeric values found.")
            mean_value = sum(values) / len(values)
            self.extra_column = f"{col_name}_mean"
            for idx, row in enumerate(self.current_data):
                row[self.extra_column] = mean_value if idx == 0 else ""
            self.display_data(self.current_data)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate mean: {e}")

    def calculate_min(self):
        col_name = simpledialog.askstring("Select Column", "Enter the column name to calculate min:")
        if not col_name:
            return
        try:
            values = [float(row[col_name]) for row in self.current_data if row.get(col_name)]
            if not values:
                raise ValueError("No valid numeric values found.")
            min_value = min(values)
            self.extra_column = f"{col_name}_min"
            for idx, row in enumerate(self.current_data):
                row[self.extra_column] = min_value if idx == 0 else ""
            self.display_data(self.current_data)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate min: {e}")

    def calculate_max(self):
        col_name = simpledialog.askstring("Select Column", "Enter the column name to calculate max:")
        if not col_name:
            return
        try:
            values = [float(row[col_name]) for row in self.current_data if row.get(col_name)]
            if not values:
                raise ValueError("No valid numeric values found.")
            max_value = max(values)
            self.extra_column = f"{col_name}_max"
            for idx, row in enumerate(self.current_data):
                row[self.extra_column] = max_value if idx == 0 else ""
            self.display_data(self.current_data)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate max: {e}")

    def clear_result_column(self):
        col_name = simpledialog.askstring("Clear Column", "Enter column name to remove (leave empty to remove result column):")
        if not col_name:
            col_name = self.extra_column
        if not col_name:
            messagebox.showinfo("Info", "No column specified to remove.")
            return

        if not self.current_data or col_name not in self.current_data[0]:
            messagebox.showwarning("Not Found", f"Column '{col_name}' not found.")
            return

        columns = list(self.current_data[0].keys())
        col_index = columns.index(col_name)

        removed = False
        deleted_data = []
        for row in self.current_data:
            if col_name in row:
                deleted_data.append(row[col_name])
                del row[col_name]
                removed = True
            else:
                deleted_data.append(None)

        if removed:
            self.deleted_columns[col_name] = {'data': deleted_data, 'index': col_index}
            if col_name == self.extra_column:
                self.extra_column = None
            self.display_data(self.current_data)
            messagebox.showinfo("Removed", f"Column '{col_name}' has been removed.")
        else:
            messagebox.showwarning("Not Found", f"Column '{col_name}' not found.")

    def undo_last_action(self):
        if not self.deleted_columns:
            messagebox.showinfo("Info", "No deleted columns to undo.")
            return

        last_col = list(self.deleted_columns.keys())[-1]
        col_info = self.deleted_columns.pop(last_col)
        restored_data = col_info['data']
        col_index = col_info['index']

        for i, row in enumerate(self.current_data):
            new_row = {}
            keys = list(row.keys())
            inserted = False
            for idx, key in enumerate(keys):
                if idx == col_index:
                    new_row[last_col] = restored_data[i]
                    inserted = True
                new_row[key] = row[key]
            if not inserted:
                new_row[last_col] = restored_data[i]
            self.current_data[i] = new_row

        self.display_data(self.current_data)
        messagebox.showinfo("Undo", f"Undo successful: column '{last_col}' restored.")

    def filter_data(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to filter.")
            return
        col_name = simpledialog.askstring("Filter Column", "Enter the column name to filter:")
        if not col_name:
            return
        if col_name not in self.current_data[0]:
            messagebox.showwarning("Not Found", f"Column '{col_name}' not found.")
            return
        filter_value = simpledialog.askstring("Filter Value", f"Enter value to filter rows where '{col_name}' equals:")
        if filter_value is None:
            return

        filtered_data = [row for row in self.current_data if str(row.get(col_name, "")) == filter_value]
        if not filtered_data:
            messagebox.showinfo("No Match", f"No rows found where '{col_name}' equals '{filter_value}'.")
            return
        self.display_data(filtered_data)
        self.status_var.set(f"Filtered rows where {col_name} == {filter_value}")

    def save_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Save File",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            if file_path.endswith('.csv'):
                with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.current_data[0].keys())
                    writer.writeheader()
                    writer.writerows(self.current_data)
            elif file_path.endswith('.json'):
                with open(file_path, mode='w', encoding='utf-8') as f:
                    json.dump(self.current_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Success", f"File saved successfully: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def close_app(self):
        if messagebox.askyesno("Exit", "Do you want to exit?"):
            self.root.quit()

    def sort_column(self, ascending=True):
        col_name = simpledialog.askstring("Sort Column", "Enter the column name to sort:")
        if not col_name:
            return
        if not self.current_data or col_name not in self.current_data[0]:
            messagebox.showwarning("Not Found", f"Column '{col_name}' not found.")
            return
        try:
            try:
                self.current_data.sort(key=lambda x: float(x.get(col_name, float('inf'))), reverse=not ascending)
            except ValueError:
                self.current_data.sort(key=lambda x: x.get(col_name, ""), reverse=not ascending)
            self.display_data(self.current_data)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot sort by column '{col_name}': {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DataViewerApp(root)
    root.mainloop()
