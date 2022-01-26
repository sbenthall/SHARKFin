import json 
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

channel.queue_declare(queue='params_queue')
channel.queue_declare(queue='prices_queue')

channel.exchange_declare('market')

# add queues to exchange
channel.queue_bind('params_queue', 'market')
channel.queue_bind('prices_queue', 'market')


def callback(ch, method, props, body):
	print('callback triggered')
	data = json.loads(body)

	seed = data['seed']
	bl = data['bl']
	sl = data['sl']

	print(f'seed: {seed}, bl: {bl}, sl: {sl}')

	ch.basic_publish(exchange='market', 
					 routing_key='prices_queue',
					 properties=pika.BasicProperties(correlation_id=props.correlation_id),
					 body='10.5'),
	# ch.basic_ack(delivery_tag=method.delivery_tag)


	# send closing price
	# send_price('localhost', 'market', 'prices_queue', '10.5')


# channel.basic_qos(prefetch_count=1)


channel.basic_consume('params_queue', on_message_callback=callback)
channel.start_consuming()




