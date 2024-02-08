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

###############################################################################
# --- Computing the risky expectations from the dividend statistics

from sharkfin.utilities import price_dividend_ratio_random_walk, lucas_expected_rate_of_return, ror_quarterly, sig_quarterly


""
def expected_quarterly_returns(dgr, dst):
    # dgr - daily dividend growth rate
    # dst - daily dividend standard deviation

    pdr = price_dividend_ratio_random_walk(
        quarterly_params["DiscFac"],
        annual_params["CRRA"],
        dgr,
        dst,
        60
    )
    
    (ror, sig) = lucas_expected_rate_of_return(pdr, dgr, dst)
    return ror_quarterly(ror, 60), sig_quarterly(sig, 60)



""
expected_quarterly_returns(1.0000882, 0.00258)

""


""

