import sys
sys.path.append('..')

import argparse
from datetime import datetime
import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)
import sharkfin.hark_portfolio_agents as hpa
from itertools import product
import json
from math import exp
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import math
import os
import pandas as pd
import time
import uuid
import yaml
import pprint

parser = argparse.ArgumentParser()
parser.add_argument("save_as", help="The name of the output for sim_stats")
parser.add_argument("-t",
                    "--tag", type=str,
                    help="a string tag to be added to the output files")


with open('config_cloud.yml', 'r') as stream:
    config = yaml.safe_load(stream)

AZURE = config['azure']

if AZURE:
    import sharkfin.azure_storage

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
    pop = hpa.AgentPopulation(agent_parameters, dist_params, 5)

    # Initialize the financial model
    fm = hpa.FinanceModel() if fm is None else fm

    fm.calculate_risky_expectations()
    agent_parameters.update(fm.risky_expectations())

    # Initialize the population model
    pop.init_simulation()

    attsim = hpa.AttentionSimulation(pop, fm, a = a, q = q, r = r, market = market)
    attsim.simulate()

    return attsim.data(), attsim.sim_stats(), attsim.history


if __name__ == '__main__':
    # requires market server to be running
    # market = hpa.ClientRPCMarket(
    #     seed_limit = 150
    # )
    market = hpa.MockMarket()
    args = parser.parse_args()

    if "BROKERSCALE" in os.environ:
        dphm = int(os.environ["BROKERSCALE"])
    else:
        dphm = 1500
    
    data, sim_stats, history = run_simulation(agent_parameters, dist_params, 4, a=0.2, q=4, r=60, market=market, dphm=dphm)

    with open(f'{args.save_as}.txt', 'w+') as f:
        f.write(str(sim_stats))

    # df.to_csv(f'{args.save_as}.csv')

    history_df = pd.DataFrame(dict([(k,pd.Series(v)) for k,v in history.items()]))
    history_df.to_csv(f'{args.save_as}_history.csv')

    data.to_csv(f'{args.save_as}_data.csv')

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(sim_stats)

