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

    @abstractmethod
    def run_market():
        """
        Runs the market for one day and returns the price.
        """
        price = 100
        return price

    @abstractmethod
    def get_simulation_price(self, seed: int, buy_sell: Tuple[int, int]):
        # does this need to be an abstract method or can it be encapsulated in daily_rate_of_return?
        pass

    @abstractmethod
    def daily_rate_of_return(self, seed: int, buy_sell: Tuple[int, int]):
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
        

class MockMarket(AbstractMarket):
    """
    A wrapper around the Market PNL model with methods for getting
    data from recent runs.

    Parameters
    ----------
    config_file
    config_local_file

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

    def __init__(self):
        self.prices = [self.default_sim_price]
        pass

    def run_market(self, seed=0, buy_sell=(0,0)):
        """
        Sample from a probability distribution
        """
        self.last_seed = seed
        self.last_buy_sell = buy_sell

        mean = 100 + np.log1p(buy_sell[0]) - np.log1p(buy_sell[1])
        std = 10 + np.log1p(buy_sell[0] + buy_sell[1])
        price = np.random.normal(mean, std)
                
        self.prices.append(price)

        return price

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

        if last_sim_price is None:
            last_sim_price = self.default_sim_price

        ror = (last_sim_price * self.simulation_price_scale - 100) / 100

        ror = (
            self.sp500_std * (ror) + self.sp500_ror
        )

        return ror

    def close_market(self):
        return
