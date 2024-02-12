import numpy as np
from HARK.ConsumptionSaving.ConsPortfolioModel import init_portfolio

######################
# Change Defaults    #
# #####################

sharkfin_portfolio = init_portfolio.copy()
sharkfin_portfolio["cycles"] = 0  # 0 for infinite horizon
sharkfin_portfolio["PermGroFac"] = [1.0]  # no drift in perm income
sharkfin_portfolio["LivPrb"] = [1.0]  # no death
sharkfin_portfolio["Rfree"] = 1.0  # risk free return, to focus on eq_prem
sharkfin_portfolio["ex_post"] = None  # ex post parameters
sharkfin_portfolio["UnempPrb"] = 0  # no unemployment

######################
# Annual Parameters  #
# #####################

annual_params = sharkfin_portfolio.copy()
annual_params["CRRA"] = 5
annual_params["DiscFac"] = 0.90
annual_params["RiskyAvg"] = 1.05  # eq_prem is RiskyAvg - Rfree = 0.05
annual_params["RiskyStd"] = 0.2  # standard deviation of risky returns
annual_params["PermShkStd"] = [0.1]  # standard deviation of permanent shocks
annual_params["TranShkStd"] = [0.1]  # standard deviation of transitory shocks

######################
# Quarterly Parameters  #
# #####################

quarterly_params = annual_params.copy()
quarterly_params["DiscFac"] = annual_params["DiscFac"] ** (1 / 4)
quarterly_params["RiskyAvg"] = annual_params["RiskyAvg"] ** (1 / 4)
quarterly_params["RiskyStd"] = annual_params["RiskyStd"] / 2
quarterly_params["PermShkStd"] = list(np.asarray(annual_params["PermShkStd"]) / 2)
quarterly_params["TranShkStd"] = list(4 * np.asarray(annual_params["TranShkStd"]))
quarterly_params["aXtraMax"] = 4 * annual_params["aXtraMax"]

""
quarterly_params["RiskyAvg"]

""
quarterly_params["RiskyStd"]

""
quarterly_params

###############################################################################
# --- Computing the risky expectations from the dividend statistics

from sharkfin.utilities import expected_quarterly_returns


""



""
expected_quarterly_returns(1.0002, 0.011)

""
1.013848  ** 4

""
n = 100

dgr_grid = np.linspace(1.000, 1.0005, n)
dst_grid = np.linspace(0.007, 0.015, n)

rors = np.zeros((n,n))
sigs = np.zeros((n,n))

for i in range(n):
    for j in range(n):
        try:
            ror, sig = expected_quarterly_returns(dgr_grid[i], dst_grid[j])
            rors[i,j] = ror - 0.0123
            sigs[i,j] = sig - 0.1
        except:
            rors[i,j] = np.nan
            sigs[i,j] = np.nan



""
rors[:20, :]

""
import matplotlib.pyplot as plt

""
error = np.absolute(ror) + np.absolute(sigs)

""
plt.imshow(error)
plt.colorbar()

###############################################################################
# Looking for '0' on both of these plots below. Notice how close that puts us to the boundary.

plt.imshow(rors)
plt.colorbar()

""
plt.imshow(sigs)
plt.colorbar()

""

