import azure_storage
import io
import os
import pandas as pd
import re

tre = re.compile("pnl/LMtransactions_SD(\d+)BL(\d+)SL(\d+).csv")

files = azure_storage.list_blobs(name_starts_with="pnl/")

def tre_data(filename):

    match = tre.match(filename['name'])

    # just some arbitary output...
    if match[1] == match[2] or match[1] == match[3]:
        print("Procesing " + filename['name'])

    message = None

    try:
        tr_data = azure_storage.download_blob(filename)
        df = pd.read_csv(
            io.StringIO(tr_data),
            delimiter='\t'
        )
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
        message = f"{str(e)}"
        final_price = None

    return {
        "seed" : match[1],
        "buy limit" : match[2],
        "sell limit" : match[3],
        "final price" : final_price,
        "message" : message
    }

records = [tre_data(fn) for fn in files]

tdf = pd.DataFrame.from_records(records)

tdf.to_csv("all_pnl_transaction_records.csv")
