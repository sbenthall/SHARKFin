from HARK.Calibration.Income.IncomeTools import sabelhaus_song_var_profile

### Configuring the agent population
from HARK.distribution import Uniform
from xarray import DataArray

dist_params = {
    "CRRA": {"bot": 2, "top": 10, "n": 3},  # Chosen for "interesting" results
    "DiscFac": {"bot": 0.936, "top": 0.978, "n": 2},  # from CSTW "MPC" results
}

# Get empirical data from Sabelhaus and Song
ssvp = sabelhaus_song_var_profile()

# Assume all the agents are 40 for now.
# We will need to make more coherent assumptions about the timing and age of the population later.
# Scaling from annual to quarterly
idx_40 = ssvp["Age"].index(40)

### parameters shared by all agents
agent_parameters = {
    "aNrmInitStd": 0.0,
    "LivPrb": [0.98**0.25],
    "PermGroFac": [1.01**0.25],
    "pLvlInitMean": 1.0,
    # initial distribution of permanent income
    "pLvlInitStd": 0.0,
    "Rfree": 1.0,
    "TranShkStd": [ssvp["TranShkStd"][idx_40] / 2],
    # Adjust non-multiplicative shock to quarterly
    "PermShkStd": [ssvp["PermShkStd"][idx_40] ** 0.25],
}

### new dictionary for new Agent Population

agent_population_params = {
    "aNrmInitStd": 0.0,
    "LivPrb": 0.98**0.25,
    "PermGroFac": 1.01**0.25,
    "pLvlInitMean": 1.0,
    "pLvlInitStd": 0.0,
    "Rfree": 1.0,
    "TranShkStd": DataArray([ssvp["TranShkStd"][idx_40] / 2], dims="age"),
    "PermShkStd": DataArray([ssvp["PermShkStd"][idx_40] ** 0.25], dims="age"),
}

continuous_dist_params = {
    "CRRA": Uniform(bot=2, top=10),
    "DiscFac": Uniform(bot=0.936, top=0.978),
    "RiskyAvg": Uniform(bot=1, top=1.2),
    "RiskyStd": Uniform(bot=0.1, top=0.3),
}

approx_params = {"CRRA": 3, "DiscFac": 2, "RiskyAvg": 3, "RiskyStd": 3}
