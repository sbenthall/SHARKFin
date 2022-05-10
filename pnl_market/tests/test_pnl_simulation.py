from pnl_market.market import MarketPNL
from sharkfin.broker import *
from sharkfin.expectations import *
from sharkfin.population import *
from sharkfin.simulation import *
import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)

def test_pnl_market():
    market = MarketPNL()

    market.run_market(buy_sell=(0,0))

    price = market.get_simulation_price()

    ror = market.daily_rate_of_return(buy_sell=(0,0))