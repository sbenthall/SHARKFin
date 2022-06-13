from sharkfin.markets import MockMarket


import numpy as np

def test_MockMarket():
    market = MockMarket()

    market.run_market()
    market.run_market(buy_sell=(10,10))
    market.run_market(buy_sell=(50,0))

    ## test dummy_run
    market.dummy_run()
    assert market.prices[-1] / market.prices[-2] == market.prices[-2] / market.prices[-3]

    assert all([p > 0 for p in market.prices])

    price = mock.get_simulation_price()

    ror = mock.daily_rate_of_return(buy_sell=(0,0))