# Installation

1. Set up a virtual environment

2. pip install -r requirements.txt

3. Use like this:

```
## List of tuples:
##  ( parameters, (i.e. coefficient of relative risk aversion CRRA)
##    number of agents represented,
##    ( initial risky percent, $$$ in risky asset, $$$ in riskless asset)
agent_classes = [
    ({'CRRA': 5.0}, 100, (0.08, 800, 9200)), # Normal consumers
    ({'CRRA': 6.0}, 50,  (0.08, 800, 9200)),  # More risk-averse consumers
    ({'CRRA': 4.0}, 50,  (0.08, 800, 9200))  #  Less risk-averse consumers
]


### parameters shared by all agents
ap = {
    'aNrmInitMean' : 1.0, # initial distribution of assets held
    'aNrmInitStd' : 0.0,
    'pLvlInitMean' : 1.0, # initial distribution of permanent income
    'pLvlInitStd' : 0.0
}

# STEP 1. Initialize the agents. (and the market?)

agents = hpa.create_agents(agent_classes, ap) # THIS IS DEPRECATED, create_agents does not exist!


# STEP 2. Create starting demand for the market.
#         Burn in the new prices.

# The initial demands for each agent
# hpa.init_prices is used to set the agent's starting
# beliefs about the price process.
init_demands = hpa.demands(agents, hpa.init_prices)

buy_sell = hpa.aggregate_buy_and_sell(
    hpa.no_demand(agents), # zero allocated to risky asset
    init_demands
)

## TODO: ABM Group reimplement the run_market method
prices = run_market(buy_sell)
old_demands = init_demands

# STEP 3. Run simulation for N rebalances

N = 10

for i in range(N):

    # simulate one period on the macro side
    hpa.simulate(agents, 1)
    new_demands = hpa.demands(agents, prices)

    buy_sell = hpa.aggregate_buy_and_sell(
        old_demands,
        new_demands
    )

    prices = run_market(buy_sell)
    old_demands = new_demands

# Testing
Run tests using `python -m pytest`, currently just running `pytest` causes import errors
```