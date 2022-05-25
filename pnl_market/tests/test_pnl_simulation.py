from pnl_market.market import MarketPNL
from sharkfin.broker import *
from sharkfin.expectations import *
from sharkfin.population import *
from sharkfin.simulation import *
import HARK.ConsumptionSaving.ConsPortfolioModel as cpm
from HARK.Calibration.Income.IncomeTools import (
     sabelhaus_song_var_profile,
)
import os

def test_pnl_market():
     cwd = os.getcwd()

     os.chdir(os.path.dirname(os.path.realpath(__file__)) + '/..')

     market = MarketPNL()

     market.run_market(buy_sell=(0,0))

     price = market.get_simulation_price()

     assert price > 0

     ror = market.daily_rate_of_return(buy_sell=(0,0))

     assert ror > 0

     os.chdir(cwd)