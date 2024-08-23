import sys
from PyQt6 import QtWidgets, uic, QtCore
import pyvisa
from pyvisa import constants
import os
import pyqtgraph as pg
from time import sleep
import pika
import threading

# Open RM
rm = pyvisa.ResourceManager()

# Path to UI file
script_directory = os.path.dirname(os.path.abspath(__file__))
ui_folder = r"/HMI_RRL_3.ui" if os.name == "posix" else r"\HMI_RRL_3.ui"
ui_dir = script_directory + ui_folder


class Interfaz(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Interfaz, self).__init__(parent)
        self.ui = uic.loadUi(ui_dir, self)
        self.rig_dmm = None
        self.rig_sp = None
        self.ls = None

        # RabbitMQ setup
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='IDN_DMM')

        # Setup GUI connections
        self.ui.c_sp.clicked.connect(self.sp_connection)
        self.ui.c_dmm.clicked.connect(self.dmm_connection)
        self.ui.c_ls.clicked.connect(self.ls_connection)
        self.ui.volt_set.clicked.connect(self.voltage_set)

        # Setup plot
        self.layout1 = self.ui.verticalLayout_3
        self.PlotWidget1 = pg.PlotWidget(name="Plot1", title=u'Temperature vs Time')
        self.PlotWidget1.setLabel('bottom', 'Time', 'min')
        self.PlotWidget1.setLabel('left', 'Temperature', '°C')
        self.PlotWidget1.setYRange(0, 50)
        self.layout1.addWidget(self.PlotWidget1)

    def dmm_connection(self):
        if self.ui.c_dmm.isChecked():
            try:
                self.rig_dmm = rm.open_resource('USB0::0x1AB1::0x0588::DM3R153200585::INSTR')
                command = ":*IDN?"
                response = self.rig_dmm.query(command)
                self.channel.basic_publish(exchange='', routing_key='IDN_DMM', body=response)
                print("Digital MultiMeter Connected!")
            except Exception as err:
                print(f'Error: {err}')
        else:
            self.rig_dmm.close()
            print("Digital MultiMeter Disconnected!")

    def consume_messages(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        def callback(ch, method, properties, body):
            print(f" [x] Received {body.decode()}")

        channel.basic_consume(queue='IDN_DMM', on_message_callback=callback, auto_ack=True)
        channel.start_consuming()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Interfaz()

    # Start the consumer in a separate thread
    consumer_thread = threading.Thread(target=window.consume_messages, daemon=True)
    consumer_thread.start()

    window.show()
    sys.exit(app.exec())
