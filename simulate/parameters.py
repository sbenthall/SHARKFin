from HARK.Calibration.Income.IncomeTools import sabelhaus_song_var_profile
from HARK.ConsumptionSaving.ConsPortfolioModel import init_portfolio

### Configuring the agent population
from HARK.distribution import Uniform
from xarray import DataArray

from sharkfin.population import SharkPopulation


def build_population(agent_type, parameters, seed=None, dphm=1500):
    num_per_type = parameters.get("num_per_type", 1)

    pop = SharkPopulation(
        agent_type, parameters, seed=seed, dollars_per_hark_money_unit=dphm
    )
    if "approx_params" in parameters:
        pop.approx_distributions(parameters["approx_params"])

    pop.create_distributed_agents()
    pop.create_database()
    pop.solve_distributed_agents()

    pop.solve(merge_by=parameters["ex_post"])

    pop.explode_agents(num_per_type)

    # initialize population model
    pop.init_simulation()

    return pop


#############################
# WHITESHARK POPULATION
#############################

# Get empirical data from Sabelhaus and Song
ssvp = sabelhaus_song_var_profile()

# Assume all the agents are 40 for now.
# We will need to make more coherent assumptions about the timing and age of the population later.
idx_40 = ssvp["Age"].index(40)

### new dictionary for new Agent Population

whiteshark_agent_population_params = {
    "aNrmInitStd": 0.0,
    "LivPrb": 0.98**0.25,
    "PermGroFac": 1.01**0.25,
    "pLvlInitMean": 1.0,
    "pLvlInitStd": 0.0,
    "Rfree": 1.0,
    # Scaling from annual to quarterly
    "TranShkStd": [ssvp["TranShkStd"][idx_40] / 2],
    "PermShkStd": [ssvp["PermShkStd"][idx_40] ** 0.25],
}

whiteshark_continuous_distributed_params = {
    "CRRA": Uniform(bot=2, top=10),
    "DiscFac": Uniform(bot=0.984, top=0.994),
    "RiskyAvg": Uniform(bot=0.9, top=1.5),
    "RiskyStd": Uniform(bot=-0.07, top=0.37),
}

whiteshark_approx_params = {"CRRA": 3, "DiscFac": 2, "RiskyAvg": 10, "RiskyStd": 10}

### Configuring the agent population

whiteshark_parameter_dict = (
    whiteshark_agent_population_params | whiteshark_continuous_distributed_params
)
whiteshark_parameter_dict["approx_params"] = whiteshark_approx_params
whiteshark_parameter_dict["ex_post"] = ["RiskyAvg", "RiskyStd"]
whiteshark_parameter_dict["AgentCount"] = 1

WHITESHARK = whiteshark_parameter_dict


#############################
# LUCAS0 POPULATION
#############################


### TODO: Population generators that take parameters like CRRA, DisCFac

init_portfolio["cycles"] = 0  # NEED THIS FOR INFINITE HORIZON
init_portfolio["PermGroFac"] = [1.0]  # no drift in perm income
# risk free return, set to 1 to focus on equity premium
init_portfolio["Rfree"] = 1.0
init_portfolio["RiskyAvg"] = 1.05  # eq_prem is RiskyAvg - Rfree = 0.05
init_portfolio["LivPrb"] = [1.0]  # no death

lucas0_agent_population_params = init_portfolio.copy()

lucas0_agent_population_params.update(
    {
        "cycles": 0,  # issue 186
        "aNrmInitStd": 0.28901524,  # calculated using dashboard from default init_portfolio stats
        # "aNrmInitMean": 6
        # "LivPrb": [0.98**0.25], -- Should this be adjusted?
        "PermGroFac": 1.0,
        "Rfree": 1.0,
        ### These are placeholders that will be set when the system is set up.
        "CRRA": 5,
        "DiscFac": 0.90,
        "ex_post": None,  # ex post heterogeneous parameters over which to merge solutions
    }
)

lucas0_parameter_dict = lucas0_agent_population_params
lucas0_parameter_dict["AgentCount"] = 1  # TODO: What should this be?
lucas0_parameter_dict["num_per_type"] = 1000

LUCAS0 = lucas0_parameter_dict
