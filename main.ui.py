import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tksheet import Sheet
from tkcalendar import DateEntry   # pip install tkcalendar
import pandas as pd
import os
from datetime import timedelta
from app import *


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AnSuongFood")

        # Create notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        # ---------------- Tab 1: ToShip ----------------
        self.tab_toship = tk.Frame(notebook)
        notebook.add(self.tab_toship, text="ToShip")

        self.filepath_sp = tk.StringVar()
        self.filepath_tts = tk.StringVar()
        self.sheet = None
        self.sheet_shipping = None

        # File selection frame
        file_frame = tk.Frame(self.tab_toship)
        file_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        tk.Label(file_frame, text="Shopee (Excel):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(file_frame, textvariable=self.filepath_sp, width=50).grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        tk.Button(file_frame, text="Browse", command=self.browse_excel).grid(row=0, column=3, padx=5, pady=5)

        tk.Label(file_frame, text="TTS (CSV):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(file_frame, textvariable=self.filepath_tts, width=50).grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="w")
        tk.Button(file_frame, text="Browse", command=self.browse_csv).grid(row=1, column=3, padx=5, pady=5)

        button_frame = tk.Frame(file_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=5, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)

        tk.Button(button_frame, text="Load Data", command=self.load_data).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(button_frame, text="Clear", command=self.clear_data).grid(row=0, column=2, padx=5, pady=5)

        # Labels for tui counts
        self.label_16_22 = tk.Label(self.tab_toship, text="")
        self.label_16_22.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="w")

        self.label_18_28 = tk.Label(self.tab_toship, text="")
        self.label_18_28.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="w")

        self.label_22_32 = tk.Label(self.tab_toship, text="")
        self.label_22_32.grid(row=3, column=0, padx=10, pady=(0, 5), sticky="w")

        # ---------------- Tab 2: Shipping ----------------
        self.tab_shipping = tk.Frame(notebook)
        notebook.add(self.tab_shipping, text="Shipping")

        # Date pickers
        shipping_frame = tk.Frame(self.tab_shipping)
        shipping_frame.pack(padx=20, pady=20, anchor="w")

        tk.Label(shipping_frame, text="From Date:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.from_date = DateEntry(shipping_frame, date_pattern="yyyy-mm-dd")
        self.from_date.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(shipping_frame, text="To Date:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.to_date = DateEntry(shipping_frame, date_pattern="yyyy-mm-dd")
        self.to_date.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        tk.Button(shipping_frame, text="Load Shipping Data", command=self.load_shipping_data).grid(row=1, column=0, columnspan=5, pady=10)

 
         # Frame for tksheet of shipping results
        self.shipping_result_frame = tk.Frame(self.tab_shipping)
        self.shipping_result_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
    # --------- File browse handlers ----------
    def browse_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*toship*.xlsx *toship*.xls")])
        if file_path and "toship" in os.path.basename(file_path).lower():
            self.filepath_sp.set(file_path)
        else:
            self.filepath_sp.set("")
            messagebox.showerror("Error", "Please select an Excel file containing 'toship' in the filename")

    def browse_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*To*Ship*.csv")])
        if file_path and "to ship" in os.path.basename(file_path).lower():
            self.filepath_tts.set(file_path)
        else:
            self.filepath_tts.set("")
            messagebox.showerror("Error", "Please select a CSV file containing 'To Ship' in the filename")

    # --------- Load ToShip data ----------
    def load_data(self):
        if self.sheet:
            self.sheet.destroy()

        excel_path = self.filepath_sp.get()
        csv_path = self.filepath_tts.get()

        if not excel_path and not csv_path:
            messagebox.showerror("Error", "Please select Shopee or TTS files")
            return

        try:
            df_order = get_qty(excel_path, csv_path)
            df_master = get_seller_sku_price()
            df = calculate_amount(df_order, df_master)
            tui_dict = calculate_tui(df_order, df_master)

            self.label_16_22.config(text=f"Tui 16x22: {tui_dict.get('tui_16_22', '')}")
            self.label_18_28.config(text=f"Tui 18x28: {tui_dict.get('tui_18_28', '')}")
            self.label_22_32.config(text=f"Tui 22x32: {tui_dict.get('tui_22_32', '')}")

            self.sheet = Sheet(
                self.tab_toship,
                data=df.values.tolist(),
                headers=df.columns.tolist(),
                width=800,
                height=400,
                show_x_scrollbar=True,
                show_y_scrollbar=True
            )
            self.sheet.enable_bindings()
            self.sheet.grid(row=4, column=0, padx=10, pady=10)

            self.sheet.set_column_widths([200, 100, 100, 100, 100, 100])
            self.sheet.align_columns(columns=[1, 2, 3, 4, 5], align="e")

            self.filepath_sp.set("")
            self.filepath_tts.set("")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def clear_data(self):
        self.filepath_sp.set("")
        self.filepath_tts.set("")
        self.label_16_22.config(text="")
        self.label_18_28.config(text="")
        self.label_22_32.config(text="")
        if self.sheet:
            self.sheet.destroy()
            self.sheet = None

    def load_shipping_data(self):
        from_date_val = self.from_date.get_date()
        to_date_val = self.to_date.get_date() + timedelta(days=1)

        if to_date_val < from_date_val:
            messagebox.showerror("Error", "To Date must be later than or equal to From Date")
            return
        
        try:
            with get_session() as session:
                data = get_order_summary(session, from_date_val, to_date_val)  # returns list of tuples

                if not data:
                    messagebox.showinfo("No Data", "No shipping data found in this range.")
                    return

                if self.sheet_shipping:
                    self.sheet_shipping.destroy()

                df = pd.DataFrame(data, columns=["shipped_date", "count", "cost_of_sales", "planned_earning", "earning"])
                # Format numeric columns to include commas and two decimal places
                numeric_columns = ["cost_of_sales", "planned_earning", "earning"]
                for col in numeric_columns:
                    df[col] = df[col].round(2).apply(lambda x: f"{x:,.2f}")

                self.sheet_shipping = Sheet(
                    self.shipping_result_frame,
                    data=df.values.tolist(),
                    headers=df.columns.tolist(),
                    width=800,
                    height=400,
                    show_x_scrollbar=True,
                    show_y_scrollbar=True
                )
                self.sheet_shipping.enable_bindings()
                self.sheet_shipping.pack(fill="both", expand=True)
                self.sheet_shipping.align_columns([1, 2, 3, 4], align="e")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load shipping data: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()