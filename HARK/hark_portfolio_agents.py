import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
import HARK.ConsumptionSaving.ConsIndShockModel as cism
from HARK.core import distribute_params
from datetime import datetime
from HARK.distribution import Uniform
import io
import itertools
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import random
import seaborn as sns
from statistics import mean


import sys

sys.path.append('.')
## TODO configuration file for this value!
sys.path.append('../PNL/py')

import util as UTIL
import pnl as pnl

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

AZURE = True

if AZURE:
    import azure_storage


### Initializing agents

def update_return(dict1, dict2):
    """
    Returns new dictionary,
    copying dict1 and updating the values of dict2
    """
    dict3 = dict1.copy()
    dict3.update(dict2)

    return dict3

def distribute(agents, dist_params):
    """
    Distribue the discount rate among a set of agents according
    the distribution from Carroll et al., "Distribution of Wealth"
    paper.

    Parameters
    ----------

    agents: list of AgentType
        A list of AgentType

    dist_params:

    Returns
    -------
        agents: A list of AgentType
    """
 
    # This is hacky. Should streamline this in HARK.

    for param in dist_params:
        agents_distributed = [
            distribute_params(
                agent,
                param,
                dist_params[param]['n'],
                Uniform(
                    bot=dist_params[param]['bot'],
                    top=dist_params[param]['top']
                )
            )
            for agent in agents
        ]

        agents = [
            agent
            for agent_dist in agents_distributed
            for agent in agent_dist
        ]

        # should be unecessary but a hack to cover a HARK bug
        # https://github.com/econ-ark/HARK/issues/994
        for agent in agents:
            agent.assign_parameters(**{param : getattr(agent, param)})

    return agents

#####
#   AgentPopulation
#####

class AgentPopulation():
    """
    A class encapsulating the population of 'macroeconomy' agents.

    These agents will be initialized with a distribution of parameters,
    such as risk aversion and discount factor.

    Parameters
    ------------
 
    base_parameters: Dict
        A dictionary of parameters to be shared by all agents.
        These correspond to parameters of the HARK ConsPortfolioModel AgentType

    dist_params: dict of dicts
        A dictionary with [m] values. Keys are parameters.
        Values are dicts with keys: bot, top, n.
        These define a discretized uniform spread of values.

    n_per_class: int
        The values of dist_params define a space of n^m
        agent classes.
        This value is the number of agents [l] of each class to include in
        population.
        Total population will be l*n^m
    """
    agents = None
    base_parameters = None
    stored_class_stats = None
    dist_params = None

    def __init__(self, base_parameters, dist_params, n_per_class):
        self.base_parameters = base_parameters
        self.dist_params = dist_params
        self.agents = self.create_distributed_agents(self.base_parameters, dist_params, n_per_class)

    def class_stats(self, store = False):
        """
        Output the statistics for each class within the population.

        Currently limited to asset level in the final simulated period (aLvl_T)
        """
        # get records for each agent with distributed parameter values and wealth (asset level: aLvl)
        records = []

        for agent in self.agents:
            for i, aLvl in enumerate(agent.state_now['aLvl']):
                record = {
                    'aLvl' : aLvl,
                    'mNrm' : agent.state_now['mNrm'][i]
                }

                for dp in self.dist_params:
                    record[dp] = agent.parameters[dp]

                records.append(record)

        agent_df = pd.DataFrame.from_records(records)

        class_stats = agent_df.groupby(
            list(self.dist_params.keys())
        ).aggregate(['mean','std']).reset_index()

        cs = class_stats
        cs['label'] = round(cs['CRRA'],2)\
                      .apply(lambda x: f'CRRA: {x}, ') \
                      + round(cs['DiscFac'], 2)\
                      .apply(lambda x : f"DiscFac: {x}")
        cs['aLvl_mean'] = cs['aLvl']['mean']
        cs['aLvl_std'] = cs['aLvl']['std']
        cs['mNrm_mean'] = cs['mNrm']['mean']
        cs['mNrm_std'] = cs['mNrm']['std']

        if store:
            self.stored_class_stats = class_stats

        return class_stats

    def create_distributed_agents(self, agent_parameters, dist_params, n_per_class):
        """
        Creates agents of the given classes with stable parameters.
        Will overwrite the DiscFac with a distribution from CSTW_MPC.

        Parameters
        ----------
        agent_parameters: dict
            Parameters shared by all agents (unless overwritten).

        dist_params: dict of dicts
            Parameters to distribute agents over, with discrete Uniform arguments

        n_per_class: int
            number of agents to instantiate per class
        """
        num_classes = math.prod([dist_params[dp]['n'] for dp in dist_params])
        agent_batches = [{'AgentCount' : num_classes}] * n_per_class

        agents = [
            cpm.PortfolioConsumerType(
                **update_return(agent_parameters, ac)
            )
            for ac
            in agent_batches
        ]

        agents = distribute(agents, dist_params)

        for agent in agents:
            agent.seed = random.randint(0,10000)
            agent.reset_rng()

        return agents

    def init_simulation(self):
        """
        Sets up the agents with their state for the state of the simulation
        """
        for agent in self.agents:
            agent.track_vars += ['pLvl','mNrm','cNrm','Share','Risky']

            agent.assign_parameters(AdjustPrb = 1.0)
            agent.T_sim = 1000 # arbitrary!
            agent.solve()

            agent.initialize_sim()

            if self.stored_class_stats is None:
                agent.state_now['mNrm'][:] = 1.0
            else:
                idx = [agent.parameters[dp] for dp in self.dist_params] 
                mNrm = self.stored_class_stats.copy() \
                    .set_index([dp for dp in self.dist_params]) \
                    .xs((idx))['mNrm']['mean']
                agent.state_now['mNrm'][:] = mNrm

            agent.state_now['aNrm'] = agent.state_now['mNrm'] \
                                      - agent.solution[0].cFuncAdj(agent.state_now['mNrm'])
            agent.state_now['aLvl'] = agent.state_now['aNrm'] * agent.state_now['pLvl']


######
#   Math Utilities
######

def ror_quarterly(ror, n_q):
    """
    Convert a daily rate of return to a rate for (n_q) days.
    """
    return pow(1 + ror, n_q) - 1

def sig_quarterly(std, n_q):
    """
    Convert a daily standard deviation to a standard deviation for (n_q) days.

    This formula only holds for special cases (see paper by Andrew Lo), 
    but since we are generating the data we meet this special case.
    """
    return math.sqrt(n_q) * std

def lognormal_moments_to_normal(mu_x, std_x):
    """
    Given a mean and standard deviation of a lognormal distribution,
    return the corresponding mu and sigma for the distribution.
    (That is, the mean and standard deviation of the "underlying"
    normal distribution.)
    """
    mu = np.log(mu_x ** 2 / math.sqrt(mu_x ** 2 + std_x ** 2))

    sigma = math.sqrt(np.log(1 + std_x ** 2 / mu_x ** 2))

    return mu, sigma

def combine_lognormal_rates(ror1, std1, ror2, std2):
    """
    Given two mean rates of return and standard deviations
    of two lognormal processes (ror1, std1, ror2, std2),
    return a third ror/sigma pair corresponding to the
    moments of the multiplication of the two original processes.
    """
    mean1 = 1 + ror1
    mean2 = 1 + ror2

    mu1, sigma1 = lognormal_moments_to_normal(mean1, std1)
    mu2, sigma2 = lognormal_moments_to_normal(mean2, std2)

    mu3 = mu1 + mu2
    var3 = sigma1 **2 + sigma2 ** 2

    ror3 = math.exp(mu3 + var3 / 2) - 1
    sigma3 = math.sqrt((math.exp(var3) - 1) * math.exp(2 * mu3 + var3))

    return ror3, sigma3

######
#   Model classes used in the simulation
######

class FinanceModel():
    """
    A class representing the financial system in the simulation.

    Contains parameter values for:
      - the capital gains expectations function
      - the dividend
      - the risky asset expectations

    Contains data structures for tracking ROR and STD over time.
    """
    # Empirical data
    sp500_ror = 0.000628
    sp500_std = 0.011988

    # Simulation parameter
    days_per_quarter = 60

    # Expectation calculation parameters
    p1 = 0.1
    delta_t1 = 30

    a = - math.log(p1) / delta_t1

    p2 = 0.1
    delta_t2 = 60

    b = math.log(p2) / delta_t2

    # Quarterly dividend rate and standard deviation.
    dividend_ror = 0.03
    dividend_std = 0.01

    # Data structures. These will change over time.
    starting_price = 100
    prices = None
    ror_list = None

    expected_ror_list = None
    expected_std_list = None

    def add_ror(self, ror):
        self.ror_list.append(ror)
        asset_price = self.prices[-1] * (1 + ror)
        self.prices.append(asset_price)
        return asset_price

    def __init__(
        self,
        dividend_ror = None,
        dividend_std = None,
        p1 = None,
        p2 = None,
        delta_t1 = None,
        delta_t2 = None
        ):

        if dividend_ror:
            self.dividend_ror = dividend_ror

        if dividend_std:
            self.dividend_std = dividend_std

        if p1:
            self.p1 = p1

        if p2:
            self.p2 = p2
        
        if delta_t1:
            self.delta_t1 = delta_t1

        if delta_t2:
            self.delta_t2 = delta_t2

        self.prices = [self.starting_price]
        self.ror_list = []
        self.expected_ror_list = []
        self.expected_std_list = []

    def calculate_risky_expectations(self):
        """
        Compute the quarterly expectations for the risky asset based on historical return rates.

        In this implementation there are a number of references to:
          - paramters that are out of scope
          - data structures that are out of scope

        These should be bundled together somehow.

        NOTE: This MUTATES the 'expected_ror_list' and so in current design
        has to be called on a schedule... this should be fixed.
        """
        # note use of data store lists for time tracking here -- not ideal
        D_t = sum([math.exp(self.a * (l + 1)) for l in range(len(self.ror_list))])
        S_t = math.exp(self.b * (len(self.prices) - 1)) # because p_0 is included in this list.

        w_0 = S_t
        w_t = [(1 - S_t) * math.exp(self.a * (t+1)) / D_t for t in range(len(self.ror_list))]

        expected_ror = w_0 * self.sp500_ror + sum(
            [w_ror[0] * w_ror[1]
             for w_ror
             in zip(w_t, self.ror_list)])
        self.expected_ror_list.append(expected_ror)

        expected_std = math.sqrt(
            w_0 * pow(self.sp500_std, 2) \
            +  sum([w_ror_er[0] * pow(w_ror_er[1] - expected_ror, 2)
                    for w_ror_er
                    in zip(w_t, self.ror_list)]))
        self.expected_std_list.append(expected_std)

    def rap(self):
        """
        Returns the current risky asset price.
        """
        return self.prices[-1]

    def risky_expectations(self):
        """
        Return quarterly expectations for the risky asset.
        These are the average and standard deviation for the asset
        including both capital gains and dividends.
        """
        # expected capital gains quarterly
        ex_cg_q_ror = ror_quarterly(
            self.expected_ror_list[-1],
            self.days_per_quarter
        )
        ex_cg_q_std = sig_quarterly(
            self.expected_std_list[-1],
            self.days_per_quarter
        )

        # factor in dividend:
        cg_w_div_ror, cg_w_div_std = combine_lognormal_rates(
            ex_cg_q_ror,
            ex_cg_q_std,
            self.dividend_ror,
            self.dividend_std
        )

        market_risky_params = {
            'RiskyAvg': 1 + cg_w_div_ror,
            'RiskyStd': cg_w_div_std
        }

        return market_risky_params

    def reset(self):
        """
        Reset the data stores back to original value.
        """
        self.prices = [100]
        self.ror_list = []

        self.expected_ror_list = []
        self.expected_std_list = []



######
#   PNL Interface methods
######

class MarketPNL():
    """
    A wrapper around the Market PNL model with methods for getting
    data from recent runs.

    Parameters
    ----------
    config_file
    config_local_file

    """
    # Properties of the PNL market model
    netlogo_ror = -0.00052125
    netlogo_std =  0.0068

    simulation_price_scale = 0.25
    default_sim_price = 400

    # Empirical data -- redundant with FinanceModel!
    sp500_ror = 0.000628
    sp500_std = 0.011988

    # limits the seeds
    seed_limit = None

    # Storing the last market arguments used for easy access to most
    # recent data
    last_buy_sell = None
    last_seed = None

    seeds = None

    # config object for PNL
    config = None

    # sample - modifier for the seed
    sample = 0

    def __init__(
        self,
        sample = 0,
        config_file = "../PNL/macroliquidity.ini",
        config_local_file = "../PNL/macroliquidity_local.ini",
        seed_limit = None
    ):
        self.config = UTIL.read_config(
            config_file = config_file,
            config_local_file = config_local_file
        )

        self.sample = 0
        self.seeds = []

        if seed_limit is not None:
            self.seed_limit = seed_limit

    def run_market(self, seed = 0, buy_sell = 0):
        """
        Runs the NetLogo market simulation with a given
        configuration (config), a tuple with the quantities
        for the brokers to buy/sell (buy_sell), and
        optionally a random seed (seed)
        """
        if seed is None:
            seed_limit = self.seed_limit if self.seed_limit is not None else 3000
            seed = (np.random.randint(seed_limit) + self.sample) % seed_limit

        self.last_seed = seed
        self.last_buy_sell = buy_sell
        self.seeds.append(seed)

        pnl.run_NLsims(
            self.config,
            broker_buy_limit = buy_sell[0],
            broker_sell_limit = buy_sell[1],
            SEED = seed,
            use_cache = True
        )

    def get_transactions(self, seed = 0, buy_sell = (0,0)):
        """
        Given a random seed (seed)
        and a tuple of buy/sell (buy_sell), look up the transactions
        from the associated output file and return it as a pandas DataFrame.
        """
        logfile = pnl.transaction_file_name(
            self.config,
            seed,
            buy_sell[0],
            buy_sell[1]
        )

        # use run_market() first to create logs
        if os.path.exists(logfile):
            try:
                transactions = pd.read_csv(
                    logfile,
                    delimiter='\t'
                )
                return transactions
            except Exception as e:
                raise(Exception(f"Error loading transactions from local file: {e}"))
        elif AZURE:
            try:
                (head, tail) = os.path.split(logfile)
                remote_transaction_file_name = os.path.join("pnl", tail)
                csv_data = azure_storage.download_blob(remote_transaction_file_name)

                df = pd.read_csv(io.StringIO(csv_data), delimiter='\t')

                if len(df.columns) < 3:
                    raise Exception(f"transaction dataframe columns insufficent: {df.columns}")

                return df
            except Exception as e:
                raise(Exception(f"Azure loading {logfile} error: {e}"))

    def get_simulation_price(self, seed = 0, buy_sell = (0,0)):
        """
        Get the price from the simulation run.
        Returns None if the transaction file was empty for some reason.

        TODO: Better docstring
        """

        transactions = self.get_transactions(seed=seed, buy_sell = buy_sell)

        try:
            prices = transactions['TrdPrice']
        except Exception as e:
            raise Exception(
                f"get_simulation_price(seed = {seed}," +
                f" buy_sell = {buy_sell}) error: " + str(e)
                + f", columns: {transactions.columns}"
            )

        if len(prices.index) == 0:
            ## BUG FIX HACK
            print("ERROR in PNL script: zero transactions. Reporting no change")
            return None

        return prices[prices.index.values[-1]]


    def daily_rate_of_return(self, seed = None, buy_sell = None):
        ## TODO: Cleanup. Use "last" parameter in just one place.
        if seed is None:
            seed = self.last_seed

        if buy_sell is None:
            buy_sell = self.last_buy_sell

        last_sim_price = self.get_simulation_price(
            seed=seed, buy_sell = buy_sell
        )

        if last_sim_price is None:
            last_sim_price = self.default_sim_price

        ror = (last_sim_price * self.simulation_price_scale - 100) / 100

        # adjust to calibrated NetLogo to S&P500
        ror = self.sp500_std * (ror - self.netlogo_ror) / self.netlogo_std + self.sp500_ror

        return ror


class MockMarket(MarketPNL):
    """
    A wrapper around the Market PNL model with methods for getting
    data from recent runs.

    Parameters
    ----------
    config_file
    config_local_file

    """
    # Properties of the PNL market model
    netlogo_ror = 0.0
    netlogo_std = 0.025

    simulation_price_scale = 0.25
    default_sim_price = 400

    # Empirical data -- redundant with FinanceModel!
    sp500_ror = 0.000628
    sp500_std = 0.011988

    # Storing the last market arguments used for easy access to most
    # recent data
    last_buy_sell = None
    last_seed = None

    def __init__(
        self
    ):
        pass

    def run_market(self, seed = 0, buy_sell = 0):
        """
        Sample from a probability distribution
        """
        self.last_seed = seed
        self.last_buy_sell = buy_sell

    def get_simulation_price(self, seed = 0, buy_sell = (0,0)):
        """
        Get the price from the simulation run.

        TODO: Better docstring
        """
        mean = 400 + np.log1p(buy_sell[0]) - np.log1p(buy_sell[1])
        std = 10 + np.log1p(buy_sell[0] + buy_sell[1])
        price = np.random.normal(mean, std)
        return price


    def daily_rate_of_return(self, seed = None, buy_sell = None):

        if seed is None:
            seed = self.last_seed

        if buy_sell is None:
            buy_sell = self.last_buy_sell

        last_sim_price = self.get_simulation_price(
            seed=seed, buy_sell = buy_sell
        )

        if last_sim_price is None:
            last_sim_price = self.default_sim_price

        ror = (last_sim_price * self.simulation_price_scale - 100) / 100

        # adjust to calibrated NetLogo to S&P500
        ror = self.sp500_std * (ror - self.netlogo_ror) / self.netlogo_std + self.sp500_ror

        return ror


####
#   Broker
####

class Broker():
    """
    A share Broker. Collects orders from agents, then trades on the market
    and reports a rate of return.

    Parameters
    ----------
    market - a MarketPNL instance
    """

    buy_limit = 0
    sell_limit = 0

    buy_sell_history = None

    market = None

    def __init__(self, market):
        self.market = market
        self.buy_sell_history = []

    def transact(self, delta_shares):
        """
        Input: an array of share deltas. positive for buy, negative for sell.
        """
        self.buy_limit += delta_shares[delta_shares > 0].sum()
        self.sell_limit += -delta_shares[delta_shares < 0].sum()

    def trade(self, seed = None):
        """
        Broker executes the trade on the financial market and then updates
        their record of the current asset price.

        Input: (optional) random seed for the simulation
        Output: Rate of return of the asset value that day.
        """

        # use integral shares here.
        buy_sell = (int(self.buy_limit), int(self.sell_limit))
        self.buy_sell_history.append(buy_sell)
        #print("Buy/Sell Limit: " + str(buy_sell))

        self.market.run_market(buy_sell = buy_sell, seed = seed)

        # clear the local limits
        self.buy_limit = 0
        self.sell_limit = 0

        return buy_sell, self.market.daily_rate_of_return()

#####
#    AttentionSimulation class
#####

class AttentionSimulation():
    """
    Encapsulates the "Oversight Code" functions of the experiment.
    Connects the Agent population model with a Broker, a Market simulation,
    and a FinanceModel of expected share prices.

    Parameters
    ----------

    agents: [HARK.AgentType]

    fm: FinanceModel

    q: int - number of quarters

    r: int - runs per quarter

    a: float - attention rate (between 0 and 1)

    """
    agents = None # replace with references to/operations on pop
    broker = None
    pop = None

    dollars_per_hark_money_unit = 1500

    # Number of days in a quarter / An empirical value based on trading calendars.
    days_per_quarter = 60

    # A FinanceModel
    fm = None

    # Simulation parameters
    quarters_per_simulation = None # Number of quarters to run total

    # Number of market runs to do per quarter
    # Valid values: 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60...
    runs_per_quarter = None

    # For John's prefered condition: days per quarter = runs per quarter
    # Best if an integer.
    days_per_run = None

    ## upping this to make more agents engaged in trade
    attention_rate = None

    # for tracking history of the simulation
    history = {}

    # dividend_ror -> on financial model
    # dividend_std -> on financial model; on MarketPNL

    # sp500_ror = 0.000628 -> on financial model; on MarketPNL
    # sp500_std = 0.011988 -> on financial model; on MarketPNL

    ## saving the time of simulation start and end
    start_time = None
    end_time = None

    def __init__(self, pop, fm, q = 1, r = None, a = None, market = None):
        self.agents = pop.agents
        self.fm = fm
        self.pop = pop

        self.quarters_per_simulation = q

        if r is not None:
            self.runs_per_quarter = r
        else:
            self.runs_per_quarter = self.days_per_quarter
        self.days_per_run = self.days_per_quarter / self.runs_per_quarter

        # TODO: Make this more variable.
        if a is not None:
            self.attention_rate = a
        else:
            self.attention_rate = 1 / self.runs_per_quarter

        # Create the Market wrapper
        market = MarketPNL() if market is None else market
        self.broker = Broker(market)

        self.history = {}
        self.history['buy_sell'] = []
        self.history['owned_shares'] = []
        self.history['total_assets'] = []
        self.history['class_stats'] = []

        # assign macro-days to each agent
        for agent in self.agents:
            agent.macro_day = random.randrange(self.days_per_quarter)

    def attend(self, agent):
        """
        Cause the agent to attend to the financial model.

        This will update their expectations of the risky asset.
        They will then adjust their owned risky asset shares to meet their
        target.

        Return the delta of risky asset shares ordered through the brokers.

        NOTE: This MUTATES the agents with their new target share amounts.
        """
        # Note: this mutates the underlying agent
        agent.assign_parameters(**self.fm.risky_expectations())

        d_shares = self.compute_share_demand(agent)

        delta_shares = d_shares - agent.shares

        # NOTE: This mutates the agent
        agent.shares = d_shares
        return delta_shares

    def compute_share_demand(self, agent):
        """
        Computes the number of shares an agent _wants_ to own.

        This involves:
          - Computing a solution function based on their
            expectations and personal properties
          - Using the solution and the agent's current normalized
            assets to compute a share number
        """
        agent.assign_parameters(AdjustPrb = 1.0)
        agent.solve()
        asset_normalized = agent.state_now['aNrm']

        # ShareFunc takes normalized market assets as argument
        risky_share = agent.solution[0].ShareFuncAdj(
            asset_normalized
        )

        # denormalize the risky share. See https://github.com/econ-ark/HARK/issues/986
        risky_asset_wealth = risky_share \
                            * asset_normalized \
                            * agent.state_now['pLvl'] \
                            * self.dollars_per_hark_money_unit 

        shares = risky_asset_wealth / self.fm.rap()

        if (np.isnan(shares)).any():
            print("ERROR: Agent has nan shares")

        return shares

    def data(self):
        """
        Returns a Pandas DataFrame of the data from the simulation run.
        """
        ## DEBUGGING
        data = None
        try:
            data_dict = {
                't' : range(len(self.fm.prices[1:])),
                'prices' : self.fm.prices[1:],
                'buy' :  [bs[0] for bs in self.broker.buy_sell_history],
                'sell' : [bs[1] for bs in self.broker.buy_sell_history],
                'owned' : self.history['owned_shares'],
                'total_assets' : self.history['total_assets'],
                'ror' : self.fm.ror_list,
                'expected_ror' : self.fm.expected_ror_list[1:],
                'expected_std' : self.fm.expected_std_list[1:],
            }

            data = pd.DataFrame.from_dict(data_dict)

        except Exception as e:
            print(e)
            print("Lengths:" + str({
                't' : len(self.fm.prices),
                'prices' : len(self.fm.prices),
                'buy' : len([None] \
                            + [bs[0] for bs in self.broker.buy_sell_history]),
                'sell' : len([None] \
                             + [bs[1] for bs in self.broker.buy_sell_history]),
                'owned' : len(self.history['owned_shares']),
                'total_assets' : len(self.history['total_assets']),
                'ror' : len([None] + self.fm.ror_list),
                'expected_ror' : len(self.fm.expected_ror_list),
                'expected_std' : len(self.fm.expected_std_list),
            }))

        return data

    def macro_update(self, agent):
        """
        Input: an agent, a FinancialModel, and a Broker

        Simulates one "macro" period for the agent (quarterly by assumption).
        For the purposes of the simulation, award the agent dividend income
        but not capital gains on the risky asset.
        """

        #agent.assign_parameters(AdjustPrb = 0.0)
        agent.solve()

        ## For risky asset gains in the simulated quarter,
        ## use only the dividend.
        true_risky_expectations = {
            "RiskyAvg" : agent.parameters['RiskyAvg'],
            "RiskyStd" : agent.parameters['RiskyStd'] 
        }

        dividend_risky_params = {
            "RiskyAvg" : 1 + self.fm.dividend_ror,
            "RiskyStd" : self.fm.dividend_std
        }

        agent.assign_parameters(**dividend_risky_params)

        agent.simulate(sim_periods=1)

        ## put back the expectations that include capital gains now
        agent.assign_parameters(**true_risky_expectations)

        # Selling off shares if necessary to
        # finance this period's consumption
        asset_level_in_shares = agent.state_now['aLvl'] \
            * self.dollars_per_hark_money_unit / self.fm.rap()

        delta = asset_level_in_shares - agent.shares
        delta[delta > 0] = 0

        agent.shares = agent.shares + delta
        self.broker.transact(delta)

    def report(self):
        data = self.data()

        fig, ax = plt.subplots(
            4, 1,
            sharex='col',
            #sharey='col',
            figsize=(12,16),
        )

        ax[0].plot(data['total_assets'], alpha=0.5, label='total assets')
        ax[0].plot([p * o for (p,o) in zip(data['prices'], data['owned'])], alpha=0.5, label='owned share value')
        ax[0].plot([100 * o for (p,o) in zip(data['prices'], data['owned'])], alpha=0.5, label='owned share quantity * p_0')
        ax[0].legend()

        ax[1].plot(data['buy'], alpha=0.5, label='buy')
        ax[1].plot(data['sell'], alpha=0.5, label='sell')
        ax[1].legend()

        ax[2].plot(data['ror'], alpha=0.5, label='ror')
        ax[2].plot(data['expected_ror'], alpha=0.5, label='expected ror')
        ax[2].legend()

        ax[3].plot(data['prices'], alpha=0.5, label='prices')
        ax[3].legend()

        ax[0].set_title("Simulation History")
        ax[0].set_ylabel("Dollars")
        ax[1].set_xlabel("t")

        plt.show()

    def report_class_stats(self, stat = 'aLvl', stat_history = None):
        if stat_history is None:
            stat_history = self.history['class_stats']

        for d, cs in enumerate(self.history['class_stats']):
            cs['time'] = d

        data = pd.concat(self.history['class_stats'])

        ax = sns.lineplot(data=data, x='time', y='aLvl_mean', hue='label')
        ax.set_title("mean aLvl by class subpopulation")

    def simulate(self, quarters = None, start = True):
        """
        Workhorse method that runs the simulation.
        """
        self.start_time = datetime.now()

        if quarters is None:
            quarters = self.quarters_per_simulation

        # Initialize share ownership for agents
        if start:
            for agent in self.agents:
                agent.shares = self.compute_share_demand(agent)

        # Main loop
        for quarter in range(quarters):
            print(f"Q-{quarter}")

            day = 0

            for run in range(self.runs_per_quarter):
                #print(f"Q-{quarter}:R-{run}")

                # Set to a number for a fixed seed, or None to rotate
                for agent in self.agents:
                    if random.random() < self.attention_rate:
                        self.broker.transact(self.attend(agent))

                buy_sell, ror = self.broker.trade()
                #print("ror: " + str(ror))

                new_run = True

                for day_in_run in range(int(self.days_per_run)):
                    updates = 0
                    for agent in self.agents:
                        if agent.macro_day == day:
                            updates = updates + 1
                            self.macro_update(agent)

                    if new_run:
                        new_run = False
                    else:
                        # sloppy
                        # problem is that this should really be nan, nan
                        # putting 0,0 here is a stopgap to make plotting code simpler
                        self.broker.buy_sell_history.append((0,0))

                    #print(f"Q-{quarter}:D-{day}. {updates} macro-updates.")

                    self.update_agent_wealth_capital_gains(self.fm.rap(), ror)

                    self.track()

                    # combine these steps?
                    risky_asset_price = self.fm.add_ror(ror)
                    self.fm.calculate_risky_expectations()

                    day = day + 1

        self.end_time = datetime.now()

    def track(self):
        """
        Tracks the current state of agent's total assets and owned shares
        """
        tal = sum(
                [agent.state_now['aLvl'].sum()
                 for agent
                 in self.agents]
                ) * self.dollars_per_hark_money_unit
        os = sum([sum(agent.shares) for agent in self.agents])

        self.history['owned_shares'].append(os)
        self.history['total_assets'].append(tal)
        self.history['class_stats'].append(self.pop.class_stats(store=False))

    def update_agent_wealth_capital_gains(self, old_share_price, ror):
        """
        For all agents,
        given the old share price
        and a rate of return

        update the agent's wealth level to adjust
        for the most recent round of capital gains.
        """

        new_share_price = old_share_price * (1 + ror)

        for agent in self.agents:
            old_raw = agent.shares * old_share_price
            new_raw = agent.shares * new_share_price

            delta_aNrm = (new_raw - old_raw) / \
                (self.dollars_per_hark_money_unit * agent.state_now['pLvl'])

            # update normalized market assets
            # if agent.state_now['aNrm'] < delta_aNrm:
            #     breakpoint()

            agent.state_now['aNrm'] = agent.state_now['aNrm'] + delta_aNrm

            if (agent.state_now['aNrm'] < 0).any():
                print(f"ERROR: Agent with CRRA {agent.parameters['CRRA']}" \
                      + "has negative aNrm after capital gains update.")
                print("Setting normalize assets and shares to 0.")
                agent.state_now['aNrm'][(agent.state_now['aNrm'] < 0)] = 0.0
                ## TODO: This change in shares needs to be registered with the Broker.
                agent.shares[(agent.state_now['aNrm'] == 0)] = 0

            # update non-normalized market assets
            agent.state_now['aLvl'] = agent.state_now['aNrm']  * agent.state_now['pLvl']

    def ror_volatility(self):
        """
        Returns the volatility of the rate of return.
        Must be run after a simulation.
        """
        return self.data()['ror'].dropna().std()

    def sim_stats(self):
        df_mean = self.history['class_stats'][-1][['label','aLvl_mean']]
        df_mean.columns = df_mean.columns.droplevel(1)
        sim_stats_mean = df_mean.set_index('label').to_dict()['aLvl_mean']

        df_std = self.history['class_stats'][-1][['label','aLvl_std']]
        df_std.columns = df_std.columns.droplevel(1)
        sim_stats_std = df_std.set_index('label').to_dict()['aLvl_std']

        sim_stats_mean = {('aLvl_mean', k) : v  for k,v in sim_stats_mean.items()}
        sim_stats_std = {('aLvl_std', k) : v  for k,v in sim_stats_std.items()}

        sim_stats = {}
        sim_stats.update(sim_stats_mean)
        sim_stats.update(sim_stats_std)

        sim_stats['q'] = self.quarters_per_simulation
        sim_stats['r'] = self.runs_per_quarter

        sim_stats['market_class'] = self.broker.market.__class__
        sim_stats['market_seeds'] = self.broker.market.seeds if 'PNL' in str(sim_stats['market_class']) else []

        sim_stats['attention'] = self.attention_rate
        sim_stats['ror_volatility'] = self.ror_volatility()

        sim_stats['dividend_ror'] = self.fm.dividend_ror
        sim_stats['dividend_std'] = self.fm.dividend_std
        sim_stats['p1'] = self.fm.p1
        sim_stats['p2'] = self.fm.p2
        sim_stats['delta_t1'] = self.fm.delta_t1
        sim_stats['delta_t2'] = self.fm.delta_t2


        sim_stats['seconds'] = (self.end_time - self.start_time).seconds

        return sim_stats
