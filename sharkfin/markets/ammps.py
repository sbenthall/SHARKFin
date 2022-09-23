from sharkfin.utilities import *
from sharkfin.markets import AbstractMarket
import numpy as np
import json
import pika
import uuid
import os
import time


class ClientRPCMarket(AbstractMarket):

    dividend_growth_rate = None
    
    dividend_std = None
    
    dividends = None
    
    prices = None

    rng = None

    def __init__(self,
        seed=None,
        queue_name='',
        host='localhost',
        dividend_growth_rate = 1.000628,
        dividend_std = 0.011988,
        price_to_dividend_ratio = 60 / 0.05,
        rng = None
        ):

        # discounted future value, divided by days per quarter
        self.price_to_dividend_ratio = price_to_dividend_ratio

        self.dividend_growth_rate = dividend_growth_rate
        self.dividend_std = dividend_std

        self.simulation_price_scale = 1
        self.default_sim_price = 100
        self.seeds = seed
        self.rng = rng if rng is not None else np.random.default_rng()

        self.latest_price = None
        self.prices = [self.default_sim_price]
        self.dividends = [self.default_sim_price / self.price_to_dividend_ratio]

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

    def run_market(self, buy_sell=(0, 0)):

        self.last_buy_sell = buy_sell

        new_dividend = self.next_dividend()
        self.dividends.append(new_dividend)

        data = {
            'bl': buy_sell[0],
            'sl': buy_sell[1],
            'dividend' : new_dividend,
            'end_simulation': False
            }

        self.response = None

        self.publish(data)

        print('waiting for response...')

        while self.response is None:
            time.sleep(4)
            self.connection.process_data_events()

        print('response received')
        response_dict = json.loads(self.response)
        response_price = response_dict["ClosingPrice"]
        self.latest_price = float(response_price)
        self.prices.append(float(response_price))

        if (response_dict["MarketState"] == "Normal"):

            return self.latest_price, new_dividend
        if (response_dict["MarketState"].startswith("Stopped:")):
            # Do something to end simulation and log message of "MarketState" field. last_price is going to be 0
            # Above we check if the `MarketState` field begins with "Stopped:" but the string will also contain a
            # message appended to the string, containing a reason for stopping. This can be passed upstream for logging.
            # An example could be "Stopped: got negative prices" or similar.
            message = response_dict["MarketState"] 
            return self.latest_price, new_dividend # pass message upstream

    def get_simulation_price(self, buy_sell=(0, 0)):
        return self.latest_price

    def daily_rate_of_return(self, buy_sell=None):
        # same as PNL class. Should this be put in the abstract base class?
        # need different scaling for AMMPS vs PNL, this needs to be changed.

        if buy_sell is None:
            buy_sell = self.last_buy_sell

        last_sim_price = self.get_simulation_price(buy_sell=buy_sell)

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
        self.publish({'seed': 0, 'bl': 0, 'sl': 0, 'dividend' : 0, 'end_simulation': True})
        self.channel.queue_delete(self.callback_queue)
        self.connection.close()
