import hark_portfolio_agents as hpa
import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)

def test_mock_market():
  mock = hpa.MockMarket()

  mock.run_market()

  price = mock.get_simulation_price()

  ror = mock.daily_rate_of_return(buy_sell=(0,0))

def test_pnl_market():
  mock = hpa.MarketPNL()

  mock.run_market(buy_sell=(0,0))

  price = mock.get_simulation_price()

  ror = mock.daily_rate_of_return(buy_sell=(0,0))

def test_agent_population():
    '''
    Sets up and runs an agent population simulation
    '''
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



    pop = hpa.AgentPopulation(agent_parameters, dist_params, n_per_class)
    
    #initialize the financial model
    fm = hpa.FinanceModel()
    
    fm.calculate_risky_expectations()
    agent_parameters.update(fm.risky_expectations())
    
    #initialize population model
    pop.init_simulation()

    # arguments to attention simulation
    n_per_class = 1
    a = 0.2
    q = 1
    r = 1
    market = None
    
    attsim = hpa.AttentionSimulation(pop, fm, a=a, q=q, r=r, market=market)
    attsim.simulate()
    
    

