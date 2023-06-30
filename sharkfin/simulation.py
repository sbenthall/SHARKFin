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
from sharkfin.markets.ammps import (
    MarketFailureError,
)  ## TODO: Move this error to higher level module
from sharkfin.broker import Broker
import sharkfin.stylized_facts as stylized_facts


class AbstractSimulation(ABC):
    """
    Abstract class from which simulation classews should inherit

    Defines common methods for all SHARK simulations.
    """

    @abstractmethod
    def daily_data(self):
        """
        Returns a Pandas DataFrame of the daily data from the simulation run.
        """
        pass

    @abstractmethod
    def sim_stats(self, seed: int, buy_sell: tuple[int, int]):
        pass

    @abstractmethod
    def simulate(self):
        pass

    def track(self, day, time_delta=0):
        """
        Tracks the current state of agent's total assets and owned shares
        """
        pass


class MarketSimulation(AbstractSimulation):
    """
    A basic version of the SHARK simulation.
    Actually has no heteregeneous agents in it --
    this only requires a market and a broker.

    Parameters
    ----------

    q: int - number of quarters

    r: int - runs per quarter

    a: float - attention rate (between 0 and 1)

    """

    # agents = None  # replace with references to/operations on pop
    broker = None

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

    ## day that the simulation ends.
    end_day = None

    # A holder for an error message
    error_message = None

    def __init__(self, q=1, r=None, market=None, days_per_quarter=60, broker_args=None):
        """
        q - number of quarters
        r - number of runs per quarter. TODO : Phase this out in favor of more use of 'days_per_quarter'

        market -- the Market class used
        days_per_quarter -- number of days per quarter
        """
        self.quarters_per_simulation = q

        self.days_per_quarter = days_per_quarter

        if r is not None:
            self.runs_per_quarter = r
        else:
            self.runs_per_quarter = self.days_per_quarter
        self.days_per_run = self.days_per_quarter / self.runs_per_quarter

        # Create the Market wrapper
        self.market = MockMarket() if market is None else market

        self.broker = Broker(self.market, broker_args=broker_args)

        self.history = {}
        self.history["buy_sell"] = []

    def burn_in(self, n_days):
        """
        Runs for n_days days with no broker activity.
        Used for warming up the agents in the market.

        Tracking is disabled during the burn-in period.
        """
        for day in range(n_days):
            self.broker.transact(np.zeros(1))

            buy_sell, ror, price, dividend = self.broker.trade()

    def daily_data(self):
        """
        Returns a Pandas DataFrame of the data from the simulation run.
        """
        ## DEBUGGING
        data = None

        data_dict = {
            "t": range(len(self.market.prices[self.burn_in_val + 1 :])),
            "prices": self.market.prices[self.burn_in_val + 1 :],
            "dividends": self.market.dividends[self.burn_in_val + 1 :],
            "buy": [bs[0] for bs in self.broker.buy_sell_history][self.burn_in_val :],
            "sell": [bs[1] for bs in self.broker.buy_sell_history][self.burn_in_val :],
            "ror": self.market.ror_list()[self.burn_in_val :],
        }

        print(f"Ran for {len(data_dict['t'])} days")

        try:
            data = pd.DataFrame.from_dict(data_dict)

        except Exception as e:
            print(e)
            print(
                "Lengths:" + str({key: len(value) for key, value in data_dict.items()})
            )

        return data

    def start_simulation(self, burn_in=None):
        self.start_time = datetime.now()
        # Initialize share ownership for agents

        if burn_in is not None:
            self.burn_in(burn_in)

        self.burn_in_val = burn_in if burn_in is not None else 0

    def simulate(self, quarters=None, start=True, burn_in=None):
        """
        DUMMY METHOD -- need to functionalize/parameterize out.
        See #88
        Workhorse method that runs the simulation.

        Parameters
        ------------

        burn_in : int or None
           If not None, then an int number of days with no broker activity to run before starting the simulation.
        """

        if start:
            self.start_simulation(burn_in)

        self.track(-1)

        day = 0

        if quarters is None:
            quarters = self.quarters_per_simulation

        # Main loop
        for quarter in range(quarters):
            print(f"Q-{quarter}")

            day_in_quarter = 0

            for run in range(self.runs_per_quarter):
                # print(f"Q-{quarter}:R-{run}")

                # Basic simulation has an attention rate of 1
                self.broker.transact(np.zeros(1))

                buy_sell, ror, price, dividend = self.broker.trade()
                # print("ror: " + str(ror))

                new_run = True

                for day_in_run in range(int(self.days_per_run)):
                    updates = 0

                    if new_run:
                        new_run = False
                    else:
                        # problem is that this should really be nan, nan
                        # putting 0,0 here is a stopgap to make plotting code simpler
                        self.broker.track((0, 0), (0, 0))

                    self.track(day)

                    day = day + 1
                    day_in_quarter = day_in_quarter + 1

        self.broker.close()

        self.end_time = datetime.now()
        self.end_day = day

    def ror_volatility(self):
        """
        Returns the volatility of the rate of return.
        Must be run after a simulation.
        """
        return self.daily_data()["ror"].dropna().std()

    def ror_mean(self):
        """
        Returns the average rate of return
        Must be run after a simulation
        """

        return self.daily_data()["ror"].dropna().mean()

    def buy_sell_stats(self):
        bs_stats = {}
        buy_limits, sell_limits = list(zip(*self.broker.buy_sell_history))

        try:
            bs_stats["max_buy_limit"] = max(buy_limits)
            bs_stats["max_sell_limit"] = max(sell_limits)

            bs_stats["idx_max_buy_limit"] = np.argmax(buy_limits)
            bs_stats["idx_max_sell_limit"] = np.argmax(sell_limits)
        except Exception as e:
            print("Failure to compute max or idx_max of buy/sell limits")
            print(e)

        try:
            bs_stats["mean_buy_limit"] = np.mean(buy_limits)
            bs_stats["mean_sell_limit"] = np.mean(sell_limits)

            bs_stats["std_buy_limit"] = np.std(buy_limits)
            bs_stats["std_sell_limit"] = np.std(sell_limits)
        except Exception as e:
            print("Failure to compute mean or std of buy/sell limits")
            print(e)

        try:
            bs_stats["kurtosis_buy_limit"] = stats.kurtosis(buy_limits)
            bs_stats["kurtosis_sell_limit"] = stats.kurtosis(sell_limits)

            bs_stats["skew_buy_limit"] = stats.skew(buy_limits)
            bs_stats["skew_sell_limit"] = stats.skew(sell_limits)

        except Exception as e:
            print("Failure to compute kurtosis or skew of buy/sell limits")
            print(e)

        return bs_stats

    def status_code_from_message(self, message):
        """
        Convert a string message into a status code.
        TODO: Make this into something configed by an external YAML file.
        """

        if message == "0" or message is None:  # OK
            return "0"
        if "Hit market maker price range" in message:
            "AMMPS Market Failure: Stopped: Hit market maker price range, shutting market down. ABC MarketMaker Best Ask and Best Bid is outside range 270 , -4 at 2018-01-04 15:45:36.898144"
            return "1"
        if "Error in received data" in message:
            "AMMPS Market Failure: Stopped: Error in received data:bl: 112897069, sl: 106621157084379922432, dividend: 0.09595866952746691, end_simulation: false Value was either too large or too small for an Int64."
            return "-2"
        if "Simulated final day but did not receive signal to end" in message:
            "AMMPS Market Failure: Stopped: Simulated final day but did not receive signal to end"
            return "3"
        else:
            return "4"

    def sim_stats(self):
        """
        Compute statistics over the simulation history.
        """

        sim_stats = {}

        sim_stats["error_message"] = self.error_message

        sim_stats["status_code"] = self.status_code_from_message(self.error_message)

        sim_stats["q"] = self.quarters_per_simulation
        sim_stats["r"] = self.runs_per_quarter

        sim_stats["market_class"] = str(self.broker.market.__class__)

        try:
            sim_stats["ror_volatility"] = self.ror_volatility()
            sim_stats["ror_mean"] = self.ror_mean()
        except Exception as e:
            print("Problem computing ror statistics")
            print(e)

        sim_stats["dividend_growth_rate"] = self.market.dividend_growth_rate
        sim_stats["dividend_shock_std"] = self.market.dividend_shock_std

        sim_stats["seconds"] = (self.end_time - self.start_time).seconds
        sim_stats["end_day"] = self.end_day

        try:
            clean_log_returns = [
                r for r in self.market.log_return_list() if not np.isnan(r)
            ]

            # stylized facts
            sim_stats["log_return_DW_statistic"] = stylized_facts.DW_test(
                np.array([r for r in clean_log_returns])
            )
            sim_stats["log_return_squared_DW_statistic"] = stylized_facts.DW_test(
                np.array([r**2 for r in clean_log_returns])
            )

            sim_stats["log_return_autocorrelation_from_DW"] = (
                2 - sim_stats["log_return_DW_statistic"]
            )
            sim_stats["log_return_squared_autocorrelation_from_DW"] = (
                2 - sim_stats["log_return_squared_DW_statistic"]
            )

            # TODO: Include less confusing autocorrelation values
            # Maybe https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.acf.html
        except Exception as e:
            print("Problem computing stylized facts")
            print(e)

        return sim_stats


class MacroSimulation(MarketSimulation):
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

    pop = None

    # A FinanceModel
    fm = None

    def __init__(
        self,
        pop,
        Fm,
        q=1,
        r=None,
        market=None,
        days_per_quarter=60,
        broker_args=None,
        fm_args={"p1": 0.1, "p2": 0.1, "delta_t1": 60, "delta_t2": 60},
    ):
        """
        pop - agent population
        Fm - expectation class

        q - number of quarters
        r - number of runs per quarter. TODO : Phase this out in favor of more use of 'days_per_quarter'

        market -- the Market class used
        days_per_quarter -- number of days per quarter

        p1,p2,d1,d2 -- memory function parameters for the financial model. TODO: move to attention simulation only.

        """

        #
        # Initialize a basic AgentType
        MarketSimulation.__init__(
            self,
            q=q,
            r=r,
            market=market,
            days_per_quarter=days_per_quarter,
            broker_args=broker_args,
        )

        self.pop = pop

        self.fm = Fm(
            self.market, days_per_quarter=self.days_per_quarter, options=fm_args
        )
        self.fm.calculate_risky_expectations()

        self.history = {}
        self.history["buy_sell"] = []
        self.history["owned_shares"] = []
        self.history["total_assets"] = []
        self.history["mean_income_level"] = []
        self.history["total_consumption_level"] = []
        self.history["permshock_std"] = []
        self.history["class_stats"] = []
        self.history["total_pop_stats"] = []

        # assign macro-days to each agent
        # This is a somewhat frustrating artifact to be cleaned up...
        for agent in self.pop.agents:
            agent.macro_day = 0

    def burn_in(self, n_days):
        """
        Runs for n_days days with no broker activity.
        Used for warming up the agents in the market.

        Tracking is disabled during the burn-in period.
        """
        for day in range(n_days):
            self.broker.transact(np.zeros(1))

            buy_sell, ror, price, dividend = self.broker.trade()

            self.pop.update_agent_wealth_capital_gains(price, ror, dividend)

            self.fm.calculate_risky_expectations()

    def daily_data(self):
        """
        Returns a Pandas DataFrame of the data from the simulation run.
        """
        data = MarketSimulation.daily_data(self)

        ## Total hacks to fix a weird bug:
        ## - Depending on whether the market chose in Mock or RPC, we get getting different lengths of broker macro history
        days_ran = len(data["t"])

        data_dict = {
            "buy_macro": [bs[0] for bs in self.broker.buy_sell_macro_history][
                -days_ran:
            ],
            "sell_macro": [bs[1] for bs in self.broker.buy_sell_macro_history][
                -days_ran:
            ],
            "owned": self.history["owned_shares"][-days_ran:],
            "total_assets": self.history["total_assets"][-days_ran:],
            "mean_income": self.history["mean_income_level"][-days_ran:],
            "total_consumption": self.history["total_consumption_level"][-days_ran:],
            #'permshock_std': self.history['permshock_std'][1:],
            "expected_ror": self.fm.expected_ror_list[-days_ran:],
            "expected_std": self.fm.expected_std_list[-days_ran:],
        }

        try:
            data = data.assign(**data_dict)

        except Exception as e:
            print(e)
            print(
                "Lengths:" + str({key: len(value) for key, value in data_dict.items()})
            )

        return data

    def start_simulation(self, burn_in=None):
        # Initialize share ownership for agents
        for agent in self.pop.agents:
            agent.shares = self.pop.compute_share_demand(agent, self.market.prices[-1])

        MarketSimulation.start_simulation(self, burn_in=burn_in)

    def simulate(self, quarters=None, start=True, burn_in=None):
        """
        DUMMY METHOD -- need to functionalize/parameterize out.
        See #88
        Workhorse method that runs the simulation.
        Also, the 'runs per quarter' introduces all sorts of confusion. See #130

        Parameters
        ------------

        burn_in : int or None
           If not None, then an int number of days with no broker activity to run before starting the simulation.
        """

        if start:
            self.start_simulation(burn_in)

        self.track(-1)

        if quarters is None:
            quarters = self.quarters_per_simulation

        # Main loop
        for quarter in range(quarters):
            print(f"Q-{quarter}")

            day = 0

            for run in range(self.runs_per_quarter):
                # print(f"Q-{quarter}:R-{run}")

                for agent in self.pop.agents:
                    self.broker.transact(
                        self.pop.attend(
                            agent, self.market.prices[-1], self.fm.risky_expectations()
                        )
                    )

                buy_sell, ror, price, dividend = self.broker.trade()
                # print("ror: " + str(ror))

                new_run = True

                for day_in_run in range(int(self.days_per_run)):
                    updates = 0
                    for agent in self.pop.agents:
                        if agent.macro_day == day:
                            updates = updates + 1
                            self.broker.transact(
                                self.pop.macro_update(agent, price), macro=True
                            )

                    if new_run:
                        new_run = False
                    else:
                        # problem is that this should really be nan, nan
                        # putting 0,0 here is a stopgap to make plotting code simpler
                        self.broker.track((0, 0), (0, 0))

                    self.pop.update_agent_wealth_capital_gains(price, ror, dividend)

                    self.track(day)

                    # combine these steps?
                    # add_ror appends to internal history list
                    # self.fm.add_ror(ror)
                    self.fm.calculate_risky_expectations()

                    day = day + 1

        self.broker.close()

        self.end_time = datetime.now()
        self.end_day = day

    def track(self, day, time_delta=0):
        """
        Tracks the current state of agent's total assets and owned shares
        """

        tal = (
            sum([agent.state_now["aLvl"].sum() for agent in self.pop.agents])
            * self.pop.dollars_per_hark_money_unit
        )
        os = sum([sum(agent.shares) for agent in self.pop.agents])

        mpl = (
            mean([agent.state_now["pLvl"].mean() for agent in self.pop.agents])
            * self.pop.dollars_per_hark_money_unit
        )

        tcl = (
            sum(
                [
                    (agent.controls["cNrm"] * agent.state_now["pLvl"]).sum()
                    for agent in self.pop.agents
                    if agent.macro_day == day
                ]
            )
            * self.pop.dollars_per_hark_money_unit
        )

        # Incomplete shock records before all agents reach macro-day, causing warnings.
        # permshock_std = np.array(
        #    [
        #        agent.shocks['PermShk']
        #        for agent in self.pop.agents
        #        if 'PermShk' in agent.shocks
        #    ]
        # ).std()

        self.history["owned_shares"].append(os)
        self.history["total_assets"].append(tal)
        self.history["mean_income_level"].append(mpl)
        self.history["total_consumption_level"].append(tcl)
        # self.history['permshock_std'].append(permshock_std)
        self.history["class_stats"].append(self.pop.class_stats(store=False))
        self.history["total_pop_stats"].append(self.pop.agent_data())
        # self.history['buy_sell'].append(self.broker.buy_sell_history[-1])

    def sim_stats(self):
        """
        Compute statistics over the simulation history.

        TODO: Refactor the bad code. Can class_stats be a more elegant data structure?
        """

        sim_stats = MarketSimulation.sim_stats(self)

        def class_stat_column_to_dict(clabel):
            df = self.history["class_stats"][-1][["label", clabel]]
            # df.columns = df.columns.droplevel(1)

            data = df.set_index("label").to_dict()[clabel]

            return {str((clabel, k)): v for k, v in data.items()}

        # All the try blocks here are confusing, bad code that should be fixed somehow.
        try:
            sim_stats.update(class_stat_column_to_dict("aLvl_mean"))
        except Exception as e:
            print(e)

        try:
            sim_stats.update(class_stat_column_to_dict("aLvl_std"))
        except Exception as e:
            print(e)

        try:
            sim_stats.update(class_stat_column_to_dict("mNrm_ratio_StE_mean"))

            sim_stats.update(class_stat_column_to_dict("mNrm_ratio_StE_std"))
        except Exception as e:
            print(e)
            print("Most likely, the SharkPopulation does not support ")

        total_pop_aLvl = self.history["total_pop_stats"][-1]["aLvl"]

        total_pop_aLvl_mean = total_pop_aLvl.mean()
        total_pop_aLvl_std = total_pop_aLvl.std()

        bs_stats = self.buy_sell_stats()
        sim_stats.update(bs_stats)

        sim_stats.update(self.fm.asset_price_stats())

        sim_stats["total_population_aLvl_mean"] = total_pop_aLvl_mean
        sim_stats["total_population_aLvl_std"] = total_pop_aLvl_std

        sim_stats.update(self.fm.options)
        sim_stats["dollars_per_hark_money_unit"] = self.pop.dollars_per_hark_money_unit

        slope, intercept, r, p, se = stats.linregress(self.market.prices[1:], self.market.dividends[1:])
        sim_stats["price_dividend_r_squared"] = r**2

        p_res = stats.pearsonr(self.market.prices[1:], self.market.dividends[1:])
        sim_stats["price_dividend_pearsonr"] = p_res.statistic

        return sim_stats


class AttentionSimulation(MacroSimulation):
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

    """

    seed = None

    ## upping this to make more agents engaged in trade
    attention_rate = None

    def __init__(
        self,
        pop,
        fm,
        q=1,
        r=None,
        a=None,
        market=None,
        days_per_quarter=60,
        rng=None,
        seed=None,
        broker_args=None,
        fm_args=None,
    ):
        super().__init__(
            pop,
            fm,
            q=q,
            r=r,
            market=market,
            days_per_quarter=days_per_quarter,
            broker_args=broker_args,
            fm_args=fm_args,
        )

        self.rng = rng if rng is not None else np.random.default_rng()

        if seed:
            self.seed = seed
        elif hasattr(rng, "seed"):
            self.seed = rng.seed

        # TODO: Make this more variable.
        if a is not None:
            self.attention_rate = a
        else:
            self.attention_rate = 1 / self.runs_per_quarter

        # assign macro-days to each agent
        for agent in self.pop.agents:
            agent.macro_day = self.rng.integers(self.days_per_quarter)

        # Additional daily values tracked.
        self.history["RiskyAvg_mean"] = []
        self.history["RiskyAvg_std"] = []
        self.history["RiskyStd_mean"] = []
        self.history["RiskyStd_std"] = []

    def simulate(self, quarters=None, start=True, burn_in=None):
        """
        Workhorse method that runs the simulation.

        In the AttentionSimulation, this is done in a special way:
         - Agents have a daily attention rate
         - This is separate from the macro-update day

        Parameters
        ------------

        burn_in : int or None
           If not None, then an int number of days with no broker activity to run before starting the simulation.
        """
        self.start_time = datetime.now()

        if start:
            self.start_simulation(burn_in)

        day = 0

        for agent in self.pop.agents:
            self.pop.attend(
                agent,
                self.market.prices[-1],
                self.fm.risky_expectations(agent),
                day=day,
            )

        self.track(-1)

        if quarters is None:
            quarters = self.quarters_per_simulation

        # Main loop
        for quarter in range(quarters):
            print(f"Q-{quarter}")

            day_of_quarter = 0

            for run in range(self.runs_per_quarter):
                # print(f"Q-{quarter}:R-{run}")

                # Set to a number for a fixed seed, or None to rotate
                for agent in self.pop.agents:
                    if self.rng.random() < self.attention_rate:
                        self.broker.transact(
                            self.pop.attend(
                                agent,
                                self.market.prices[-1],
                                self.fm.risky_expectations(agent),
                                day=day,
                            )
                        )

                try:
                    buy_sell, pror, price, dividend = self.broker.trade()

                except MarketFailureError as e:
                    print("Ending simulation")
                    self.error_message = str(e)
                    break

                new_run = True

                for day_in_run in range(int(self.days_per_run)):
                    updates = 0
                    for agent in self.pop.agents:
                        if agent.macro_day == day_of_quarter:
                            updates = updates + 1
                            self.broker.transact(
                                self.pop.macro_update(agent, price), macro=True
                            )

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

                    self.pop.update_agent_wealth_capital_gains(price, pror, dividend)

                    self.track(day)

                    # combine these steps?
                    # add_ror appends to internal history list
                    # self.fm.add_ror(ror)
                    self.fm.calculate_risky_expectations()

                    day = day + 1
                    day_of_quarter = day_of_quarter + 1

            else:  ## Super obscure syntax choice to break out of nested loop
                print("Normal day")
                continue  ## TODO: remove/revise 'runs' functionality

            print("Market stopped")
            self.end_time = datetime.now()
            self.end_day = day
            return

        self.broker.close()

        self.end_time = datetime.now()
        self.end_day = day

    def sim_stats(self):
        sim_stats = super().sim_stats()

        sim_stats["attention"] = self.attention_rate

        if self.seed is not None:
            sim_stats["seed"] = self.seed


        sim_stats['Expectations_RiskyAvg_mean_final'] = self.history["RiskyAvg_mean"][-1]
        sim_stats["Expectations_RiskyAvg_std_final"] = self.history["RiskyAvg_std"][-1]
        sim_stats["Expectations_RiskyStd_mean_final"] = self.history["RiskyStd_mean"][-1]
        sim_stats["Expectations_RiskyStd_std_final"] = self.history["RiskyStd_std"][-1]

        return sim_stats

    def report_class_stats(self, stat="aLvl", stat_history=None):
        if stat_history is None:
            stat_history = self.history["class_stats"]

        for d, cs in enumerate(self.history["class_stats"]):
            cs["time"] = d

        data = pd.concat(self.history["class_stats"])

        ax = sns.lineplot(data=data, x="time", y="aLvl_mean", hue="label")
        ax.set_title("mean aLvl by class subpopulation")

    def track(self, day, time_delta=0):
        """
        Tracks the current state of agent's total assets and owned shares
        """
        super().track(
            day,
            time_delta
        )

        RiskyAvg_all_agents = np.array([agent.parameters['RiskyAvg'] for agent in self.pop.agents])
        RiskyStd_all_agents = np.array([agent.parameters['RiskyStd'] for agent in self.pop.agents])

        self.history["RiskyAvg_mean"].append(np.mean(RiskyAvg_all_agents))
        self.history["RiskyAvg_std"].append(np.std(RiskyAvg_all_agents))
        self.history["RiskyStd_mean"].append(np.mean(RiskyStd_all_agents))
        self.history["RiskyStd_std"].append(np.std(RiskyStd_all_agents))

class CalibrationSimulation(MarketSimulation):
    """
    A simulation in which the broker makes no activity for some number of days,
    then executes a preset buy and sell order.
    Used to test the price impact on the market.
    """

    market = None

    def __init__(self, q=1, r=None, a=None, market=None):
        MarketSimulation.__init__(self, q=q, r=r, market=market)

        self.history["run_times"] = []

    def simulate(self, start=True, buy_sell_shock=(0, 0), burn_in=0):
        """
        Workhorse method that runs the simulation.
        """
        self.start_time = datetime.now()

        if start:
            self.start_simulation(burn_in)

        self.track(-1)

        start_time = datetime.now()

        day = burn_in if burn_in is not None else 0

        buy = buy_sell_shock[0]
        sell = -buy_sell_shock[1]

        try:
            self.broker.transact(np.array((buy, sell)))
            buy_sell, ror, price, dividend = self.broker.trade()

            end_time = datetime.now()
            time_delta = end_time - start_time

            self.track(day + 1, time_delta=time_delta)

            self.broker.close()

            self.end_time = datetime.now()
            self.end_day = day

        except MarketFailureError as e:
            print("Ending simulation")
            self.end_time = datetime.now()
            self.end_day = day
            self.error_message = str(e)

    def track(self, day, time_delta=0):
        """
        Tracks the current state of agent's total assets and owned shares
        """

        # self.history['buy_sell'].append(self.broker.buy_sell_history[-1])
        self.history["run_times"].append(time_delta)

    def daily_data(self):
        """
        Returns a Pandas DataFrame of the data from the simulation run.
        """
        ## DEBUGGING
        data = None

        data_dict = {
            "t": range(len(self.market.prices) - self.burn_in_val),
            "prices": self.market.prices[self.burn_in_val :],
            "dividends": self.market.dividends[self.burn_in_val :],
            "buy": [None]
            + [bs[0] for bs in self.broker.buy_sell_history][self.burn_in_val :],
            "sell": [None]
            + [bs[1] for bs in self.broker.buy_sell_history][self.burn_in_val :],
            "ror": [None] + self.market.ror_list()[self.burn_in_val :],
            "market_times": self.history["run_times"],
        }

        try:
            data = pd.DataFrame.from_dict(data_dict)

        except Exception as e:
            print(e)
            print(
                "Lengths:" + str({key: len(value) for key, value in data_dict.items()})
            )

        return data


class SeriesSimulation(MarketSimulation):
    """
    A simulation in which the broker executes a predefined series
    of buy and sell orders, without input from macroeconomic agents.

    Used for testing, calibration, and synthetic data creation.
    """

    market = None

    def __init__(self, q=1, r=None, a=None, market=None):
        super().__init__(q=q, r=r, market=market)

        self.history["run_times"] = []

    def simulate(self, start=True, series=[(0, 0)], burn_in=0):
        """
        Workhorse method that runs the simulation.
        """
        self.start_time = datetime.now()

        if start:
            self.start_simulation(burn_in)

        self.track(-1)

        day = burn_in if burn_in is not None else 0

        for order in series:
            day_start_time = datetime.now()

            buy = order[0]
            sell = -order[1]

            self.broker.transact(np.array((buy, sell)))
            buy_sell, ror, price, dividend = self.broker.trade()

            day_end_time = datetime.now()
            time_delta = day_end_time - day_start_time

            self.track(day + 1, time_delta=time_delta)

            day = day + 1

        self.broker.close()

        self.end_time = datetime.now()
        self.end_day = day

    def track(self, day, time_delta=0):
        """
        Tracks the current state of agent's total assets and owned shares
        """

        # self.history['buy_sell'].append(self.broker.buy_sell_history[-1])
        self.history["run_times"].append(time_delta)

    def daily_data(self):
        """
        Returns a Pandas DataFrame of the data from the simulation run.
        """
        ## DEBUGGING
        data = None

        data_dict = {
            "t": range(len(self.market.prices) - self.burn_in_val),
            "prices": self.market.prices[self.burn_in_val :],
            "dividends": self.market.dividends[self.burn_in_val :],
            "buy": [None]
            + [bs[0] for bs in self.broker.buy_sell_history][self.burn_in_val :],
            "sell": [None]
            + [bs[1] for bs in self.broker.buy_sell_history][self.burn_in_val :],
            "ror": [None] + self.market.ror_list()[self.burn_in_val :],
            "market_times": self.history["run_times"],
        }

        try:
            data = pd.DataFrame.from_dict(data_dict)

        except Exception as e:
            print(e)
            print(
                "Lengths:" + str({key: len(value) for key, value in data_dict.items()})
            )

        return data


"""
For visualizing the data from a simulation
"""


def visualize_simulation_data(data):
    plt.rcParams.update(
        {
            "text.usetex": False,
            "font.family": "serif",
            "font.serif": ["Palatino"],
        }
    )

    fig, ax = plt.subplots(
        4,
        sharex="col",
        figsize=(14, 16),
    )

    ax[0].plot(data["total_assets"], alpha=0.5, label="Total assets")
    ax[0].plot(
        [p * o for (p, o) in zip(data["prices"], data["owned"])],
        alpha=0.5,
        label="Owned share value",
    )
    ax[0].plot(
        [100 * o for (p, o) in zip(data["prices"], data["owned"])],
        alpha=0.5,
        label="Owned share quantity * price at time 0",
    )
    ax[0].legend()

    ax[1].plot(data["buy"], alpha=0.5, label="Buy limit")
    ax[1].plot(-data["sell"], alpha=0.5, label="Sell limit")
    ax[1].plot(data["buy_macro"], alpha=0.5, label="Buy orders from macro updates")
    ax[1].plot(-data["sell_macro"], alpha=0.5, label="Sell orders from macro updates")
    ax[1].legend()

    ax[2].plot(data["ror"], alpha=0.5, label="Market rate-of-return")
    ax[2].plot(data["expected_ror"], alpha=0.5, label="Expected ror")
    ax[2].plot(np.zeros(data["expected_ror"].shape), alpha=0.5)
    ax[2].legend()

    ax[3].plot(data["prices"], alpha=0.5, label="Price of asset")
    ax[3].legend()

    ax[0].set_title("Simulation History")
    ax[0].set_ylabel("Dollars")
    ax[1].set_ylabel("Shares")
    ax[2].set_ylabel("Rate of change")
    ax[3].set_ylabel("Dollars")
    ax[3].set_xlabel("Time in Days")

    plt.tight_layout()
    plt.savefig("asset_bubble_run_long.png")
    plt.show()
