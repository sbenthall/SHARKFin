from sharkfin.markets import MockMarket
from sharkfin.markets.ammps import ClientRPCMarket
from sharkfin.utilities import price_dividend_ratio_random_walk
import unittest


import numpy as np

class TestMockMarket(unittest.TestCase):

    def test_mock(self):

        market = MockMarket(dividend_growth_rate = 0.000628, dividend_std = 0.011988)

        market.run_market()
        market.run_market(buy_sell=(10,10))
        market.run_market(buy_sell=(50,0))

        ## test dummy_run
        market.dummy_run()
        self.assertAlmostEqual(market.prices[-1] / market.prices[-2], market.prices[-2] / market.prices[-3])

        # all prices should be positive
        assert all([p > 0 for p in market.prices])

        price = market.get_simulation_price()

        ror = market.daily_rate_of_price_return()

        assert len(market.prices) == len(market.dividends)

        assert market.ror_list()[2] == (market.prices[3] + market.dividends[3]) / market.prices[2] - 1

class TestRPCMarket(unittest.TestCase):

    def test_rpc_market(self):
        ## mainly testing abstract class instantiation and syntax at this point
        try:
            ClientRPCMarket()

        except Exception as e:
            print(e)


class TestMarketErrors(unittest.TestCase):

    def test_stopped_market(self):

        dividend_growth_rate = 1.000628
        dividend_std = 0.011988

        pdr = price_dividend_ratio_random_walk(0.95, 5, dividend_growth_rate, dividend_std, 90)

        market = MockMarket(
            dividend_growth_rate = 1.000628,
            dividend_std = 0.011988,
            price_to_dividend_ratio=pdr
            )

        market.run_market()
        market.run_market(buy_sell=(10,10))
        market.run_market(buy_sell=(50,0))

        # This is the intervention:

        market.dividends.append(market.next_dividend())
        market.latest_price = np.nan
        market.prices.append(np.nan)

        price = market.get_simulation_price()
        ror = market.daily_rate_of_price_return()
        ror_list = market.ror_list()

