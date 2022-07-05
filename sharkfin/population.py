from dataclasses import dataclass
from typing import NewType

import HARK.ConsumptionSaving.ConsIndShockModel as cism
import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
import pandas as pd
from HARK.core import AgentType
from HARK.distribution import (
    Distribution,
    IndexDistribution,
    combine_indep_dstns,
)
from HARK.interpolation import LinearInterpOnInterp1D, LinearInterpOnInterp2D
from xarray import DataArray

from sharkfin.utilities import *

ParameterDict = NewType("ParameterDict", dict)


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

    def __init__(self, base_parameters, dist_params, n_per_class, rng=None):
        self.base_parameters = base_parameters
        self.dist_params = dist_params
        self.agents = self.create_distributed_agents(
            self.base_parameters, dist_params, n_per_class, rng=rng
        )

    def agent_df(self):
        """
        Output a dataframe for agent attributes

        returns agent_df from class_stats
        """

        records = []

        for agent in self.agents:
            for i, aLvl in enumerate(agent.state_now["aLvl"]):
                record = {
                    "aLvl": aLvl,
                    "mNrm": agent.state_now["mNrm"][i],
                    "cNrm": agent.controls["cNrm"][i]
                    if "cNrm" in agent.controls
                    else None,
                    # difference between mNrm and the equilibrium mNrm from BST
                    "mNrm_ratio_StE": agent.state_now["mNrm"][i] / agent.mNrmStE,
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
        agent_df =  self.agent_df()

        class_stats = (
            agent_df.groupby(list(self.dist_params.keys()))
            .aggregate(["mean", "std"])
            .reset_index()
        )

        cs = class_stats
        cs["label"] = round(cs["CRRA"], 2).apply(lambda x: f"CRRA: {x}, ") + round(
            cs["DiscFac"], 2
        ).apply(lambda x: f"DiscFac: {x}")
        cs["aLvl_mean"] = cs["aLvl"]["mean"]
        cs["aLvl_std"] = cs["aLvl"]["std"]
        cs["mNrm_mean"] = cs["mNrm"]["mean"]
        cs["mNrm_std"] = cs["mNrm"]["std"]
        cs["mNrm_ratio_StE_mean"] = cs["mNrm_ratio_StE"]["mean"]
        cs["mNrm_ratio_StE_std"] = cs["mNrm_ratio_StE"]["std"]

        if store:
            self.stored_class_stats = class_stats

        return class_stats

    def create_distributed_agents(
        self, agent_parameters, dist_params, n_per_class, rng=None
    ):
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
        num_classes = math.prod([dist_params[dp]["n"] for dp in dist_params])
        agent_batches = [{"AgentCount": num_classes}] * n_per_class

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
            agent.track_vars += ["pLvl", "mNrm", "cNrm", "Share", "Risky"]

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

                agent.state_now["mNrm"][:] = mNrmStE
                agent.mNrmStE = (
                    mNrmStE  # saving this for later, in case we do the analysis.
                )
            else:
                idx = [agent.parameters[dp] for dp in self.dist_params]
                mNrm = (
                    self.stored_class_stats.copy()
                    .set_index([dp for dp in self.dist_params])
                    .xs((idx))["mNrm"]["mean"]
                )
                agent.state_now["mNrm"][:] = mNrm

            agent.state_now["aNrm"] = agent.state_now["mNrm"] - agent.solution[
                0
            ].cFuncAdj(agent.state_now["mNrm"])
            agent.state_now["aLvl"] = agent.state_now["aNrm"] * agent.state_now["pLvl"]


# Agent List
class AgentList:
    def __init__(self, agents, dist_params, rng):
        # super special nested list data structure
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
                    dist_params[param]["n"],
                    # allow other types of distributions
                    # allow support for HARK distributions
                    Uniform(
                        bot=dist_params[param]["bot"], top=dist_params[param]["top"]
                    ),
                )
                for agent in agents
            ]

            for agent_dist in agents_distributed:
                for agent in agent_dist:
                    ## Why is this happening like this?
                    # To revisit with new Population class
                    agent.seed = rng.integers(100000000)
                    agent.reset_rng()
                    agent.IncShkDstn[0].seed = rng.integers(0, 100000000)
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


@dataclass
class AgentPopulationNew:
    agent_class: AgentType
    parameter_dict: ParameterDict
    t_age: int = None
    agent_class_count: int = None

    def __post_init__(self):

        self.time_var = self.agent_class.time_vary
        self.time_inv = self.agent_class.time_inv

        self.dist_params = []
        param_dict = self.parameter_dict
        for key_param in param_dict:
            parameter = param_dict[key_param]
            if (
                isinstance(parameter, DataArray) and parameter.dims[0] == "agent"
            ) or isinstance(parameter, Distribution):
                self.dist_params.append(key_param)

        self.infer_counts()

    def infer_counts(self):

        param_dict = self.parameter_dict

        # if agent_clas_count is not specified, infer from parameters
        if self.agent_class_count is None:

            agent_class_count = 1
            for key_param in param_dict:
                parameter = param_dict[key_param]
                if isinstance(parameter, DataArray) and parameter.dims[0] == "agent":
                    agent_class_count = max(agent_class_count, parameter.shape[0])
                elif isinstance(parameter, (Distribution, IndexDistribution)):
                    agent_class_count = None
                    break

            self.agent_class_count = agent_class_count

        if self.t_age is None:

            t_age = 1
            for key_param in param_dict:
                parameter = param_dict[key_param]
                if isinstance(parameter, DataArray) and parameter.dims[-1] == "age":
                    t_age = max(t_age, parameter.shape[-1])
                    # there may not be a good use for this feature yet as time varying distributions
                    # are entered as list of moments (Avg, Std, Count, etc)
                elif isinstance(parameter, (Distribution, IndexDistribution)):
                    t_age = None
                    break
            self.t_age = t_age

        # return t_age and agent_class_count

    def approx_distributions(self, approx_params: dict):

        param_dict = self.parameter_dict

        self.continuous_distributions = {}

        self.discrete_distributions = {}

        for key in approx_params:
            if key in param_dict and isinstance(param_dict[key], Distribution):
                discrete_points = approx_params[key]
                discrete_distribution = param_dict[key].approx(discrete_points)
                self.continuous_distributions[key] = param_dict[key]
                self.discrete_distributions[key] = discrete_distribution
            else:
                print(
                    "Warning: parameter {} is not a Distribution found in agent class {}".format(
                        key, self.agent_class
                    )
                )

        if len(self.discrete_distributions) > 1:
            joint_dist = combine_indep_dstns(
                *list(self.discrete_distributions.values())
            )

        keys = list(self.discrete_distributions.keys())
        for i in range(len(self.discrete_distributions)):
            param_dict[keys[i]] = DataArray(joint_dist.X[i], dims=("agent"))

        self.infer_counts()

    def parse_params(self):

        param_dict = self.parameter_dict

        agent_dicts = []  # container for dictionaries of each agent subgroup
        for agent in range(self.agent_class_count):
            agent_params = {}

            for key_param in param_dict:
                parameter = param_dict[key_param]

                if key_param in self.time_var:
                    # parameters that vary over time have to be repeated
                    parameter_per_t = []
                    for t in range(self.t_age):
                        if isinstance(parameter, DataArray):
                            if parameter.dims[0] == "agent":
                                if parameter.dims[-1] == "age":
                                    # if the parameter is a list, it's agent and time
                                    parameter_per_t.append(parameter[agent][t].item())
                                else:
                                    parameter_per_t.append(parameter[agent].item())
                            elif parameter.dims[0] == "age":
                                # if kind is time, it applies to all agents but varies over time
                                parameter_per_t.append(parameter[t].item())
                        elif isinstance(parameter, (int, float)):
                            # if kind is fixed, it applies to all agents at all times
                            parameter_per_t.append(parameter)

                    agent_params[key_param] = parameter_per_t

                elif key_param in self.time_inv:
                    if (
                        isinstance(parameter, DataArray)
                        and parameter.dims[0] == "agent"
                    ):
                        agent_params[key_param] = parameter[agent].item()
                    elif isinstance(parameter, (int, float)):
                        agent_params[key_param] = parameter

                else:
                    if isinstance(parameter, DataArray):
                        if parameter.dims[0] == "agent":
                            if parameter.dims[-1] == "age":
                                # if the parameter is a list, it's agent and time
                                agent_params[key_param] = list(parameter[agent].item())
                            else:
                                agent_params[key_param] = list(parameter[agent].item())
                        elif parameter.dims[0] == "age":
                            agent_params[key_param] = [parameter.item()]
                    elif isinstance(parameter, (int, float)):
                        agent_params[key_param] = parameter

            agent_dicts.append(agent_params)

        self.agent_dicts = agent_dicts

    def agent_df(self):
        """
        Output a dataframe for agent attributes

        returns agent_df from class_stats
        """

        if self.agent_database is None:

            records = []

            for agent in self.agents:
                for i, aLvl in enumerate(agent.state_now["aLvl"]):
                    record = {
                        "aLvl": aLvl,
                        "mNrm": agent.state_now["mNrm"][i],
                        "cNrm": agent.controls["cNrm"][i]
                        if "cNrm" in agent.controls
                        else None,
                        # difference between mNrm and the equilibrium mNrm from BST
                        "mNrm_ratio_StE": agent.state_now["mNrm"][i] / agent.mNrmStE,
                    }

                    for dp in self.dist_params:
                        record[dp] = agent.parameters[dp]

                    records.append(record)

            self.agent_database = pd.DataFrame.from_records(records)

        return self.agent_database

    def class_stats(self, store=False):
        """
        Output the statistics for each class within the population.

        Currently limited to asset level in the final simulated period (aLvl_T)
        """
        agent_df = self.agent_df()

        class_stats = (
            agent_df.groupby(list(self.dist_params.keys()))
            .aggregate(["mean", "std"])
            .reset_index()
        )

        cs = class_stats
        cs["label"] = round(cs["CRRA"], 2).apply(lambda x: f"CRRA: {x}, ") + round(
            cs["DiscFac"], 2
        ).apply(lambda x: f"DiscFac: {x}")
        cs["aLvl_mean"] = cs["aLvl"]["mean"]
        cs["aLvl_std"] = cs["aLvl"]["std"]
        cs["mNrm_mean"] = cs["mNrm"]["mean"]
        cs["mNrm_std"] = cs["mNrm"]["std"]
        cs["mNrm_ratio_StE_mean"] = cs["mNrm_ratio_StE"]["mean"]
        cs["mNrm_ratio_StE_std"] = cs["mNrm_ratio_StE"]["std"]

        if store:
            self.stored_class_stats = class_stats

        return class_stats

    def create_distributed_agents(self):

        self.agents = [
            self.agent_class.__class__(**agent_dict) for agent_dict in self.agent_dicts
        ]

    def create_database(self):

        database = pd.DataFrame(self.agent_dicts)
        database["agents"] = self.agents

        self.agent_database = database

    def solve_distributed_agents(self):
        # see Market class for an example of how to solve distributed agents in parallel

        for agent in self.agents:
            agent.solve()

    def unpack_solutions(self):

        self.solution = [agent.solution for agent in self.agents]

    def init_simulation(self, T_sim=1000):
        """
        Sets up the agents with their state for the state of the simulation
        """
        for agent in self.agents:
            agent.track_vars += ["pLvl", "mNrm", "cNrm", "Share", "Risky"]
            agent.T_sim = T_sim
            agent.initialize_sim()

    def solve(self, merge_by=None):

        self.solve_distributed_agents()

        if merge_by is not None:
            self.solution = AgentPopulationSolution(self)
            self.solution.merge_solutions(continuous_states=merge_by)


class AgentPopulationSolution:
    def __init__(self, agent_population):
        self.agent_population = agent_population

        self.dist_params = self.agent_population.dist_params
        self.agent_database = self.agent_population.agent_database

    def merge_solutions(self, continuous_states):

        # check that continous states are in heterogeneous parameters
        for state in continuous_states:
            if state not in self.dist_params:
                raise AttributeError(
                    "{} is not an agent-varying parameter.".format(state)
                )

        discrete_params = list(set(self.dist_params) - set(continuous_states))

        grouped = self.agent_database.groupby(discrete_params)
        solution_database = []

        for name, group in grouped:
            group.sort_values(by=continuous_states)
            in_grouped = group.groupby("RiskyStd")

            std_vals = np.unique(group.RiskyStd)

            cFunc_by_std = []
            shareFunc_by_std = []
            for std, in_group in in_grouped:
                agents = list(in_group.agents)
                avg = np.array(in_group.RiskyAvg)

                cFunc_by_std.append(
                    LinearInterpOnInterp1D(
                        [agent.solution[0].cFuncAdj for agent in agents], avg
                    )
                )

                shareFunc_by_std.append(
                    (
                        LinearInterpOnInterp1D(
                            [agent.solution[0].ShareFuncAdj for agent in agents], avg
                        )
                    )
                )

            cFunc = LinearInterpOnInterp2D(cFunc_by_std, std_vals)
            shareFunc = LinearInterpOnInterp2D(shareFunc_by_std, std_vals)

            solution_database.append(
                {
                    discrete_params[0]: name[0],
                    discrete_params[1]: name[1],
                    "cFunc": cFunc,
                    "shareFunc": shareFunc,
                }
            )

        self.solution_database = pd.DataFrame(solution_database)

        self.solution_database = self.solution_database.set_index(discrete_params)

        return self.solution_database
