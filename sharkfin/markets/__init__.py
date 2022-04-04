from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple
class AbstractMarket(ABC):
    '''
    Abstract class from which market models should inherit

    defines common methods for all market models.
    '''

    @abstractmethod
    def run_market():
        pass

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
        

class MockMarket(AbstractMarket):
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

    seeds = []

    def __init__(self):
        pass

    def run_market(self, seed=0, buy_sell=0):
        """
        Sample from a probability distribution
        """
        self.last_seed = seed
        self.last_buy_sell = buy_sell

    def get_simulation_price(self, seed=0, buy_sell=(0, 0)):
        """
        Get the price from the simulation run.

        TODO: Better docstring
        """
        mean = 400 + np.log1p(buy_sell[0]) - np.log1p(buy_sell[1])
        std = 10 + np.log1p(buy_sell[0] + buy_sell[1])
        price = np.random.normal(mean, std)
        return price

    def daily_rate_of_return(self, seed=None, buy_sell=None):

        if seed is None:
            seed = self.last_seed

        if buy_sell is None:
            buy_sell = self.last_buy_sell

        last_sim_price = self.get_simulation_price(seed=seed, buy_sell=buy_sell)

        if last_sim_price is None:
            last_sim_price = self.default_sim_price

        ror = (last_sim_price * self.simulation_price_scale - 100) / 100

        # adjust to calibrated NetLogo to S&P500
        ror = (
            self.sp500_std * (ror - self.netlogo_ror) / self.netlogo_std
            + self.sp500_ror
        )

        return ror

    def close_market(self):
        return
