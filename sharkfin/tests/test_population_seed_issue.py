import numpy as np
from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType

from sharkfin.population import SharkPopulation, SharkPopulationSolution
from simulate.parameters import LUCAS0, WHITESHARK


def train_pop(pop, parameter_dict):
    if "approx_params" in parameter_dict:
        pop.approx_distributions(parameter_dict["approx_params"])
    else:
        pop.continuous_distributions = {}
        pop.discrete_distributions = {}

    pop.create_distributed_agents()
    pop.create_database()
    pop.solve_distributed_agents()

    pop.solve(merge_by=parameter_dict["ex_post"])  # merge_by=["RiskyAvg", "RiskyStd"])

    pop.explode_agents(3)



def test_random_seeds():
    LUCAS0['T_sim'] = 100

    pop1 = SharkPopulation(
        SequentialPortfolioConsumerType,
        LUCAS0.copy(),
        dollars_per_hark_money_unit=1500,
        seed = 2001
    )

    pop2 = SharkPopulation(
        SequentialPortfolioConsumerType,
        LUCAS0.copy(),
        dollars_per_hark_money_unit=1500,
        seed = 1776
    )

    train_pop(pop1, LUCAS0.copy())
    train_pop(pop2, LUCAS0.copy())

    p1a0 = pop1.agent_database["agents"][0]
    p1a1 = pop1.agent_database["agents"][1]
    p2a0 = pop1.agent_database["agents"][0]

    ### Different income seeds within one population
    assert(p1a0.PermShkStd.seed != p1a1.PermShkStd.seed)

    ### Different income seeds across two populations with different seeds
    assert(p1a0.PermShkStd.seed != p2a0.PermShkStd.seed)
