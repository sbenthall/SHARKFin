import sys
sys.path.append('..')

import argparse
from datetime import datetime
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)
from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType
from simulate.parameters import (
    agent_population_params,
    approx_params,
    continuous_dist_params,
)

import json
from math import exp
import numpy as np
import os
import pandas as pd

from sharkfin.markets import MockMarket
from sharkfin.markets.ammps import ClientRPCMarket
from sharkfin.population import AgentPopulation
from sharkfin.simulation import AttentionSimulation, CalibrationSimulation
from sharkfin.expectations import FinanceModel, UsualExpectations


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


parser = argparse.ArgumentParser()
## TODO: Grid parameters?
parser.add_argument("save_as", help="The name of the output for sim_stats")
parser.add_argument("-t",
                    "--tag", type=str,
                    help="a string tag to be added to the output files",
                    default='')

# General simulation arguments
parser.add_argument('-d', '--seed', help='random seed', default=0)
parser.add_argument('--quarters', help='number of quarters', default=2)
parser.add_argument('--runs', help='runs per simulation', default = 60)

# Population parameters
parser.add_argument('--popn', help='Population:number of agents per population class', default=25)

# Specific to AttentionSimulation
parser.add_argument('--attention', help='AttentionSimulation: chance that agent pays attention to the market on a day', default = 0.05)
parser.add_argument('--dphm', help='AttentionSimulation: dollars per HARK money unit', default = 1500)

# General market arguments
# TODO market_type: MockMarket # this determines which Market class to use.
parser.add_argument('--market', help='Market: name of Market class', default = "MockMarket")

# Choose which simulation
parser.add_argument('--simulation', help='Which simulation. Options: Attention, Calibration', default = "Attention")

parser.add_argument('--dividend_growth_rate', help='Market: daily average growth rate of the dividend', default = 1.000628)
parser.add_argument('--dividend_std', help='Market: daily standard deviation fo the dividend', default = 0.011988)

# Specific to RabbitMQ AMMPS Market 
parser.add_argument('-q', '--queue', help='RabbitMQ: name of rabbitmq queue', default='rpc_queue')
parser.add_argument('-r', '--rhost', help='RabbitMQ: rabbitmq server location', default='localhost')

# Expectations module
parser.add_argument('--expectations', help='Expectations: name of Expectations class. Options: FinanceModel, UsualExpectations', default = "FinanceModel")

# Memory-based FinanceModel arguments
parser.add_argument('--p1', help='FinanceModel: memory parameter p1', default=0.1)
parser.add_argument('--p2', help='FinanceModel: memory parameter p2', default=0.1)
parser.add_argument('--d1', help='FinanceModel: memory parameter d1', default=60)
parser.add_argument('--d2', help='FinanceModel: memory parameter d2', default=60)

# Chum parameters
parser.add_argument('--buysize', help='Chum: buy size to shock', default=0)
parser.add_argument('--sellsize', help='Chum: sell size to shock', default=0)
parser.add_argument('--pad', help='Nmber of days to burn in the market', default=None)


timestamp_start = datetime.now().strftime("%Y-%b-%d_%H:%M")

### Configuring the agent population

parameter_dict = agent_population_params | continuous_dist_params
parameter_dict["AgentCount"] = 1

def build_population(agent_type, parameters, rng = None, dphm = 1500):
    pop = AgentPopulation(agent_type(), parameters, rng = rng, dollars_per_hark_money_unit = dphm)
    pop.approx_distributions(approx_params)
    pop.parse_params()

    pop.create_distributed_agents()
    pop.create_database()
    pop.solve_distributed_agents()

    pop.solve(merge_by=["RiskyAvg", "RiskyStd"])

    # initialize population model
    pop.init_simulation()

    return pop

def run_attention_simulation(
    agent_parameters,
    a = None,
    q = None,
    r = 1,
    market = None,
    fm = None,
    dphm = 1500,
    p1 = 0.1,
    p2 = 0.1,
    d1 = 60,
    d2 = 60,
    rng = None,
    pad = None,
    seed = None
    ):

    # initialize population
    pop = build_population(
        SequentialPortfolioConsumerType,
        agent_parameters,
        rng = rng,
        dphm = dphm
        )

    sim = AttentionSimulation(
        pop, fm, a = a, q = q, r = r, market = market, rng = rng, seed = seed,
        fm_args = {
            'p1' : p1,
            'p2' : p2,
            'delta_t1' : d1,
            'delta_t2' : d2
        })
    
    sim.simulate(burn_in = pad)

    return sim.daily_data(), sim.sim_stats(), sim.history, sim.pop.class_stats()


def run_chum_simulation(
    agent_parameters,
    a = None,
    q = None,
    r = 1,
    fm = None,
    market = None,
    dphm=1500,
    buy=0,
    sell=0,
    pad=30,
    seed = None
    ):

    # initialize population
    pop = build_population(
        SequentialPortfolioConsumerType,
        agent_parameters,
        dphm = dphm,
        rng = rng
        )

    sim = CalibrationSimulation(a = a, q = q, r = r, market = market)
    
    sim.simulate(burn_in=pad, buy_sell_shock=(buy, sell))

    sim_stats = sim.sim_stats()
    sim_stats['seed'] = seed

    return sim.daily_data(), sim_stats, sim.history, pd.DataFrame.from_records({}) #, sim.pop.class_stats()

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
    expectations_class_name = str(args.expectations)
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

    ## Chum parameters
    buysize = int(args.buysize)
    sellsize = int(args.sellsize)
    pad = int(args.pad) - 1 if args.pad is not None else None


    print(" ".join([str(x) for x in [
        host,
        queue,
        seed,
        popn,
        quarters,
        runs,
        market_class_name,
        expectations_class_name,
        dividend_growth_rate,
        dividend_std,
        attention,
        dphm,
        p1,
        p2,
        d1,
        d2,
        buysize,
        sellsize,
        pad
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
        print(f"{market_class_name} is not a known market class. Using MockMarket.")
        market_class = MockMarket

    market = market_class(**market_args)

    expectations_class = None

    if expectations_class_name == "FinanceModel":
        expectations_class = FinanceModel
    elif expectations_class_name == "UsualExpectations":
        expectations_class = UsualExpectations
    else:
        print(f"{expectations_class_name} is not a known Expectations class. Using UsualExpectations.")
        expectations_class = UsualExpectations

    sim_method = None

    if args.simulation == 'Attention':
        data, sim_stats, history, class_stats = run_attention_simulation(
            parameter_dict,
            a = attention, 
            q = quarters, 
            r= runs,
            market = market,
            fm = expectations_class,
            dphm = dphm,
            p1 = p1,
            p2 = p2,
            d1 = d1,
            d2 = d2,
            rng = rng,
            pad = pad,
            seed = seed
        )
    elif args.simulation == 'Calibration':
        data, sim_stats, history, class_stats = run_chum_simulation(
            parameter_dict,
            a = attention, q = quarters, r = runs, 
            market=market, 
            dphm=dphm, 
            buy= buysize, 
            sell= sellsize, 
            pad= pad,
            seed = seed
            )
    else:
        print(f"No known --simulation {args.simulation}. Valid options include: Attention, Calibration")

    history_df = pd.DataFrame(dict([(k,pd.Series(v)) for k,v in history.items()]))

    filename = args.save_as + ("-" + args.tag if args.tag != '' else '')

    try:
        history_df.to_csv(f'{filename}_history.csv')
    except:
        print("No usable history")

    try:
        class_stats.to_csv(f'{filename}_class_stats.csv')
    except:
        print("No usable class stats")

    with open(f'{filename}_sim_stats.txt', 'w+') as f:
        sim_stats['filename'] = filename
        f.write(json.dumps(sim_stats, cls=NpEncoder))

    try:
        data.to_csv(f'{filename}_data.csv')
    except:
        print("No usable daily data")


    print("Ending the run_any_simulation.py script")