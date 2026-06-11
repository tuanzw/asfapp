import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Union, List, Type

import os, csv, glob, shutil
from schemas import *
from services import *

from mappings import shipped_order_index_mappings, datetime_fields


earning_index_mappings = {
    "sp_income": {
        'skiprows': 17,
        0: 'settled_time',
        1: 'type',
        2: 'detail',
        3: 'order_id',
        5: 'earning',
    },
    "tts_income": {
        0: 'order_id',
        1: 'type',
        3: 'settled_time',
        5: 'earning'
    },
}


def load_with_index_mapping(filepath: str, source: str, 
                            filtered_date: Optional[Union[str, date, datetime]] = None, type = None) -> pd.DataFrame:
    mapping: dict = earning_index_mappings[source]

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
                df[col],
                errors="raise",
                dayfirst=True
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


if __name__ == '__main__':
    df = load_with_index_mapping('my_balance_transaction_report.shopee.20251001_20251015.xlsx','sp')

    mask = df['type'] == 'Điều chỉnh'
    df.loc[mask, 'order_id'] = df.loc[mask, 'detail'].apply(
        lambda x: x.split(':')[1].strip().split(' ')[0].strip() if ':' in x else '-'
    )

    print(df)