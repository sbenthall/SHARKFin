from hark_portfolio_agents import *
import numpy as np

class CalibrationSimulation(AttentionSimulation):
	def pad_market(self, n_days=30):
		for day in range(n_days):
			for agent in self.agents:
				self.broker.transact(np.zeros(1))

			buy_sell, ror = self.broker.trade()

			self.update_agent_wealth_capital_gains(self.fm.rap(), ror)

			self.track(day)

			risky_asset_price = self.fm.add_ror(ror)
			self.fm.calculate_risky_expectations()