from sharkfin.expectations import FinanceModel, UsualExpectations
from sharkfin.markets import MockMarket


import numpy as np

def test_FinanceModel():
    fm = FinanceModel(MockMarket(), days_per_quarter = 30)

    fm.market.run_market()
    fm.calculate_risky_expectations()

    fm.market.run_market()
    fm.calculate_risky_expectations()

    a = fm.risky_expectations()

    ror1 = fm.market.ror_list()
    estd1 = fm.expected_std_list.copy()

    fm.market.run_market()
    fm.calculate_risky_expectations()
    
    fm.market.run_market()
    fm.calculate_risky_expectations()

    fm.market.run_market()
    fm.calculate_risky_expectations()

    fm.market.run_market()
    fm.calculate_risky_expectations()

    b = fm.risky_expectations()
    
    ror2 = fm.market.ror_list()
    estd2 = fm.expected_std_list.copy()

    assert len(ror1) != len(ror2)
    assert len(estd1) != len(estd2)
    assert a != b

def test_UsualExpectations():
    fm = UsualExpectations(MockMarket(), days_per_quarter = 30)

    fm.market.run_market()
    fm.calculate_risky_expectations()

    fm.market.run_market()
    fm.calculate_risky_expectations()

    a = fm.risky_expectations()

    ror1 = fm.market.ror_list()
    estd1 = fm.expected_std_list.copy()

    fm.market.run_market()
    fm.calculate_risky_expectations()
    
    fm.market.run_market()
    fm.calculate_risky_expectations()

    fm.market.run_market()
    fm.calculate_risky_expectations()

    fm.market.run_market()
    fm.calculate_risky_expectations()

    b = fm.risky_expectations()
    
    ror2 = fm.market.ror_list()
    estd2 = fm.expected_std_list.copy()

    assert len(ror1) != len(ror2)
    assert len(estd1) != len(estd2)
    assert a == b