import sys
sys.path.append('..')

import argparse
from datetime import datetime
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)

from math import exp
import numpy as np
import os
import pandas as pd
import time
import uuid
import pprint

from sharkfin.markets import MockMarket
from sharkfin.markets.ammps import ClientRPCMarket
from sharkfin.population import AgentPopulation
from sharkfin.simulation import AttentionSimulation
from sharkfin.expectations import FinanceModel

parser = argparse.ArgumentParser()
## TODO: Grid parameters?
parser.add_argument("save_as", help="The name of the output for sim_stats")
parser.add_argument("-t",
                    "--tag", type=str,
                    help="a string tag to be added to the output files")

# General simulation arguments
parser.add_argument('-d', '--seed', help='random seed', default=0)
parser.add_argument('--popn', help='number of agents per population class', default=25)
parser.add_argument('--quarters', help='number of quarters', default=2)
parser.add_argument('--runs', help='runs per simulation', default = 60)

# Specific to AttentionSimulation
parser.add_argument('--attention', help='chance that agent pays attention to the market on a day', default = 0.05)
parser.add_argument('--dphm', help='dollars per HARK money unit', default = 1500)

# General market arguments
# TODO market_type: MockMarket # this determines which Market class to use.
parser.add_argument('--market', help='name of Market class', default = "MockMarket")
parser.add_argument('--dividend_growth_rate', help='daily average growth rate of the dividend', default = 1.000628)
parser.add_argument('--dividend_std', help='daily standard deviation fo the dividend', default = 0.011988)

# Specific to RabbitMQ AMMPS Market 
parser.add_argument('-q', '--queue', help='name of rabbitmq queue', default='rpc_queue')
parser.add_argument('-r', '--rhost', help='rabbitmq server location', default='localhost')

# Memory-based FinanceModel arguments
parser.add_argument('--p1', help='memory parameter p1', default=0.1)
parser.add_argument('--p2', help='memory parameter p2', default=0.1)
parser.add_argument('--d1', help='memory parameter d1', default=60)
parser.add_argument('--d2', help='memory parameter d2', default=60)


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
    popn = 5,
    a = None,
    q = None,
    r = 1,
    market = None,
    dphm=1500,
    p1 = 0.1,
    p2 = 0.1,
    d1 = 60,
    d2 = 60,
    rng = None
    ):

    # initialize population
    pop = AgentPopulation(agent_parameters, dist_params, popn, rng = rng)

    # Initialize the population model
    pop.init_simulation()

    sim = AttentionSimulation(
        pop, FinanceModel, a = a, q = q, r = r, market = market, dphm = dphm, rng = rng)
    
    sim.simulate()

    return sim.data(), sim.sim_stats(), sim.history

def env_param(name, default):
    return os.environ[name] if name in os.environ else default


if __name__ == '__main__':
    args = parser.parse_args()

    # General simulation arguments
    seed = int(args.seed)
    popn = int(args.popn)
    quarters = int(args.quarters)
    runs = int(args.runs)

    # General market arguments
    market_class_name = str(args.market)
    dividend_growth_rate = float(args.dividend_growth_rate)
    dividend_std = float(args.dividend_std)

    # Specific to AttentionSimulation
    attention = float(args.attention)
    dphm = int(args.dphm)

    # Memory-based FinanceModel arguments
    p1 = float(args.p1)
    p2 = float(args.p2)
    d1 = float(args.d1)
    d2 = float(args.d2)

    # Specific to RabbitMQ AMMPS Market 
    host = args.rhost
    queue = args.queue


    print(" ".join([str(x) for x in [
        host,
        queue,
        seed,
        popn,
        quarters,
        runs,
        market_class_name,
        dividend_growth_rate,
        dividend_std,
        attention,
        dphm,
        p1,
        p2,
        d1,
        d2
        ]]))

    # random number generator with seed
    rng = np.random.default_rng(seed)

    market_args = {
        'dividend_growth_rate' : dividend_growth_rate,
        'dividend_std' : dividend_std,
        'rng' : rng
    }

    market_class = None

    if market_class_name == "MockMarket":
        market_class = MockMarket
    elif market_class_name == "ClientRPCMarket":
        market_class = ClientRPCMarket
        market_args['queue_name'] = queue
        market_args['host'] = host
    else:
        print(f"{market_class_name} is not a know market class. Using MockMarket.")
        market_class = MockMarket

    market = market_class(**market_args)

    data, sim_stats, history = run_simulation(
        agent_parameters,
        dist_params,
        popn = popn, 
        a = attention, 
        q = quarters, 
        r= runs,
        market = market,
        dphm = dphm,
        p1 = p1,
        p2 = p2,
        d1 = d1,
        d2 = d2,
        rng = rng
        )

    history_df = pd.DataFrame(dict([(k,pd.Series(v)) for k,v in history.items()]))
    history_df.to_csv(f'{args.save_as}_history.csv')

    with open(f'{args.save_as}_sim_stats.txt', 'w+') as f:
        f.write(str(sim_stats))

    data.to_csv(f'{args.save_as}_data.csv')


