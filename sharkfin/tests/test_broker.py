from sharkfin.broker import *
from sharkfin.markets import MockMarket

import numpy as np

def test_broker():
    broker = Broker(MockMarket())

    broker.transact(np.array([-1, 1, -1, 1]))

    assert broker.buy_limit == 2

    broker.transact(np.array([1, -1, 1, -1]), macro = True)

    assert broker.buy_limit == 4
    assert broker.buy_orders_macro == 2

    buy_sell, ror, price, dividend = broker.trade()

    assert buy_sell[1] == 4

    assert broker.buy_sell_history[0][0] == 4
    assert broker.buy_sell_macro_history[0][0] == 2
    
    broker.track((0,0), (0,0))

    assert broker.buy_sell_history[1][0] == 0