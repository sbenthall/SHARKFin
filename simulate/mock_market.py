import json 
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

channel.queue_declare(queue='rpc_queue')

def counter():
    i = 0
    while True:
        yield i
        i += 1

c = counter()

def on_request(ch, method, props, body):
    data = json.loads(body)

    if 'end_simulation' in data and data['end_simulation'] is True:
        channel.stop_consuming()
        return

    print(f'seed: {data["seed"]}, bl: {data["bl"]}, sl: {data["sl"]}')

    response = data['seed'] + data['bl'] + data['sl']

    # response = next(c)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

print("Awaiting RPC requests")
channel.start_consuming()




