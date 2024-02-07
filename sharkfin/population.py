from copy import deepcopy
from dataclasses import dataclass
from functools import partial
from pprint import pprint
from typing import NewType

import HARK.ConsumptionSaving.ConsIndShockModel as cism
import numpy as np
import pandas as pd
from HARK.core import AgentPopulation
from HARK.interpolation import BilinearInterpOnInterp1D, TrilinearInterpOnInterp1D

from sharkfin.utilities import *

ParameterDict = NewType("ParameterDict", dict)


@dataclass
class SharkPopulation(AgentPopulation):
    dollars_per_hark_money_unit: float = 1500

    def __post_init__(self):
        self.parameters = deepcopy(self.parameters)
        super().__post_init__()
        self.stored_class_stats = None

    def agent_data(self):
        """
        Output a dataframe for agent attributes
         -- this is not the same as the agent_database,
            but rather is a specially designed dataframe
            used for reporting.

        returns agent_data from class_stats
        """

        # suppress assignment warnings
        pdomca = pd.options.mode.chained_assignment = None
        pd.options.mode.chained_assignment = None  # default='warn'

        agent_data = self.agent_database[self.ex_ante_hetero_params + ["agents"]]

        data_calls = {
            "aLvl": lambda a: a.state_now["aLvl"],
            "mNrm": lambda a: a.state_now["mNrm"],
            "cNrm": lambda a: a.controls["cNrm"]
            if "cNrm" in a.controls
            else np.full(a.AgentCount, np.nan),
            "mNrm_ratio_StE": lambda a: a.state_now["mNrm"] / a.mNrmStE,
        }

        for dc in data_calls:
            col = agent_data.loc[:, "agents"].apply(data_calls[dc])
            agent_data[dc] = col

        agent_data = agent_data.explode(list(data_calls.keys()))

        pd.options.mode.chained_assignment = pdomca

        return agent_data

    def class_stats(self, store=False):
        """
        Output the statistics for each class within the population.

        Currently limited to asset level in the final simulated period (aLvl_T)
        """
        agent_data = self.agent_data().drop(columns="agents")

        if self.ex_ante_hetero_params is None or len(self.ex_ante_hetero_params) == 0:
            cs = agent_data.aggregate(["mean", "std"])

            mean_data = cs.loc["mean"].to_dict()
            std_data = cs.loc["std"].to_dict()

            # this collapse the data into one row with appropriate column names
            all_data = {k + "_mean": [mean_data[k]] for k in mean_data}
            all_data.update({k + "_std": [std_data[k]] for k in std_data})
            all_data["label"] = ["all"]

            cs = pd.DataFrame.from_dict(all_data)

        else:
            cs = (
                agent_data.groupby(self.ex_ante_hetero_params)
                .aggregate(["mean", "std"])
                .reset_index()
            )

            label = ""

            for param in self.ex_ante_hetero_params:
                label += round(cs[param], 2).apply(lambda x: f"{param}={x}, ")

            cs["label"] = label.str[:-2]

            cs.columns = ["_".join(col).strip("_") for col in cs.columns.values]

        if store:
            self.stored_class_stats = cs

        return cs

    def solve_distributed_agents(self):
        # see Market class for an example of how to solve distributed agents in parallel

        for agent in self.agents:
            agent.solve()

    def explode_agents(self, num):
        exploded_agents = []
        exploded_dicts = []

        rng = np.random.default_rng(self.seed)

        for i, agent in enumerate(self.agents):
            for j in range(num):
                double_agent = deepcopy(agent)
                double_agent.seed = rng.integers(0, 2**31 - 1)
                double_agent.reset_rng()
                double_agent.update_income_process()
                exploded_agents.append(double_agent)
                exploded_dicts.append(deepcopy(self.population_parameters[i]))

        self.agents = exploded_agents
        self.population_parameters = exploded_dicts

        self.create_database()

    def init_simulation(self, T_sim=1000):
        """
        Sets up the agents with their state for the state of the simulation
        """
        for agent in self.agents:
            agent.track_vars += ["pLvl", "mNrm", "cNrm", "Share", "Risky"]
            agent.T_sim = T_sim
            agent.initialize_sim()

            if self.stored_class_stats is None:
                ## build an IndShockConsumerType "double" of this agent, with the same parameters
                parameters = agent.parameters.copy()
                if "Rfree" in parameters and isinstance(parameters["Rfree"], list):
                    # patch potential bug until HARK is updated
                    parameters["Rfree"] = parameters["Rfree"][0]
                cism.IndShockConsumerType(**parameters)

                ###
                agent.mNrmStE = 0
                ###
                ###
            else:
                idx = [agent.parameters[dp] for dp in self.distributed_params]
                aNrm = (
                    self.stored_class_stats.copy()
                    .set_index([dp for dp in self.distributed_params])
                    .xs((idx))["aNrm"]["mean"]
                )
                agent.state_now["aNrm"][:] = aNrm

            #agent.state_now["aNrm"] = agent.state_now["mNrm"] - agent.solution[
            #    0
            #].cFuncAdj(agent.state_now["mNrm"])
            #agent.state_now["aLvl"] = agent.state_now["aNrm"] * agent.state_now["pLvl"]

    def solve(self, merge_by=None):
        self.solve_distributed_agents()

        self.solution = SharkPopulationSolution(self)
        self.solution.merge_solutions(continuous_states=merge_by)
        self.ex_ante_hetero_params = self.solution.ex_ante_hetero_params

    def attend(self, agent, price, risky_expectations, day=None):
        """
        Cause the agent to attend to the financial model.

        This will update their expectations of the risky asset.
        They will then adjust their owned risky asset shares to meet their
        target.

        Return the delta of risky asset shares ordered through the brokers.

        NOTE: This MUTATES the agents with their new target share amounts.

        Params
        ------
        day: None or int -- If int, then record the day on the agent.
        """
        # It's a little weird using assign_parameters for this but...
        if day is not None and "attention_days" in agent.parameters:
            attention_days = agent.parameters["attention_days"]
            attention_days.append(day)
            agent.assign_parameters(**{"attention_days": attention_days})
        elif day is not None:
            agent.assign_parameters(**{"attention_days": [day]})

        # Note: this mutates the underlying agent
        # we should also assign their solution
        agent.assign_parameters(**risky_expectations)
        self.assign_solution(agent)

        target_shares = self.compute_share_demand(agent, price)

        delta_shares = target_shares - agent.shares

        # NOTE: This mutates the agent
        agent.shares = target_shares

        if np.any(agent.shares < 0):
            print("ERROR: Agent has negative shares after attention.")

        return delta_shares

    def assign_solution(self, agent):
        """
        Assign the respective solution to the agent using the master solution and
        the agent's perceptions of the market.
        """

        if self.ex_ante_hetero_params is None or len(self.ex_ante_hetero_params) == 0:
            return

        # assign solution before simulating
        # get master solution
        pop_solution = self.solution.solution_database

        # get solution for agent subgroup
        # functions = pop_solution.loc[agent.CRRA, agent.DiscFac]

        keys = [agent.parameters[key] for key in self.ex_ante_hetero_params]
        functions = pop_solution.loc[tuple(keys)]

        # Using their expectations, construct function depending on
        # perceptions/beliefs about the stock market

        cFuncAdj = partial(functions["cFuncAdj"], y=agent.RiskyAvg, z=agent.RiskyStd)
        ShareFuncAdj = partial(
            functions["ShareFuncAdj"], y=agent.RiskyAvg, z=agent.RiskyStd
        )
        SequentialShareFuncAdj = partial(
            functions["SequentialShareFuncAdj"], y=agent.RiskyAvg, z=agent.RiskyStd
        )

        agent.solution[0].ShareFuncAdj = ShareFuncAdj
        agent.solution[0].cFuncAdj = cFuncAdj
        agent.solution[0].SequentialShareFuncAdj = SequentialShareFuncAdj

    def compute_share_demand(self, agent, price):
        """
        Computes the number of shares an agent _wants_ to own.

        Inputs:
         - an agent
         - current asset price

        This involves:
          - Computing a solution function based on their
            expectations and personal properties
          - Using the solution and the agent's current normalized
            assets to compute a share number
        """

        asset_normalized = agent.state_now["aNrm"]

        if np.any(asset_normalized < 0):
            print("ERROR: An agent has negative assets after compute demand.")

        # ShareFuncAdj takes normalized market resources as argument
        # SequentialShareFuncAdj takes normalized assets as argument
        risky_share = agent.solution[0].SequentialShareFuncAdj(asset_normalized)
        # risky_share = np.clip(risky_share, 0, 1)

        if np.any(risky_share < 0):
            print(
                "Warning: An agent has negative risky share. Setting to 0. Need to fix solution!"
            )
            print(f"RiskyAvg: {agent.RiskyAvg}, RiskyStd: {agent.RiskyStd}")
            risky_share[risky_share < 0] = 0.0

        if np.any(risky_share > 1):
            print(
                "Warning: An agent has risky share > 1.0. Setting to 1. Need to fix solution!"
            )
            print(f"RiskyAvg: {agent.RiskyAvg}, RiskyStd: {agent.RiskyStd}")
            risky_share[risky_share > 1] = 1.0

        # denormalize the risky share. See https://github.com/econ-ark/HARK/issues/986
        risky_asset_wealth = (
            risky_share
            * asset_normalized
            * agent.state_now["pLvl"]
            * self.dollars_per_hark_money_unit
        )

        shares = risky_asset_wealth / price

        if (np.isnan(shares)).any():
            print("ERROR: Agent desires nan shares")

        if np.any(shares < 0):
            print("ERROR: Agent has negative share target")

        return shares

    def macro_update(self, agent, price):
        """
        Input: an agent, current asset price

        Simulates one "macro" period for the agent (quarterly by assumption).
        For the purposes of the simulation, award the agent dividend income
        but not capital gains on the risky asset.

        Output: The difference in shares (really, sales of shares) in order
        to finance consumption; must be passed to a broker.
        """

        true_risky_expectations = {
            "RiskyAvg": agent.parameters["RiskyAvg"],
            "RiskyStd": agent.parameters["RiskyStd"],
        }

        # assigning solution based on agent's true expectations
        # the true agent's expectations should already be assigned
        self.assign_solution(agent)

        # No change -- both capital gains and dividends awarded daily. See #100
        macro_risky_params = {
            "RiskyAvg": 1,
            "RiskyStd": 0,
        }

        # Now that the agent has their true expectations policy assigned,
        # simulate using the no change marco expectations to avoid
        # realization of market returns and asset growth
        agent.assign_parameters(**macro_risky_params)
        agent.simulate(sim_periods=1)

        if np.any(agent.state_now["aNrm"]) < 0:
            print("ERROR: Agent has negative assets after macro update.")

        if np.any(agent.controls["Share"]) < 0:
            print("ERROR: Agent has negative risky share after macro update.")
            print(true_risky_expectations)

        if np.any(agent.controls["Share"]) > 1:
            print("ERROR: Agent has share > 1 after macro update.")
            print(true_risky_expectations)

        ## put back the expectations that include capital gains now
        agent.assign_parameters(**true_risky_expectations)

        # Selling off shares if necessary to
        # finance this period's consumption
        asset_level_in_shares = (
            agent.state_now["aLvl"] * self.dollars_per_hark_money_unit / price
        )

        delta = asset_level_in_shares - agent.shares
        delta[delta > 0] = 0

        agent.shares = agent.shares + delta

        return delta

    def update_agent_wealth_capital_gains(self, new_share_price, pror, dividend):
        """
        For all agents,
        given the old share price
        and a rate of return

        update the agent's wealth level to adjust
        for the most recent round of capital gains.
        """

        old_share_price = new_share_price / (1 + pror)

        for agent in self.agents:
            old_raw = agent.shares * old_share_price
            new_raw = agent.shares * new_share_price
            dividends = agent.shares * dividend

            delta_aNrm = (new_raw - old_raw + dividends) / (
                self.dollars_per_hark_money_unit * agent.state_now["pLvl"]
            )

            # update normalized market assets
            # if agent.state_now['aNrm'] < delta_aNrm:
            #     breakpoint()

            agent.state_now["aNrm"] = agent.state_now["aNrm"] + delta_aNrm

            if (agent.state_now["aNrm"] < 0).any():
                print(
                    f"ERROR: Agent with CRRA {agent.parameters['CRRA']}"
                    + "has negative aNrm after capital gains update."
                )
                pprint(
                    {
                        "aNrm": agent.state_now["aNrm"],
                        "shares": agent.shares,
                        "pLvl": agent.state_now["pLvl"],
                        "delta_aNrm": delta_aNrm,
                        "dividend": dividend,
                        "pror": pror,
                    }
                )
                print("Setting normalize assets and shares to 0.")
                agent.state_now["aNrm"][(agent.state_now["aNrm"] < 0)] = 0.0
                ## TODO: This change in shares needs to be registered with the Broker.
                agent.shares[(agent.state_now["aNrm"] == 0)] = 0

            # update non-normalized market assets
            agent.state_now["aLvl"] = agent.state_now["aNrm"] * agent.state_now["pLvl"]


class SharkPopulationSolution:
    def __init__(self, agent_population):
        self.agent_population = agent_population

        self.distributed_params = self.agent_population.distributed_params
        self.agent_database = self.agent_population.agent_database

    def merge_solutions(self, continuous_states):
        if continuous_states is None or continuous_states == []:
            if self.distributed_params is None or self.distributed_params == []:
                self.solution_database = self.agent_database
            else:
                self.solution_database = self.agent_database.set_index(
                    self.distributed_params
                )
            self.ex_ante_hetero_params = []

        else:
            # check that continous states are in heterogeneous parameters
            for state in continuous_states:
                if state not in self.distributed_params:
                    raise AttributeError(
                        "{} is not an agent-varying parameter.".format(state)
                    )

            if len(continuous_states) == 2:
                self._merge_solutions_2d(continuous_states)
            elif len(continuous_states) == 3:
                self._merge_solutions_3d(continuous_states)

    def _merge_solutions_2d(self, continuous_states):
        discrete_params = list(set(self.distributed_params) - set(continuous_states))
        discrete_params.sort()

        self.ex_ante_hetero_params = discrete_params

        grouped = self.agent_database.groupby(discrete_params)
        solution_database = []

        for name, group in grouped:
            group.sort_values(by=continuous_states)

            cnt0_vals = np.unique(group[continuous_states[0]])
            cnt1_vals = np.unique(group[continuous_states[1]])

            group = group.set_index(continuous_states)

            cFuncAdj_interpolators = []
            ShareFuncAdj_interpolators = []
            SequentialShareFuncAdj_interpolators = []
            for cnt0 in cnt0_vals:
                temp_cFuncAdj = []
                temp_ShareFuncAdj = []
                temp_SequentialShareFuncAdj = []
                for cnt1 in cnt1_vals:
                    temp_cFuncAdj.append(
                        group.loc[cnt0, cnt1].agents.solution[0].cFuncAdj
                    )
                    temp_ShareFuncAdj.append(
                        group.loc[cnt0, cnt1].agents.solution[0].ShareFuncAdj
                    )
                    temp_SequentialShareFuncAdj.append(
                        group.loc[cnt0, cnt1].agents.solution[0].SequentialShareFuncAdj
                    )
                cFuncAdj_interpolators.append(temp_cFuncAdj)
                ShareFuncAdj_interpolators.append(temp_ShareFuncAdj)
                SequentialShareFuncAdj_interpolators.append(temp_SequentialShareFuncAdj)

            cFuncAdj = BilinearInterpOnInterp1D(
                cFuncAdj_interpolators, cnt0_vals, cnt1_vals
            )
            ShareFuncAdj = BilinearInterpOnInterp1D(
                ShareFuncAdj_interpolators, cnt0_vals, cnt1_vals
            )
            SequentialShareFuncAdj = BilinearInterpOnInterp1D(
                SequentialShareFuncAdj_interpolators, cnt0_vals, cnt1_vals
            )

            solution_database.append(
                {
                    discrete_params[0]: name[0],
                    discrete_params[1]: name[1],
                    "cFuncAdj": cFuncAdj,
                    "ShareFuncAdj": ShareFuncAdj,
                    "SequentialShareFuncAdj": SequentialShareFuncAdj,
                }
            )

        self.solution_database = pd.DataFrame(solution_database)

        self.solution_database = self.solution_database.set_index(discrete_params)

    def _merge_solutions_3d(self, continuous_states):
        discrete_params = list(set(self.distributed_params) - set(continuous_states))
        discrete_params.sort()

        self.ex_ante_hetero_params = discrete_params

        grouped = self.agent_database.groupby(discrete_params)
        solution_database = []

        for name, group in grouped:
            group.sort_values(by=continuous_states)

            cnt0_vals = np.unique(group[continuous_states[0]])
            cnt1_vals = np.unique(group[continuous_states[1]])
            cnt2_vals = np.unique(group[continuous_states[2]])

            group = group.set_index(continuous_states)

            cFuncAdj_interpolators = []
            ShareFuncAdj_interpolators = []
            SequentialShareFuncAdj_interpolators = []
            for cnt0 in cnt0_vals:
                temp0_cFuncAdj = []
                temp0_ShareFuncAdj = []
                temp0_SequentialShareFuncAdj = []
                for cnt1 in cnt1_vals:
                    temp1_cFuncAdj = []
                    temp1_ShareFuncAdj = []
                    temp1_SequentialShareFuncAdj = []
                    for cnt2 in cnt2_vals:
                        temp1_cFuncAdj.append(
                            group.loc[cnt0, cnt1, cnt2].agents.solution[0].cFuncAdj
                        )
                        temp1_ShareFuncAdj.append(
                            group.loc[cnt0, cnt1, cnt2].agents.solution[0].ShareFuncAdj
                        )
                        temp1_SequentialShareFuncAdj.append(
                            group.loc[cnt0, cnt1, cnt2]
                            .agents.solution[0]
                            .SequentialShareFuncAdj
                        )
                    temp0_cFuncAdj.append(temp1_cFuncAdj)
                    temp0_ShareFuncAdj.append(temp1_ShareFuncAdj)
                    temp0_SequentialShareFuncAdj.append(temp1_SequentialShareFuncAdj)
                cFuncAdj_interpolators.append(temp0_cFuncAdj)
                ShareFuncAdj_interpolators.append(temp0_ShareFuncAdj)
                SequentialShareFuncAdj_interpolators.append(
                    temp0_SequentialShareFuncAdj
                )

            cFuncAdj = TrilinearInterpOnInterp1D(
                cFuncAdj_interpolators, cnt0_vals, cnt1_vals, cnt2_vals
            )
            ShareFuncAdj = TrilinearInterpOnInterp1D(
                ShareFuncAdj_interpolators, cnt0_vals, cnt1_vals, cnt2_vals
            )
            SequentialShareFuncAdj = TrilinearInterpOnInterp1D(
                SequentialShareFuncAdj_interpolators, cnt0_vals, cnt1_vals, cnt2_vals
            )

            solution_database.append(
                {
                    discrete_params[0]: name,
                    # discrete_params[1]: name[1],
                    "cFuncAdj": cFuncAdj,
                    "ShareFuncAdj": ShareFuncAdj,
                    "SequentialShareFuncAdj": SequentialShareFuncAdj,
                }
            )

        self.solution_database = pd.DataFrame(solution_database)

        self.solution_database = self.solution_database.set_index(discrete_params)
