from pnl_market.market import MarketPNL
from sharkfin.broker import *
from sharkfin.expectations import *
from sharkfin.population import *
from sharkfin.simulation import *
import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)

def test_pnl_market():
    market = MarketPNL()

    market.run_market(buy_sell=(0,0))

    price = market.get_simulation_price()

    ror = market.daily_rate_of_return(buy_sell=(0,0))

'''
def test_calibration_simulation():
    ''''''
    Sets up and runs an agent population simulation
    ''''''
    dist_params = {
    'CRRA' : {'bot' : 2, 'top' : 10, 'n' : 2}, # Chosen for "interesting" results
    'DiscFac' : {'bot' : 0.936, 'top' : 0.978, 'n' : 2} # from CSTW "MPC" results
    }

    ssvp = sabelhaus_song_var_profile()

    #assume all agents are 27
    idx_27 = ssvp['Age'].index(27)

    #parameters shared by all agents
    agent_parameters = {
        'aNrmInitStd' : 0.0,
        'LivPrb' : [0.98 ** 0.25],
        'PermGroFac': [1.01 ** 0.25],
        'pLvlInitMean' : 1.0, # initial distribution of permanent income
        'pLvlInitStd' : 0.0,
        'Rfree' : 1.0,
        'TranShkStd' : [ssvp['TranShkStd'][idx_27] / 2],  # Adjust non-multiplicative shock to quarterly
        'PermShkStd' : [ssvp['PermShkStd'][idx_27] ** 0.25]
    }

    n_per_class = 1

    pop = AgentPopulation(agent_parameters, dist_params, n_per_class)
    
    #initialize the financial model
    fm = FinanceModel()
    
    fm.calculate_risky_expectations()
    agent_parameters.update(fm.risky_expectations())
    
    #initialize population model
    pop.init_simulation()

    # arguments to attention simulation
    
    a = 0.2
    q = 1
    r = 1
    market = None
    
    sim = CalibrationSimulation(pop, fm, a=a, q=q, r=r, market=market)
    sim.pad_market(n_days=1)
    sim.simulate()

    assert(sim.history['buy_sell'][0] == (0, 0))
    ## testing for existence of this class stat
    sim.pop.class_stats()['mNrm_ratio_StE_mean']

    sim.data()['sell_macro']
'''