from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType

from sharkfin.expectations import *
from sharkfin.population import *
from sharkfin.simulation import *
from simulate.parameters import (
    agent_population_params,
    continuous_dist_params,
    approx_params
)


def test_mock_market():
    mock = MockMarket()

    mock.run_market()

    price = mock.get_simulation_price()

    ror = mock.daily_rate_of_return(buy_sell=(0, 0))


# See #72 #74 - either make this conditional on proper PNL installation
# or remove if we are deprecating that feature
#
# def test_pnl_market():
#  mock = hpa.MarketPNL()
#
#  mock.run_market(buy_sell=(0,0))
#
#  price = mock.get_simulation_price()
#
#  ror = mock.daily_rate_of_return(buy_sell=(0,0))

def test_attention_simulation():
    '''
    Sets up and runs an agent population simulation
    '''
    parameter_dict = agent_population_params | continuous_dist_params

    pop = AgentPopulation(SequentialPortfolioConsumerType(), parameter_dict)
    pop.approx_distributions(approx_params)
    pop.parse_params()

    pop.create_distributed_agents()

    # initialize the financial model
    fm = FinanceModel()

    fm.calculate_risky_expectations()
    parameter_dict.update(fm.risky_expectations())

    # initialize population model
    pop.init_simulation()

    # arguments to attention simulation

    a = 0.2
    q = 1
    r = 1
    market = None

    attsim = AttentionSimulation(pop, fm, a=a, q=q, r=r, market=market)
    attsim.simulate()

    ## testing for existence of this class stat
    attsim.pop.class_stats()['mNrm_ratio_StE_mean']

    attsim.data()['sell_macro']


def test_calibration_simulation():
    '''
    Sets up and runs an agent population simulation
    '''
    dist_params = {
        'CRRA': {'bot': 2, 'top': 10, 'n': 2},  # Chosen for "interesting" results
        'DiscFac': {'bot': 0.936, 'top': 0.978, 'n': 2}  # from CSTW "MPC" results
    }

    ssvp = sabelhaus_song_var_profile()

    # assume all agents are 27
    idx_27 = ssvp['Age'].index(27)

    # parameters shared by all agents
    agent_parameters = {
        'aNrmInitStd': 0.0,
        'LivPrb': [0.98 ** 0.25],
        'PermGroFac': [1.01 ** 0.25],
        'pLvlInitMean': 1.0,  # initial distribution of permanent income
        'pLvlInitStd': 0.0,
        'Rfree': 1.0,
        'TranShkStd': [ssvp['TranShkStd'][idx_27] / 2],  # Adjust non-multiplicative shock to quarterly
        'PermShkStd': [ssvp['PermShkStd'][idx_27] ** 0.25]
    }

    n_per_class = 1

    pop = AgentPopulation(agent_parameters, dist_params, n_per_class)

    # initialize the financial model
    fm = FinanceModel()

    fm.calculate_risky_expectations()
    agent_parameters.update(fm.risky_expectations())

    # initialize population model
    pop.init_simulation()

    # arguments to Calibration simulation

    q = 1
    r = 1
    market = None

    sim = CalibrationSimulation(pop, fm, q=q, r=r, market=market)
    sim.simulate(n_days=2, buy_sell_shock=(200, 600))

    assert (sim.history['buy_sell'][0] == (0, 0))
    # assert(len(sim.history['buy_sell']) == 3) # need the padded day
    data = sim.data()

    assert (len(data['prices']) == 3)
