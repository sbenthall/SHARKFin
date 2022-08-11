from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple

class AbstractMarket(ABC):
    '''
    Abstract class from which market models should inherit

    defines common methods for all market models.
    '''

    @property
    @abstractmethod
    def prices(self):
        """
        A list of prices, beginning with the default price.
        """
        pass

    @property
    @abstractmethod
    def dividends(self):
        """
        A list of dividends, beginning with the default price.
        """
        pass

    @property
    @abstractmethod
    def dividend_growth_rate(self):
        """
        A list of prices, beginning with the default price.
        """
        pass

    @property
    @abstractmethod
    def dividend_std(self):
        """
        A list of prices, beginning with the default price.
        """
        pass

    @property
    @abstractmethod
    def rng(self):
        """
        A random number generator
        """
        pass

    @abstractmethod
    def run_market(self) -> tuple([float, float]):
        """
        Runs the market for one day and returns the price.
        """
        price = 100
        dividend = 5.0 / 60
        return price, dividend

    @abstractmethod
    def get_simulation_price(self, seed: int, buy_sell: Tuple[int, int]):
        # does this need to be an abstract method or can it be encapsulated in daily_rate_of_return?
        pass

    @abstractmethod
    def daily_rate_of_return(self, seed: int, buy_sell: Tuple[int, int]):
        """
        Just the ROR of the price, not including the dividend.
        """
        pass

    @abstractmethod
    def close_market():
        pass

    def asset_price_stats(self):
        """
        Get statistics on the price of the asset for final reporting.
        """
        price_stats = {}

        price_stats['min_asset_price'] = min(self.prices)
        price_stats['max_asset_price'] = max(self.prices)

        price_stats['idx_min_asset_price'] = np.argmin(self.prices)
        price_stats['idx_max_asset_price'] = np.argmax(self.prices)

        price_stats['mean_asset_price'] = np.mean(self.prices)
        price_stats['std_asset_price'] = np.std(self.prices)

        return price_stats

    def dummy_run(self):
        """
        This acts as if the market 'ran' for one day, but uses the most recent rate of return
        to compute the next price without any stochasticity.
        """
        price = self.prices[-1] / self.prices[-2] * self.prices[-1]
        self.prices.append(price)

        price_to_dividend_ratio = 60 / 0.05
        dividend = price / price_to_dividend_ratio
        self.dividends.append(dividend)
        
        return price, dividend

    def ror_list(self):
        """
        Get a list of the rates of return, INCLUDING the dividend.
        Note the difference with daily_rate_of_return.
        This should be refactored for clarity.

        TODO: THIS WON'T WORK WITH SOME MARKETS WITH A DIFFERENT ROR CALCULATION?
        """
        return [((self.prices[i+1] + self.dividends[i + 1])/ self.prices[i]) - 1 for i in range(len(self.prices) - 1)]


    def log_return_list(self):
        """
        Get a list of the log returns....

        Log returns are defined as the log(price_t+1 / price_t).

        --- These should not _include_ the dividend because the price _reflects_ the dividend

        """
        return [np.log((self.prices[i+1]  + self.dividends[i + 1]) / self.prices[i]) for i in range(len(self.prices) - 1)]

    def next_dividend(self):
        """
        Gets a new dividend value from the old dividend value.
        Uses the dividend growth rate and std.
        A lognormal walk by default, can be overridden.
        """

        div_psi_ror = 1
        # target variance of the price distribution with no broker impact
        div_psi_std = self.dividend_std

        # mean of underlying normal distribution
        exp_ror = np.log((div_psi_ror ** 2) / np.sqrt(div_psi_ror ** 2 + div_psi_std ** 2))
        # standard deviation of underlying distribution
        exp_std = np.sqrt(np.log(1 + div_psi_std ** 2 / div_psi_ror ** 2))

        return self.dividends[-1] * self.rng.lognormal(exp_ror, exp_std) * self.dividend_growth_rate


class MockMarket(AbstractMarket):
    """
    A simple market that produces prices and dividends according to a lognormal
    random walk.
    """
    simulation_price_scale = 1.0
    default_sim_price = 100

    # Empirical data -- redundant with FinanceModel!
    sp500_ror = 0.000628
    sp500_std = 0.011988

    # Storing the last market arguments used for easy access to most
    # recent data
    last_buy_sell = None
    last_seed = None

    seeds = []

    prices = None
    dividends = None

    dividend_growth_rate = None
    dividend_std = None

    rng = None

    def __init__(
        self,
        dividend_growth_rate = 1.000628,
        dividend_std = 0.011988,
        price_to_dividend_ratio = 60 / 0.05,
        rng = None
        ):
        """
        """
        # discounted future value, divided by days per quarter
        self.price_to_dividend_ratio = price_to_dividend_ratio

        self.dividend_growth_rate = dividend_growth_rate
        self.dividend_std = dividend_std

        self.prices = [self.default_sim_price]
        self.dividends = [self.default_sim_price / self.price_to_dividend_ratio]

        self.rng = rng if rng is not None else np.random.default_rng()

    def run_market(self, seed=0, buy_sell=(0,0)):
        """
        Sample from a probability distribution
        """
        self.last_seed = seed
        self.last_buy_sell = buy_sell

        print("run_market, buy_sell: " + str(buy_sell))

        new_dividend = self.next_dividend()
        new_price = new_dividend * self.price_to_dividend_ratio

        self.prices.append(new_price) ## TODO: Should this be when the new rate of return is computed?

        print('price: ' + str(new_price))

        self.dividends.append(new_dividend)

        return new_price, new_dividend

    def get_simulation_price(self, seed=0, buy_sell=(0, 0)):
        """
        Get the price from the simulation run.

        TODO: Refactor this -- the original PNL market was convoluted and this API can be streamlined.
        """

        return self.prices[-1]

    def daily_rate_of_return(self, seed=None, buy_sell=None):

        if seed is None:
            seed = self.last_seed

        if buy_sell is None:
            buy_sell = self.last_buy_sell

        last_sim_price = self.get_simulation_price(seed=seed, buy_sell=buy_sell)

        #if last_sim_price is None:
        #   last_sim_price = self.default_sim_price

        # ror = (last_sim_price * self.simulation_price_scale - 100) / 100
        ror = (self.prices[-1] - self.prices[-2])/self.prices[-2]

        return ror

    def close_market(self):
        return
