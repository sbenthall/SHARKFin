from HARK.Calibration.Income.IncomeTools import sabelhaus_song_var_profile

### Configuring the agent population
from HARK.distribution import Uniform
from xarray import DataArray

from sharkfin.population import AgentPopulation


def build_population(agent_type, parameters, rng=None, dphm=1500):

    num_per_type = parameters.pop("num_per_type", 1)

    pop = AgentPopulation(
        agent_type(), parameters, rng=rng, dollars_per_hark_money_unit=dphm
    )
    if "approx_params" in parameters:
        pop.approx_distributions(parameters["approx_params"])
    pop.parse_params()

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
    "TranShkStd": DataArray([ssvp["TranShkStd"][idx_40] / 2], dims="age"),
    "PermShkStd": DataArray([ssvp["PermShkStd"][idx_40] ** 0.25], dims="age"),
}

whiteshark_continuous_dist_params = {
    "CRRA": Uniform(bot=2, top=10),
    "DiscFac": Uniform(bot=0.936, top=0.978),
    "RiskyAvg": Uniform(bot=0.9, top=1.5),
    "RiskyStd": Uniform(bot=-0.07, top=0.37),
}

whiteshark_approx_params = {"CRRA": 3, "DiscFac": 2, "RiskyAvg": 10, "RiskyStd": 10}

### Configuring the agent population

whiteshark_parameter_dict = (
    whiteshark_agent_population_params | whiteshark_continuous_dist_params
)
whiteshark_parameter_dict["approx_params"] = whiteshark_approx_params
whiteshark_parameter_dict["ex_post"] = ["RiskyAvg", "RiskyStd"]
whiteshark_parameter_dict["AgentCount"] = 1

WHITESHARK = whiteshark_parameter_dict


#############################
# LUCAS0 POPULATION
#############################


### TODO: Population generators that take parameters like CRRA, DisCFac

lucas0_agent_population_params = {
    "cycles": 0,  # issue 186
    "aNrmInitStd": 0.0,
    "LivPrb": 0.98**0.25,
    "PermGroFac": 1.0,
    "pLvlInitMean": 0.0,  ## Intention: Shut down income. But this might not do it.
    "pLvlInitStd": 0.0,
    "Rfree": 1.0,
    # Scaling from annual to quarterly
    "TranShkStd": [0],
    "PermShkStd": [0],
    ### These are placeholders that will be set when the system is set up.
    "CRRA": 5,
    "DiscFac": 0.96,
    "ex_post": None,  # ex post heterogeneous parameters over which to merge solutions
}

lucas0_parameter_dict = lucas0_agent_population_params
lucas0_parameter_dict["AgentCount"] = 10  # TODO: What should this be?
lucas0_agent_population_params["num_per_type"] = 10

LUCAS0 = lucas0_parameter_dict
