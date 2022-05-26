from sharkfin.utilities import *
from sharkfin.markets import AbstractMarket
import numpy as np
import json
import pika
import uuid
import os
import time


class ClientRPCMarket(AbstractMarket):
    def __init__(self, seed_limit=None, queue_name='', host='localhost'):
        self.simulation_price_scale = 1
        self.default_sim_price = 100

        # stuff from MarketPNL that we may or may not need

        # Empirical data -- redundant with FinanceModel!

        # limits the seeds
        seed_limit = None

        # Storing the last market arguments used for easy access to most
        # recent data


        # config object for PNL - do we need for AMMPS?

        # sample - modifier for the seed

        # self.config = UTIL.read_config(
        #     config_file = config_file,
        #     config_local_file = config_local_file
        # )

        self.sample = 0
        self.seeds = []

        # if seed_limit is not None:
        #     self.seed_limit = seed_limit

        self.seed_limit = seed_limit

        self.latest_price = None
        self.prices = [self.default_sim_price]

        self.rpc_queue_name = queue_name
        self.rpc_host_name = host

        self.init_rpc()

    def _get_rpc_market_host(self):
        ''' method to get the env variable contining the hostname of the rpc server
            if the varible is not set it will fallback to localhost
        '''
        if self.rpc_host_env_var in os.environ:
            rpc_host = os.environ[self.rpc_host_env_var]
        else:
            rpc_host = 'localhost'
        return rpc_host
    
    def _get_rpc_queue_name(self):
        ''' method to get the env variable containing the queue name to be used for the rpc calls
            if the variable is not set it will fall back to a blank name
        '''
        if self.rpc_queue_env_var in os.environ:
            rpc_queue_name = os.environ[self.rpc_queue_env_var]
        else:
            rpc_queue_name = 'rpc_queue'
        return rpc_queue_name

    def init_rpc(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rpc_host_name)
        )

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=False)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True,
        )

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def run_market(self, seed=None, buy_sell=(0, 0)):
        if seed is None:
            seed_limit = self.seed_limit if self.seed_limit is not None else 3000
            seed = (np.random.randint(seed_limit) + self.sample) % seed_limit

        self.last_seed = seed
        self.last_buy_sell = buy_sell
        self.seeds.append(seed)

        data = {'seed': seed, 'bl': buy_sell[0], 'sl': buy_sell[1], 'end_simulation': False}

        self.response = None

        self.publish(data)

        print('waiting for response...')

        while self.response is None:
            time.sleep(4)
            self.connection.process_data_events()

        print('response received')

        self.latest_price = float(self.response)
        self.prices.append(float(self.response))

        return self.latest_price

    def get_simulation_price(self, seed=0, buy_sell=(0, 0)):
        return self.latest_price

    def daily_rate_of_return(self, seed=None, buy_sell=None):
        # same as PNL class. Should this be put in the abstract base class?
        # need different scaling for AMMPS vs PNL, this needs to be changed.

        ## TODO: Cleanup. Use "last" parameter in just one place.
        if seed is None:
            seed = self.last_seed

        if buy_sell is None:
            buy_sell = self.last_buy_sell

        last_sim_price = self.get_simulation_price(seed=seed, buy_sell=buy_sell)

        if last_sim_price is None:
            last_sim_price = self.default_sim_price

        # ror = (last_sim_price * self.simulation_price_scale - 100) / 100
        ror = (self.latest_price - self.prices[-2])/self.prices[-2]

        # adjust to calibrated NetLogo to S&P500
        # do we need to calibrate AMMPS to S&P as well?

        # modularize calibration 
        # ror = self.sp500_std * (ror - self.netlogo_ror) / self.netlogo_std + self.sp500_ror

        return ror

    def publish(self, data):
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key=self.rpc_queue_name,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(data),
        )


    def close_market(self): 
        self.publish({'seed': 0, 'bl': 0, 'sl': 0, 'end_simulation': True})

        self.connection.close()