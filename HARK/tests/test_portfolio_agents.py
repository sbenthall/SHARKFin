import hark_portfolio_agents as hpa

def test_mock_market():
	mock = hpa.MockMarket()

	mock.run_market()

	price = mock.get_simulation_price()

	ror = mock.daily_rate_of_return(buy_sell=(0,0))

def test_pnl_market():
	mock = hpa.MarketPNL()

	mock.run_market(buy_sell=(0,0))

	price = mock.get_simulation_price()

	ror = mock.daily_rate_of_return(buy_sell=(0,0))