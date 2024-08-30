import sys
from PyQt6 import QtWidgets, uic
import pyvisa
import os
import Ice
import IceStorm
import threading
import time

Ice.loadSlice('IM.ice')
import Demo
threading.Thread(target=os.system("/opt/Ice-3.7/bin/icebox --Ice.Config=icebox.cfg")).start()

# Path to UI file
script_directory = os.path.dirname(os.path.abspath(__file__))
ui_folder = r"/HMI_RRL_3.ui" if os.name == "posix" else r"\HMI_RRL_3.ui"
ui_dir = script_directory + ui_folder

# Open RM
rm = pyvisa.ResourceManager()
print(rm.list_resources())

# Clase que maneja la interfaz gráfica
class Interfaz(QtWidgets.QMainWindow):
    def __init__(self, publisher, parent=None):
        super(Interfaz, self).__init__(parent)
        self.ui = uic.loadUi(ui_dir, self)
        self.rig_dmm = None
        self.publisher = publisher

        # Setup GUI connections
        self.ui.c_dmm.clicked.connect(self.dmm_connection)

    def dmm_connection(self):
        if self.ui.c_dmm.isChecked():
            try:
                self.rig_dmm = rm.open_resource('USB0::0x1AB1::0x0588::DM3R153200585::INSTR')
                command = ":*IDN?"
                response = self.rig_dmm.query(command)
                print("Digital MultiMeter Connected!")

                # Publica el IDN usando IceStorm
                self.publisher.publish_idn(response)

            except Exception as err:
                print(f'Error: {err}')
        else:
            if self.rig_dmm:
                self.rig_dmm.close()
            print("Digital MultiMeter Disconnected!")


# Clase que maneja la publicación de mensajes en IceStorm
class IcePublisher:
    def __init__(self, communicator, topic_name="idnTopic"):
        self.topic = None
        self.setup_topic(communicator, topic_name)

    def setup_topic(self, communicator, topic_name):
        manager = IceStorm.TopicManagerPrx.checkedCast(communicator.propertyToProxy('TopicManager.Proxy'))

        try:
            self.topic = manager.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            self.topic = manager.create(topic_name)

    def publish_idn(self, idn):
        if self.topic is not None:
            publisher = self.topic.getPublisher()
            publisher = publisher.ice_oneway()
            DMM = Demo.DMMPrx.uncheckedCast(publisher)
            DMM.printIDN(idn)


# Clase que maneja la suscripción y recepción de mensajes en IceStorm
class IceSubscriber(threading.Thread):
    def __init__(self, communicator, topic_name="idnTopic"):
        super(IceSubscriber, self).__init__()
        self.communicator = communicator
        self.topic_name = topic_name
        self.daemon = True  # Para que el hilo termine con la aplicación

    def run(self):
        topic = None
        manager = IceStorm.TopicManagerPrx.checkedCast(self.communicator.propertyToProxy('TopicManager.Proxy'))

        try:
            topic = manager.retrieve(self.topic_name)
        except IceStorm.NoSuchTopic:
            topic = manager.create(self.topic_name)

        adapter = self.communicator.createObjectAdapter("Clock.Subscriber")
        subscriber = adapter.add(DMMI(), Ice.Identity(name=Ice.generateUUID()))
        adapter.activate()

        subscriber = subscriber.ice_oneway()

        try:
            topic.subscribeAndGetPublisher({}, subscriber)
        except IceStorm.AlreadySubscribed:
            print("reactivating persistent subscriber")

        self.communicator.waitForShutdown()


# Implementación del suscriptor
class DMMI(Demo.DMM):
    def printIDN(self, body):
        print(body)


if __name__ == "__main__":
    # Inicia la comunicación con Ice
    with Ice.initialize(sys.argv, "subpub.cfg") as communicator:

        # Crea el publicador y suscriptor
        
        publisher = IcePublisher(communicator)
        subscriber = IceSubscriber(communicator)
        subscriber.start()

        # Inicia la aplicación de la interfaz gráfica
        app = QtWidgets.QApplication(sys.argv)
        window = Interfaz(publisher)
        window.show()

        sys.exit(app.exec())
