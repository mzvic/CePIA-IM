import sys
from PyQt6 import QtWidgets, uic
import pyvisa
import os
import pyqtgraph as pg
import pika
import threading
import csv
from datetime import datetime
from time import sleep

# Open RM
rm = pyvisa.ResourceManager()

# Path to UI file
script_directory = os.path.dirname(os.path.abspath(__file__))
ui_folder = r"/HMI_RRL_3.ui" if os.name == "posix" else r"\HMI_RRL_3.ui"
ui_dir = script_directory + ui_folder

# CSV file path
csv_file_path = os.path.join(script_directory, f"DATA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")


class RabbitMQHandler:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            self.channel = self.connection.channel()
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Connection error: {e}")
            sleep(5)
            self.connect()

    def publish_message(self, queue_name, message):
        try:
            self.connect()
            self.channel.queue_declare(queue=queue_name)
            self.channel.basic_publish(exchange='', routing_key=queue_name, body=message)
            print(f" [x] Sent {message} to queue {queue_name}")
        except pika.exceptions.StreamLostError as e:
            print(f"StreamLostError: {e}, attempting to reconnect")
            self.connect()
            self.publish_message(queue_name, message)

    def consume_messages(self, queue_name, callback):
        try:
            self.connect()
            self.channel.queue_declare(queue=queue_name)

            def inner_callback(ch, method, properties, body):
                message = body.decode()
                callback(message)

            self.channel.basic_consume(queue=queue_name, on_message_callback=inner_callback, auto_ack=True)
            self.channel.start_consuming()
        except pika.exceptions.AMQPChannelError as e:
            print(f"AMQPChannelError: {e}, possibly the queue is empty or there is a channel issue")
            # Reintentar la conexión y la suscripción a la cola
            self.connect()
            self.consume_messages(queue_name, callback)
        except pika.exceptions.StreamLostError as e:
            print(f"StreamLostError: {e}, attempting to reconnect")
            self.connect()
            self.consume_messages(queue_name, callback)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

class Interfaz(QtWidgets.QMainWindow):
    def __init__(self, rabbit_handler, parent=None):
        super(Interfaz, self).__init__(parent)
        self.ui = uic.loadUi(ui_dir, self)
        self.rig_dmm = None
        self.ls = None  
        self.rabbit_handler = rabbit_handler

        # Setup GUI connections
        self.ui.c_dmm.clicked.connect(self.dmm_connection)
        self.ui.c_ls.clicked.connect(self.ls_connection)

        self.start_consuming_messages()

        # Setup CSV file
        self.setup_csv()

    def dmm_connection(self):
        if self.ui.c_dmm.isChecked():
            try:
                self.rig_dmm = rm.open_resource('USB0::0x1AB1::0x0588::DM3R153200585::INSTR')
                command = ":MEAS:VOLT:DC?"
                response = self.rig_dmm.query(command)

                self.rabbit_handler.publish_message("IDN_DMM", response)

                print("Digital MultiMeter Connected!")
            except Exception as err:
                print(f'Error: {err}')
        else:
            if self.rig_dmm:
                self.rig_dmm.close()
            print("Digital MultiMeter Disconnected!")

    def ls_connection(self):
        if self.ui.c_ls.isChecked():
            try:
                self.ls = rm.open_resource("COM5", baud_rate=57600, parity=pyvisa.constants.Parity.odd, data_bits=7)
                command = "CRDG? B" 
                response = self.ls.query(command)

                self.rabbit_handler.publish_message("IDN_LS", response)

                print("LakeShore Model 336 Connected!")
            except Exception as e:
                print(f"Error: {e}")
        else:
            if self.ls:
                self.ls.close()
            print("LakeShore Model 336 Disconnected!")

    def start_consuming_messages(self):
        if self.c_dmm.isChecked():
            consumer_thread_dmm = threading.Thread(
                target=lambda: self.rabbit_handler.consume_messages("IDN_DMM", self.handle_message_dmm),
                daemon=True
            )
            consumer_thread_dmm.start()
        if self.c_ls.isChecked():
            consumer_thread_ls = threading.Thread(
                target=lambda: self.rabbit_handler.consume_messages("IDN_LS", self.handle_message_ls),
                daemon=True
            )
            consumer_thread_ls.start()

    def handle_message_dmm(self, message):
        voltage = float(message.strip())
        self.write_to_csv(voltage=voltage)
        print(f"Voltage received and stored: {voltage} V")

    def handle_message_ls(self, message):
        temperature = float(message.strip())
        self.write_to_csv(temp=temperature)
        print(f"Temperature received and stored: {temperature} C")

    def write_to_csv(self, voltage=None, temp=None):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [current_time]
        if voltage is not None:
            row.append(voltage)
        if temp is not None:
            row.append(temp)

        with open(csv_file_path, 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(row)

    def setup_csv(self):
        if not os.path.exists(csv_file_path):
            with open(csv_file_path, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(["Timestamp", "Voltage", "Temperature"])


if __name__ == "__main__":
    rabbit_handler = RabbitMQHandler()

    # Iniciar la aplicación Qt
    app = QtWidgets.QApplication(sys.argv)
    window = Interfaz(rabbit_handler)
    window.show()
    sys.exit(app.exec())
