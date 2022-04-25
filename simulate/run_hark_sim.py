from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType

from sharkfin.population import AgentPopulation, AgentPopulationSolution
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
ap.create_database()
ap.solve_distributed_agents()

ap.init_simulation()

solution = AgentPopulationSolution(ap)
solution.merge_solutions(["RiskyAvg", "RiskyStd"])

