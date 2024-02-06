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

    # initialize population model
    pop1.init_simulation()
    pop1.simulate()

    pop2.init_simulation()
    pop2.simulate()

    pLvls1 = pop1.agent_database["agents"].map(lambda a: a.history["pLvl"].T)
    pLvls2 = pop2.agent_database["agents"].map(lambda a: a.history["pLvl"].T)

    ### Different income levels within one population
    assert((pLvls1[0] - pLvls1[1]).sum() != 0)

    ### Different income levels across two populations with different seeds
    assert((pLvls1[0] - pLvls2[0]).sum() != 0)

    ### BUT ... what about for the first 28 periods? Within a population:
    assert((pLvls1[0][:,:28] - pLvls1[1][:,:28]).sum() != 0)

    ### Across populations with different seeds
    assert((pLvls1[0][:,:28] - pLvls2[0][:,:28]).sum() != 0)