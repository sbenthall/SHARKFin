import numpy as np
from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType
import matplotlib.pyplot as plt
from sharkfin.population import SharkPopulation, SharkPopulationSolution
from sharkfin.utilities import price_dividend_ratio_random_walk
from simulate.parameters import WHITESHARK, LUCAS0

from sharkfin.expectations import UsualExpectations
from sharkfin.markets import MockMarket

LUCAS0

# +
dividend_growth_rate = 1.000203
dividend_std = 0.011983

rng = 23409

market_args = {
        "dividend_growth_rate": dividend_growth_rate,
        "dividend_std": dividend_std,
        "rng": rng,
        "price_to_dividend_ratio": price_dividend_ratio_random_walk(
            LUCAS0['DiscFac'], LUCAS0['CRRA'], dividend_growth_rate, dividend_std
        ),
    }
# -

ue = UsualExpectations(MockMarket(**market_args))
ue.calculate_risky_expectations()
risky_expectations = ue.risky_expectations()

risky_expectations

parameter_dict = LUCAS0.copy()

parameter_dict['aNrmInitMean'] = 10

parameter_dict.update(risky_expectations)

parameter_dict['T_sim'] = 1500

parameter_dict

pop = SharkPopulation(
    SequentialPortfolioConsumerType,
    parameter_dict,
    dollars_per_hark_money_unit=1000,
)

if "approx_params" in parameter_dict:
    pop.approx_distributions(parameter_dict["approx_params"])
else:
    pop.continuous_distributions = {}
    pop.discrete_distributions = {}

pop.create_distributed_agents()
pop.create_database()
pop.solve_distributed_agents()

pop.solve(merge_by=parameter_dict["ex_post"])  # merge_by=["RiskyAvg", "RiskyStd"])

pop.explode_agents(40)

for ag in pop.agent_database['agents']:
    ag.track_vars += ['aNrm', "TranShk"]

a0h = pop.agent_database['agents'][0]

a0h.parameters

# initialize population model
pop.init_simulation()

pop.simulate()

assert pop.agent_database['agents'].map(lambda a: a.history['mNrm'][100]).std() > 0.00000001

history_mNrm = np.stack(pop.agent_database['agents'].map(lambda a: np.log(a.history['mNrm'])).values)

plt.plot(history_mNrm.mean(axis=0))
plt.xlabel("t - time")
plt.ylabel("mean log mNrm")
plt.show()

history_cNrm = np.stack(pop.agent_database['agents'].map(lambda a: np.log(a.history['cNrm'])).values)

plt.plot(history_mNrm.mean(axis=0))
plt.xlabel("t - time")
plt.ylabel("mean log cNrm")
plt.show()

history_aNrm = np.stack(pop.agent_database['agents'].map(lambda a: np.log(a.history['aNrm'])).values)

plt.plot(history_mNrm.mean(axis=0))
plt.xlabel("t - time")
plt.ylabel("mean log aNrm")
plt.show()


