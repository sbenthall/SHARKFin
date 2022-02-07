from dataclasses import dataclass
from typing import NewType

from HARK.core import AgentType
from HARK.distribution import Distribution, IndexDistribution
from xarray import DataArray

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
                if isinstance(parameter, DataArray) and parameter.dims[0] == "agent":
                    agent_class_count = max(agent_class_count, parameter.shape[0])
                elif isinstance(parameter, (Distribution, IndexDistribution)):
                    t_cycle = None
                    break

            self.agent_class_count = agent_class_count

        if self.t_cycle is None:

            t_cycle = 1
            for key_param in param_dict:
                parameter = param_dict[key_param]
                if isinstance(parameter, DataArray) and parameter.dims[-1] == "time":
                    t_cycle = max(t_cycle, parameter.shape[-1])
                    # there may not be a good use for this feature yet as time varying distributions
                    # are entered as list of moments (Avg, Std, Count, etc)
                elif isinstance(parameter, (Distribution, IndexDistribution)):
                    t_cycle = None
                    break
            self.t_cycle = t_cycle

    def approx_distributions(self, approx_params: dict):

        param_dict = self.parameter_dict

        self.distributions = {}

        for key in approx_params:
            if key in param_dict and isinstance(param_dict[key], Distribution):
                discrete_distribution = param_dict[key].approx(approx_params[key])
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

        agent_dicts = []  # container for dictionaries of each agent subgroup
        for agent in range(self.agent_class_count):
            agent_params = {}

            for key_param in param_dict:
                parameter = param_dict[key_param]

                if key_param in self.time_var:
                    # parameters that vary over time have to be repeated
                    parameter_per_t = []
                    for t in range(self.t_cycle):
                        if isinstance(parameter, DataArray):
                            if parameter.dims[0] == "agent":
                                if parameter.dims[-1] == "time":
                                    # if the parameter is a list, it's agent and time
                                    parameter_per_t.append(parameter[agent][t].item())
                                else:
                                    parameter_per_t.append(parameter[agent].item())
                            elif parameter.dims[0] == "time":
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
                            if parameter.dims[-1] == "time":
                                # if the parameter is a list, it's agent and time
                                agent_params[key_param] = [
                                    parameter[agent][t].item() for t in range(t_cycle)
                                ]
                            else:
                                agent_params[key_param] = parameter[agent].item()
                        elif parameter.dims[0] == "time":
                            agent_params[key_param] = [
                                parameter[t].item() for t in range(t_cycle)
                            ]
                    elif isinstance(parameter, (int, float)):
                        agent_params[key_param] = parameter

            agent_dicts.append(agent_params)

        self.agent_dicts = agent_dicts

    def create_distributed_agents(self):

        self.agents = [
            self.agent_class.__init__(**agent_dict) for agent_dict in self.agent_dicts
        ]

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

parameters["AgentCount"] = DataArray([100, 100, 100], dims=("agent"))
parameters["CRRA"] = 2.0  # applies to all
# applies per distinct agent type at all times
parameters["DiscFac"] = DataArray([0.96, 0.97, 0.98], dims=("agent"))
# applies to all per time cycle
parameters["LivPrb"] = DataArray([0.98, 0.98, 0.98], dims=("time"))
# applies to each agent each cycle
parameters["TranShkStd"] = DataArray(
    [[0.2, 0.2, 0.2], [0.2, 0.2, 0.2], [0.2, 0.2, 0.2]], dims=("agent", "time")
)

parameters = ParameterDict(parameters)

from HARK.ConsumptionSaving.ConsIndShockModel import IndShockConsumerType

# important to pass initialized agent so time_vary and time_inv are filled out
agent_pop = AgentPopulation(IndShockConsumerType(), parameters)

agent_pop.parse_params()
