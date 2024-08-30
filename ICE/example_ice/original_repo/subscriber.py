#!/usr/bin/env python
#
# Copyright (c) ZeroC, Inc. All rights reserved.
#

import signal
import sys
import Ice
import IceStorm

Ice.loadSlice('Clock.ice')
import Demo


class ClockI(Demo.Clock):
    def tick(self, date, current):
        print(date)

def run(communicator):
    topicName = "time"

    manager = IceStorm.TopicManagerPrx.checkedCast(communicator.propertyToProxy('TopicManager.Proxy'))

    try:
        topic = manager.retrieve(topicName)
    except IceStorm.NoSuchTopic:
        topic = manager.create(topicName)

    print(f"Subscribed to topic: {topicName}")

    adapter = communicator.createObjectAdapter("Clock.Subscriber")
    subscriber = adapter.add(ClockI(), Ice.Identity(name=Ice.generateUUID()))
    adapter.activate()

    print(f"Subscriber ID: {subscriber.ice_getIdentity().name}")

    subscriber = subscriber.ice_oneway()

    try:
        topic.subscribeAndGetPublisher({}, subscriber)  # No QoS settings
        print("Subscription successful.")
    except IceStorm.AlreadySubscribed:
        print("reactivating persistent subscriber")

    communicator.waitForShutdown()

    topic.unsubscribe(subscriber)


with Ice.initialize(sys.argv, "config.sub") as communicator:

    signal.signal(signal.SIGINT, lambda signum, frame: communicator.shutdown())
    if hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, lambda signum, frame: communicator.shutdown())
    status = run(communicator)
