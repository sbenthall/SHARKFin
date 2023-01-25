import numpy as np
from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType
from sharkfin.population import AgentPopulation, AgentPopulationSolution
from simulate.parameters import (
    WHITESHARK,
    LUCAS0 
)

def test_lucas_agent_population():

    pop_DiscFac = 0.95
    pop_CRRA = 5

    parameter_dict = LUCAS0.copy()

    parameter_dict['DiscFac'] = pop_DiscFac,
    parameter_dict['CRRA'] = pop_CRRA

    pop = AgentPopulation(
        SequentialPortfolioConsumerType(),
        parameter_dict,
        rng = None,
        dollars_per_hark_money_unit = 1500
        )

    if 'approx_params' in parameter_dict:
        pop.approx_distributions(parameter_dict['approx_params'])
    pop.parse_params()

    pop.create_distributed_agents()
    pop.create_database()
    pop.solve_distributed_agents()

    pop.solve(merge_by = parameter_dict['ex_post']) #merge_by=["RiskyAvg", "RiskyStd"])

    # initialize population model
    pop.init_simulation()

    return pop

def test_whiteshark_agent_population():

    seed = 14
    # Initializing an Agent Population

    # Step 1 - create agent population with initial parameters
    ap = AgentPopulation(
        SequentialPortfolioConsumerType(),
        WHITESHARK,
        rng=np.random.default_rng(seed),
    )
    # ADD PRINT LINE AFTER EVERY STEP
    print("created agent population")

    # Step 2 - provide approximation parameters
    ap.approx_distributions(WHITESHARK['approx_params'])
    print("approximated continuous distributions")

    # Step 3 - parse all parameters to create distributed agent parameter dictionaries
    ap.parse_params()
    print("parsed parameters")

    # Step 4 - create distributed agents and put them in a list
    ap.create_distributed_agents()
    print("created distributed agents")

    # Step 5 - create pandas database of agents for better selection by parameters
    ap.create_database()
    print("created agent database")

    # Step 6 - solve each of the agent groups in the population
    ap.solve_distributed_agents()
    print("solved distributed agents")

    # Step 7 - initialize simulation for each agent sub-population
    ap.init_simulation()
    print("initialized simulation")

    # Step 8 - create master solution as attribute of population
    ap.solve(WHITESHARK["ex_post"])

    # Creating Master Solution for agent Population separately

    # Step 1. create Agent Population Solution (must follow 1-6 above before this)
    solution = AgentPopulationSolution(ap)
    print("created solution object")

    # Step 2. provide parameters that will become state variables
    solution.merge_solutions(WHITESHARK["ex_post"])
    solution.merge_solutions(["CRRA", "RiskyAvg", "RiskyStd"])
    print("merged solutions")

    ap.agent_data()
    ap.class_stats()

    # test solutions

    for agent in ap.agents:

        # before assigning master solution

        cFuncAdj = agent.solution[0].cFuncAdj
        shareFunc = agent.solution[0].ShareFuncAdj

        # after assigning master solution

        ap.assign_solution(agent)

        before = cFuncAdj(10)
        after = agent.solution[0].cFuncAdj(10)

        assert np.allclose(before, after)

        before = shareFunc(10)
        after = agent.solution[0].ShareFuncAdj(10)

        assert np.allclose(before, after)
