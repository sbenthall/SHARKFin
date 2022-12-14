from HARK.core import distribute_params
from HARK.distribution import Uniform
import math
import numpy as np
import random
from itertools import chain

# Distribution Utilities
def update_return(dict1, dict2):
    """
    Returns new dictionary,
    copying dict1 and updating the values of dict2
    """
    dict3 = dict1.copy()
    dict3.update(dict2)

    return dict3


def distribute(agents, dist_params):
    """
    Distribue the discount rate among a set of agents according
    the distribution from Carroll et al., "Distribution of Wealth"
    paper.

    Parameters
    ----------

    agents: list of AgentType
        A list of AgentType

    dist_params:

    Returns
    -------
        agents: A list of AgentType
    """

    # This is hacky. Should streamline this in HARK.

    for param in dist_params:
        agents_distributed = [
            distribute_params(
                agent,
                param,
                dist_params[param]['n'],
                Uniform(bot=dist_params[param]['bot'], top=dist_params[param]['top']),
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

##### Lucas Pricing Equations



def price_dividend_ratio_random_walk(DiscFac, CRRA, dividend_std):
    ## From Equation 21 from the C. Carroll Lucas asset pricing notes:
    ## http://www.econ2.jhu.edu/people/ccarroll/public/lecturenotes/AssetPricing/LucasAssetPrice.pdf

    ## theta is discount rate (derived from discount factor)
    theta = 1 / DiscFac - 1

    ## Need to get the standard deviation of the underlying normal distribution
    div_psi_ror = 1
    # target variance of the price distribution with no broker impact
    div_psi_std = dividend_std

    # mean of underlying normal distribution
    exp_ror = np.log((div_psi_ror ** 2) / np.sqrt(div_psi_ror ** 2 + div_psi_std ** 2))
    # standard deviation of underlying distribution
    exp_std = np.sqrt(np.log(1 + div_psi_std ** 2 / div_psi_ror ** 2))

    return 1.0 / (theta - (0.5 * CRRA * (1 - CRRA) * (exp_std ** 2)))


"""
TODO

def lucas_expected_rate_of_return():

    pdr # price-dividend ratio

    d_growth_rate # dividend mean rate of return
    d_std # dividend standard deviation

    p_growth_rate = pdr * d_growth_rate #?
    p_std = pdr * d_std #?

    ror = ((d_1 + p_1)   / p_0)
"""