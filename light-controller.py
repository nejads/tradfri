from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from actions import tradfriActions
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
from datetime import datetime

import configparser
import json
import os
import sys
import sys
import threading
import time

received_all_event = threading.Event()
received_count = 0 #Cause infinite loop on listining to the topic

def get_conf():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    conf = configparser.ConfigParser()
    conf.read(script_dir + '/tradfri.cfg')
    return conf

conf = get_conf()

def power(command):
    hubip = conf.get('tradfri', 'hubip')
    apiuser = conf.get('tradfri', 'apiuser')
    apikey = conf.get('tradfri', 'apikey')
    group_ids = json.loads(conf.get('group', 'ids'))
    for groupid in group_ids:
        print(groupid)
        tradfriActions.power_group(hubip, apiuser, apikey, groupid, command)

# MQTT Callbacks
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))

def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))
    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()
        resubscribe_future.add_done_callback(on_resubscribe_complete)

def on_resubscribe_complete(resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        print("Resubscribe results: {}".format(resubscribe_results))

        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))

def on_message_received(topic, payload, **kwargs):
    print("{} - Received message from topic '{}': {}".format(str(datetime.now()), topic, payload))
    command = json.loads(payload)["power"]
    if command == "on"  or command == "off":
        power(command)
    else:
        print("ERROR: Insufficient command")

if __name__ == "__main__":
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=conf.get('mqtt', 'endpoint'),
        cert_filepath=conf.get('mqtt', 'cert'),
        pri_key_filepath=conf.get('mqtt', 'key'),
        client_bootstrap=client_bootstrap,
        ca_filepath=conf.get('mqtt', 'root-ca'),
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=conf.get('mqtt', 'client-id'),
        clean_session=False,
        keep_alive_secs=6)

    print("Connecting to {} with client ID '{}'...".format(
        conf.get('mqtt', 'endpoint'), conf.get('mqtt', 'client-id')))

    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    # Subscribe
    print("Subscribing to topic '{}'...".format(conf.get('mqtt', 'topic')))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=conf.get('mqtt', 'topic'),
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))

    if  not received_all_event.is_set():
        print("Waiting for all messages to be received...")

    received_all_event.wait()
    print("{} message(s) received.".format(received_count))

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")
