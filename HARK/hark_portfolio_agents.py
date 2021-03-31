import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
import HARK.ConsumptionSaving.ConsIndShockModel as cism
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

    # TODO: Revisit. Why simulate the agents 1 period here?
    for agent in agents:
        agent.track_vars += ['pLvl','mNrm','Share','Risky']

        agent.AdjustPrb = 1.0
        agent.T_sim = 1000 # arbitrary!
        agent.solve()
        agent.initialize_sim()
        agent.simulate(sim_periods = 1)

        #change it back
        # agent.AdjustPrb = 0.0

    return agents


### Initializing financial values

### These are used for the agent's starting estimations
### of the risky asset

market_rate_of_return = 0.000628
market_standard_deviation = 0.011988




### Agent updating

def simulate(agents, periods):
    print("simulating macro agents")
    for agent in agents:
        agent.solve()

        ## Reduce variance on the HARK agent's expected
        ## market return
        store_RiskyStd = agent.RiskyStd
        agent.RiskyStd = 0

        agent.T_sim = periods
        agent.initialize_sim()

        agent.simulate()
        agent.RiskyStd = store_RiskyStd

def update_agent(agent, risky_share, transactions):
    """
    Given an agent, their risky share, and quarterly prices...
        - give the agent new risky expectations based on prices
        - compute and set the agent's market resources
    """
    re = risky_expectations(transactions)

    # agent market resources ('m') are normalized ('Nrm')
    # by the level of permanent income ('pLvl').
    # This constitutes the real assets of the simulated agent.
    assets = agent.state_now['mNrm'] * agent.state_now['pLvl']

    # initial assets held by the agent this past period.
    initial_assets = agent.history['mNrm'][0] \
                     * agent.history['pLvl'][0]

    # initial market resources held in the risky asset.
    initial_risky_assets = initial_assets * risky_share

    # value of risky assets according to their current market price.
    risky_assets_actual_value = initial_risky_assets * \
                                risky_actual_return(transactions)[0]

    # The appreciated value of the risk asset for the simulated agent.
    risky_assets_simulated_value = initial_risky_assets * \
                                   agent.history['Risky'][:,0].prod()

    actual_assets = assets \
                    + risky_assets_actual_value \
                    - risky_assets_simulated_value

    # if the assets are negative--you couldn't have consumed what you did
    # set your money to 0
    assets[assets < 0] = 0

    # normalize the assets and assign them back to the agent.
    agent.state_now['mNrm'] = assets / agent.state_now['pLvl']

    agent.assign_parameters(**re)


def update_agents(agents, transactions):
    for agent in agents:
        update_agent(agent, agent.history['Share'][0], transactions)


##### Computing demand

def demand(agent, transactions):
    '''
    Input:
      - an agent
      - an order book

   Returns: For the agent, their solution for:
      - the risky share
      - the dollar value of risky assets
      - the dollar value of non-risky market assets
    '''
    agent.solve()

    market_resources = agent.state_now['mNrm']
    permanent_income = agent.state_now['pLvl']

    # ShareFunc takes normalized market resources as argument
    risky_share = agent.solution[0].ShareFuncAdj(
        market_resources
    )

    return (risky_share, # proportion
            # allocation to risky asset
            market_resources * risky_share,
            # allocation to risk-free asset
            market_resources * (1 - risky_share))


def demands(agents, transactions):
    """
    For a list of agents, returns the demands of all the agents
     - note side effects for demand function
    """
    print("Getting risky asset demand for all agents")
    return [demand(agent, transactions) for agent in agents]


def no_demand(agents):
    return [(np.zeros(a.AgentCount),
             np.zeros(a.AgentCount),
             np.ones(a.AgentCount)) for a in agents]

### Aggregation

def aggregate_buy_and_sell(old_demand, new_demand):
    """
    Input
      - old demand - of form of output of demand() function
      - new demand

    Output:
      - tuple with aggregate amount (in $$$) to buy and sell of risky asset.
    """
    print("computing aggregate buy/sell transactions")
    buy = 0
    sell = 0

    for i, d in enumerate(old_demand):
        for j in range(len(old_demand)):
            dr = new_demand[i][1][j] - old_demand[i][1][j]

            if dr > 0: # if dr > 0
                buy += dr  # add the dr to the buys
            else:
                sell -= dr # add the dr to the sell side

    return buy, sell


### DEPRECATED
### Estimating risky asset properties


def best_fit_slope_and_intercept(xs,ys):
    """
    Fits a line to the (x,y) data.
    """
    m = (((mean(xs)*mean(ys)) - mean(xs*ys)) /
         ((mean(xs)*mean(xs)) - mean(xs*xs)))

    b = mean(ys) - m*mean(xs)

    return m, b

def estimated_rate_of_return(transactions):
    """
    Estimates rate of return on prices
    """

    # volume adjusted average order price
    avg_price = (transactions['TrdPrice'] * transactions['TrdQuant']).sum() \
                / transactions['TrdQuant'].sum()

    # using midpoint of first buy/sell order book prices
    # to get the "starting price"
    first_price = transactions['TrdPrice'].values[0]

    return avg_price / first_price

def estimated_std_of_return(transactions):
    """
    Empirical standard deviation of prices.
    """

    ## WARNING: This way of computing expected standard
    ##          deviations from the order book makes little sense
    ##          Should be volume-weighted based on transactions, probably.

    return np.std(transactions['TrdPrice'].values)


def risky_expectations(transactions):
    """
    A parameter dictionary with expected properties
    of the risky asset based on historical prices.
    """

    risky_params = {
        'RiskyAvg': estimated_rate_of_return(transactions),
        'RiskyStd': estimated_std_of_return(transactions),
    }

    return risky_params

def risky_actual_return(transactions):
    """
    Actual return on investment in risky asset in the last quarter.

    Returns: (mid return, buy return, sell return)
    For now, all these values will be the same.
    """

    first_price = transactions['TrdPrice'].values[0]

    avg_price = (transactions['TrdPrice'] * transactions['TrdQuant']).sum() \
                / transactions['TrdQuant'].sum()

    avg_return = avg_price / first_price

    return (
        avg_return,
        avg_return,
        avg_return
    )
