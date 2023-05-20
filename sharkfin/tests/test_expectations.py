import HARK.ConsumptionSaving.ConsIndShockModel as cism
from sharkfin.expectations import FinanceModel, InferentialExpectations, UsualExpectations
from sharkfin.markets import MockMarket

import numpy as np
import unittest

class TestFinanceModel(unittest.TestCase):

    def test_FinanceModel(self):
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

class TestUsualExpectations(unittest.TestCase):
    def test_UsualExpectations(self):
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
    
        b = fm.risky_expectations()
    
        ror2 = fm.market.ror_list()
        estd2 = fm.expected_std_list.copy()

        assert len(ror1) != len(ror2)
        assert len(estd1) != len(estd2)
        assert a == b

class TestInferentialExpectations(unittest.TestCase):
    def test_InferentialExpectations(self):

        ### Testing with zeta below the p-value
        agent = cism.IndShockConsumerType()
        rng = np.random.default_rng(seed = 20230424)
        market = MockMarket(rng = rng)
        fm = InferentialExpectations(market, days_per_quarter = 30)

        print(fm.daily_ror)
        
        fm.zeta = 0.35

        fm.market.run_market()
        fm.calculate_risky_expectations()

        fm.market.run_market()
        fm.calculate_risky_expectations()

        agent.assign_parameters(**{'attention_days' : [0, 1]})
        ## Should be USUAL expectations
        usual = fm.risky_expectations(agent)

        ### Testing with zeta above the p-value

        agent = cism.IndShockConsumerType()
        rng = np.random.default_rng(seed = 20230424)
        fm = InferentialExpectations(MockMarket(rng = rng), days_per_quarter = 30)

        fm.zeta = 0.45

        fm.market.run_market()
        fm.calculate_risky_expectations()

        fm.market.run_market()
        fm.calculate_risky_expectations()

        agent.assign_parameters(**{'attention_days' : [0, 1]})
        # Should be STRANGE expectations
        strange = fm.risky_expectations(agent)

        # USUAL != STRANGE
        assert usual['RiskyAvg'] != strange['RiskyAvg']
        assert usual['RiskyStd'] != strange['RiskyStd']

        ## But using only one of the market ROR points (the one closest to the mean)
        ## means the p-value does not mean the threshold.
        agent.assign_parameters(**{'attention_days' : [1]})
        usual_2 = fm.risky_expectations(agent)

        self.assertAlmostEqual(usual['RiskyAvg'], usual_2['RiskyAvg'])
        self.assertAlmostEqual(usual['RiskyStd'], usual_2['RiskyStd'])

        usual_fm = UsualExpectations(market, days_per_quarter = 30)
        usual_fm.calculate_risky_expectations()
        u_3 = usual_fm.risky_expectations()

        assert usual['RiskyAvg'] == u_3['RiskyAvg']
        assert usual['RiskyStd'] == u_3['RiskyStd']