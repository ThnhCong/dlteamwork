import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import json

class DataViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Teamwork group1")
        self.root.geometry("1200x900")

        self.create_widgets()

    def create_widgets(self):
        # Load Button
        load_button = ttk.Button(self.root, text="Load CSV or JSON", command=self.load_file)
        load_button.pack(pady=10)

        # Treeview Widget
        self.tree = ttk.Treeview(self.root, show="headings")
        self.tree.pack(expand=True, fill='both')

        # Scrollbars
        vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')

    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV or JSON file",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            # Try reading with utf-8, fallback to iso-8859-1
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
                data = read_file_with_encoding(file_path, 'iso-8859-1')  # or 'windows-1252'

            if data:
                self.display_data(data)
            else:
                messagebox.showinfo("No Data", "File loaded but contains no data.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")


    def display_data(self, data):
        # Clear previous content
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []

        # Determine columns
        columns = list(data[0].keys())
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='w')

        # Insert rows
        for row in data:
            values = [row.get(col, "") for col in columns]
            self.tree.insert("", "end", values=values)

if __name__ == "__main__":
    root = tk.Tk()
    app = DataViewerApp(root)
    root.mainloop()
