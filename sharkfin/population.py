import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
import HARK.ConsumptionSaving.ConsIndShockModel as cism
from sharkfin.utilities import *
import math
import pandas as pd
import random

class AgentPopulation:
    """
    A class encapsulating the population of 'macroeconomy' agents.

    These agents will be initialized with a distribution of parameters,
    such as risk aversion and discount factor.

    Parameters
    ------------

    base_parameters: Dict
        A dictionary of parameters to be shared by all agents.
        These correspond to parameters of the HARK ConsPortfolioModel AgentType

    dist_params: dict of dicts
        A dictionary with [m] values. Keys are parameters.
        Values are dicts with keys: bot, top, n.
        These define a discretized uniform spread of values.

    n_per_class: int
        The values of dist_params define a space of n^m
        agent classes.
        This value is the number of agents [l] of each class to include in
        population.
        Total population will be l*n^m
    """

    agents = None
    base_parameters = None
    stored_class_stats = None
    dist_params = None

    def __init__(self, base_parameters, dist_params, n_per_class, rng = None):
        self.base_parameters = base_parameters
        self.dist_params = dist_params
        self.agents = self.create_distributed_agents(
            self.base_parameters, dist_params, n_per_class, rng = rng
        )

    def agent_df(self):
        '''
        Output a dataframe for agent attributes

        returns agent_df from class_stats
        '''

        records = []

        for agent in self.agents:
            for i, aLvl in enumerate(agent.state_now['aLvl']):
                record = {
                    'aLvl': aLvl,
                    'mNrm': agent.state_now['mNrm'][i],
                    'cNrm': agent.controls['cNrm'][i]
                    if 'cNrm' in agent.controls
                    else None,
                }

                for dp in self.dist_params:
                    record[dp] = agent.parameters[dp]

                records.append(record)

        return pd.DataFrame.from_records(records)

    def class_stats(self, store=False):
        """
        Output the statistics for each class within the population.

        Currently limited to asset level in the final simulated period (aLvl_T)
        """
        # get records for each agent with distributed parameter values and wealth (asset level: aLvl)
        records = []

        for agent in self.agents:
            for i, aLvl in enumerate(agent.state_now['aLvl']):
                record = {
                    'aLvl': aLvl,
                    'mNrm': agent.state_now['mNrm'][i],
                    # difference between mNrm and the equilibrium mNrm from BST
                    'mNrm_ratio_StE': agent.state_now['mNrm'][i] / agent.mNrmStE,
                }

                for dp in self.dist_params:
                    record[dp] = agent.parameters[dp]

                records.append(record)

        agent_df = pd.DataFrame.from_records(records)

        class_stats = (
            agent_df.groupby(list(self.dist_params.keys()))
            .aggregate(['mean', 'std'])
            .reset_index()
        )

        cs = class_stats
        cs['label'] = round(cs['CRRA'], 2).apply(lambda x: f'CRRA: {x}, ') + round(
            cs['DiscFac'], 2
        ).apply(lambda x: f"DiscFac: {x}")
        cs['aLvl_mean'] = cs['aLvl']['mean']
        cs['aLvl_std'] = cs['aLvl']['std']
        cs['mNrm_mean'] = cs['mNrm']['mean']
        cs['mNrm_std'] = cs['mNrm']['std']
        cs['mNrm_ratio_StE_mean'] = cs['mNrm_ratio_StE']['mean']
        cs['mNrm_ratio_StE_std'] = cs['mNrm_ratio_StE']['std']

        if store:
            self.stored_class_stats = class_stats

        return class_stats

    def create_distributed_agents(self, agent_parameters, dist_params, n_per_class, rng = None):
        """
        Creates agents of the given classes with stable parameters.
        Will overwrite the DiscFac with a distribution from CSTW_MPC.

        Parameters
        ----------
        agent_parameters: dict
            Parameters shared by all agents (unless overwritten).

        dist_params: dict of dicts
            Parameters to distribute agents over, with discrete Uniform arguments

        n_per_class: int
            number of agents to instantiate per class
        """
        num_classes = math.prod([dist_params[dp]['n'] for dp in dist_params])
        agent_batches = [{'AgentCount': num_classes}] * n_per_class

        rng = rng if rng is not None else np.random.default_rng()

        agents = [
            cpm.PortfolioConsumerType(
                seed=rng.integers(0, 2**31 - 1),
                **update_return(agent_parameters, ac),
            )
            for ac in agent_batches
        ]

        agents = AgentList(agents, dist_params, rng)

        return agents

    def init_simulation(self):
        """
        Sets up the agents with their state for the state of the simulation
        """
        for agent in self.agents:
            agent.track_vars += ['pLvl', 'mNrm', 'cNrm', 'Share', 'Risky']

            agent.assign_parameters(AdjustPrb=1.0)
            agent.T_sim = 1000  # arbitrary!
            agent.solve()

            agent.initialize_sim()

            if self.stored_class_stats is None:

                ## build an IndShockConsumerType "double" of this agent, with the same parameters
                ind_shock_double = cism.IndShockConsumerType(**agent.parameters)

                ## solve to get the mNrmStE value
                ## that is, the Steady-state Equilibrium value of mNrm, for the IndShockModel
                ind_shock_double.solve()
                mNrmStE = ind_shock_double.solution[0].mNrmStE

                agent.state_now['mNrm'][:] = mNrmStE
                agent.mNrmStE = (
                    mNrmStE  # saving this for later, in case we do the analysis.
                )
            else:
                idx = [agent.parameters[dp] for dp in self.dist_params]
                mNrm = (
                    self.stored_class_stats.copy()
                    .set_index([dp for dp in self.dist_params])
                    .xs((idx))['mNrm']['mean']
                )
                agent.state_now['mNrm'][:] = mNrm

            agent.state_now['aNrm'] = agent.state_now['mNrm'] - agent.solution[
                0
            ].cFuncAdj(agent.state_now['mNrm'])
            agent.state_now['aLvl'] = agent.state_now['aNrm'] * agent.state_now['pLvl']


# Agent List
class AgentList:
    def __init__(self, agents, dist_params, rng):
        #super special nested list data structure
        self.agent_cats = []
        self.idx = -1

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

        # does this create a list of lists of distributed agents? (self.agent_cats)

        for param in dist_params:
            agents_distributed = [
                distribute_params(
                    agent,
                    param,
                    dist_params[param]['n'],
                    # allow other types of distributions
                    # allow support for HARK distributions
                    Uniform(
                        bot=dist_params[param]['bot'],
                        top=dist_params[param]['top']
                    )
                )
                for agent in agents
            ]

            for agent_dist in agents_distributed:
                for agent in agent_dist:
                    ## Why is this happening like this?
                    # To revisit with new Population class
                    agent.seed = rng.integers(100000000)
                    agent.reset_rng()
                    agent.IncShkDstn[0].seed = rng.integers(0,100000000)
                    agent.IncShkDstn[0].reset()

    # return agents
        self.agent_cats = agents_distributed

        self.flattened = list(chain(*self.agent_cats))

        
    def __iter__(self):
        return self


    def __next__(self):
        self.idx += 1

        if self.idx >= len(self.flattened):
            self.idx = -1
            raise StopIteration

        return self.flattened[self.idx]


    def iter_subpops(self):
        for subpop in self.agent_cats:
            yield subpop