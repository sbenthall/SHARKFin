import azure_storage
import io
import os
import pandas as pd
import re
import argparse

prefix = " 004-48-attn-study"
blobs = azure_storage.list_blobs(name_starts_with=prefix)

def tre_data(blob):
    print(blob['name'])
    try:
        tr_data = azure_storage.download_blob(
            blob['name'], write=True
        )
        df = pd.read_csv(
            io.StringIO(tr_data)
        )
    except Exception as e:
        print(e)
        pass

    return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Study saved data from a simulation')
    parser.add_argument('--prefix', default=" 004-48-attn-study")
    args = parser.parse_args()

    dfs = [tre_data(blob) for blob in blobs]

    tdf = pd.concat(dfs)

    tdf.to_csv(f"{args.prefix.lstrip()}-all_records.csv")

