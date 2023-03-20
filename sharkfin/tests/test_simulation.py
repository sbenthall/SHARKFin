import numpy as np
from HARK.ConsumptionSaving.ConsPortfolioModel import SequentialPortfolioConsumerType
from pytest import approx

from sharkfin.broker import *
from sharkfin.expectations import *
from sharkfin.population import *
from sharkfin.simulation import *
from simulate.parameters import LUCAS0, WHITESHARK, build_population

## MARKET SIMULATIONS


def test_market_simulation():
    """
    Sets up and runs a MarketSimulation with no population.
    """

    # arguments to Calibration simulation

    q = 1
    r = 60
    market = None

    sim = MarketSimulation(q=q, r=r, market=market)
    sim.simulate(burn_in=2)

    data = sim.daily_data()

    assert len(data["prices"]) == 60


def test_calibration_simulation():
    """
    Sets up and runs an agent population simulation
    """
    # arguments to Calibration simulation

    q = 1
    r = 1
    market = None

    sim = CalibrationSimulation(q=q, r=r, market=market)
    sim.simulate(burn_in=2, buy_sell_shock=(200, 600))

    assert sim.broker.buy_sell_history[1] == (0, 0)
    # assert(len(sim.history['buy_sell']) == 3) # need the padded day
    data = sim.daily_data()

    assert len(data["prices"]) == 2


def test_series_simulation():
    """
    Sets up and runs an agent population simulation
    """

    # arguments to Calibration simulation

    q = 1
    r = 1
    market = None

    sim = SeriesSimulation(q=q, r=r, market=market)
    sim.simulate(
        burn_in=2,
        series=[
            (10000, 0),
            (10000, 0),
            (10000, 0),
            (10000, 0),
            (0, 10000),
            (0, 10000),
            (0, 10000),
            (0, 10000),
        ],
    )

    assert sim.broker.buy_sell_history[2] == (10000, 0)
    # assert(len(sim.history['buy_sell']) == 3) # need the padded day
    data = sim.daily_data()

    assert len(data["prices"]) == 9


## MACRO SIMULATIONS


def test_macro_simulation():
    """
    Sets up and runs an simulation with an agent population.
    """
    # initialize population
    pop = build_population(
        SequentialPortfolioConsumerType,
        WHITESHARK,
        rng=np.random.default_rng(1),
    )

    # arguments to attention simulation

    # a = 0.2
    q = 1
    r = 30
    market = None

    days_per_quarter = 30

    attsim = MacroSimulation(
        pop,
        FinanceModel,
        # a=a,
        q=q,
        r=r,
        market=market,
        days_per_quarter=days_per_quarter,
    )
    attsim.simulate(burn_in=20)

    ## testing for existence of this class stat
    attsim.pop.class_stats()["mNrm_ratio_StE_mean"]

    attsim.daily_data()["sell_macro"]

    attsim.sim_stats()

    assert attsim.days_per_quarter == days_per_quarter
    assert attsim.fm.days_per_quarter == days_per_quarter

    data = attsim.daily_data()

    assert len(data["prices"]) == 30


def test_attention_simulation():
    """
    Sets up and runs an agent population simulation
    """

    # initialize population
    pop = build_population(
        SequentialPortfolioConsumerType,
        WHITESHARK,
        rng=np.random.default_rng(1),
    )

    # arguments to attention simulation

    a = 0.2
    q = 1
    r = 1
    market = None

    days_per_quarter = 30

    attsim = AttentionSimulation(
        pop,
        FinanceModel,
        a=a,
        q=q,
        r=r,
        market=market,
        days_per_quarter=days_per_quarter,
        fm_args={"p1": 0.5},
    )
    attsim.simulate(burn_in=20)

    ## testing for existence of this class stat
    attsim.pop.class_stats()["mNrm_ratio_StE_mean"]

    assert attsim.fm.p1 == 0.5

    attsim.daily_data()["sell_macro"]

    sim_stats = attsim.sim_stats()

    assert attsim.days_per_quarter == days_per_quarter
    assert attsim.fm.days_per_quarter == days_per_quarter

    assert sim_stats["end_day"] == 30

    data = attsim.daily_data()

    assert len(data["prices"]) == 30

    ### Test the market failure case:
    ror_mean_1 = attsim.ror_mean()

    ## mutating these values as if the market had failed.
    attsim.market.prices[-1] = np.nan

    ror_mean_2 = attsim.ror_mean()

    assert ror_mean_1 == approx(ror_mean_2)


def test_lucas0_simulation():
    """
    Sets up and runs an simulation with an agent population.
    """
    # initialize population
    pop = build_population(
        SequentialPortfolioConsumerType,
        LUCAS0,
        rng=np.random.default_rng(1),
    )

    # arguments to attention simulation

    # a = 0.2
    q = 1
    r = 30
    market = None

    days_per_quarter = 30

    attsim = MacroSimulation(
        pop,
        FinanceModel,
        # a=a,
        q=q,
        r=r,
        market=market,
        days_per_quarter=days_per_quarter,
    )
    attsim.simulate(burn_in=20)

    ## testing for existence of this class stat
    attsim.pop.class_stats()["mNrm_ratio_StE_mean"]

    attsim.daily_data()["sell_macro"]

    attsim.sim_stats()

    assert attsim.days_per_quarter == days_per_quarter
    assert attsim.fm.days_per_quarter == days_per_quarter

    data = attsim.daily_data()

    assert len(data["prices"]) == 30
