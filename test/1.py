#!/usr/bin/env python
import pika
import sys

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='task_queue')
channel.queue_declare(queue='task_queue2')


message = "Hello World!"
channel.basic_publish(
    exchange='',
    routing_key='task_queue',
    body=message
    )
channel.basic_publish(
    exchange='',
    routing_key='task_queue2',
    body=message
    )
connection.close()

