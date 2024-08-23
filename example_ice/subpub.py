#!/usr/bin/env python
#
# Copyright (c) ZeroC, Inc. All rights reserved.
#

import signal
import sys
import Ice
import IceStorm
import time
import threading

Ice.loadSlice('Clock.ice')
import Demo

# Variable para almacenar la referencia global al topic
topic = None

class ClockI(Demo.Clock):
    def tick(self, date, current):
        print(date)

def run(communicator):
    global topic
    topicName = "time"
    manager = IceStorm.TopicManagerPrx.checkedCast(communicator.propertyToProxy('TopicManager.Proxy'))

    try:
        topic = manager.retrieve(topicName)
    except IceStorm.NoSuchTopic:
        topic = manager.create(topicName)

    adapter = communicator.createObjectAdapter("Clock.Subscriber")
    subscriber = adapter.add(ClockI(), Ice.Identity(name=Ice.generateUUID()))
    adapter.activate()

    subscriber = subscriber.ice_oneway()

    try:
        topic.subscribeAndGetPublisher({}, subscriber)  # No QoS settings
    except IceStorm.AlreadySubscribed:
        print("reactivating persistent subscriber")

    communicator.waitForShutdown()

    topic.unsubscribe(subscriber)


def publish_ticks(communicator):
    global topic
    while topic is None:
        time.sleep(0.1)  # Espera hasta que topic esté inicializado

    publisher = topic.getPublisher() 
    publisher = publisher.ice_oneway()
    clock = Demo.ClockPrx.uncheckedCast(publisher)
    print("publishing tick events. Press ^C to terminate the application.")

    while not communicator.isShutdown():
        clock.tick(time.strftime("%m/%d/%Y %H:%M:%S"))
        time.sleep(1)


with Ice.initialize(sys.argv, "subpub.cfg") as communicator:

    signal.signal(signal.SIGINT, lambda signum, frame: communicator.shutdown())
    if hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, lambda signum, frame: communicator.shutdown())

    # Ejecuta el hilo para publicar los ticks
    threading.Thread(target=publish_ticks, args=(communicator,)).start()
    
    # Ejecuta la lógica del subscriber
    status = run(communicator)
