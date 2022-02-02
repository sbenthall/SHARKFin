import hark_portfolio_agents as hpa
	
market = hpa.ClientRPCMarket()



# ror = market.daily_rate_of_return()

# print(ror)

for i in range(10):
	market.run_market(seed=1, buy_sell=(2, 3))

	ror = market.daily_rate_of_return()

	print(market.latest_price, ror)


