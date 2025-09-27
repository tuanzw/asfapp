import pandas as pd
import csv
import shutil
import os
from datetime import datetime

from logger import logger



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
        converters={0: str, 1: float}
    )
    return df


def calculate_amount(df_order, df_master) -> pd.DataFrame:
    df = pd.merge(df_order, df_master, on="seller_sku", how="outer")
    df = df.fillna(0).astype({"sp_qty": int, "tts_qty": int, "sum_qty": int})
    df["amount"] = df["sum_qty"] * df["price"]

    # Update 'amount' for hoanh_thanh_500g
    mask = df['seller_sku'] == 'hoanh_thanh_500g'
    df.loc[mask, 'amount'] = df.loc[mask, 'sum_qty'] * df.loc[mask, 'price'] - (df.loc[mask, 'sum_qty'] // 20) * 10

    total_amount = df["amount"].sum()
    df = df.rename(columns={'amount': f'amount: {total_amount}'})
    df = df[df['sum_qty'] > 0]
    return df

def to_csv(df: pd.DataFrame):
    output = f'ASFood_{datetime.strftime(datetime.now(),'%Y%m%d%H%M%S')}.csv'
    df.to_csv(output, index=False)

if __name__ == "__main__":
    # df_order = get_qty('Order.toship.20250826_20250925 (1).xlsx', 'To Ship order-2025-09-25-21_15.csv')
    # df_master = get_seller_sku_price()
    # df = calculate_amount(df_order, df_master)
    # to_csv(df)
    # print(df)
    print(get_qty_tts('To Ship order-2025-09-27-13_18.csv'))