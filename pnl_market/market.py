from sharkfin.markets import AbstractMarket

import pandas as pd

import pnl_market.py.pnl as pnl
import pnl_market.py.util as UTIL

import logging

import os


logger = logging.getLogger()
logger.setLevel(logging.INFO)

AZURE = pnl.AZURE

if AZURE:
    from sharkfin import azure_storage
    
class MarketPNL(AbstractMarket):
    """
    A wrapper around the Market PNL model with methods for getting
    data from recent runs.

    Parameters
    ----------
    config_file
    config_local_file

    """

    # Properties of the PNL market model
    netlogo_ror = -0.00052125
    netlogo_std = 0.0068

    simulation_price_scale = 0.25
    default_sim_price = 400

    # Empirical data -- redundant with FinanceModel!
    sp500_ror = 0.000628
    sp500_std = 0.011988

    # limits the seeds
    seed_limit = None

    # Storing the last market arguments used for easy access to most
    # recent data
    last_buy_sell = None
    last_seed = None

    seeds = None

    # config object for PNL
    config = None

    # sample - modifier for the seed
    sample = 0

    def __init__(
        self,
        sample=0,
        config_file=os.path.dirname(os.path.realpath(__file__)) + "/macroliquidity.ini",
        config_local_file=os.path.dirname(os.path.realpath(__file__)) + "/macroliquidity_local.ini",
        seed_limit=None,
    ):
        self.config = UTIL.read_config(
            config_file=config_file, config_local_file=config_local_file
        )

        self.sample = 0
        self.seeds = []

        if seed_limit is not None:
            self.seed_limit = seed_limit

    def run_market(self, seed=0, buy_sell=0):
        """
        Runs the NetLogo market simulation with a given
        configuration (config), a tuple with the quantities
        for the brokers to buy/sell (buy_sell), and
        optionally a random seed (seed)
        """
        if seed is None:
            seed_limit = self.seed_limit if self.seed_limit is not None else 3000
            seed = (np.random.randint(seed_limit) + self.sample) % seed_limit

        self.last_seed = seed
        self.last_buy_sell = buy_sell
        self.seeds.append(seed)

        pnl.run_NLsims(
            self.config,
            broker_buy_limit=buy_sell[0],
            broker_sell_limit=buy_sell[1],
            SEED=seed,
            use_cache=True,
        )

    def get_transactions(self, seed=0, buy_sell=(0, 0)):
        """
        Given a random seed (seed)
        and a tuple of buy/sell (buy_sell), look up the transactions
        from the associated output file and return it as a pandas DataFrame.
        """
        logfile = pnl.transaction_file_name(self.config, seed, buy_sell[0], buy_sell[1])

        # use run_market() first to create logs
        if os.path.exists(logfile):
            try:
                transactions = pd.read_csv(logfile, delimiter='\t')
                return transactions
            except Exception as e:
                raise (Exception(f"Error loading transactions from local file: {e}"))
        elif AZURE:
            try:
                (head, tail) = os.path.split(logfile)
                remote_transaction_file_name = os.path.join("pnl", tail)
                csv_data = azure_storage.download_blob(remote_transaction_file_name)

                df = pd.read_csv(io.StringIO(csv_data), delimiter='\t')

                if len(df.columns) < 3:
                    raise Exception(
                        f"transaction dataframe columns insufficent: {df.columns}"
                    )

                return df
            except Exception as e:
                raise (Exception(f"Azure loading {logfile} error: {e}"))

    def get_simulation_price(self, seed=0, buy_sell=(0, 0)):
        """
        Get the price from the simulation run.
        Returns None if the transaction file was empty for some reason.

        TODO: Better docstring
        """

        transactions = self.get_transactions(seed=seed, buy_sell=buy_sell)

        try:
            prices = transactions['TrdPrice']
        except Exception as e:
            raise Exception(
                f"get_simulation_price(seed = {seed},"
                + f" buy_sell = {buy_sell}) error: "
                + str(e)
                + f", columns: {transactions.columns}"
            )

        if len(prices.index) == 0:
            ## BUG FIX HACK
            print("ERROR in PNL script: zero transactions. Reporting no change")
            return None

        return prices[prices.index.values[-1]]

    def daily_rate_of_return(self, seed=None, buy_sell=None):
        ## TODO: Cleanup. Use "last" parameter in just one place.
        if seed is None:
            seed = self.last_seed

        if buy_sell is None:
            buy_sell = self.last_buy_sell

        last_sim_price = self.get_simulation_price(seed=seed, buy_sell=buy_sell)

        if last_sim_price is None:
            last_sim_price = self.default_sim_price

        ror = (last_sim_price * self.simulation_price_scale - 100) / 100

        # adjust to calibrated NetLogo to S&P500
        ror = (
            self.sp500_std * (ror - self.netlogo_ror) / self.netlogo_std
            + self.sp500_ror
        )

        return ror

    def close_market(self):
        return