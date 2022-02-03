from collections import namedtuple
from dataclasses import dataclass
from typing import NewType

from HARK.core import AgentType
from HARK.distribution import Distribution, IndexDistribution

ParameterDict = NewType("ParameterDict", dict)


@dataclass
class AgentPopulation:
    agent_class: AgentType
    parameter_dict: ParameterDict
    t_cycle: int = None
    agent_class_count: int = None

    def __post_init__(self):

        self.time_var = self.agent_class.time_vary
        self.time_inv = self.agent_class.time_inv

        param_dict = self.parameter_dict

        # if agent_clas_count is not specified, infer from parameters
        if self.agent_class_count is None:

            agent_class_count = 1
            for key_param in param_dict:
                parameter = param_dict[key_param]
                if parameter.kind == "agent":
                    if isinstance(parameter.value, list):
                        agent_class_count = max(agent_class_count, len(parameter.value))
                    elif isinstance(parameter.value, Distribution) or isinstance(
                        parameter.value, IndexDistribution
                    ):
                        # distributions may be passed without specifying counts
                        # so in this case we leave evaluation of number of agents for later
                        agent_class_count = 1
                        break

            self.agent_class_count = agent_class_count

        if self.t_cycle is None:

            t_cycle = 1
            for key_param in param_dict:
                if parameter.kind == "time":
                    if isinstance(parameter.value, list):
                        t_cycle = max(t_cycle, len(parameter.value))
                    # there may not be a good use for this feature yet as time varying distributions
                    # are entered as list of moments (Avg, Std, Count, etc)
                    elif isinstance(parameter.value, Distribution) or isinstance(
                        parameter.value, IndexDistribution
                    ):
                        t_cycle = 1
                        break
            self.t_cycle = t_cycle

    def approx_distributions(self, approx_params: dict):

        param_dict = self.parameter_dict

        self.distributions = {}

        for key in approx_params:
            if key in param_dict and isinstance(param_dict[key].value, Distribution):
                discrete_distribution = param_dict[key].value.approx(approx_params[key])
                self.distributions[key] = (param_dict[key], discrete_distribution)
                param_dict[key] = discrete_distribution.X
            else:
                print(
                    "Warning: parameter {} is not a Distribution found in agent class {}".format(
                        key, self.agent_class
                    )
                )

    def parse_params(self):

        param_dict = self.parameter_dict

        agent_dicts = []
        for agent in range(self.agent_class_count):
            agent_params = {}

            for key_param in param_dict:
                parameter = param_dict[key_param]

                if key_param in self.time_var:
                    # parameters that vary over time have to be repeated
                    parameter_per_t = []
                    for t in range(self.t_cycle):
                        if parameter.kind == "agent":
                            if isinstance(parameter.value, list):
                                # if the parameter is a list, it's agent and time
                                parameter_per_t.append(parameter.value[agent][t])
                            else:
                                parameter_per_t.append(parameter.value[agent])
                        elif parameter.kind == "time":
                            # if kind is time, it applies to all agents but varies over time
                            # assert parameter.value is list
                            parameter_per_t.append(parameter.value[t])
                        elif parameter.kind == "fixed":
                            # if kind is fixed, it applies to all agents at all times
                            # assert parameter.value is not list
                            parameter_per_t.append(parameter.value)

                    agent_params[key_param] = parameter_per_t

                elif key_param in self.time_inv:
                    if parameter.kind == "agent":
                        # assert parameter.value is list
                        agent_params[key_param] = parameter.value[agent]
                    if parameter.kind == "fixed":
                        # assert parameter.value is not list
                        agent_params[key_param] = parameter.value

                else:
                    if parameter.kind == "agent":
                        for agent in range(self.agent_class_count):
                            if isinstance(parameter.value[agent], list):
                                # if the parameter is a list, it's agent and time
                                agent_params[key_param] = [
                                    parameter.value[agent][t] for t in range(t_cycle)
                                ]
                            else:
                                agent_params[key_param] = parameter.value[agent]
                    elif parameter.kind == "time":
                        agent_params[key_param] = [
                            parameter.value[t] for t in range(t_cycle)
                        ]
                    else:
                        agent_params[key_param] = parameter.value

            agent_dicts.append(agent_params)

        self.agent_dicts = agent_dicts

    def create_distributed_agents(self):

        self.agents = [self.agent_class(parameters) for parameters in self.agent_dicts]

    def solve_distributed_agents(self):

        for agent in self.agents:
            agent.solve()

    def unpack_solutions(self):

        self.solution = [agent.solution for agent in self.agents]


class AgentPopulationSolution:
    def __init__(self, agent_population):

        self.agent_population = agent_population


t_cycle = 3
agent_class_count = 3

parameters = {}
parameters["T_cycle"] = t_cycle
parameters["AgentClassCount"] = agent_class_count

hark_param = namedtuple("HARK_parameter", "value kind")

parameters["CRRA"] = hark_param(2.0, "fixed")  # applies to all
# applies per distinct agent type at all times
parameters["DiscFac"] = hark_param([0.96, 0.97, 0.98], "agent")
# applies to all per time cycle
parameters["LivPrb"] = hark_param([0.98, 0.98, 0.98], "time")
# applies to each agent each cycle
parameters["TranShkStd"] = hark_param(
    [[0.2, 0.2, 0.2], [0.2, 0.2, 0.2], [0.2, 0.2, 0.2]], "agent"
)

parameters = Parameters(parameters)

from HARK.ConsumptionSaving.ConsIndShockModel import IndShockConsumerType

agent_pop = AgentPopulation(IndShockConsumerType, parameters, 3, 3)

agent_pop.parse_params()
