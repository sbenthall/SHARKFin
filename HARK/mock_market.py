import json 
import pika

def send_price(addr, exch_name, rkey, body):
	channel.basic_publish(exch_name, rkey, body)

def callback(ch, method, properties, body):
	print('callback triggered')
	data = json.loads(body)

	seed = data['seed']
	bl = data['bl']
	sl = data['sl']

	print(f'seed: {seed}, bl: {bl}, sl: {sl}')

	# send closing price
	send_price('localhost', 'prices', 'prices_queue', '10.5')


con_addr = 'localhost'

connection = pika.BlockingConnection(pika.ConnectionParameters(con_addr))
channel = connection.channel()

channel.exchange_declare('params')
channel.exchange_declare('prices')

params_queue = channel.queue_declare('params_queue')
prices_queue = channel.queue_declare('prices_queue')

channel.queue_bind('params_queue', 'params')
channel.queue_bind('prices_queue', 'prices')



channel.basic_consume('params_queue', callback)
channel.start_consuming()