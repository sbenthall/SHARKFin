import hark_portfolio_agents as hpa
	
market = hpa.ClientRPCMarket()

x = market.run_market(seed=1, buy_sell=(2, 3))
print(x)