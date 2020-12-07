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

def create_agents(agent_classes, ap):
    """
    Initialize the agent objects according to standard
    parameterization ap and agent_classes definition.

    Returns a list of HARK agents.
      - these agents will have computed starting risky shares
    """
    agents = [
        cpm.PortfolioConsumerType(
            AgentCount = ac[1],
            aNrmInitMean = ac[2],
            **update_return(ap, ac[0])
        )
        for ac
        in agent_classes
    ]

    for agent in agents:
        agent.track_vars += ['pLvlNow','mNrmNow','ShareNow','RiskyNow']

        agent.AdjustPrb = 1.0
        agent.T_sim = 1
        agent.solve()
        agent.initializeSim()
        agent.simulate()

        #change it back
        # agent.AdjustPrb = 0.0

    return agents


### Initializing prices

init_prices = np.array([1.0, 1.06, 0.98, 1.05])


### Estimating risky asset properties


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
    #m, b = best_fit_slope_and_intercept(np.arange(prices.size), prices)

    #return 1 + m * prices.size

    return prices[-1] / prices[0]

def estimated_std_of_return(prices):
    """
    Empirical standard deviation of prices.
    """
    return np.std(prices)

def risky_actual_return(orders):
    """
    Actual return on investment in risky asset in the last quarter.
    """

    ## TODO: This needs to be a bit more sophisticated
    prices = orders['OrderPrice'].values

    return prices[-1] / prices[0]

def risky_expectations(orders):
    """
    A parameter dictionary with expected properties
    of the risky asset based on historical prices.
    """

    ## TODO: This needs to be a bit more sophisticated
    prices = orders['OrderPrice'].values

    risky_params = {
        'RiskyAvg': estimated_rate_of_return(prices),
        'RiskyStd': estimated_std_of_return(prices),
    }

    return risky_params


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
        agent.initializeSim()

        agent.simulate()
        agent.RiskyStd = store_RiskyStd

def new_assets(agent, risky_share, orders):
    """
    agent - a HARK AgentType after simulation has been run for a quarter
    prices - prices from the previous quarter

    returns true assets following previous quarter of prices
    """
    # current assets according to HARK model.
    assets = agent.state_now['mNrmNow'] * agent.state_now['pLvlNow']

    # old assets according to HARK model
    old_assets = agent.history['mNrmNow'][0][0] * agent.history['pLvlNow'][0][0]

    old_risky_assets = old_assets * risky_share

    actual_risky_assets_now = old_risky_assets * risky_actual_return(orders)

    hark_risky_assets_now = old_risky_assets * \
                            agent.history['RiskyNow'][:,0].prod()

    actual_assets = assets + actual_risky_assets_now - hark_risky_assets_now

    return actual_assets


def update_agent(agent, risky_share, orders):
    """
    Given an agent, their risky share, and quarterly prices...
        - give the agent new risky expectations based on prices
        - compute and set the agent's market resources
    """
    re = risky_expectations(orders)
    assets = new_assets(agent, risky_share, orders)

    # if the assets are negative--you couldn't have consumed what you did
    # set your money to 0
    assets[assets < 0] = 0

    # normalize the assets
    agent.state_now['mNrmNow'] = assets / agent.state_now['pLvlNow']

    agent.assignParameters(**re)


def update_agents(agents, orders):
    for agent in agents:
        update_agent(agent, agent.history['ShareNow'][0], orders)


##### Computing demand

def demand(agent, orders):
    '''
    Input:
      - an agent
      - a price list

   Returns:
      - the risky share
      - the dollar value of risky assets
      - the dollar value of non-risky market assets
    '''
    agent.solve()

    market_resources = agent.state_now['mNrmNow']
    permanent_income = agent.state_now['pLvlNow']

    # ShareFunc takes normalized market resources as argument
    risky_share = agent.solution[0].ShareFuncAdj(
        market_resources
    )

    return (risky_share, # proportion
            # allocation to risky asset
            market_resources * risky_share,
            # allocation to risk-free asset
            market_resources * (1 - risky_share))


def demands(agents, orders):
    """
    For a list of agents, returns the demands of all the agents
     - note side effects for demand function
    """
    print("Getting risky asset demand for all agents")
    return [demand(agent, orders) for agent in agents]


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
    print("computing aggregate buy/sell orders")
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
