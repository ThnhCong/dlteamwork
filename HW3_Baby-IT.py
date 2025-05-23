import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import csv
import json
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
from datetime import datetime
import numpy as np # Needed for np.arange for y-axis ticks
from tkinter.simpledialog import askstring
from PIL import Image, ImageTk
from playsound import playsound
class DataViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple data analysis - Pandas")
        self.root.geometry("1300x800")

        self.original_data = []
        self.current_data = []
        self.extra_column = None
        self.deleted_columns = {}

        self.create_widgets()
        self.root.bind('<Control-z>', lambda event: self.undo_last_action())
        self.root.bind('<F2>', lambda event: self.rename_column())
        self.root.bind("<Control-o>", lambda event: self.load_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind('<Control-f>', lambda event: self.filter_data())

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
        edit_menu.add_command(label="Remove", command=self.clear_result_column)
        edit_menu.add_command(label="Filter", command=self.filter_data)
        edit_menu.add_command(label="Add Column (MonthYear)", command=self.add_month_year_column)
        edit_menu.add_command(label="Rename", command=self.rename_column)
        edit_menu.add_separator()
        edit_menu.add_command(label="Undo", command=self.undo_last_action)

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
            total = sum(float(row.get(col_name, 0)) for row in self.current_data if row.get(col_name))
            self.extra_column = f"{col_name}_sum"
            for idx, row in enumerate(self.current_data):
                if self.extra_column in row and idx != 0:
                    del row[self.extra_column]
                row[self.extra_column] = total if idx == 0 else ""
            self.display_data(self.current_data)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate sum: {e}")

    def calculate_mean(self):
        col_name = simpledialog.askstring("Select Column", "Enter the column name to calculate mean:")
        if not col_name:
            return
        try:
            values = [float(row[col_name]) for row in self.current_data if row.get(col_name) is not None and str(row.get(col_name)).strip() != '']
            if not values:
                raise ValueError("No valid numeric values found.")
            mean_value = sum(values) / len(values)
            self.extra_column = f"{col_name}_mean"
            for idx, row in enumerate(self.current_data):
                if self.extra_column in row and idx != 0:
                    del row[self.extra_column]
                row[self.extra_column] = mean_value if idx == 0 else ""
            self.display_data(self.current_data)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate mean: {e}")

    def calculate_min(self):
        col_name = simpledialog.askstring("Select Column", "Enter the column name to calculate min:")
        if not col_name:
            return
        try:
            values = [float(row[col_name]) for row in self.current_data if row.get(col_name) is not None and str(row.get(col_name)).strip() != '']
            if not values:
                raise ValueError("No valid numeric values found.")
            min_value = min(values)
            self.extra_column = f"{col_name}_min"
            for idx, row in enumerate(self.current_data):
                if self.extra_column in row and idx != 0:
                    del row[self.extra_column]
                row[self.extra_column] = min_value if idx == 0 else ""
            self.display_data(self.current_data)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate min: {e}")

    def calculate_max(self):
        col_name = simpledialog.askstring("Select Column", "Enter the column name to calculate max:")
        if not col_name:
            return
        try:
            values = [float(row[col_name]) for row in self.current_data if row.get(col_name) is not None and str(row.get(col_name)).strip() != '']
            if not values:
                raise ValueError("No valid numeric values found.")
            max_value = max(values)
            self.extra_column = f"{col_name}_max"
            for idx, row in enumerate(self.current_data):
                if self.extra_column in row and idx != 0:
                    del row[self.extra_column]
                row[self.extra_column] = max_value if idx == 0 else ""
            self.display_data(self.current_data)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot calculate max: {e}")

    def clear_result_column(self):
        col_name = simpledialog.askstring("Clear Column", "Enter column name to remove (leave empty to remove the last result column):")
        if not col_name:
            col_name = self.extra_column
        if not col_name:
            messagebox.showinfo("Info", "No column specified to remove.")
            return

        if not self.current_data or col_name not in self.current_data[0]:
            messagebox.showwarning("Not Found", f"Column '{col_name}' not found.")
            return

        current_columns = list(self.current_data[0].keys())
        try:
            col_index = current_columns.index(col_name)
        except ValueError:
            messagebox.showwarning("Not Found", f"Column '{col_name}' not found.")
            return

        deleted_data = []
        for row in self.current_data:
            deleted_data.append(row.pop(col_name, None))

        self.deleted_columns[col_name] = {'data': deleted_data, 'index': col_index}
        if col_name == self.extra_column:
            self.extra_column = None
        self.display_data(self.current_data)
        messagebox.showinfo("Removed", f"Column '{col_name}' has been removed.")

    def undo_last_action(self):
        if not self.deleted_columns:
            messagebox.showinfo("Info", "No deleted columns to undo.")
            return

        last_col_name = list(self.deleted_columns.keys())[-1]
        col_info = self.deleted_columns.pop(last_col_name)
        restored_data_values = col_info['data']
        original_index = col_info['index']

        for i, row in enumerate(self.current_data):
            temp_list = list(row.items())

            temp_list.insert(original_index, (last_col_name, restored_data_values[i]))

            self.current_data[i] = dict(temp_list)

        self.display_data(self.current_data)
        messagebox.showinfo("Undo", f"Undo successful: column '{last_col_name}' restored.")

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
            self.current_data.sort(key=lambda x: float(x.get(col_name, float('inf')) if str(x.get(col_name, '')).strip() != '' else float('inf')), reverse=not ascending)
        except ValueError:
            self.current_data.sort(key=lambda x: x.get(col_name, ""), reverse=not ascending)
        self.display_data(self.current_data)
        messagebox.showinfo("Sort", f"Data sorted by '{col_name}' {'ascending' if ascending else 'descending'}.")

    def create_pie_chart(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to create a chart.")
            return

        col_name = simpledialog.askstring("Pie Chart", "Enter the column name for the pie chart (categorical data):")
        if not col_name:
            return

        if not self.current_data or col_name not in self.current_data[0]:
            messagebox.showwarning("Column Not Found", f"Column '{col_name}' not found in the data.")
            return

        try:
            column_values = [row.get(col_name) for row in self.current_data if row.get(col_name) is not None and str(row.get(col_name)).strip() != '']
            value_counts = Counter(column_values)

            labels = list(value_counts.keys())
            sizes = list(value_counts.values())

            if not sizes:
                messagebox.showinfo("No Data", "No valid data found in the selected column for charting.")
                return

            plt.figure(figsize=(8, 8))
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            plt.title(f"Pie Chart of {col_name}")
            plt.axis('equal')
            plt.show()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create pie chart:\n{e}")

    def create_custom_bar_chart(self):
        """
        Creates a bar chart where the X-axis is user-selected (string, int, float)
        and the Y-axis is a user-selected numeric column, aggregated by X-axis category.
        Includes data labels on bars and sets Y-axis ticks to increments of 100.
        """
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to create a chart.")
            return

        x_col_name = simpledialog.askstring("Bar Chart - Categories (X-axis)", "Enter the column name for categories (X-axis, e.g., 'Product', 'Age', 'Score'):")
        if not x_col_name:
            return

        if not self.current_data or x_col_name not in self.current_data[0]:
            messagebox.showwarning("Column Not Found", f"Category column '{x_col_name}' not found in the data.")
            return

        y_col_name = simpledialog.askstring("Bar Chart - Values (Y-axis)", "Enter the numeric column name for values (Y-axis, e.g., 'Sales', 'Quantity'):")
        if not y_col_name:
            return

        if not self.current_data or y_col_name not in self.current_data[0]:
            messagebox.showwarning("Column Not Found", f"Value column '{y_col_name}' not found in the data.")
            return

        # Ask the user for the aggregation method
        aggregation_method = simpledialog.askstring("Aggregation Method", "Enter aggregation method (sum, mean, count). Default is sum:")
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
                # Convert category to a string for consistent dictionary key
                category_key = str(category)
                try:
                    numeric_val = float(value)
                    aggregated_data[category_key]['values'].append(numeric_val)
                    aggregated_data[category_key]['count'] += 1
                except (ValueError, TypeError):
                    # Skip rows where the numeric value is invalid
                    continue

        if not aggregated_data:
            messagebox.showinfo("No Data", "No valid data found for charting after aggregation. Check your column selections and data types.")
            return

        # Process aggregated data based on the chosen method
        final_categories = []
        final_values = []

        # Sort categories for consistent plotting order
        # Attempt to sort numerically first, then alphabetically
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
                    final_values.append(0) # Should not happen if count > 0 check is there
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

    def add_month_year_column(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to add 'MonthYear' column.")
            return

        date_col_name = simpledialog.askstring("Add 'MonthYear' Column", "Enter the column name containing date information (e.g., 'Date', 'TransactionDate'):")
        if not date_col_name:
            return

        if date_col_name not in self.current_data[0]:
            messagebox.showwarning("Column Not Found", f"Date column '{date_col_name}' not found in the data.")
            return

        if "MonthYear" in self.current_data[0]:
            if not messagebox.askyesno("Overwrite Column", "'MonthYear' column already exists. Do you want to overwrite it?"):
                return

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
            messagebox.showwarning("No Dates Parsed", "Could not parse any dates from the specified column into MonthYear format. Check your date column format.")
            return

        self.current_data = new_data_with_monthyear
        self.display_data(self.current_data)
        messagebox.showinfo("Success", f"'MonthYear' column added successfully. ({parsed_count} dates parsed)")

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

    def rename_column(self):
        if not self.current_data:
            messagebox.showinfo("Info", "No data loaded to rename a column.")
            return

        old_col = simpledialog.askstring("Rename Column", "Enter the current column name:")
        if not old_col or old_col not in self.current_data[0]:
            messagebox.showwarning("Invalid Column", f"Column '{old_col}' not found.")
            return

        new_col = simpledialog.askstring("Rename Column", f"Enter the new name for column '{old_col}':")
        if not new_col:
            messagebox.showinfo("Cancelled", "Renaming cancelled.")
            return

        for row in self.current_data:
            row[new_col] = row.pop(old_col, "")

        if self.extra_column == old_col:
            self.extra_column = new_col

        self.display_data(self.current_data)
        messagebox.showinfo("Renamed", f"Column '{old_col}' has been renamed to '{new_col}'.")

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

        except Exception as e:
            messagebox.showerror("Error", f"Failed to plot line chart:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DataViewerApp(root)
    root.mainloop()
