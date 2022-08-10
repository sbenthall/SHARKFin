from HARK.Calibration.Income.IncomeTools import sabelhaus_song_var_profile
from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType
from sharkfin.broker import *
from sharkfin.expectations import *
from sharkfin.population import *
from sharkfin.simulation import *
from simulate.parameters import (
    agent_population_params,
    approx_params,
    continuous_dist_params,
)

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

def test_calibration_simulation():
    """
    Sets up and runs an agent population simulation
    """

    parameter_dict = agent_population_params | continuous_dist_params

    parameter_dict["AgentCount"] = 1

    pop = AgentPopulation(SequentialPortfolioConsumerType(), parameter_dict)
    pop.approx_distributions(approx_params)
    pop.parse_params()

    pop.create_distributed_agents()
    pop.create_database()
    pop.solve_distributed_agents()

    pop.solve(merge_by=["RiskyAvg", "RiskyStd"])

    # initialize population model
    pop.init_simulation()

    # arguments to Calibration simulation

    q = 1
    r = 1
    market = None

    sim = CalibrationSimulation(pop, FinanceModel, q=q, r=r, market=market)
    sim.simulate(burn_in=2, buy_sell_shock=(200, 600))

    assert sim.broker.buy_sell_history[1] == (0, 0)
    # assert(len(sim.history['buy_sell']) == 3) # need the padded day
    data = sim.data()

    assert len(data["prices"]) == 4


def test_attention_simulation():
    """
    Sets up and runs an agent population simulation
    """
    parameter_dict = agent_population_params | continuous_dist_params

    parameter_dict["AgentCount"] = 1

    pop = AgentPopulation(SequentialPortfolioConsumerType(), parameter_dict, dollars_per_hark_money_unit=2000)
    pop.approx_distributions(approx_params)
    pop.parse_params()

    pop.create_distributed_agents()
    pop.create_database()
    pop.solve_distributed_agents()

    pop.solve(merge_by=["RiskyAvg", "RiskyStd"])

    # initialize population model
    pop.init_simulation()

    # arguments to attention simulation

    a = 0.2
    q = 1
    r = 1
    market = None

    days_per_quarter = 30

    attsim = AttentionSimulation(
        pop,
        FinanceModel,
        a=a,
        q=q,
        r=r,
        market=market,
        days_per_quarter=days_per_quarter,
    )
    attsim.simulate()

    ## testing for existence of this class stat
    attsim.pop.class_stats()["mNrm_ratio_StE_mean"]

    attsim.data()["sell_macro"]

    attsim.sim_stats()

    assert attsim.days_per_quarter == days_per_quarter
    assert attsim.fm.days_per_quarter == days_per_quarter
