import argparse
from datetime import datetime
import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)
import hark_portfolio_agents as hpa
from itertools import product
import json
from math import exp
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import math
import os
import pandas as pd
import sys
import time
import uuid
import yaml

parser = argparse.ArgumentParser()
parser.add_argument("config", help="The name of a config file.")
parser.add_argument("-t",
                    "--tag", type=str,
                    help="a string tag to be added to the output files")


with open('config_cloud.yml', 'r') as stream:
    config = yaml.safe_load(stream)

AZURE = config['azure']

if AZURE:
    import azure_storage

timestamp_start = datetime.now().strftime("%Y-%b-%d_%H:%M")

### Configuring the agent population

dist_params = {
    'CRRA' : {'bot' : 2, 'top' : 10, 'n' : 3}, # Chosen for "interesting" results
    'DiscFac' : {'bot' : 0.936, 'top' : 0.978, 'n' : 2} # from CSTW "MPC" results
}

# Get empirical data from Sabelhaus and Song
ssvp = sabelhaus_song_var_profile()

# Assume all the agents are 40 for now.
# We will need to make more coherent assumptions about the timing and age of the population later.
# Scaling from annual to quarterly
idx_40 = ssvp['Age'].index(40)

### parameters shared by all agents
agent_parameters = {
    'aNrmInitStd' : 0.0,
    'LivPrb' : [0.98 ** 0.25],
    'PermGroFac': [1.01 ** 0.25],
    'pLvlInitMean' : 1.0, # initial distribution of permanent income
    'pLvlInitStd' : 0.0,
    'Rfree' : 1.0,
    'TranShkStd' : [ssvp['TranShkStd'][idx_40] / 2],  # Adjust non-multiplicative shock to quarterly
    'PermShkStd' : [ssvp['PermShkStd'][idx_40] ** 0.25]
}

def run_simulation(
    agent_parameters,
    dist_params,
    n_per_class,
    a = None,
    q = None,
    r = 1,
    fm = None,
    market = None,
    dphm=1500):

    # initialize population
    pop = hpa.AgentPopulation(agent_parameters, dist_params, n_per_class)

    # Initialize the financial model
    fm = hpa.FinanceModel() if fm is None else fm

    fm.calculate_risky_expectations()
    agent_parameters.update(fm.risky_expectations())

    # Initialize the population model
    pop.init_simulation()

    attsim = hpa.AttentionSimulation(pop, fm, a=a, q=q, r=r, market=market, dphm=dphm)
    attsim.simulate()

    return attsim.sim_stats()

def sample_simulation(args):
    """
    args: attention, dividend_ror, dividend_std, mock, sample, dollars_per_hark_money_unit
    """
    print(f"New case: {args}")

    case_id = args[0]

    attention = args[1][0]
    dividend_ror = args[1][1]
    dividend_std = args[1][2]
    mock = args[1][3]
    p1 = args[1][4]
    p2 = args[1][5]
    delta_t1 = args[1][6]
    delta_t2 = args[1][7]
    sample = args[1][8]
    config = args[1][9]
    dollars_per_hark_money = args[1][10]


    # super hack
    if not mock:
        time.sleep((attention + dividend_ror) / 100000)
        time.sleep(sample / 1000000)
    np.random.seed()

    # Initialize the financial model
    fm = hpa.FinanceModel(
        dividend_ror = dividend_ror,
        dividend_std = dividend_std,
        p1 = p1,
        p2 = p2,
        delta_t1 = delta_t1,
        delta_t2 = delta_t2
    )

    if mock:
        market = hpa.MockMarket()
    else:
        market = hpa.MarketPNL(
            sample = sample,
            seed_limit = config['seed_limit']
        )

    try:
        record = run_simulation(
            agent_parameters,
            dist_params,
            config['pop_n'],
            a = attention,
            q = config['q'],
            r = config['r'],
            fm = fm,
            market = market,
            dphm=dollars_per_hark_money
        )


        print(record)
        stat_path = os.path.join(
            "out",
            f"simstat-{timestamp_start}-c{case_id}.csv"
        )
        record_df = pd.DataFrame.from_records([record])
        #record_df.to_csv(stat_path)

        return record

    except Exception as e:
        return {
            "error" : e,
            'attention' : attention,
            'dividend_ror' : dividend_ror,
            'dividend_std' : dividend_std,
            'mock' : mock,
            'p1' : p1,
            'p2' : p2,
            'delta_t1' : delta_t1,
            'delta_t2' : delta_t2,
            'sample' : sample
        }


def main():
    args = parser.parse_args()

    config_path = args.config

    print(args.config)
    print(args.tag)

    if not os.path.exists(config_path):
        config = azure_storage.download_blob(config_path, write = True)

    with open(config_path, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    samples = range(config['data_n'])

    pool = multiprocessing.Pool()

    cases = product(
        config['attention_range'],
        config['dividend_ror_range'],
        config['dividend_std_range'],
        config['mock_range'],
        config['p1_range'],
        config['p2_range'],
        config['delta_t1_range'],
        config['delta_t2_range'],
        samples,
        [config],
        config['dollars_per_hark_money_unit']
        )

    ### Update the meta document

    meta = {
        'start' : timestamp_start,
    }
    meta.update(config)

    filename_stamp = timestamp_start +"-" + str(uuid.uuid4())[:4]
    if args.tag:
        tag = args.tag.lstrip() + "-"
    else:
        tag = ""

    if AZURE:
        config_fn = f"{tag}config-{filename_stamp}.yml"
        path = "."

        azure_storage.upload_file(
            config_fn,
            local_file_name = config_path
        )

    print("Running parallel simulations")
    records = pool.map(sample_simulation, enumerate(cases))
    pool.close()

    print("Closing pool, attempting to upload data.")

    good_records = [r for r in records if 'error' not in r]
    bad_records = [r for r in records if 'error' in r]

    data = pd.DataFrame.from_records(good_records)

    error_data = pd.DataFrame.from_records(bad_records)

    timestamp_end = datetime.now().strftime("%Y-%b-%d_%H:%M")

    ### Update the meta document

    meta.update({'end' : timestamp_end})

    meta_fn = f'{tag}meta-{filename_stamp}.json'

    if AZURE:
        azure_storage.json_to_blob(meta, path, meta_fn)
    else:
        local_path = os.path.join(path, meta_fn)
        # trying to overwrite here
        with open(local_path, 'w') as json_file:
            json.dump(meta, json_file)

    path = "out"
    study_fn = f"{tag}study-{filename_stamp}.csv"
    error_fn = f"{tag}errors-{filename_stamp}.csv"
    if AZURE:
        azure_storage.dataframe_to_blob(
            data, path, study_fn
        )
        azure_storage.dataframe_to_blob(
            error_data, path, error_fn
        )
    else:
        data.to_csv(os.path.join(path,study_fn))
        error_data.to_csv(os.path.join(path,error_fn))

    print(f"Completed with data upload. {len(records)} records.")


if __name__ == "__main__":
    main()
