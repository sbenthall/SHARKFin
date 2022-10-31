import sys
sys.path.append('..')

import argparse
from datetime import datetime
import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)
from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType
# import sharkfin.hark_portfolio_agents as hpa
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

from sharkfin.markets.ammps import ClientRPCMarket
from sharkfin.broker import *
from sharkfin.expectations import *
from sharkfin.population import *
from sharkfin.simulation import *

from simulate.parameters import (
    agent_population_params,
    approx_params,
    continuous_dist_params,
)


parser = argparse.ArgumentParser()
parser.add_argument("save_as", help="The name of the output for sim_stats")
parser.add_argument("-t",
                    "--tag", type=str,
                    help="a string tag to be added to the output files")

timestamp_start = datetime.now().strftime("%Y-%b-%d_%H:%M")

### Configuring the agent population

parameter_dict = agent_population_params | continuous_dist_params
parameter_dict["AgentCount"] = 1

def build_population(agent_type, parameters, rng = None, dphm = 1500):
    pop = AgentPopulation(agent_type(), parameters, rng = rng, dollars_per_hark_money_unit=dphm)
    pop.approx_distributions(approx_params)
    pop.parse_params()

    pop.create_distributed_agents()
    pop.create_database()
    pop.solve_distributed_agents()

    pop.solve(merge_by=["RiskyAvg", "RiskyStd"])

    # initialize population model
    pop.init_simulation()

    return pop

def run_simulation(
    agent_parameters,
    a = None,
    q = None,
    r = 1,
    fm = None,
    market = None,
    dphm=1500,
    rng = None):

    # initialize population
    pop = build_population(
        SequentialPortfolioConsumerType,
        agent_parameters,
        rng = rng,
        dphm = dphm
        )

    # Initialize the financial model
    fm = FinanceModel() if fm is None else fm

    fm.calculate_risky_expectations()
    agent_parameters.update(fm.risky_expectations())

    # Initialize the population model
    pop.init_simulation()

    attsim = AttentionSimulation(pop, fm, a = a, q = q, r = r, market = market)
    attsim.simulate()

    return attsim.data(), attsim.sim_stats(), attsim.history


if __name__ == '__main__':
    # requires market server to be running
    dphm = int(os.environ['BROKERSCALE']) if 'BROKERSCALE' in os.environ else 1500
    host = os.environ['RPCHOST'] if 'RPCHOST' in os.environ else 'localhost'
    queue = os.environ['RPCQUEUE'] if 'RPCQUEUE' in os.environ else 'rpc_queue'

    market = ClientRPCMarket(host=host, queue_name=queue)
    
    data, sim_stats, history = run_simulation(parameter_dict, a=0.2, q=1, r=4, market=market, dphm=dphm)

    with open(f'{args.save_as}.txt', 'w+') as f:
        f.write(str(sim_stats))

    # df.to_csv(f'{args.save_as}.csv')

    history_df = pd.DataFrame(dict([(k,pd.Series(v)) for k,v in history.items()]))
    history_df.to_csv(f'{args.save_as}_history.csv')

    data.to_csv(f'{args.save_as}_data.csv')

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(sim_stats)

