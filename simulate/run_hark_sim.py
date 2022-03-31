from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType

from macro.agent_population import AgentPopulation
from simulate.parameters import (
    agent_population_params,
    continuous_dist_params,
    approx_params,
)

parameter_dict = agent_population_params | continuous_dist_params

ap = AgentPopulation(SequentialPortfolioConsumerType(), parameter_dict)
ap.approx_distributions(approx_params)
ap.parse_params()

ap.create_distributed_agents()
ap.solve_distributed_agents()

ap.init_simulation()
