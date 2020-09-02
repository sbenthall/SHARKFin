import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
import HARK.ConsumptionSaving.ConsIndShockModel as cism
import numpy as np

### Initializing agents

def update_return(dict1, dict2):
    """
    Returns new dictionary,
    copying dict1 and updating the values of dict2
    """
    dict3 = dict1.copy()
    dict3.update(dict2)

    return dict3

def create_agents(agent_classes, ap):
    """
    Initialize the agent objects according to standard
    parameterization ap and agent_classes definition.

    Returns a list of HARK agents.
    """
    agents = [
        cpm.PortfolioConsumerType(
            AgentCount = ac[1],
            **update_return(ap, ac[0])
        )
        for ac
        in agent_classes
    ]

    for a in agents:
        a.track_vars += ['pLvlNow','mNrmNow','ShareNow','RiskyNow']

    return agents


### Estimating risky asset properties
from statistics import mean

def best_fit_slope_and_intercept(xs,ys):
    """
    Fits a line to the (x,y) data.
    """
    m = (((mean(xs)*mean(ys)) - mean(xs*ys)) /
         ((mean(xs)*mean(xs)) - mean(xs*xs)))

    b = mean(ys) - m*mean(xs)

    return m, b

def estimated_rate_of_return(prices):
    """
    Estimates quarterly rate of return on prices
    """
    m, b = best_fit_slope_and_intercept(np.arange(prices.size), prices)

    return 1 + m * prices.size

def estimated_std_of_return(prices):
    """
    Empirical standard deviation of prices.
    """
    return np.std(prices)

def risky_actual_return(prices):
    """
    Actual return on investment in risky asset in the last quarter.
    """
    return prices[-1] / prices[0]

def risky_expectations(prices):
    """
    A parameter dictionary with expected properties
    of the risky asset based on historical prices.
    """

    risky_params = {
        'RiskyAvg': estimated_rate_of_return(prices),
        'RiskyStd': estimated_std_of_return(prices),
    }

    return risky_params


### Agent updating

def new_assets(agent, risky_share, prices):
    """
    agent - a HARK AgentType after simulation has been run for a quarter
    prices - prices from the previous quarter

    returns true assets following previous quarter of prices
    """
    # current assets according to HARK model.
    assets = agent.mNrmNow / agent.pLvlNow

    # old assets according to HARK model
    old_assets = agent.history['mNrmNow'][0] * agent.history['pLvlNow'][0]

    old_risky_assets = old_assets * risky_share

    actual_risky_assets_now = old_risky_assets * risky_actual_return(prices)

    hark_risky_assets_now = old_risky_assets * agent.history['RiskyNow'][:,0].prod()

    actual_assets = assets + actual_risky_assets_now - hark_risky_assets_now

    return actual_assets


def update_agent(agent, risky_share, prices):
    """
    Given an agent, their risky share, and quarterly prices...
        - give the agent new risky expectations based on prices
        - compute and set the agent's market resources
    """
    re = risky_expectations(prices)
    assets = new_assets(agent, risky_share, prices)

    # normalize the assets
    agent.mNrmNow = assets / agent.pLvlNow

    agent.assignParameters(**re)


##### Computing demand

def demand(agent, prices):
    '''
    Input:
      - an agent
      - a price list

    Side Effects:
      - updates the agent's assets and risky expectations

    Returns:
      - the risky share
      - the dollar value of risky assets
      - the dollar value of non-risky market assets
    '''

    update_agent(agent, agent.history['ShareNow'][0], prices)
    agent.solve()

    market_resources = agent.mNrmNow
    permanent_income = agent.pLvlNow

    # ShareFunc takes normalized market resources as argument
    risky_share = agent.solution[0].ShareFuncAdj(
        market_resources * permanent_income)

    return (risky_share, # proportion
            market_resources * risky_share, # allocation to risky asset
            market_resources * (1 - risky_share)) # allocation to risk-free asset

### Aggregation

def aggregate_buy_and_sell(old_demand, new_demand):
    """
    Input
      - old demand - of form of output of demand() function
      - new demand

    Output:
      - tuple with aggregate amount (in $$$) to buy and sell of risky asset.
    """
    buy = 0
    sell = 0

    for i, d in enumerate(old_demand):
        for j in range(len(old_demand)):
            dr = new_demand[i][1][j] - old_demand[i][1][j]

            if dr > 0: # if dr > 0
                buy += dr  # add the dr to the buys
            else:
                sell += dr # add the dr to the sell side

    return buy, sell
