import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import csv
import json
import matplotlib.pyplot as plt
from collections import Counter, defaultdict, deque
from datetime import datetime
from tkinter.simpledialog import askstring
import copy
import pandas as pd

class DataViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple data analysis - Pandas")
        self.root.geometry("1300x800")

        self.original_data = []
        self.current_data = []
        self.extra_column = None
        # self.deleted_columns = {} # Không còn cần thiết nữa

        self.undo_stack = deque() # Stack để lưu trữ các trạng thái dữ liệu trước đó
        self.redo_stack = deque() # Stack để lưu trữ các trạng thái dữ liệu đã undo
        self.max_undo_levels = 50 # Giới hạn số lượng bước undo để tiết kiệm bộ nhớ

        self.create_widgets()
        self.root.bind('<Control-z>', lambda event: self.undo_last_action())
        self.root.bind('<Control-y>', lambda event: self.redo_last_action()) # Thêm bind cho Redo
        self.root.bind('<F2>', lambda event: self.rename_column())
        self.root.bind("<Control-o>", lambda event: self.load_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind('<Control-f>', lambda event: self.filter_data())

    def _record_current_state_for_undo(self):
        if len(self.undo_stack) >= self.max_undo_levels:
            self.undo_stack.popleft()  # Xóa phần tử cũ nhất nếu stack đầy
        # Lưu bản sao sâu (deep copy) của dữ liệu hiện tại
        self.undo_stack.append(copy.deepcopy(self.current_data))
        self.redo_stack.clear()  # Xóa redo stack khi có hành động mới
        self._update_undo_redo_button_states()  # Cập nhật trạng thái nút

    def _update_undo_redo_button_states(self):
        if hasattr(self, 'undo_button'):  # Đảm bảo nút đã được tạo
            if self.undo_stack:
                self.undo_button.config(state=tk.NORMAL)
            else:
                self.undo_button.config(state=tk.DISABLED)

        if hasattr(self, 'redo_button'):  # Đảm bảo nút đã được tạo
            if self.redo_stack:
                self.redo_button.config(state=tk.NORMAL)
            else:
                self.redo_button.config(state=tk.DISABLED)

    def calculate_count(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded.")
            return

        col_name = askstring("Count Column", "Enter the column name to count values:")
        if not col_name:
            return

        # Kiểm tra xem cột có tồn tại trong dữ liệu hay không
        if col_name not in self.current_data[0]:
            messagebox.showwarning("Invalid Column", f"Column '{col_name}' not found.")
            return

        try:
            self._record_current_state_for_undo()
            # Đếm số lần xuất hiện của mỗi giá trị trong cột
            value_counts = Counter(row.get(col_name, None) for row in
                                   self.current_data)  # Thay '' bằng None để dễ dàng nhận diện giá trị null

            # Nếu không có giá trị nào, hiển thị thông báo lỗi
            if not value_counts:
                messagebox.showinfo("Info", "No values found to count.")
                return

            # Thêm cột count vào dữ liệu (chỉ thêm vào dòng đầu tiên)
            self.extra_column = f"{col_name}_count"
            first_row = self.current_data[0]
            first_row[self.extra_column] = json.dumps(dict(value_counts))  # Lưu trữ dưới dạng chuỗi JSON

            # Cập nhật hiển thị dữ liệu
            self.display_data(self.current_data)
            messagebox.showinfo("Count Complete", f"Counted values in column '{col_name}'.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to count values:\n{e}")
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
        edit_menu.add_command(label="Remove Column", command=self.clear_result_column)  # Đổi tên cho rõ ràng hơn
        edit_menu.add_command(label="Filter", command=self.filter_data)
        edit_menu.add_command(label="Add Column (MonthYear)", command=self.add_month_year_column)
        edit_menu.add_command(label="Rename Column", command=self.rename_column)  # Đổi tên cho rõ ràng hơn
        edit_menu.add_separator()
        edit_menu.add_command(label="Undo", command=self.undo_last_action)
        edit_menu.add_command(label="Redo", command=self.redo_last_action)

        calculate_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Calculate", menu=calculate_menu)
        calculate_menu.add_command(label="Sum", command=self.calculate_sum)
        calculate_menu.add_command(label="Mean", command=self.calculate_mean)
        calculate_menu.add_command(label="Min", command=self.calculate_min)
        calculate_menu.add_command(label="Max", command=self.calculate_max)
        calculate_menu.add_command(label="Count", command=self.calculate_count)

        sort_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sort", menu=sort_menu)
        sort_menu.add_command(label="Sort A -> Z", command=lambda: self.sort_column(ascending=True))
        sort_menu.add_command(label="Sort Z -> A", command=lambda: self.sort_column(ascending=False))

        chart_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Chart", menu=chart_menu)
        chart_menu.add_command(label="Pie Chart", command=self.create_pie_chart)
        chart_menu.add_command(label="Bar Chart (Custom)", command=self.create_custom_bar_chart)
        chart_menu.add_command(label="Bar Chart (Month/Year Aggregate)", command=self.create_month_year_bar_chart)
        chart_menu.add_command(label="Line Chart", command=self.create_line_chart)

        self.tree = ttk.Treeview(self.root, show="headings")
        self.tree.pack(expand=True, fill='both')

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")  # Trạng thái ban đầu
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w')
        self.status_bar.pack(side='bottom', fill='x')

        self.undo_button = tk.Button(self.root, text="Undo", command=self.undo_last_action)
        self.undo_button.pack(side="right", padx=5, pady=5)
        self.redo_button = tk.Button(self.root, text="Redo", command=self.redo_last_action)
        self.redo_button.pack(side="right", padx=5, pady=5)

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
                self._record_current_state_for_undo()  # Ghi lại trạng thái ban đầu sau khi load file
                self.status_var.set(f"File loaded: {file_path}")
            else:
                messagebox.showinfo("No Data", "File loaded but contains no data.")
                self.status_var.set("File loaded but no data.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")
            self.status_var.set(f"Error loading file: {e}")

    def display_data(self, data):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []

        if not data:
            return

        all_columns = sorted(list(set(key for row in data for key in row.keys())))
        self.tree["columns"] = all_columns
        for col in all_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='w')

        for row in data:
            values = [row.get(col, "") for col in all_columns]
            self.tree.insert("", "end", values=values)

    def calculate_sum(self):
        col_name = simpledialog.askstring("Select Column", "Enter the column name to calculate sum:")
        if not col_name:
            return
        try:
            df = pd.DataFrame(self.current_data)

            if col_name not in df.columns:
                raise KeyError(f"Column '{col_name}' does not exist.")

            self._record_current_state_for_undo()

            # Chuyển đổi sang số, lỗi sẽ thành NaN
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            total = df[col_name].sum()

            if pd.isna(total):
                raise ValueError("No valid numeric values to sum.")

            self.extra_column = f"{col_name}_sum"

            # Chỉ gán giá trị vào dòng đầu tiên, các dòng khác rỗng
            df[self.extra_column] = ""
            df.at[0, self.extra_column] = total

            self.current_data = df.to_dict(orient='records')
            self.display_data(self.current_data)
            self.status_var.set(f"Sum calculated for '{col_name}'.")

        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate sum: {e}")
            self.status_var.set(f"Error calculating sum: {e}")

    def calculate_mean(self):
        col_name = simpledialog.askstring("Select Column", "Enter the column name to calculate mean:")
        if not col_name:
            return
        try:
            df = pd.DataFrame(self.current_data)

            if col_name not in df.columns:
                raise KeyError(f"Column '{col_name}' does not exist.")

            self._record_current_state_for_undo()

            # Chuyển cột sang float, bỏ qua giá trị không hợp lệ
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            mean_value = df[col_name].mean()

            if pd.isna(mean_value):
                raise ValueError("No valid numeric values found.")

            self.extra_column = f"{col_name}_mean"

            # Chỉ ghi giá trị vào dòng đầu tiên
            df[self.extra_column] = ""
            df.at[0, self.extra_column] = mean_value

            self.current_data = df.to_dict(orient='records')
            self.display_data(self.current_data)
            self.status_var.set(f"Mean calculated for '{col_name}'.")

        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate mean: {e}")
            self.status_var.set(f"Error calculating mean: {e}")

    def calculate_min(self):
        col_name = simpledialog.askstring("Select Column", "Enter the column name to calculate min:")
        if not col_name:
            return
        try:
            df = pd.DataFrame(self.current_data)

            if col_name not in df.columns:
                raise KeyError(f"Column '{col_name}' does not exist.")

            self._record_current_state_for_undo()

            # Chuyển cột thành dạng số, lỗi sẽ bị NaN
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            min_value = df[col_name].min()

            if pd.isna(min_value):
                raise ValueError("No valid numeric values found.")

            self.extra_column = f"{col_name}_min"

            df[self.extra_column] = ""
            df.at[0, self.extra_column] = min_value

            self.current_data = df.to_dict(orient='records')
            self.display_data(self.current_data)
            self.status_var.set(f"Min calculated for '{col_name}'.")

        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate min: {e}")
            self.status_var.set(f"Error calculating min: {e}")

    def calculate_max(self):
        col_name = simpledialog.askstring("Select Column", "Enter the column name to calculate max:")
        if not col_name:
            return
        try:
            df = pd.DataFrame(self.current_data)

            if col_name not in df.columns:
                raise KeyError(f"Column '{col_name}' does not exist.")

            self._record_current_state_for_undo()

            # Chuyển cột thành dạng số, lỗi sẽ bị NaN
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
            max_value = df[col_name].max()

            if pd.isna(max_value):
                raise ValueError("No valid numeric values found.")

            self.extra_column = f"{col_name}_max"

            df[self.extra_column] = ""
            df.at[0, self.extra_column] = max_value

            self.current_data = df.to_dict(orient='records')
            self.display_data(self.current_data)
            self.status_var.set(f"Max calculated for '{col_name}'.")

        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate max: {e}")
            self.status_var.set(f"Error calculating max: {e}")

    def clear_result_column(self):
        col_name = simpledialog.askstring("Clear Column","Enter column name to remove (leave empty to remove the last result column):")
        if not col_name:
            col_name = self.extra_column
        if not col_name:
            messagebox.showinfo("Info", "No column specified to remove.")
            return

        try:
            df = pd.DataFrame(self.current_data)

            if col_name not in df.columns:
                messagebox.showwarning("Not Found", f"Column '{col_name}' not found.")
                return

            self._record_current_state_for_undo()

            df.drop(columns=[col_name], inplace=True)

            if col_name == self.extra_column:
                self.extra_column = None

            self.current_data = df.to_dict(orient='records')
            self.display_data(self.current_data)

            messagebox.showinfo("Removed", f"Column '{col_name}' has been removed.")
            self.status_var.set(f"Column '{col_name}' removed.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove column: {e}")
            self.status_var.set(f"Error removing column: {e}")


    def undo_last_action(self):
        if not self.undo_stack:
            messagebox.showinfo("Info", "No actions to undo.")
            return

        self.redo_stack.append(copy.deepcopy(self.current_data))
        self.current_data = self.undo_stack.pop()
        self.display_data(self.current_data)
        messagebox.showinfo("Undo", "Last action undone.")
        self.status_var.set("Last action undone.")
        self._update_undo_redo_button_states()  # Cập nhật trạng thái nút

    def redo_last_action(self):
        if not self.redo_stack:
            messagebox.showinfo("Info", "No actions to redo.")
            return
        self.undo_stack.append(copy.deepcopy(self.current_data))
        self.current_data = self.redo_stack.pop()

        self.display_data(self.current_data)
        messagebox.showinfo("Redo", "Last action redone.")
        self.status_var.set("Last action redone.")
        self._update_undo_redo_button_states()  # Cập nhật trạng thái nút

    def filter_data(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to filter.")
            return

        col_name = simpledialog.askstring("Filter Column", "Enter the column name to filter:")
        if not col_name:
            return

        try:
            df = pd.DataFrame(self.current_data)

            if col_name not in df.columns:
                messagebox.showwarning("Not Found", f"Column '{col_name}' not found.")
                return

            filter_value = simpledialog.askstring("Filter Value",
                                                  f"Enter value to filter rows where '{col_name}' equals:")
            if filter_value is None:
                return

            # So sánh dưới dạng chuỗi
            filtered_df = df[df[col_name].astype(str) == filter_value]

            if filtered_df.empty:
                messagebox.showinfo("No Match", f"No rows found where '{col_name}' equals '{filter_value}'.")
                self.status_var.set(f"No match for filter '{col_name}' == '{filter_value}'.")
                return

            self.display_data(filtered_df.to_dict(orient='records'))
            self.status_var.set(f"Filtered rows where {col_name} == {filter_value}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to filter data: {e}")
            self.status_var.set(f"Error filtering data: {e}")

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
                    all_keys = set()
                    for row in self.current_data:
                        all_keys.update(row.keys())
                    writer = csv.DictWriter(f, fieldnames=list(all_keys))
                    writer.writeheader()
                    writer.writerows(self.current_data)
            elif file_path.endswith('.json'):
                with open(file_path, mode='w', encoding='utf-8') as f:
                    json.dump(self.current_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Success", f"File saved successfully: {file_path}")
            self.status_var.set(f"File saved: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")
            self.status_var.set(f"Error saving file: {e}")

    def close_app(self):
        if messagebox.askyesno("Exit", "Do you want to exit?"):
            self.root.quit()

    def sort_column(self, ascending=True):
        col_name = simpledialog.askstring("Sort Column", "Enter the column name to sort:")
        if not col_name:
            return
        if not self.current_data:
            messagebox.showwarning("No Data", "No data loaded to sort.")
            return

        try:
            df = pd.DataFrame(self.current_data)

            if col_name not in df.columns:
                messagebox.showwarning("Not Found", f"Column '{col_name}' not found.")
                return

            self._record_current_state_for_undo()

            # Thử chuyển sang số, nếu thất bại thì giữ nguyên chuỗi
            df[col_name] = pd.to_numeric(df[col_name], errors='ignore')

            # Sắp xếp
            df = df.sort_values(by=col_name, ascending=ascending, na_position='last')

            self.current_data = df.to_dict(orient='records')
            self.display_data(self.current_data)

            messagebox.showinfo("Sort", f"Data sorted by '{col_name}' {'ascending' if ascending else 'descending'}.")
            self.status_var.set(f"Data sorted by '{col_name}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to sort data: {e}")
            self.status_var.set(f"Error sorting data: {e}")

    def create_pie_chart(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to create a chart.")
            return

        col_name = simpledialog.askstring("Pie Chart", "Enter the column name for the pie chart (categorical data):")
        if not col_name:
            return

        try:
            df = pd.DataFrame(self.current_data)

            if col_name not in df.columns:
                messagebox.showwarning("Column Not Found", f"Column '{col_name}' not found in the data.")
                return

            # Lọc bỏ giá trị null, rỗng
            series = df[col_name].dropna().astype(str).str.strip()
            series = series[series != ""]

            if series.empty:
                messagebox.showinfo("No Data", "No valid data found in the selected column for charting.")
                return

            value_counts = series.value_counts()

            plt.figure(figsize=(8, 8))
            plt.pie(value_counts, labels=value_counts.index, autopct='%1.1f%%', startangle=90)
            plt.title(f"Pie Chart of {col_name}")
            plt.axis('equal')  # Giữ tỷ lệ tròn
            plt.show()

            self.status_var.set(f"Pie chart created for '{col_name}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create pie chart:\n{e}")
            self.status_var.set(f"Error creating pie chart: {e}")

    def create_custom_bar_chart(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to create a chart.")
            return

        x_col_name = simpledialog.askstring("Bar Chart - Categories (X-axis)",
                                            "Enter the column name for categories (X-axis, e.g., 'Product', 'Age', 'Score'):")
        if not x_col_name:
            return

        if not self.current_data or x_col_name not in self.current_data[0]:
            messagebox.showwarning("Column Not Found", f"Category column '{x_col_name}' not found in the data.")
            return

        y_col_name = simpledialog.askstring("Bar Chart - Values (Y-axis)",
                                            "Enter the numeric column name for values (Y-axis, e.g., 'Sales', 'Quantity'):")
        if not y_col_name:
            return

        if not self.current_data or y_col_name not in self.current_data[0]:
            messagebox.showwarning("Column Not Found", f"Value column '{y_col_name}' not found in the data.")
            return

        aggregation_method = simpledialog.askstring("Aggregation Method",
                                                    "Enter aggregation method (sum, mean, count). Default is sum:")
        if not aggregation_method:
            aggregation_method = "sum"
        aggregation_method = aggregation_method.lower()

        if aggregation_method not in ["sum", "mean", "count"]:
            messagebox.showwarning("Invalid Method", "Invalid aggregation method. Using 'sum' by default.")
            aggregation_method = "sum"

        aggregated_data = defaultdict(lambda: {'values': [], 'count': 0})

        for row in self.current_data:
            category = row.get(x_col_name)
            value = row.get(y_col_name)

            if category is not None and str(category).strip() != '':
                category_key = str(category)
                try:
                    numeric_val = float(value)
                    aggregated_data[category_key]['values'].append(numeric_val)
                    aggregated_data[category_key]['count'] += 1
                except (ValueError, TypeError):
                    continue

        if not aggregated_data:
            messagebox.showinfo("No Data",
                                "No valid data found for charting after aggregation. Check your column selections and data types.")
            return

        final_categories = []
        final_values = []

        try:
            sorted_keys = sorted(aggregated_data.keys(), key=lambda x: float(x))
        except ValueError:
            sorted_keys = sorted(aggregated_data.keys())

        for cat_key in sorted_keys:
            final_categories.append(cat_key)
            if aggregation_method == "sum":
                final_values.append(sum(aggregated_data[cat_key]['values']))
            elif aggregation_method == "mean":
                if aggregated_data[cat_key]['count'] > 0:
                    final_values.append(sum(aggregated_data[cat_key]['values']) / aggregated_data[cat_key]['count'])
                else:
                    final_values.append(0)
            elif aggregation_method == "count":
                final_values.append(aggregated_data[cat_key]['count'])

        if not final_categories or not final_values:
            messagebox.showinfo("No Data", "No valid data to plot after aggregation.")
            return

        plt.figure(figsize=(12, 7))
        bars = plt.bar(final_categories, final_values, color='teal')
        plt.xlabel(x_col_name)
        plt.ylabel(f"{aggregation_method.capitalize()} of {y_col_name}")
        plt.title(f"{aggregation_method.capitalize()} of {y_col_name} by {x_col_name}")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
        self.status_var.set(f"Bar chart created for {y_col_name} by {x_col_name}.")

    def add_month_year_column(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to add 'MonthYear' column.")
            return

        date_col_name = simpledialog.askstring("Add 'MonthYear' Column",
                                               "Enter the column name containing date information (e.g., 'Date', 'TransactionDate'):")
        if not date_col_name:
            return

        if date_col_name not in self.current_data[0]:
            messagebox.showwarning("Column Not Found", f"Date column '{date_col_name}' not found in the data.")
            return

        if "MonthYear" in self.current_data[0]:
            if not messagebox.askyesno("Overwrite Column",
                                       "'MonthYear' column already exists. Do you want to overwrite it?"):
                return

        self._record_current_state_for_undo()  # Ghi lại trạng thái trước khi thêm cột

        new_data_with_monthyear = []
        parsed_count = 0
        for row in self.current_data:
            new_row = row.copy()
            date_str = row.get(date_col_name)
            month_year_value = ""

            if date_str is not None and str(date_str).strip() != '':
                try:
                    date_obj = None
                    if 'T' in date_str:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    elif '-' in date_str and len(date_str) >= 10:
                        try:
                            date_obj = datetime.strptime(date_str[:10], '%Y-%m-%d')
                        except ValueError:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    elif '/' in date_str:
                        try:
                            date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                        except ValueError:
                            try:
                                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                            except ValueError:
                                pass
                    elif len(date_str) == 7 and date_str[4] == '-':
                        try:
                            date_obj = datetime.strptime(date_str, '%Y-%m')
                        except ValueError:
                            pass
                    elif len(date_str) == 6 and date_str.isdigit():
                        try:
                            date_obj = datetime.strptime(date_str, '%Y%m')
                        except ValueError:
                            pass

                    if date_obj:
                        month_year_value = date_obj.year * 100 + date_obj.month
                        parsed_count += 1
                except (ValueError, TypeError):
                    pass

            new_row["MonthYear"] = month_year_value
            new_data_with_monthyear.append(new_row)

        if parsed_count == 0:
            messagebox.showwarning("No Dates Parsed",
                                   "Could not parse any dates from the specified column into MonthYear format. Check your date column format.")
            return

        self.current_data = new_data_with_monthyear
        self.display_data(self.current_data)
        messagebox.showinfo("Success", f"'MonthYear' column added successfully. ({parsed_count} dates parsed)")
        self.status_var.set(f"'MonthYear' column added. {parsed_count} dates parsed.")


    def create_month_year_bar_chart(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to create a chart.")
            return

        if "MonthYear" not in self.current_data[0]:
            messagebox.showwarning("Missing Column", "Please add the 'MonthYear' column first using 'Edit -> Add Column (MonthYear)'.")
            return

        numeric_col_name = simpledialog.askstring("Month/Year Bar Chart", "Enter the numeric column name to aggregate (X-axis, e.g., 'Sales', 'Quantity'):")
        if not numeric_col_name:
            return

        if numeric_col_name not in self.current_data[0]:
            messagebox.showwarning("Column Not Found", f"Numeric column '{numeric_col_name}' not found in the data.")
            return

        aggregation_method = simpledialog.askstring("Aggregation Method", "Enter aggregation method (sum, mean, count). Default is sum:")
        if not aggregation_method:
            aggregation_method = "sum"
        aggregation_method = aggregation_method.lower()

        if aggregation_method not in ["sum", "mean", "count"]:
            messagebox.showwarning("Invalid Method", "Invalid aggregation method. Using 'sum' by default.")
            aggregation_method = "sum"


        month_year_aggregation = defaultdict(lambda: {'values': [], 'count': 0})

        for row in self.current_data:
            month_year_key = row.get("MonthYear")
            numeric_value = row.get(numeric_col_name)

            if month_year_key is not None and str(month_year_key).strip() != '' and numeric_value is not None and str(numeric_value).strip() != '':
                try:
                    my_key_str = str(month_year_key) # Ensure key is string
                    value = float(numeric_value)

                    month_year_aggregation[my_key_str]['values'].append(value)
                    month_year_aggregation[my_key_str]['count'] += 1
                except (ValueError, TypeError):
                    continue

        if not month_year_aggregation:
            messagebox.showinfo("No Data", "No valid 'MonthYear' or numeric data found for charting.")
            return

        sorted_month_year_keys_int = sorted([int(k) for k in month_year_aggregation.keys()])
        sorted_month_year_labels = [str(k) for k in sorted_month_year_keys_int]

        final_values = []
        for k in sorted_month_year_keys_int:
            cat_key = str(k) # Convert back to string for dictionary lookup
            if aggregation_method == "sum":
                final_values.append(sum(month_year_aggregation[cat_key]['values']))
            elif aggregation_method == "mean":
                if month_year_aggregation[cat_key]['count'] > 0:
                    final_values.append(sum(month_year_aggregation[cat_key]['values']) / month_year_aggregation[cat_key]['count'])
                else:
                    final_values.append(0)
            elif aggregation_method == "count":
                final_values.append(month_year_aggregation[cat_key]['count'])

        if not sorted_month_year_labels or not final_values:
            messagebox.showinfo("No Data", "No valid data to plot after aggregation.")
            return

        plt.figure(figsize=(12, 7))
        bars = plt.bar(sorted_month_year_labels, final_values, color='skyblue')

        plt.xlabel(f"Month-Year (YYYYMM)")
        plt.ylabel(f"{aggregation_method.capitalize()} of {numeric_col_name}")
        plt.title(f"{aggregation_method.capitalize()} of {numeric_col_name} by Month and Year")
        plt.xticks(rotation=70, ha='right')
        plt.tight_layout()
        plt.show()
        self.status_var.set(f"Month/Year bar chart created for {numeric_col_name}.")

    def rename_column(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to rename a column.")
            return

        old_col = simpledialog.askstring("Rename Column", "Enter the current column name:")
        if not old_col:
            return

        try:
            df = pd.DataFrame(self.current_data)

            if old_col not in df.columns:
                messagebox.showwarning("Invalid Column", f"Column '{old_col}' not found.")
                return

            new_col = simpledialog.askstring("Rename Column", f"Enter the new name for column '{old_col}':")
            if not new_col:
                messagebox.showinfo("Cancelled", "Renaming cancelled.")
                return

            self._record_current_state_for_undo()

            df.rename(columns={old_col: new_col}, inplace=True)

            if self.extra_column == old_col:
                self.extra_column = new_col

            self.current_data = df.to_dict(orient='records')
            self.display_data(self.current_data)

            messagebox.showinfo("Renamed", f"Column '{old_col}' has been renamed to '{new_col}'.")
            self.status_var.set(f"Column '{old_col}' renamed to '{new_col}'.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename column: {e}")
            self.status_var.set(f"Error renaming column: {e}")

    def create_line_chart(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to create a line chart.")
            return

        x_col = simpledialog.askstring("Line Chart", "Enter the X-axis column:")
        y_col = simpledialog.askstring("Line Chart", "Enter the Y-axis column:")

        if not x_col or not y_col:
            return

        if x_col not in self.current_data[0] or y_col not in self.current_data[0]:
            messagebox.showwarning("Column Not Found", "One or both columns not found.")
            return

        try:
            x_vals = []
            y_vals = []

            for row in self.current_data:
                x_val = row.get(x_col)
                y_val = row.get(y_col)

                if x_val is None or y_val is None:
                    continue

                try:
                    y_val_float = float(y_val)
                    x_vals.append(str(x_val))  # Convert x to string for consistent labels
                    y_vals.append(y_val_float)
                except ValueError:
                    continue  # skip if y cannot be converted to float

            if not x_vals or not y_vals:
                messagebox.showinfo("No Data", "No valid numeric data found for plotting.")
                return

            plt.figure(figsize=(12, 6))
            plt.plot(x_vals, y_vals, marker='o', linestyle='-', color='blue')
            plt.title(f"{y_col} over {x_col}")
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            plt.show()
            self.status_var.set(f"Line chart created for {y_col} over {x_col}.")


        except Exception as e:
            messagebox.showerror("Error", f"Failed to plot line chart:\n{e}")
            self.status_var.set(f"Error creating line chart: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DataViewerApp(root)
    root.mainloop()
