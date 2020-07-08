import os
import shlex
import subprocess
import sys

global coap 
coap = '/usr/local/bin/coap-client'

def get_payload(value): 
    if value == 'on':
        return '{ "5850" : 1 }'
    else:
        return '{ "5850" : 0 }'

def power_group(hubip, apiuser, apikey, groupid, value):
    """ function for power on/off tradfri lightbulb group """
    tradfriHub = 'coaps://{}:5684/15004/{}' .format(hubip, groupid)
    payload = get_payload(value)
    
    api = '{} -m put -u "{}" -k "{}" -e \'{}\' "{}"'.format(
            coap, apiuser, apikey, payload, tradfriHub)
    args = shlex.split(api)
    
    if os.path.exists(coap):
        subprocess.run(args)
    else:
        sys.stderr.write('[-] libcoap: could not find libcoap\n')
        sys.exit(1)
