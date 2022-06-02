# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import ipywidgets as widgets
from simulate.parameters import agent_parameters
from HARK.ConsumptionSaving.ConsPortfolioModel import PortfolioConsumerType
from sharkfin.expectations import FinanceModel
from HARK.utilities import plot_funcs

# %% pycharm={"name": "#%%\n"} jupyter={"outputs_hidden": false}
agent_parameters["cycles"] = 0


# %% pycharm={"name": "#%%\n"} jupyter={"outputs_hidden": false}
def portfolio_choice(RiskyAvg=1.08, RiskyStd=0.2, CRRA=5.0, DiscFac=0.9):

    agent_parameters["RiskyAvg"] = RiskyAvg
    agent_parameters["RiskyStd"] = RiskyStd
    agent_parameters["CRRA"] = CRRA
    agent_parameters["DiscFac"] = DiscFac

    print("Solving...")

    agent = PortfolioConsumerType(**agent_parameters)
    agent.solve()

    print("Solved!")

    plot_funcs(agent.solution[0].ShareFuncAdj, 0, 100)


# %% pycharm={"name": "#%%\n"} jupyter={"outputs_hidden": false}
widgets.interact(
    portfolio_choice,
    RiskyAvg=(1.0, 1.1, 0.01),
    RiskyStd=(0.0, 0.5, 0.01),
    CRRA=(2, 10, 4),
    DiscFac=(0.9, 0.99, 0.01),
    continuous_update=False,
)

# %% pycharm={"name": "#%%\n"} jupyter={"outputs_hidden": false}
portfolio_choice(RiskyAvg=1.01, RiskyStd=0.01, CRRA=6.0, DiscFac=0.95)
