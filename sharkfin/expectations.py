from sharkfin.utilities import *
import math
import numpy as np

from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple

from HARK.distribution import Lognormal
import math
from scipy.stats import lognorm, ks_1samp

def scipy_stats_lognorm_from_mean_std(mean, std):
    hark_lognorm = Lognormal.from_mean_std(mean, std)

    dist = lognorm(
        s = hark_lognorm.sigma,
        scale = math.exp(hark_lognorm.mu)
    )

    return dist

class AbstractExpectations(ABC):
    '''
    Abstract class from which Expectations should inherit

    defines common methods for all market models.
    '''

    @property
    @abstractmethod
    def market(self):
        """
        The Market object that this class models.
        """
        pass


    @abstractmethod
    def calculate_risky_expectations(self):
        """
        Compute the quarterly expectations for the risky asset based on historical return rates.

        In this implementation there are a number of references to:
          - parameters that are out of scope
          - data structures that are out of scope

        These should be bundled together somehow.

        NOTE: This MUTATES the 'expected_ror_list' and so in current design
        has to be called on a schedule... this should be fixed.
        """
        pass

    @abstractmethod
    def risky_expectations(self, agent = None):
        """
        Return quarterly expectations for the risky asset.
        These are the average and standard deviation for the asset
        including both capital gains and dividends.

        Params
        -------

        agent: AgentType -- the agent for whom the risky expectations are being taken.
        """
        pass

    @abstractmethod
    def reset(self):
        """
        Reset the data stores back to original value.
        """
        pass

class UsualExpectations(AbstractExpectations):
    """
    The Lucas "usual" expectations of the market.
    Beliefs about the risky asset are constant
    and based on the dividend process driving the
    market prices.

    This class still performs basic bookkeeping functions
    to fit the simulation interface.
    """
    # These are the S&P500 numbers but see how in __init__
    # these are being replaced by numbers derived from the Market.
    # That is better design; we need to make sure the Market is getting
    # the right values.
    daily_ror = 0.000628
    daily_std = 0.011988

    # Simulation parameter
    days_per_quarter = 60

    # Data structures. These will change over time.
    starting_price = 100 # USE FROM MARKET

    expected_ror_list = None
    expected_std_list = None

    market = None

    def __init__(
        self,
        market,
        days_per_quarter = None,
        options = None
    ):

        self.market = market

        if days_per_quarter:
            self.days_per_quarter = days_per_quarter

        self.prices = [self.starting_price]

        ### Expected daily ROR and SD assuming
        ### 1. A constant price-to-dividend-ratio
        ### 2. A constant mean dividend growth rate
        ### 3. A (lognormal) random dividend walk
        pdr = self.market.price_to_dividend_ratio
        dgr = self.market.dividend_growth_rate
        dsd = self.market.dividend_shock_std

        # this assumes daily_ror is actually the daily price change.
        # need to double check this math.
        adjuster = ((1 + dgr) + (1 + dgr) / pdr)

        self.daily_ror = adjuster - 2
        self.daily_std = dsd * adjuster

        # self.ror_list = []
        self.expected_ror_list = []
        self.expected_std_list = []

        self.options = options

    def asset_price_stats(self):
        """
        Get statistics on the price of the asset for final reporting.
        TODO: CHANGE SIM TO GET THESE FROM MARKET AND REMOVE
        """
        return self.market.asset_price_stats()

    def calculate_risky_expectations(self):
        """
        Just repeats the constant belief parameters.

        NOTE: This MUTATES the 'expected_ror_list' and so in current design
        has to be called on a schedule... this should be fixed.
        """

        expected_ror = self.daily_ror
        self.expected_ror_list.append(expected_ror)

        expected_std = self.daily_std
        self.expected_std_list.append(expected_std)

    def rap(self):
        """
        Returns the current risky asset price. MOVE TO MARKET
        """
        return self.market.prices[-1]

    def risky_expectations(self, agent = None):
        """
        Return quarterly expectations for the risky asset.
        These will be constant.
        """
        # expected capital gains quarterly
        ex_cg_q_ror = ror_quarterly(self.expected_ror_list[-1], self.days_per_quarter)
        ex_cg_q_std = sig_quarterly(self.expected_std_list[-1], self.days_per_quarter)

        market_risky_params = {'RiskyAvg': 1 + ex_cg_q_ror, 'RiskyStd': ex_cg_q_std}

        return market_risky_params

    def reset(self):
        """
        Reset the data stores back to original value.
        """
        self.prices = [100]
        #self.ror_list = []
        ## TODO: Reset the market?!

        self.expected_ror_list = []
        self.expected_std_list = []


class FinanceModel(AbstractExpectations):
    """
    A class representing the financial system in the simulation.

    Contains parameter values for:
      - the capital gains expectations function
      - the dividend
      - the risky asset expectations

    Contains data structures for tracking ROR and STD over time.
    """

    # Empirical data
    sp500_ror = 0.000628
    sp500_std = 0.011988

    # Simulation parameter
    days_per_quarter = 60

    # Expectation calculation parameters
    p1 = 0.1
    delta_t1 = 60

    a = -math.log(p1) / delta_t1

    p2 = 0.1
    delta_t2 = 60

    b = math.log(p2) / delta_t2

    # Data structures. These will change over time.
    starting_price = 100 # USE FROM MARKET
    #prices = None
    #ror_list = None

    expected_ror_list = None
    expected_std_list = None

    market = None

    def __init__(
        self,
        market,
        days_per_quarter = None,
        options = {
            'p1' : None,
            'p2' : None,
            'delta_t1' : None,
            'delta_t2' : None,
        }
    ):
        self.market = market

        if 'p1' in options:
            self.p1 = options["p1"]

        if 'p2' in options:
            self.p2 = options["p2"]

        if 'delta_t1' in options:
            self.delta_t1 = options["delta_t1"]

        if 'delta_t2' in options:
            self.delta_t2 = options["delta_t2"]

        if days_per_quarter:
            self.days_per_quarter = days_per_quarter

        self.prices = [self.starting_price]
        # self.ror_list = []
        self.expected_ror_list = []
        self.expected_std_list = []

        self.options = options

    def asset_price_stats(self):
        """
        Get statistics on the price of the asset for final reporting.
        TODO: CHANGE SIM TO GET THESE FROM MARKET AND REMOVE
        """
        return self.market.asset_price_stats()

    def calculate_risky_expectations(self):
        """
        Compute the quarterly expectations for the risky asset based on historical return rates.

        In this implementation there are a number of references to:
          - parameters that are out of scope
          - data structures that are out of scope

        These should be bundled together somehow.

        NOTE: This MUTATES the 'expected_ror_list' and so in current design
        has to be called on a schedule... this should be fixed.
        """

        ror_list = self.market.ror_list()

        # note use of data store lists for time tracking here -- not ideal
        D_t = sum([math.exp(self.a * (l + 1)) for l in range(len(ror_list))])
        S_t = math.exp(
            self.b * (len(self.market.prices) - 1)
        )  # because p_0 is included in this list.

        w_0 = S_t
        w_t = [
            (1 - S_t) * math.exp(self.a * (t + 1)) / D_t
            for t in range(len(ror_list))
        ]

        expected_ror = w_0 * self.sp500_ror + sum(
            [w_ror[0] * w_ror[1] for w_ror in zip(w_t, ror_list)]
        )
        self.expected_ror_list.append(expected_ror)

        expected_std = math.sqrt(
            w_0 * pow(self.sp500_std, 2)
            + sum(
                [
                    w_ror_er[0] * pow(w_ror_er[1] - expected_ror, 2)
                    for w_ror_er in zip(w_t, ror_list)
                ]
            )
        )
        self.expected_std_list.append(expected_std)

    def rap(self):
        """
        Returns the current risky asset price. MOVE TO MARKET
        """
        return self.market.prices[-1]

    def risky_expectations(self, agent = None):
        """
        Return quarterly expectations for the risky asset.
        These are the average and standard deviation for the asset
        including both capital gains and dividends.
        """
        # expected capital gains quarterly
        ex_cg_q_ror = ror_quarterly(self.expected_ror_list[-1], self.days_per_quarter)
        ex_cg_q_std = sig_quarterly(self.expected_std_list[-1], self.days_per_quarter)

        market_risky_params = {'RiskyAvg': 1 + ex_cg_q_ror, 'RiskyStd': ex_cg_q_std}

        return market_risky_params

    def reset(self):
        """
        Reset the data stores back to original value.
        """
        self.prices = [100]
        #self.ror_list = []
        ## TODO: Reset the market?!

        self.expected_ror_list = []
        self.expected_std_list = []


class InferentialExpectations(FinanceModel):
    """
    An expectations model that reports either the UsualExpectations
    or the expectations based on the chartist FinanceModel with probability
    dependent on the goodness of fit of the UsualExpectations to
    price data.
    """
    # USUAL expectation daily ROR and STD
    daily_ror = 0.000628
    daily_std = 0.011988

    # p-level threshold of rejection of null-hypothesis (USUAL)
    # 1 - confidence level.
    # zeta = 0 -> always use usual expectations
    # zeta = 1 -> always use strange expectations.
    zeta = 0.0

    market = None

    def __init__(
        self,
        market,
        days_per_quarter = None,
        options = {
            'p1' : None,
            'p2' : None,
            'delta_t1' : None,
            'delta_t2' : None,
            'zeta' : 0.5
            }
    ):

        super().__init__(market=market, days_per_quarter = days_per_quarter, options = options)

        usual = UsualExpectations(market, days_per_quarter, options)

        self.daily_ror = usual.daily_ror
        self.daily_std = usual.daily_std

        if 'zeta' in options:
            self.zeta = options['zeta']

    def risky_expectations(self, agent = None):
        """
        Return quarterly expectations for the risky asset.
        
        Stochastically determine whether to use the USUAL expectations, 
        or the STRANGE expectations resulting from the FinanceModel, based
        on the goodness-of-fit of the USUAL expectations and the zeta threshold
        parameter.
        """

        usual_ror = self.daily_ror
        usual_std = self.daily_std

        usual_dist = scipy_stats_lognorm_from_mean_std(1 + usual_ror, usual_std)

        observed_ror = None
        if 'attention_days' in agent.parameters:
            observed_ror = np.array(self.market.ror_list())[agent.parameters['attention_days']] + 1

        strange_ror = self.expected_ror_list[-1]
        strange_std = self.expected_std_list[-1]
        #strange_dist = scipy_stats_lognorm_from_mean_std(1 + strange_ror, strange_std)

        if observed_ror is not None:
            try:

                ksd = ks_1samp(observed_ror, usual_dist.cdf)
                #print(ksd)
            except Exception as e:
                print(f"observed_ror: {observed_ror}")
                print(f"usual dist: {usual_dist.mean()}. {usual_dist.std()}")
                print(e)
                raise e

            if ksd.pvalue < self.zeta:
                #print(f"STRANGE: observed_ror: {observed_ror}, p: {ksd.pvalue} <= zeta = {self.zeta}")
                ## TODO: Add noise to this to prevent herding....
                ror = strange_ror
                std = strange_std
            else:
                ror = usual_ror
                std = usual_std

        else:
            # with no observations assume usual
            ror = usual_ror
            std = usual_std

        # expected quarterly returns
        q_ror = ror_quarterly( ror , self.days_per_quarter)
        q_std = sig_quarterly( std , self.days_per_quarter)

        market_risky_params = {'RiskyAvg': 1 + q_ror, 'RiskyStd': q_std}

        return market_risky_params
