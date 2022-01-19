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
	send_price('localhost', 'market', 'prices_queue', '10.5')


con_addr = 'localhost'

connection = pika.BlockingConnection(pika.ConnectionParameters(con_addr))
channel = connection.channel()

channel.exchange_declare('market')

params_queue = channel.queue_declare('params_queue')
prices_queue = channel.queue_declare('prices_queue')

channel.queue_bind('params_queue', 'market')
channel.queue_bind('prices_queue', 'market')



channel.basic_consume('params_queue', callback)
channel.start_consuming()