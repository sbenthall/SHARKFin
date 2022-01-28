from collections import namedtuple
from typing import NewType
from HARK.core import AgentType

Parameters = NewType("Parameters", "dict")


class AgentPopulation:
    def __init__(
        self,
        agent_class: AgentType,
        parameter_dict: Parameters,
        t_cycle: int,
        agent_class_count: int,
    ):
        self.agent_class = agent_class
        self.parameter_dict = parameter_dict
        self.t_cycle = t_cycle
        self.agent_class_count = agent_class_count

        self.time_var = agent_class.time_vary_
        self.time_inv = agent_class.time_inv_

    def parse_params(self):

        param_dict = self.parameter_dict

        agent_dicts = []
        for agent in range(self.agent_class_count):
            agent_params = {}

            for key_param in param_dict:

                if key_param in self.time_var:
                    # parameters that vary over time have to be repeated
                    parameter_per_t = []
                    for t in range(self.t_cycle):
                        if param_dict[key_param].kind == "agent":
                            if param_dict[key_param].value is list:
                                # if the parameter is a list, it's agent and time
                                parameter_per_t.append(
                                    param_dict[key_param].value[agent][t]
                                )
                            else:
                                parameter_per_t.append(
                                    param_dict[key_param].value[agent]
                                )
                        elif param_dict[key_param].kind == "time":
                            # if kind is time, it applies to all agents but varies over time
                            # assert param_dict[key_param].value is list
                            parameter_per_t.append(param_dict[key_param].value[t])
                        elif param_dict[key_param].kind == "fixed":
                            # if kind is fixed, it applies to all agents at all times
                            # assert param_dict[key_param].value is not list
                            parameter_per_t.append(param_dict[key_param].value)

                    agent_params[key_param] = parameter_per_t

                elif key_param in self.time_inv:
                    if param_dict[key_param].kind == "agent":
                        # assert param_dict[key_param].value is list
                        agent_params[key_param] = param_dict[key_param].value[agent]
                    if param_dict[key_param].kind == "fixed":
                        # assert param_dict[key_param].value is not list
                        agent_params[key_param] = param_dict[key_param].value

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
