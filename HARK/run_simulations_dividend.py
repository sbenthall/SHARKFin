import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)
import hark_portfolio_agents as hpa
import logging
import math
from math import exp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math


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



## Configuring the parameter grid

sim_params = {
    "pop_n" : 25,
    "q" : 8,
    "r" : 10
}

data_n = 32 # 64

def run_simulation(agent_parameters, dist_params, n_per_class, a = None, q = None, r = 1, fm = None, market = None):

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

    return attsim.sim_stats()

def sample_simulation(dividend):
    records = []

    for i in range(data_n):
        # Initialize the financial model
        fm = hpa.FinanceModel(
            dividend_ror = dividend[0],
            dividend_std = dividend[1]
        )

        record = run_simulation(
            agent_parameters,
            dist_params,
            sim_params['pop_n'],
            # a = attention, ## This is what's changing
            fm = fm, ## this is what's changing
            q = sim_params['q'],
            r = sim_params['r'],
            market = hpa.MockMarket()
        )
        records.append(record)

    return pd.DataFrame.from_records(records)

import multiprocessing

pool = multiprocessing.Pool()

dividend_range = [
    (0.001, 0.001), (0.03, 0.001), (0.06, 0.001),
    (0.001, 0.01), (0.03, 0.01), (0.06, 0.01),
    (0.001, 0.02), (0.03, 0.02), (0.06, 0.02),
    ]
dfs = pool.map(sample_simulation, dividend_range)
pool.close()

data = pd.concat(dfs)

data.to_csv("dividend-study.csv")
