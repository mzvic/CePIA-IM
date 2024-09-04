#!/usr/bin/env python
import pika
import threading
import time 
def publish_message_queue1(message):
    for i in range(10):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='task_queue')
        if i == 9:
            channel.basic_publish(
                exchange='',
                routing_key='task_queue',
                body="END"
            )
        else:
            channel.basic_publish(
                exchange='',
                routing_key='task_queue',
                body=message
            )
            connection.close()
        time.sleep(2)

def publish_message_queue2(message):
    for i in range(10):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='task_queue2')
        if i == 9:
            channel.basic_publish(
                exchange='',
                routing_key='task_queue2',
                body="END"
            )
        else:
            channel.basic_publish(
                exchange='',
                routing_key='task_queue2',
                body=message
            )
        connection.close()
        time.sleep(1)

message = "Hello World!"

thread1 = threading.Thread(target=publish_message_queue1, args=(message,))
thread2 = threading.Thread(target=publish_message_queue2, args=(message,))

thread1.start()
thread2.start()

thread1.join()
thread2.join()
