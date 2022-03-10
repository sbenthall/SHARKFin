from HARK.Calibration.Income.IncomeTools import sabelhaus_song_var_profile

### Configuring the agent population

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
    "LivPrb": [0.98 ** 0.25],
    "PermGroFac": [1.01 ** 0.25],
    "pLvlInitMean": 1.0,  # initial distribution of permanent income
    "pLvlInitStd": 0.0,
    "Rfree": 1.0,
    "TranShkStd": [
        ssvp["TranShkStd"][idx_40] / 2
    ],  # Adjust non-multiplicative shock to quarterly
    "PermShkStd": [ssvp["PermShkStd"][idx_40] ** 0.25],
}
