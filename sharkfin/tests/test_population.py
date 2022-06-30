from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType

from sharkfin.population import AgentPopulationNew, AgentPopulationSolution
from simulate.parameters import (
    agent_population_params,
    continuous_dist_params,
    approx_params,
)

parameter_dict = agent_population_params | continuous_dist_params

parameter_dict["cycles"] = 1


def test_agent_population():

    # Initializing an Agent Population

    # Step 1 - create agent population with initial parameters
    ap = AgentPopulationNew(SequentialPortfolioConsumerType(), parameter_dict)

    # Step 2 - provide approximation parameters
    ap.approx_distributions(approx_params)

    # Step 3 - parse all parameters to create distributed agent parameter dictionaries
    ap.parse_params()

    # Step 4 - create distributed agents and put them in a list
    ap.create_distributed_agents()

    # Step 5 - create pandas database of agents for better selection by parameters
    ap.create_database()

    # Step 6 - solve each of the agent groups in the population
    # ap.solve_distributed_agents()

    # Because solving takes so long, create fake terminal solution

    solution = [ap.agents[0].solution_terminal]

    for agent in ap.agents:
        agent.solution = solution

    # Step 7 - initialize simulation for each agent sub-population
    ap.init_simulation()

    # Step 8 - create master solution as attribute of population
    # ap.solve(["RiskyAvg", "RiskyStd"])

    # Creating Master Solution for agent Population separately

    # Step 1. create Agent Population Solution (must follow 1-6 above before this)
    solution = AgentPopulationSolution(ap)

    # Step 2. provide parameters that will become state variables
    solution.merge_solutions(["RiskyAvg", "RiskyStd"])
