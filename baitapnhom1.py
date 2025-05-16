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
        self.extra_column = None  # Theo dõi cột phụ được thêm (sum/mean)
        # Lưu lại các cột đã xóa để có thể hoàn tác: {col_name: {'data': [...], 'index': int}}
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
        edit_menu.add_command(label="Remove")
        edit_menu.add_command(label="Filter")
        edit_menu.add_command(label="Add")
        # Chuyển 2 chức năng Clear và Return vào Edit
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear Result Column", command=self.clear_result_column)
        edit_menu.add_command(label="Return Last Deleted Column", command=self.return_deleted_column)

        calculate_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Calculate", menu=calculate_menu)
        calculate_menu.add_command(label="Sum", command=self.calculate_sum)
        calculate_menu.add_command(label="Mean", command=self.calculate_mean)

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

        self.undo_button = tk.Button(self.root, text="Undo")
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

    def clear_result_column(self):
        col_name = simpledialog.askstring("Clear Column", "Enter column name to clear (leave empty to clear result column):")
        if not col_name:
            col_name = self.extra_column
        if not col_name:
            messagebox.showinfo("Info", "No column specified to clear.")
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
        else:
            messagebox.showwarning("Not Found", f"Column '{col_name}' not found.")

    def return_deleted_column(self):
        if not self.deleted_columns:
            messagebox.showinfo("Info", "No deleted columns to return.")
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
                # Nếu vị trí cột là cuối cùng
                new_row[last_col] = restored_data[i]
            self.current_data[i] = new_row

        self.display_data(self.current_data)
        messagebox.showinfo("Restored", f"Column '{last_col}' has been restored.")

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
        # Hỏi người dùng chọn cột cần sắp xếp
        col_name = simpledialog.askstring("Sort Column", "Enter the column name to sort:")
        if not col_name:
            return
        if not self.current_data or col_name not in self.current_data[0]:
            messagebox.showwarning("Not Found", f"Column '{col_name}' not found.")
            return
        try:
            # Sort theo kiểu số nếu có thể, nếu lỗi thì sort kiểu chuỗi
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
