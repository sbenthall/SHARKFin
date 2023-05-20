import numpy as np
from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType
import matplotlib.pyplot as plt
from sharkfin.population import SharkPopulation, SharkPopulationSolution
from simulate.parameters import WHITESHARK, LUCAS0

from sharkfin.expectations import UsualExpectations
from sharkfin.markets import MockMarket

ue = UsualExpectations(MockMarket())
ue.calculate_risky_expectations()
risky_expectations = ue.risky_expectations()

parameter_dict = LUCAS0.copy()

parameter_dict.update(risky_expectations)

parameter_dict['T_sim'] = 3000

pop = SharkPopulation(
    SequentialPortfolioConsumerType,
    parameter_dict,
    dollars_per_hark_money_unit=1500,
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

pop.explode_agents(3000)

# initialize population model
pop.init_simulation()

pop.simulate()

assert pop.agent_database['agents'].map(lambda a: a.history['mNrm'][100]).std() > 0.00000001

history = np.stack(pop.agent_database['agents'].map(lambda a: np.log(a.history['mNrm'])).values)

plt.plot(history.mean(axis=0))
plt.xlabel("t - time")
plt.ylabel("mean log mNrm")
plt.show()
