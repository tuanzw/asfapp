import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Union, List, Type

import os, csv, glob, shutil
from schemas import *
from services import *

from mappings import shipped_order_index_mappings, datetime_fields
# from logger import logger



def get_qty_sp(filepath) -> pd.DataFrame:
    if not filepath:  # covers None or ''
        return pd.DataFrame(columns=["seller_sku", "sp_qty"])
    
    df: pd.DataFrame = pd.read_excel(filepath, sheet_name=0, header=0, usecols="S, Z", 
        converters={0: str, 1: int}
    )
    df = df.rename(columns={df.columns[0]: 'seller_sku', df.columns[1]: 'sp_qty'})

    df = df.groupby(by="seller_sku", as_index=False)["sp_qty"].sum()
    return df


def get_qty_tts(filepath) -> pd.DataFrame:
    if not filepath:  # covers None or ''
        return pd.DataFrame(columns=["seller_sku", "tts_qty"])
    
    df: pd.DataFrame = pd.read_csv(filepath, usecols=[6, 9],
        converters={0: str, 1: int}
    )
    df = df.rename(columns={df.columns[0]: 'seller_sku', df.columns[1]: 'tts_qty'})

    df = df.groupby(by="seller_sku", as_index=False)["tts_qty"].sum()
    return df


def get_qty(filepath_sp, filepath_tts) -> pd.DataFrame:
    df_sp = get_qty_sp(filepath_sp)
    df_tts = get_qty_tts(filepath_tts)
    df = pd.merge(df_sp, df_tts, on="seller_sku", how="outer")
    df = df.fillna(0).astype({"sp_qty": int, "tts_qty": int})
    df["sum_qty"] = df["sp_qty"] + df["tts_qty"]
    return df

def get_seller_sku_price() -> pd.DataFrame:
    df: pd.DataFrame = pd.read_csv('seller_sku-pricing.csv',
        converters={0:str, 1:float, 2:float, 3:float, 4:int, 5:int, 6:int}
    )
    return df

def calculate_tui(df_order, df_master) -> dict:
    df_seller_sku_price = df_master.iloc[:, [0, 1, 4, 5, 6]]
    df = pd.merge(df_order, df_seller_sku_price, on="seller_sku", how="outer")
    df = df.fillna(0).astype({"sp_qty": int, "tts_qty": int, "sum_qty": int})
    df["tui_16_22"] = df["sum_qty"] * df["tui_16_22"]
    df["tui_18_28"] = df["sum_qty"] * df["tui_18_28"]
    df["tui_22_32"] = df["sum_qty"] * df["tui_22_32"]

    return {
        'tui_16_22': df['tui_16_22'].sum(),
        'tui_18_28': df['tui_18_28'].sum(),
        'tui_22_32': df['tui_22_32'].sum(),
    }
    

def calculate_amount(df_order, df_master) -> pd.DataFrame:
    df_seller_sku_price = df_master.iloc[:, [0, 1]]
    df = pd.merge(df_order, df_seller_sku_price, on="seller_sku", how="outer")
    df = df.fillna(0).astype({"sp_qty": int, "tts_qty": int, "sum_qty": int})
    df["amount"] = df["sum_qty"] * df["price"]

    # Update 'amount' for hoanh_thanh_500g
    mask = df['seller_sku'] == 'hoanh_thanh_500g'
    df.loc[mask, 'amount'] = df.loc[mask, 'sum_qty'] * df.loc[mask, 'price'] - (df.loc[mask, 'sum_qty'] // 20) * 10000

    total_amount = df["amount"].sum() / 1000
    df = df.rename(columns={'amount': f'amount: {total_amount}'})
    df["price"] = df["price"] / 1000
    df["price"] = df["price"].astype(int)
    df = df[df['sum_qty'] > 0]
    return df

def to_csv(df: pd.DataFrame):
    output = f'ASFood_{datetime.strftime(datetime.now(),'%Y%m%d%H%M%S')}.csv'
    df.to_csv(output, index=False)

def load_with_index_mapping(filepath: str, source: str, 
                            filtered_date: Optional[Union[str, date, datetime]] = None, type = None, datetime_format = "%Y-%m-%d %H:%M") -> pd.DataFrame:
    mapping: dict = shipped_order_index_mappings[source]

    # read only needed columns
    usecols = list(mapping.keys())

    kwargs = {}
    if mapping.get('sheet_name') is not None:
        kwargs.update({'sheet_name': mapping.get('sheet_name')})
        usecols.remove('sheet_name')
    if mapping.get('skiprows') is not None:
        kwargs.update({'skiprows': mapping.get('skiprows')})
        usecols.remove('skiprows')
    
    df = pd.read_excel(filepath, usecols=usecols,  converters={0: str}, **kwargs) if filepath.endswith(("xlsx", "xls")) else pd.read_csv(filepath, usecols=usecols, converters={0: str}, **kwargs)

    # rename by mapping
    df.columns = [mapping[idx] for idx in usecols]

    df['order_id'] = df['order_id'].str.strip()

    # normalize datetime columns
    for col in df.columns:
        if col in datetime_fields and col in df:
            df[col] = pd.to_datetime(
                df[col].astype(str).str.strip(),
                errors="raise",
                format=datetime_format,
            )

    # filter by shipped_time if requested
    if filtered_date is not None:
        if isinstance(filtered_date, date) and not isinstance(filtered_date, datetime):
            target_date = filtered_date
        else:
            target_date = pd.to_datetime(filtered_date, dayfirst=True, errors="raise").date()

        if "shipped_time" not in df.columns:
            return df.iloc[0:0]

        df = df[df["shipped_time"].dt.date == target_date].copy()

    if type is not None:
        df = df[df["type"] == "Order"]

    df.insert(0, 'channel', source.split('_')[0])
    return df



def calculate_cost_of_sales(df: pd.DataFrame, price_df: pd.DataFrame) -> pd.DataFrame:
    if "seller_sku" in df.columns and "qty" in df.columns:
        df = df.merge(price_df, on="seller_sku", how="left")
        df["cost_of_sales"] = df["qty"] * (df["price"].fillna(0) + df["cover_bag"].fillna(0) + df["box_stamp"].fillna(0))
    return df

def add_platform_fee(df: pd.DataFrame) -> pd.DataFrame:
    fee_cols = ['platform_fixed_fee', 'platform_service_fee', 'platform_payment_fee']
    # keep only the columns that actually exist in df
    existing_cols = [col for col in fee_cols if col in df.columns]

    if existing_cols:  # if at least one fee column is present
        df["platform_fee"] = df[existing_cols].sum(axis=1, skipna=True) + 1620
    else:
        # if none of the columns exist, set platform_fee = 0
        df["platform_fee"] = 0

    return df



def safe_groupby_sum(df: pd.DataFrame, group_cols: list, sum_cols: list) -> pd.DataFrame:
    existing_group_cols = [col for col in group_cols if col in df.columns]
    existing_sum_cols = [col for col in sum_cols if col in df.columns]

    if not existing_group_cols:
        raise ValueError("None of the specified groupby columns exist in the DataFrame.")
    if not existing_sum_cols:
        raise ValueError("None of the specified sum columns exist in the DataFrame.")

    return df.groupby(existing_group_cols, as_index=False)[existing_sum_cols].sum()

def apply_seller_voucher_n_discount(df: pd.DataFrame) -> pd.DataFrame:
    if "seller_voucher" in df.columns and "after_discount_amount" in df.columns:
        df["after_discount_amount"] = df["after_discount_amount"] - df["seller_voucher"].fillna(0)
    if "seller_discount" in df.columns and "after_discount_amount" in df.columns:
        df["after_discount_amount"] = df["after_discount_amount"] - df["seller_discount"].fillna(0)
    return df


def transform_order_data(df: pd.DataFrame) -> pd.DataFrame:
    df = calculate_cost_of_sales(df, get_seller_sku_price())

    df = add_platform_fee(df)

    group_cols = ["channel", "order_id", "shipped_time", "seller_voucher", "platform_fee"]
    sum_cols = ["cost_of_sales", "seller_discount", "after_discount_amount"]
    df = safe_groupby_sum(df, group_cols, sum_cols)

    df = apply_seller_voucher_n_discount(df)

    return df


def transform_to_order_model(df: pd.DataFrame, schema_type: Type[OrderBase] = OrderCreate) -> List[OrderBase]:
    orders = []
    for i, row in df.iterrows():
        try:
            order_data = schema_type(**row.to_dict())
            orders.append(order_data)
        except Exception as e:
            print(f"Row {i} failed validation: {e}")
    return orders

def extract_order_details(df: pd.DataFrame) -> list[OrderDetailCreate]:
    """
    Extract valid line-item records from a raw (pre-aggregation) DataFrame.

    A valid row must have:
      - order_id: non-null, non-empty after stripping whitespace
      - seller_sku: non-null, non-empty after stripping whitespace
      - qty: castable to int and >= 1
    """
    required = {"order_id", "seller_sku", "qty"}
    if not required.issubset(df.columns):
        return []

    details = []
    for _, row in df.iterrows():
        try:
            order_id   = str(row["order_id"]).strip()
            seller_sku = str(row["seller_sku"]).strip()
            qty        = int(row["qty"])

            if not order_id or not seller_sku or qty < 1:
                continue

            details.append(OrderDetailCreate(
                order_id=order_id,
                seller_sku=seller_sku,
                qty=qty,
            ))
        except (ValueError, TypeError):
            continue

    return details


def insertOrUpdateOrders(sp_filter, tts_filter, filtered_date: Optional[Union[str, date, datetime]] = None):
    sp_files = glob.glob(sp_filter)
    tts_files = glob.glob(tts_filter)
    
    try:
        for sp in sp_files:
            df = load_with_index_mapping(sp, 'sp', filtered_date)

            # --- NEW: extract and upsert order details ---
            try:
                details = extract_order_details(df)
                upsert_order_details(details)
            except Exception as e:
                print(f"[order-details] SP detail upsert failed for {sp}: {e}")
            # --- END NEW ---

            df = transform_order_data(df)
            sp_orders = transform_to_order_model(df)
            upsert_orders(sp_orders)
            shutil.move(os.path.join(sp), os.path.join('backup', sp))

        for tts in tts_files:
            df = load_with_index_mapping(tts, 'tts', filtered_date, datetime_format="%d/%m/%Y %H:%M:%S")

            # --- NEW: extract and upsert order details ---
            try:
                details = extract_order_details(df)
                upsert_order_details(details)
            except Exception as e:
                print(f"[order-details] TTS detail upsert failed for {tts}: {e}")
            # --- END NEW ---

            df = transform_order_data(df)
            tts_orders = transform_to_order_model(df)
            upsert_orders(tts_orders)
            shutil.move(os.path.join(tts), os.path.join('backup', tts))

    except Exception as e:
        print(e)    

        
def insertOrUpdateEarnings(sp_filter, tts_filter, filtered_date: Optional[Union[str, date, datetime]] = None, type = None):
    sp_files = glob.glob(sp_filter)
    tts_files = glob.glob(tts_filter)
    
    try:
        for sp in sp_files:
            df = load_with_index_mapping(sp, 'sp_income', filtered_date, datetime_format="%Y-%m-%d %H:%M:%S")
            
            mask = df['type'] == 'Điều chỉnh'
            df.loc[mask, 'order_id'] = df.loc[mask, 'detail'].apply(
                lambda x: x.split(':')[1].strip().split(' ')[0].strip() if ':' in x else '-'
            )

            sp_orders = transform_to_order_model(df, schema_type=OrderUpdate)
            update_earnings(sp_orders)
            shutil.move(os.path.join(sp), os.path.join('backup', sp))

        for tts in tts_files:
            df = load_with_index_mapping(tts, 'tts_income', filtered_date, type, datetime_format="%Y/%m/%d")
            tts_orders = transform_to_order_model(df, schema_type=OrderUpdate)
            update_earnings(tts_orders)
            shutil.move(os.path.join(tts), os.path.join('backup', tts))

    except Exception as e:
        print(e)    


if __name__ == "__main__":
    # filtered_date = datetime.now() + timedelta(-1)
    filtered_date = None
    if not os.path.exists('backup'):
        os.mkdir('backup')

    insertOrUpdateOrders(sp_filter='Order.shipping*.xlsx', tts_filter='Shipped order*.csv', filtered_date=filtered_date)
    insertOrUpdateEarnings(sp_filter='my_balance_transaction_report.shopee*.xlsx', tts_filter='income_*.xlsx', type='Order')