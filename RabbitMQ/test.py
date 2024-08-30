import time
import pyvisa
import pika
import json
import csv
import threading

def publisher():
    rm = pyvisa.ResourceManager()
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='instrument_data')

    try:
        instrument_1 = rm.open_resource('USB0::0x1AB1::0x0588::DM3R153200585::INSTR')
        while True:
            data_1 = instrument_1.query(":MEASure:CURRent:DC?")
            
            data = {
                "instrument_1": data_1,
                "timestamp": time.time()
            }
            print(data)
            channel.basic_publish(exchange='', routing_key='instrument_data', body=json.dumps(data))
            time.sleep(1)

    except KeyboardInterrupt:
        print("Cerrando conexión...")

    finally:
        connection.close()

def write_to_csv(ch, method, properties, body):
    data = json.loads(body)
    with open('data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([data['timestamp'], data['instrument_1']])

def subscriber():

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='instrument_data')
    channel.basic_consume(queue='instrument_data', on_message_callback=write_to_csv, auto_ack=True)

    print("waiting message")
    channel.start_consuming()

if __name__ == "__main__":
    with open('data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Instrument 1"])

    publisher_thread = threading.Thread(target=publisher)
    subscriber_thread = threading.Thread(target=subscriber)
    publisher_thread.start()
    subscriber_thread.start()