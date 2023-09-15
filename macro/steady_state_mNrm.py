import numpy as np
from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType
import matplotlib.pyplot as plt
from sharkfin.population import SharkPopulation, SharkPopulationSolution
from sharkfin.utilities import price_dividend_ratio_random_walk
from simulate.parameters import WHITESHARK, LUCAS0

from sharkfin.expectations import UsualExpectations
from sharkfin.markets import MockMarket

# ## Setup

LUCAS0

# +
dividend_growth_rate = 1.000203
dividend_std = 0.011983

rng = 23409

market_args = {
        "dividend_growth_rate": dividend_growth_rate,
        "dividend_std": dividend_std,
        "rng": rng,
        "price_to_dividend_ratio": price_dividend_ratio_random_walk(
            LUCAS0['DiscFac'], LUCAS0['CRRA'], dividend_growth_rate, dividend_std
        ),
    }
# -

ue = UsualExpectations(MockMarket(**market_args))
ue.calculate_risky_expectations()
risky_expectations = ue.risky_expectations()

parameter_dict = LUCAS0.copy()

parameter_dict['aNrmInitMean'] = 1
parameter_dict['aNrmInitStd'] = 0.1

parameter_dict.update(risky_expectations)

parameter_dict

parameter_dict['T_sim'] = 4000

pop = SharkPopulation(
    SequentialPortfolioConsumerType,
    parameter_dict,
    dollars_per_hark_money_unit=1000,
)

if "approx_params" in parameter_dict:
    pop.approx_distributions(parameter_dict["approx_params"])
else:
    pop.continuous_distributions = {}
    pop.discrete_distributions = {}

pop.create_distributed_agents()
pop.create_database()
pop.solve_distributed_agents()

pop.solve(merge_by=parameter_dict["ex_post"])  # merge_by=["RiskyAvg", "RiskyStd"])

pop.explode_agents(30)

for ag in pop.agent_database['agents']:
    ag.track_vars += ['aNrm', "TranShk"]
    ag.assign_parameters(sim_common_Rrisky = False)

a0h = pop.agent_database['agents'][0]

a0h

# +
PARAMS = a0h.parameters

PARAMS['aNrmInitMean'] = 1
PARAMS['aNrmInitStd'] = 0.01
PARAMS['T_sim'] = 2000

at = SequentialPortfolioConsumerType(**PARAMS)
at.assign_parameters(AgentCount = 1500)

at.track_vars += ['aNrm', 'cNrm', 'Risky', 'Share', 'aLvl']
at.solve()
# -

# ## Using the solution functions

cFunc = at.solution[0].cFuncAdj
ShareFunc = at.solution[0].ShareFuncAdj


def expected_increase(mNrm):
    share = ShareFunc(mNrm)
    
    aNrm = mNrm - cFunc(mNrm)
    
    mNrm_next = aNrm * (share * at.parameters['RiskyAvg'] + (1 - share) * at.parameters['Rfree']) + 1
    
    gain = mNrm_next - aNrm
    
    return gain


# +
mNrm = np.linspace(7.5, 30, 1000)

plt.plot(mNrm, cFunc(mNrm), label ='c')

plt.plot(mNrm, expected_increase(mNrm), label = 'gain')

plt.legend()

# +
mNrm = np.linspace(0, 50, 1000)

plt.plot(mNrm, cFunc(mNrm), label ='c')

plt.plot(mNrm, expected_increase(mNrm), label = 'gain')

plt.legend()
# -

expected_increase(mNrm) > cFunc(mNrm)

plt.plot(mNrm, cFunc(mNrm) - expected_increase(mNrm), label ='c - gain ')


# ## Simulating with SharkPopulation

a0h.parameters

# initialize population model
pop.init_simulation()

pop.simulate()

assert pop.agent_database['agents'].map(lambda a: a.history['mNrm'][100]).std() > 0.00000001



# +
import pandas as pd

hist = pop.agent_database['agents'][0].history

data = pd.concat([
    pd.DataFrame(
        {var : np.log(agent.history[var].flatten())
         for var in agent.history}).reset_index()
    for agent
    in pop.agent_database['agents']
    
])
# -

data.shape

# +
import seaborn as sns

sns.lineplot(
    data = data,
    x = 'index',
    y = 'mNrm'
)
# -

sns.lineplot(
    data = data,
    x = 'index',
    y = 'cNrm'
)

data.columns

sns.lineplot(
    data = data[data['index'] < 100],
    x = 'index',
    y = 'Risky'
)

# ## Single AgentType testing (should be faster)

# +
PARAMS = a0h.parameters

PARAMS['aNrmInitMean'] = 1
PARAMS['aNrmInitStd'] = 0.01
PARAMS['T_sim'] = 2000

# +
at = SequentialPortfolioConsumerType(**PARAMS)
at.assign_parameters(AgentCount = 1500)

at.track_vars += ['aNrm', 'cNrm', 'Risky', 'Share', 'aLvl']
at.solve()
at.initialize_sim()
at.simulate()

# +
agent_histories = []

for a in range(3):
    df = pd.DataFrame(
        {'log_' + var : np.log(at.history[var][:, a].flatten())
         for var in at.history}).reset_index()
    df = df.rename(columns={'index' : 't'})
    df['agent'] = a
    agent_histories.append(df)

data = pd.concat(agent_histories)
# -

sns.lineplot(
    data = data,
    x = 't',
    y = 'log_aLvl'
)

sns.lineplot(
    data = data,
    x = 't',
    y = 'log_aNrm'
)

np.log(4000)

data[data['t'] > 3000]['log_aNrm'].mean()

np.exp(data[data['t'] > 3000]['log_aNrm'].mean())

sns.lineplot(
    data = data,
    x = 't',
    y = 'log_Risky'
)

sns.lineplot(
    data = data,
    x = 't',
    y = 'log_cNrm'
)

sns.lineplot(
    data = data,
    x = 't',
    y = 'log_Share'
)








