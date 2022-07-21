import sys
sys.path.append('..')

import argparse
from datetime import datetime
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)

from math import exp
import os
import pandas as pd

from sharkfin.markets.ammps import ClientRPCMarket
from sharkfin.population import AgentPopulation
from sharkfin.simulation import CalibrationSimulation
from sharkfin.expectations import FinanceModel

parser = argparse.ArgumentParser()
parser.add_argument("save_as", help="The name of the output for sim_stats")
parser.add_argument("-t",
                    "--tag", type=str,
                    help="a string tag to be added to the output files")
parser.add_argument('-q', '--queue', help='name of rabbitmq queue', default='rpc_queue')
parser.add_argument('-r', '--rhost', help='rabbitmq server location', default='localhost')

parser.add_argument('-b', '--buysize', help='buy size to shock', default=0)
parser.add_argument('-s', '--sellsize', help='sell size to shock', default=0)
parser.add_argument('-p', '--pad', help='number of days to pad market', default=31)

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
    dphm=1500,
    buy=0,
    sell=0,
    pad=30):

    # initialize population
    pop = AgentPopulation(agent_parameters, dist_params, 5)

    # Initialize the population model
    pop.init_simulation()

    sim = CalibrationSimulation(pop, FinanceModel, a = a, q = q, r = r, market = market)
    
    sim.simulate(pad, buy_sell_shock=(buy, sell))

    return sim.data(), sim.history

def env_param(name, default):
    return os.environ[name] if name in os.environ else default


if __name__ == '__main__':
    args = parser.parse_args()

    # requires market server to be running
    # dphm = int(env_param('BROKERSCALE', 1500))
    # host = env_param('RPCHOST', 'localhost')
    # queue = env_param('RPCQUEUE', 'rpc_queue')
    host = args.rhost
    queue = args.queue

    buy = int(args.buysize)
    sell = int(args.sellsize)
    pad = int(args.pad) - 1

    market = ClientRPCMarket(host=host, queue_name=queue)

    data, history = run_simulation(agent_parameters, dist_params, 4, 
                                   a=0.2, q=4, r=4, 
                                   market=market, 
                                   dphm=1500, 
                                   buy=buy, 
                                   sell=sell, 
                                   pad=pad)

    history_df = pd.DataFrame(dict([(k,pd.Series(v)) for k,v in history.items()]))
    history_df.to_csv(f'{args.save_as}_history.csv')

    data.to_csv(f'{args.save_as}_data.csv')

