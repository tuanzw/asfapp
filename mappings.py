shipped_order_index_mappings = {
    "sp": {
        0: 'order_id',
        13: 'shipped_time',
        19: 'seller_sku',
        24: 'seller_discount',
        26: 'qty',
        28: 'after_discount_amount',
        30: 'seller_voucher',
        49: 'platform_fixed_fee',
        50: 'platform_service_fee',
        51: 'platform_payment_fee',
    },
    "tts": {
        0: 'order_id',
        6: 'seller_sku',
        9: 'qty',
        14: 'seller_discount',
        15: 'after_discount_amount',
        27: 'shipped_time',
    },
    "tts_income": {
        0: 'order_id',
        1: 'type',
        3: 'settled_time',
        5: 'earning'
    },
    # "sp_income": {
    #     'sheet_name': 2,
    #     'skiprows': 2,
    #     1: 'type',
    #     2: 'order_id',
    #     8: 'settled_time',
    #     12: 'earning'
    # },
    "sp_income": {
        'skiprows': 17,
        0: 'settled_time',
        1: 'type',
        2: 'detail',
        3: 'order_id',
        5: 'earning',
    },
}

datetime_fields = {"shipped_time", "delivered_time", "settled_time"}