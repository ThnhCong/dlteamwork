import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import json

class DataViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Teamwork group1")
        self.root.geometry("1300x800")

        self.original_data = []  # Dữ liệu gốc để hoàn tác
        self.current_data = []   # Dữ liệu hiện tại đang hiển thị

        self.create_widgets()

    def create_widgets(self):
        # Tạo thanh menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Tạo menu 'File'
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)

        # Thêm các mục vào menu 'File'
        file_menu.add_command(label="Open", command=self.load_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.close_app)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Remove", command=self.remove)
        edit_menu.add_command(label="Filter", command=self.filter)
        edit_menu.add_command(label="Add", command=self.add)

        calculate_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Calculate", menu=calculate_menu)
        calculate_menu.add_command(label="Sum", command=self.sum)
        calculate_menu.add_command(label="Mean", command=self.mean)
        calculate_menu.add_command(label="counts", command=self.counts)

        sort_menu =tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sort", menu=sort_menu)
        sort_menu.add_command(label="Sort A -> Z")
        sort_menu.add_command(label="Sort Z -> A")
        # Tạo Treeview để hiển thị dữ liệu
        self.tree = ttk.Treeview(self.root, show="headings")
        self.tree.pack(expand=True, fill='both')

        # Thêm thanh trạng thái
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

    #remove columns
    #filter
    #add
    #sum
    #mean
    #counts
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

if __name__ == "__main__":
    root = tk.Tk()
    app = DataViewerApp(root)
    root.mainloop()
