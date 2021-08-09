import os
import pandas as pd
import re

tre = re.compile("LMtransactions_SD(\d+)BL(\d+)SL(\d+).csv")

files = os.listdir('logs')

transactions = [f for f in files if 'LMtransactions' in f]

def tre_data(filename):
    match = tre.match(filename)

    message = None
    
    try:
        df = pd.read_csv(filename, delimiter = "\t")


        prices = df['TrdPrice']

        if len(prices.index) == 0:
            ## BUG FIX HACK
            print("ERROR in PNL script: zero transactions.")
            final_price = None
            message = "Zero transactions"
        else:
            final_price = prices[prices.index.values[-1]]
    except Exception as e:
        print(e)
        message = "No columns found"
        final_price = None

    return {
        "seed" : match[1],
        "buy limit" : match[2],
        "sell limit" : match[3],
        "final price" : final_price,
        "message" : message
    }

records = [tre_data(fn) for fn in transactions]

tdf = pd.DataFrame.from_records(records)

tdf.to_csv("all_pnl_transaction_records.csv")
