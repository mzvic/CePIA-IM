#!/usr/bin/env python
#
# Copyright (c) ZeroC, Inc. All rights reserved.
#

import signal
import sys
import time
import Ice
import IceStorm

Ice.loadSlice('Clock.ice')
import Demo

def run(communicator):

    topicName = "time"

    manager = IceStorm.TopicManagerPrx.checkedCast(communicator.propertyToProxy('TopicManager.Proxy'))

    try:
        topic = manager.retrieve(topicName)
    except IceStorm.NoSuchTopic:
        topic = manager.create(topicName)

    publisher = topic.getPublisher() 
    publisher = publisher.ice_oneway()
    clock = Demo.ClockPrx.uncheckedCast(publisher)

    print("publishing tick events. Press ^C to terminate the application.")

    while 1:
        clock.tick(time.strftime("%m/%d/%Y %H:%M:%S"))
        clock.tick("AAAAAAAAAAAAAAAAAAAAAAAAA")
        time.sleep(1)

#
# Ice.initialize returns an initialized Ice communicator,
# the communicator is destroyed once it goes out of scope.
#
with Ice.initialize(sys.argv, "config.pub") as communicator:
    signal.signal(signal.SIGINT, lambda signum, frame: communicator.destroy())
    if hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, lambda signum, frame: communicator.destroy())
    status = run(communicator)
