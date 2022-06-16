from sharkfin.markets import MockMarket
import unittest


import numpy as np

class TestMockMarket(unittest.TestCase):

    def test_mock(self):
        market = MockMarket()

        market.run_market()
        market.run_market(buy_sell=(10,10))
        market.run_market(buy_sell=(50,0))

        ## test dummy_run
        market.dummy_run()
        self.assertAlmostEqual(market.prices[-1] / market.prices[-2], market.prices[-2] / market.prices[-3])

        # all prices should be positive
        assert all([p > 0 for p in market.prices])

        price = market.get_simulation_price()

        ror = market.daily_rate_of_return(buy_sell=(0,0))

        assert len(market.prices) == len(market.dividends)

        assert market.ror_list()[2] == (market.prices[3] + market.dividends[3]) / market.prices[2] - 1