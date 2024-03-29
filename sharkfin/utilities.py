from HARK.core import distribute_params
from HARK.distribution import Uniform
from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType
import math
import numpy as np
import random
from itertools import chain

from scipy.interpolate import CubicSpline
from scipy.optimize import fsolve


# Distribution Utilities
def update_return(dict1, dict2):
    """
    Returns new dictionary,
    copying dict1 and updating the values of dict2
    """
    dict3 = dict1.copy()
    dict3.update(dict2)

    return dict3


def distribute(agents, distributed_params):
    """
    Distribue the discount rate among a set of agents according
    the distribution from Carroll et al., "Distribution of Wealth"
    paper.

    Parameters
    ----------

    agents: list of AgentType
        A list of AgentType

    distributed_params:

    Returns
    -------
        agents: A list of AgentType
    """

    # This is hacky. Should streamline this in HARK.

    for param in distributed_params:
        agents_distributed = [
            distribute_params(
                agent,
                param,
                distributed_params[param]["n"],
                Uniform(
                    bot=distributed_params[param]["bot"],
                    top=distributed_params[param]["top"],
                ),
            )
            for agent in agents
        ]

        for agent_dist in agents_distributed:
            for agent in agent_dist:
                agent.seed = random.randint(0, 100000000)
                agent.reset_rng()
                agent.IncShkDstn[0].seed = random.randint(0, 100000000)
                agent.IncShkDstn[0].reset()

        agents = [agent for agent_dist in agents_distributed for agent in agent_dist]

    return agents


# Math Utilities
def ror_quarterly(ror, n_q):
    """
    Convert a daily rate of return to a rate for (n_q) days.
    """
    return pow(1 + ror, n_q) - 1


def sig_quarterly(std, n_q):
    """
    Convert a daily standard deviation to a standard deviation for (n_q) days.

    This formula only holds for special cases (see paper by Andrew Lo),
    but since we are generating the data we meet this special case.
    """
    return math.sqrt(n_q) * std


def lognormal_moments_to_normal(mu_x, std_x):
    """
    Given a mean and standard deviation of a lognormal distribution,
    return the corresponding mu and sigma for the distribution.
    (That is, the mean and standard deviation of the "underlying"
    normal distribution.)
    """
    mu = np.log(mu_x**2 / math.sqrt(mu_x**2 + std_x**2))

    sigma = math.sqrt(np.log(1 + std_x**2 / mu_x**2))

    return mu, sigma


def combine_lognormal_rates(ror1, std1, ror2, std2):
    """
    Given two mean rates of return and standard deviations
    of two lognormal processes (ror1, std1, ror2, std2),
    return a third ror/sigma pair corresponding to the
    moments of the multiplication of the two original processes.
    """
    mean1 = 1 + ror1
    mean2 = 1 + ror2

    mu1, sigma1 = lognormal_moments_to_normal(mean1, std1)
    mu2, sigma2 = lognormal_moments_to_normal(mean2, std2)

    mu3 = mu1 + mu2
    var3 = sigma1**2 + sigma2**2

    ror3 = math.exp(mu3 + var3 / 2) - 1
    sigma3 = math.sqrt((math.exp(var3) - 1) * math.exp(2 * mu3 + var3))

    return ror3, sigma3


def interp_func(x,y):
    def func(z):
        return np.interp(z, x, y)
    
    return func

##### Lucas Pricing Equations

import math


def price_dividend_ratio_random_walk(
    DiscFac, CRRA, dividend_growth_rate, dividend_std, days_per_quarter
):
    ## From Equation 30 from the C. Carroll Lucas asset pricing notes:
    ## http://www.econ2.jhu.edu/people/ccarroll/public/lecturenotes/AssetPricing/LucasAssetPrice.pdf

    ## theta is discount rate (derived from discount factor)

    ## Let the 'subjective return' SR be: (maybe not a good name)
    ## $\beta e^{(1 - \rho)(\gamma - \rho\sigma^2_d/2)$
    ## or, equivalently
    ## $\Gamma^{1-\rho} \beta (\sigma^2_\phi + 1)^{(\rho - 1)\rho /2}$
    ## where
    ## Gamma -- dividend_growth_rate (daily)
    ## beta -- DiscFac (converted to daily)
    ## rho -- CRRA
    ## sigma_phi -- dividend_std
    ##
    ## "Impatience condition": SR < 1
    ##
    ## Price/dividend ratio = SR / (1 - SR)
    ##

    # Assuming DiscFac in argument in quarterly
    DiscFac_daily = DiscFac ** (1.0 / days_per_quarter)

    dividend_shock_std = dividend_std / math.sqrt(dividend_growth_rate)

    subjective_return = (
        dividend_growth_rate ** (1 - CRRA)
        * DiscFac_daily
        * (dividend_shock_std**2 + 1) ** (CRRA * (CRRA - 1) / 2)
    )

    print("subjective_return: " + str(subjective_return))
    assert subjective_return < 1

    return subjective_return / (1 - subjective_return)

def lucas_expected_rate_of_return(pdr, dgr, dsd):
    ### Expected daily ROR and SD assuming
    ### 1. pdr - A constant price-to-dividend-ratio
    ### 2. dgr - A constant mean dividend growth rate
    ### 3. dsd - A (lognormal) random dividend walk

    adjuster = (1 + pdr) / pdr

    # expected daily ror is (1 + pdr) gamma / pdr
    daily_ror = adjuster * dgr - 1
    daily_std = dsd * adjuster * dgr

    return daily_ror, daily_std

def expected_quarterly_returns(DiscFac, CRRA, dgr, dst, days_per_quarter):
    # DiscFac - quarterly discount factor
    # CRRA - CRRA
    # dgr - daily dividend growth rate
    # dst - daily dividend standard deviation

    pdr = price_dividend_ratio_random_walk(
        DiscFac,
        CRRA,
        dgr,
        dst,
        days_per_quarter
    )
    
    (ror, sig) = lucas_expected_rate_of_return(pdr, dgr, dst)
    return ror_quarterly(ror, days_per_quarter), sig_quarterly(sig, days_per_quarter)


## Computing the target wealth

def compute_target_wealth(
    CRRA=6.0,
    DiscFac=0.9,
    RiskyAvg=1.08,
    RiskyStd=0.20,
    PermShkStd=[0.0],
    PermGroFac=[1.0001],
    UnempPrb=0.00
):
    agent_parameters = {}

    agent_parameters["CRRA"] = CRRA
    agent_parameters["DiscFac"] = DiscFac
    agent_parameters["RiskyAvg"] = RiskyAvg
    agent_parameters["RiskyStd"] = RiskyStd
    agent_parameters["PermShkStd"] = PermShkStd
    agent_parameters["PermGroFac"] = PermGroFac
    agent_parameters["UnempPrb"] = UnempPrb
    agent_parameters["LivPrb"] = [1.0]
    
    agent = SequentialPortfolioConsumerType(**agent_parameters)
    
    linear_roots, log_linear_roots, cubic_spline_roots = [], [], []
    
    try:
        agent.solve()
        solved = True
    except Exception as e:
        solved = False
        
        return solved, linear_roots, log_linear_roots, cubic_spline_roots

    cFunc = agent.solution[0].cFuncAdj
    ShareFunc = agent.solution[0].ShareFuncAdj

    def expected_increase(ShareFunc, cFunc, mNrm):
        share = ShareFunc(mNrm)
        aNrm = mNrm - cFunc(mNrm)

        mNrm_next = (
            aNrm
            * (
                share * agent.parameters["RiskyAvg"]
                + (1 - share) * agent.parameters["Rfree"]
            )
            + 1
        )

        gain = mNrm_next - aNrm
        return gain

    def expected_m_next(mNrm):
        share = ShareFunc(mNrm)
        aNrm = mNrm - cFunc(mNrm)
        mNrm_next = (
            aNrm
            * (
                share * agent.parameters["RiskyAvg"]
                + (1 - share) * agent.parameters["Rfree"]
            )
            + 1
        )

        return mNrm_next

    mNrm = np.linspace(0, 5, 1000)

    # plt.plot(mNrm, cFunc(mNrm), label="c")

    #plt.plot(mNrm, mNrm - expected_m_next(mNrm), label="m - E[m']")

    linear_roots = fsolve(interp_func(mNrm, mNrm - expected_m_next(mNrm)), [mNrm[0]])
    log_linear_roots = np.log(fsolve(interp_func(mNrm, mNrm - expected_m_next(mNrm)), [mNrm[0]]))
    cubic_spline_roots = CubicSpline(mNrm,  mNrm - expected_m_next(mNrm)).roots()
    print(f"m - E[m] linear interp roots: {linear_roots}")
    print(f"m - E[m] log roots: {log_linear_roots}")
    print(f"m - E[m] CubicSpine roots: {cubic_spline_roots}")

    #plt.plot(mNrm, np.zeros_like(mNrm), label="0")

    #plt.plot(mNrm, (mNrm - cFunc(mNrm)) * ShareFunc(mNrm), label ="wealth-into-market" )

    #plt.legend()
    
    return solved, linear_roots, log_linear_roots, cubic_spline_roots