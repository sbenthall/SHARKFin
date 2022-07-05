from abc import ABC, abstractmethod
from sharkfin.utilities import *
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from statistics import mean
from scipy import stats
from sharkfin.markets import MockMarket
from sharkfin.broker import Broker
import sharkfin.stylized_facts as stylized_facts

class AbstractSimulation(ABC):
    '''
    Abstract class from which simulation classews should inherit

    Defines common methods for all SHARK simulations.
    '''

    @abstractmethod
    def data(self):
        """
        Returns a Pandas DataFrame of the data from the simulation run.
        """
        pass
    
    @abstractmethod
    def sim_stats(self, seed: int, buy_sell: tuple[int, int]):
        pass

    @abstractmethod
    def simulate(self):
        pass
   

class BasicSimulation(AbstractSimulation):
    """
    A basic version of the SHARK simulation.

    Parameters
    ----------

    agents: [HARK.AgentType]

    fm: FinanceModel

    q: int - number of quarters

    r: int - runs per quarter

    a: float - attention rate (between 0 and 1)

    """

    agents = None  # replace with references to/operations on pop
    broker = None
    pop = None

    # Number of days in a quarter / An empirical value based on trading calendars.
    days_per_quarter = 60

    # A FinanceModel
    fm = None

    # Simulation parameters
    quarters_per_simulation = None  # Number of quarters to run total

    # Number of market runs to do per quarter
    # Valid values: 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60...
    runs_per_quarter = None

    # For John's prefered condition: days per quarter = runs per quarter
    # Best if an integer.
    days_per_run = None

      # for tracking history of the simulation
    history = {}

    ## saving the time of simulation start and end
    start_time = None
    end_time = None

    def __init__(
        self, pop, Fm, q=1, r=None, market=None, dphm=1500, days_per_quarter = 60,
        p1 = 0.1,
        p2 = 0.1,
        d1 = 60,
        d2 = 60 
    ):
        """
        pop - agent population
        fm - expectation class

        """
        self.agents = pop.agents

        self.pop = pop

        self.dollars_per_hark_money_unit = dphm

        self.quarters_per_simulation = q

        self.days_per_quarter = days_per_quarter

        if r is not None:
            self.runs_per_quarter = r
        else:
            self.runs_per_quarter = self.days_per_quarter
        self.days_per_run = self.days_per_quarter / self.runs_per_quarter

        # Create the Market wrapper
        self.market = MockMarket() if market is None else market

        self.fm = Fm(
            self.market,
            p1 = p1,
            p2 = p2,
            delta_t1 = d1,
            delta_t2 = d2,
            days_per_quarter = self.days_per_quarter
            )
        self.fm.calculate_risky_expectations()

        self.broker = Broker(self.market)

        self.history = {}
        self.history['buy_sell'] = []
        self.history['owned_shares'] = []
        self.history['total_assets'] = []
        self.history['mean_income_level'] = []
        self.history['total_consumption_level'] = []
        self.history['permshock_std'] = []
        self.history['class_stats'] = []
        self.history['total_pop_stats'] = []

        # assign macro-days to each agent
        # This is a somewhat frustrating artifact to be cleaned up...
        for agent in self.agents:
            agent.macro_day = 0

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
        agent.assign_parameters(AdjustPrb=1.0)
        agent.solve()
        cNrm = agent.controls['cNrm'] if 'cNrm' in agent.controls else 0
        asset_normalized = agent.state_now['aNrm'] + cNrm
        # breakpoint()

        # ShareFunc takes normalized market assets as argument
        risky_share = agent.solution[0].ShareFuncAdj(asset_normalized)

        # denormalize the risky share. See https://github.com/econ-ark/HARK/issues/986
        risky_asset_wealth = (
            risky_share
            * asset_normalized
            * agent.state_now['pLvl']
            * self.dollars_per_hark_money_unit
        )

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
        
        data_dict = {
            't': range(len(self.market.prices[1:])),
            'prices': self.market.prices[1:],
            'buy': [bs[0] for bs in self.broker.buy_sell_history],
            'sell': [bs[1] for bs in self.broker.buy_sell_history],
            'buy_macro': [bs[0] for bs in self.broker.buy_sell_macro_history],
            'sell_macro': [bs[1] for bs in self.broker.buy_sell_macro_history],
            'owned': self.history['owned_shares'][1:],
            'total_assets': self.history['total_assets'][1:],
            'mean_income': self.history['mean_income_level'][1:],
            'total_consumption': self.history['total_consumption_level'][1:],
            'permshock_std': self.history['permshock_std'][1:],
            'ror': self.market.ror_list(),
            'expected_ror': self.fm.expected_ror_list[1:],
            'expected_std': self.fm.expected_std_list[1:],
        }

        try:
            data = pd.DataFrame.from_dict(data_dict)

        except Exception as e:
            print(e)
            print(
                "Lengths:"
                + str(
                    {
                        key: len(value) for key,value in data_dict.items()
                    }
                )
            )

        return data

    def macro_update(self, agent):
        """
        Input: an agent, a FinancialModel, and a Broker

        Simulates one "macro" period for the agent (quarterly by assumption).
        For the purposes of the simulation, award the agent dividend income
        but not capital gains on the risky asset.
        """

        # agent.assign_parameters(AdjustPrb = 0.0)
        agent.solve()

        ## For risky asset gains in the simulated quarter,
        ## use only the dividend.
        true_risky_expectations = {
            "RiskyAvg": agent.parameters['RiskyAvg'],
            "RiskyStd": agent.parameters['RiskyStd'],
        }


        # No change -- both capital gains and dividends awarded daily. See #100
        macro_risky_params = {
            "RiskyAvg": 1,
            "RiskyStd": 0,
        }

        agent.assign_parameters(**macro_risky_params)

        agent.simulate(sim_periods=1)

        ## put back the expectations that include capital gains now
        agent.assign_parameters(**true_risky_expectations)

        # Selling off shares if necessary to
        # finance this period's consumption
        asset_level_in_shares = (
            agent.state_now['aLvl'] * self.dollars_per_hark_money_unit / self.fm.rap()
        )

        delta = asset_level_in_shares - agent.shares
        delta[delta > 0] = 0

        agent.shares = agent.shares + delta
        self.broker.transact(delta, macro=True)

    def report(self):
        data = self.data()

        fig, ax = plt.subplots(
            4,
            1,
            sharex='col',
            # sharey='col',
            figsize=(12, 16),
        )

        ax[0].plot(data['total_assets'], alpha=0.5, label='total assets')
        ax[0].plot(
            [p * o for (p, o) in zip(data['prices'], data['owned'])],
            alpha=0.5,
            label='owned share value',
        )
        ax[0].plot(
            [100 * o for (p, o) in zip(data['prices'], data['owned'])],
            alpha=0.5,
            label='owned share quantity * p_0',
        )
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

    def report_class_stats(self, stat='aLvl', stat_history=None):
        if stat_history is None:
            stat_history = self.history['class_stats']

        for d, cs in enumerate(self.history['class_stats']):
            cs['time'] = d

        data = pd.concat(self.history['class_stats'])

        ax = sns.lineplot(data=data, x='time', y='aLvl_mean', hue='label')
        ax.set_title("mean aLvl by class subpopulation")

    def simulate(self, quarters=None, start=True):
        """
        DUMMY METHOD -- need to functionalize/parameterize out.
        See #88
        Workhorse method that runs the simulation.
        """
        self.start_time = datetime.now()

        if quarters is None:
            quarters = self.quarters_per_simulation

        # Initialize share ownership for agents
        if start:
            for agent in self.agents:
                agent.shares = self.compute_share_demand(agent)

        ## ?
        self.track(-1)

        # Main loop
        for quarter in range(quarters):
            print(f"Q-{quarter}")

            day = 0

            for run in range(self.runs_per_quarter):
                # print(f"Q-{quarter}:R-{run}")

                # Basic simulation has an attention rate of 1
                self.broker.transact(self.attend(agent))

                buy_sell, ror, price, dividend = self.broker.trade()
                # print("ror: " + str(ror))

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
                        # problem is that this should really be nan, nan
                        # putting 0,0 here is a stopgap to make plotting code simpler
                        self.broker.track((0, 0),(0, 0))

                    self.update_agent_wealth_capital_gains(price, ror)

                    self.track(day)

                    # combine these steps?
                    # add_ror appends to internal history list
                    #self.fm.add_ror(ror) 
                    self.fm.calculate_risky_expectations()

                    day = day + 1

        self.broker.close()

        self.end_time = datetime.now()

    def track(self, day):
        """
        Tracks the current state of agent's total assets and owned shares
        """
        tal = (
            sum([agent.state_now['aLvl'].sum() for agent in self.agents])
            * self.dollars_per_hark_money_unit
        )
        os = sum([sum(agent.shares) for agent in self.agents])

        mpl = (
            mean([agent.state_now['pLvl'].mean() for agent in self.agents])
            * self.dollars_per_hark_money_unit
        )

        tcl = (
            sum(
                [
                    (agent.controls['cNrm'] * agent.state_now['pLvl']).sum()
                    for agent in self.agents
                    if agent.macro_day == day
                ]
            )
            * self.dollars_per_hark_money_unit
        )

        permshock_std = np.array(
            [
                agent.shocks['PermShk']
                for agent in self.agents
                if 'PermShk' in agent.shocks
            ]
        ).std()

        self.history['owned_shares'].append(os)
        self.history['total_assets'].append(tal)
        self.history['mean_income_level'].append(mpl)
        self.history['total_consumption_level'].append(tcl)
        self.history['permshock_std'].append(permshock_std)
        self.history['class_stats'].append(self.pop.class_stats(store=False))
        self.history['total_pop_stats'].append(self.pop.agent_df())
        # self.history['buy_sell'].append(self.broker.buy_sell_history[-1])

    def update_agent_wealth_capital_gains(self, new_share_price, ror, dividend):
        """
        For all agents,
        given the old share price
        and a rate of return

        update the agent's wealth level to adjust
        for the most recent round of capital gains.
        """

        old_share_price = new_share_price / (1 + ror)

        for agent in self.agents:
            old_raw = agent.shares * old_share_price
            new_raw = agent.shares * new_share_price
            dividends = agent.shares * dividend

            delta_aNrm = (new_raw - old_raw + dividends) / (
                self.dollars_per_hark_money_unit * agent.state_now['pLvl']
            )

            # update normalized market assets
            # if agent.state_now['aNrm'] < delta_aNrm:
            #     breakpoint()

            agent.state_now['aNrm'] = agent.state_now['aNrm'] + delta_aNrm

            if (agent.state_now['aNrm'] < 0).any():
                print(
                    f"ERROR: Agent with CRRA {agent.parameters['CRRA']}"
                    + "has negative aNrm after capital gains update."
                )
                print("Setting normalize assets and shares to 0.")
                agent.state_now['aNrm'][(agent.state_now['aNrm'] < 0)] = 0.0
                ## TODO: This change in shares needs to be registered with the Broker.
                agent.shares[(agent.state_now['aNrm'] == 0)] = 0

            # update non-normalized market assets
            agent.state_now['aLvl'] = agent.state_now['aNrm'] * agent.state_now['pLvl']

    def ror_volatility(self):
        """
        Returns the volatility of the rate of return.
        Must be run after a simulation.
        """
        return self.data()['ror'].dropna().std()

    def ror_mean(self):
        """
        Returns the average rate of return
        Must be run after a simulation
        """

        return self.data()['ror'].dropna().mean()

    def buy_sell_stats(self):
        bs_stats = {}
        buy_limits, sell_limits = list(zip(*self.broker.buy_sell_history))

        bs_stats['max_buy_limit'] = max(buy_limits)
        bs_stats['max_sell_limit'] = max(sell_limits)

        bs_stats['idx_max_buy_limit'] = np.argmax(buy_limits)
        bs_stats['idx_max_sell_limit'] = np.argmax(sell_limits)

        bs_stats['mean_buy_limit'] = np.mean(buy_limits)
        bs_stats['mean_sell_limit'] = np.mean(sell_limits)

        bs_stats['std_buy_limit'] = np.std(buy_limits)
        bs_stats['std_sell_limit'] = np.std(sell_limits)

        bs_stats['kurtosis_buy_limit'] = stats.kurtosis(buy_limits)
        bs_stats['kurtosis_sell_limit'] = stats.kurtosis(sell_limits)

        bs_stats['skew_buy_limit'] = stats.skew(buy_limits)
        bs_stats['skew_sell_limit'] = stats.skew(sell_limits)

        return bs_stats

    def sim_stats(self):

        ## TODO: Can this processing be made less code-heavy?
        df_mean = self.history['class_stats'][-1][['label', 'aLvl_mean']]
        df_mean.columns = df_mean.columns.droplevel(1)
        sim_stats_mean = df_mean.set_index('label').to_dict()['aLvl_mean']

        df_std = self.history['class_stats'][-1][['label', 'aLvl_std']]
        df_std.columns = df_std.columns.droplevel(1)
        sim_stats_std = df_std.set_index('label').to_dict()['aLvl_std']

        df_mNrm_ratio_StE_mean = self.history['class_stats'][-1][
            ['label', 'mNrm_ratio_StE_mean']
        ]
        df_mNrm_ratio_StE_mean.columns = df_mNrm_ratio_StE_mean.columns.droplevel(1)
        sim_stats_mNrm_ratio_StE_mean = df_mNrm_ratio_StE_mean.set_index(
            'label'
        ).to_dict()['mNrm_ratio_StE_mean']

        df_mNrm_ratio_StE_std = self.history['class_stats'][-1][
            ['label', 'mNrm_ratio_StE_std']
        ]
        df_mNrm_ratio_StE_std.columns = df_mNrm_ratio_StE_std.columns.droplevel(1)
        sim_stats_mNrm_ratio_StE_std = df_mNrm_ratio_StE_std.set_index(
            'label'
        ).to_dict()['mNrm_ratio_StE_std']

        sim_stats_mean = {('aLvl_mean', k): v for k, v in sim_stats_mean.items()}
        sim_stats_std = {('aLvl_std', k): v for k, v in sim_stats_std.items()}
        sim_stats_mNrm_ratio_StE_mean = {
            ('mNrm_ratio_StE_mean', k): v
            for k, v in sim_stats_mNrm_ratio_StE_mean.items()
        }
        sim_stats_mNrm_ratio_StE_std = {
            ('mNrm_ratio_StE_std', k): v
            for k, v in sim_stats_mNrm_ratio_StE_std.items()
        }

        total_pop_aLvl = self.history['total_pop_stats'][-1]['aLvl']
        total_pop_aLvl_mean = total_pop_aLvl.mean()
        total_pop_aLvl_std = total_pop_aLvl.std()

        bs_stats = self.buy_sell_stats()

        sim_stats = {}
        sim_stats.update(sim_stats_mean)
        sim_stats.update(sim_stats_std)
        sim_stats.update(bs_stats)
        sim_stats.update(self.fm.asset_price_stats())
        sim_stats.update(sim_stats_mNrm_ratio_StE_mean)
        sim_stats.update(sim_stats_mNrm_ratio_StE_std)

        sim_stats['q'] = self.quarters_per_simulation
        sim_stats['r'] = self.runs_per_quarter

        sim_stats['market_class'] = self.broker.market.__class__
        sim_stats['market_seeds'] = self.broker.market.seeds # seed list should be a requirement for any market class.

        sim_stats['ror_volatility'] = self.ror_volatility()
        sim_stats['ror_mean'] = self.ror_mean()

        sim_stats['total_population_aLvl_mean'] = total_pop_aLvl_mean
        sim_stats['total_population_aLvl_std'] = total_pop_aLvl_std

        sim_stats['p1'] = self.fm.p1
        sim_stats['p2'] = self.fm.p2
        sim_stats['delta_t1'] = self.fm.delta_t1
        sim_stats['delta_t2'] = self.fm.delta_t2
        sim_stats['dollars_per_hark_money_unit'] = self.dollars_per_hark_money_unit

        sim_stats['seconds'] = (self.end_time - self.start_time).seconds

        # stylized facts
        sim_stats['log_return_autocorrelation'] = stylized_facts.DW_test(
            np.array([r for r in self.market.ror_list()])) - 2
        sim_stats['log_return_squared_autocorrelation'] = stylized_facts.DW_test(
            np.array([r ** 2 for r in self.market.ror_list()])) - 2

        return sim_stats

class AttentionSimulation(BasicSimulation):
    """
    A simulation in which agent behavior is characterized by:
     - an attention rate, which is the chance per day of updating expectations
     - a macro-day, which is the day of each quarter that an agent experiences labor income, dividends, and consumption

    Parameters
    ----------

    agents: [HARK.AgentType]

    fm: FinanceModel

    q: int - number of quarters

    r: int - runs per quarter

    a: float - attention rate (between 0 and 1)

    market: Market

    dphm: int

    """

    ## upping this to make more agents engaged in trade
    attention_rate = None

    def __init__(self, pop, fm, q=1, r=None, a=None, market=None, dphm=1500, days_per_quarter = 60, rng = None):

        super().__init__(pop, fm, q=q, r=r, market=market, dphm=dphm, days_per_quarter = days_per_quarter)

        self.rng = rng if rng is not None else np.random.default_rng()

        # TODO: Make this more variable.
        if a is not None:
            self.attention_rate = a
        else:
            self.attention_rate = 1 / self.runs_per_quarter

        # assign macro-days to each agent
        for agent in self.agents:
            agent.macro_day = self.rng.integers(self.days_per_quarter)

    def simulate(self, quarters=None, start=True):
        """
        Workhorse method that runs the simulation.

        In the AttentionSimulation, this is done in a special way:
         - Agents have a daily attention rate
         - This is separate from the macro-update day
        """
        self.start_time = datetime.now()

        if quarters is None:
            quarters = self.quarters_per_simulation

        # Initialize share ownership for agents
        if start:
            for agent in self.agents:
                agent.shares = self.compute_share_demand(agent)

        
        self.track(-1)

        # Main loop
        for quarter in range(quarters):
            print(f"Q-{quarter}")

            day = 0

            for run in range(self.runs_per_quarter):
                # print(f"Q-{quarter}:R-{run}")

                # Set to a number for a fixed seed, or None to rotate
                for agent in self.agents:
                    if self.rng.random() < self.attention_rate:
                        self.broker.transact(self.attend(agent))

                buy_sell, ror, price, dividend = self.broker.trade()
                # print("ror: " + str(ror))

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
                        self.broker.buy_sell_history.append((0, 0))
                        self.broker.buy_sell_macro_history.append((0, 0))
                        self.market.dummy_run()

                    # print(f"Q-{quarter}:D-{day}. {updates} macro-updates.")

                    self.update_agent_wealth_capital_gains(price, ror, dividend)

                    self.track(day)

                    # combine these steps?
                    # add_ror appends to internal history list
                    #self.fm.add_ror(ror) 
                    self.fm.calculate_risky_expectations()

                    day = day + 1

        self.broker.close()

        self.end_time = datetime.now()

    def sim_stats(self):

        sim_stats = super().sim_stats()

        sim_stats['attention'] = self.attention_rate

        return sim_stats


class CalibrationSimulation(BasicSimulation):
    """
    A simulation in which the broker makes no activity for some number of days,
    then executes a preset buy and sell order.
    Used to test the price impact on the market.
    """
    market = None

    def __init__(self, pop, fm, q=1, r=None, a=None, market=None, dphm=1500):

        super().__init__(pop, fm, q=q, r=r, market=market, dphm=dphm)

        self.history['run_times'] = []

    def simulate(self, n_days, start=True, buy_sell_shock=(0, 0)):
        """
        Workhorse method that runs the simulation.
        """
        self.start_time = datetime.now()

        # Initialize share ownership for agents
        if start:
            for agent in self.agents:
                agent.shares = self.compute_share_demand(agent)
                #self.macro_update(agent)

        self.track(-1, 0)

        for day in range(n_days):
            start_time = datetime.now()

            # is this needed for chum?
            for agent in self.agents:
                self.broker.transact(np.zeros(1))

            buy_sell, ror, price, dividend = self.broker.trade()
                
            self.update_agent_wealth_capital_gains(price, ror, dividend)

            # combine these steps?
            # add_ror appends to internal history list
            #self.fm.add_ror(ror) 
            self.fm.calculate_risky_expectations()

            end_time = datetime.now()

            time_delta = end_time - start_time

            self.track(day, time_delta)



        # last day shock
        start_time = datetime.now()

        buy = buy_sell_shock[0]
        sell = -buy_sell_shock[1]

        self.broker.transact(np.array((buy, sell)))
        buy_sell, ror, price, dividend = self.broker.trade()

        self.update_agent_wealth_capital_gains(price, ror, dividend)

        # self.fm.add_ror(ror)
        self.fm.calculate_risky_expectations()

        end_time = datetime.now()
        time_delta = end_time - start_time

        self.track(day+1, time_delta)

        self.broker.close()

        self.end_time = datetime.now()

    def track(self, day, time_delta):
        """
        Tracks the current state of agent's total assets and owned shares
        """

        #self.history['buy_sell'].append(self.broker.buy_sell_history[-1])
        self.history['run_times'].append(time_delta)

    def data(self):
        """
        Returns a Pandas DataFrame of the data from the simulation run.
        """
        ## DEBUGGING
        data = None

        data_dict = {
            't': range(len(self.market.prices)),
            'prices': self.market.prices,
            'buy': [None] + [bs[0] for bs in self.broker.buy_sell_history],
            'sell': [None] +  [bs[1] for bs in self.broker.buy_sell_history],
            'ror': [None] + self.market.ror_list(),
            'expected_ror': self.fm.expected_ror_list,
            'expected_std': self.fm.expected_std_list,
            'market_times': self.history['run_times']
        }

        try:
            data = pd.DataFrame.from_dict(data_dict)

        except Exception as e:
            print(e)
            print(
                "Lengths:"
                + str(
                    {
                        key : len(value) for key, value in data_dict.items()
                    }
                )
            )

        return data