import tkinter as tk
from tkinter import filedialog
from tksheet import Sheet
import pandas as pd
from app import *

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AnSuongFood")

        # Variables to store file paths
        self.filepath_sp = tk.StringVar()
        self.filepath_tts = tk.StringVar()

        # Frame for file selection
        file_frame = tk.Frame(self.root)
        file_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        # Excel file selection
        tk.Label(file_frame, text="Shopee (Excel):").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(file_frame, textvariable=self.filepath_sp, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(file_frame, text="Browse", command=self.browse_excel).grid(row=0, column=2, padx=5, pady=5)

        # CSV file selection
        tk.Label(file_frame, text="TTS (CSV):").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(file_frame, textvariable=self.filepath_tts, width=50).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(file_frame, text="Browse", command=self.browse_csv).grid(row=1, column=2, padx=5, pady=5)

        # Button to load data and display sheet
        tk.Button(file_frame, text="Load Data", command=self.load_data).grid(row=2, column=1, padx=5, pady=5)

        # Placeholder for sheet widget
        self.sheet = None

    def browse_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.filepath_sp.set(file_path)

    def browse_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.filepath_tts.set(file_path)

    def load_data(self):
        # Clear previous sheet if exists
        if self.sheet:
            self.sheet.destroy()

        # Get file paths
        excel_path = self.filepath_sp.get()
        csv_path = self.filepath_tts.get()

        if not excel_path and not csv_path:
            tk.messagebox.showerror("Error", "Please select Shopee or TTS files")
            return

        try:
            # Load data using provided functions
            df_order = get_qty(excel_path, csv_path)
            df_master = get_seller_sku_price()
            df = calculate_amount(df_order, df_master)

            # Create tksheet widget
            self.sheet = Sheet(
                self.root,
                data=df.values.tolist(),  # Include total row
                headers=df.columns.tolist(),  # Use DataFrame columns as headers
                width=800,
                height=400,
                show_x_scrollbar=True,
                show_y_scrollbar=True
            )
            self.sheet.enable_bindings()  # Enable default bindings
            self.sheet.grid(row=1, column=0, padx=10, pady=10)

            # Adjust column widths for better readability
            self.sheet.set_column_widths([200, 100, 100, 100, 100, 100])

            # Align numeric columns (sp_qty, tts_qty, sum_qty, price, amount) to the right
            numeric_columns = [1, 2, 3, 4, 5]  # Column indices for sp_qty, tts_qty, sum_qty, price, amount
            self.sheet.align_columns(columns=numeric_columns, align="e")  # 'e' for east (right)

            to_csv(df)

        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to load data: {str(e)}")

# Initialize and run the Tkinter app
root = tk.Tk()
app = App(root)
root.mainloop()


# import tkinter as tk
# from tksheet import Sheet
# import pandas as pd
# from app import *

# df_order = get_qty('Order.toship.20250826_20250925 (1).xlsx', 'To Ship order-2025-09-25-21_15.csv')
# df_master = get_seller_sku_price()
# df = calculate_amount(df_order, df_master)

# # Create the Tkinter application
# class App:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("DataFrame Display with tksheet")

#         # Create a tksheet widget
#         self.sheet = Sheet(
#             self.root,
#             data=df.values.tolist(),  # Include total row
#             headers=df.columns.tolist(),  # Use DataFrame columns as headers
#             width=800,
#             height=400,
#             show_x_scrollbar=True,
#             show_y_scrollbar=True
#         )
#         self.sheet.enable_bindings()  # Enable default bindings
#         self.sheet.grid(row=0, column=0, padx=10, pady=10)

#         # Adjust column widths for better readability
#         self.sheet.set_column_widths([200, 100, 100, 100, 100, 100])

#         # Align numeric columns (sp_qty, tts_qty, sum_qty, price, amount) to the right
#         numeric_columns = [1, 2, 3, 4, 5]  # Column indices for sp_qty, tts_qty, sum_qty, price, amount
#         self.sheet.align_columns(columns=numeric_columns, align="e")  # 'e' for east (right)

# # Initialize and run the Tkinter app
# root = tk.Tk()
# app = App(root)
# root.mainloop()