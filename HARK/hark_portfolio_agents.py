import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
import HARK.ConsumptionSaving.ConsIndShockModel as cism
from HARK.core import distribute_params
from HARK.distribution import Uniform
import numpy as np
from statistics import mean


### Initializing agents

def update_return(dict1, dict2):
    """
    Returns new dictionary,
    copying dict1 and updating the values of dict2
    """
    dict3 = dict1.copy()
    dict3.update(dict2)

    return dict3

def create_agents(agent_classes, agent_parameters):
    """
    Initialize the agent objects according to standard
    parameterization agent_parameters and agent_classes definition.

    Parameters
    ----------

    agent_classes: list of dicts
        Parameters for each HARK AgentType
        # TODO: Rename, conflict with Python 'class' term

    agent_parameters: dict
        Parameters shared by all agents (unless overwritten).

    Returns
    -------
        agents: a list of HARK agents.
    """
    agents = [
        cpm.PortfolioConsumerType(
            **update_return(agent_parameters, ac)
        )
        for ac
        in agent_classes
    ]

    # This is hacky. Should streamline this in HARK.
    agents_distributed = [
        distribute_params(
            agent,
            'DiscFac',
            5,
            Uniform(bot=0.936, top=0.978)
        ) 
        for agent in agents
    ]

    # distribute the discount factors/time preference/beta
    # from CSTW "Distribution of Wealth"
    agents = [
        agent
        for agent_dist in agents_distributed
        for agent in agent_dist
    ]


    # should be unecessary but a hack to cover a HARK bug
    for agent in agents:
        agent.assign_parameters(
            DiscFac = agent.DiscFac,
            AgentCount = agent.AgentCount
        )

    # TODO: Revisit. Why simulate the agents 1 period here?
    for agent in agents:
        agent.track_vars += ['pLvl','mNrm','cNrm','Share','Risky']

        agent.assign_parameters(AdjustPrb = 1.0)
        agent.T_sim = 1000 # arbitrary!
        agent.solve()

        ### make and equivalent PF model and solve it
        ### to get the steady-state wealth

        pf_clone = cism.PerfForesightConsumerType(**agent.parameters)
        pf_clone.assign_parameters(Rfree = pf_clone.parameters['RiskyAvg'])
        pf_clone.solve()

        agent.initialize_sim()

        # set normalize assets to steady state market resources.
        agent.state_now['mNrm'][:] = pf_clone.solution[0].mNrmStE
        agent.state_now['aNrm'] = agent.state_now['mNrm'] - agent.solution[0].cFuncAdj(agent.state_now['mNrm'])
        agent.state_now['aLvl'] = agent.state_now['aNrm'] * agent.state_now['pLvl']

        #agent.simulate(sim_periods = 1)

        #change it back
        # agent.AdjustPrb = 0.0

    return agents


### Initializing financial values

### These are used for the agent's starting estimations
### of the risky asset

market_rate_of_return = 0.000628
market_standard_deviation = 0.011988
