from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import configparser
import argparse
import json 
import time 

from actions import tradfriActions

def parse_conf():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    conf = configparser.ConfigParser()
    conf.read(script_dir + '/tradfri.cfg')
    
    hubip = conf.get('tradfri', 'hubip')
    apiuser = conf.get('tradfri', 'apiuser')
    apikey = conf.get('tradfri', 'apikey')
    group_ids = json.loads(conf.get('group', 'ids'))
    
    return hubip, apiuser, apikey, group_ids

def power_on():
    hubip, apiuser, apikey, group_ids = parse_conf()
    for groupid in group_ids:
        print(groupid)
        tradfriActions.power_group(hubip, apiuser, apikey, groupid, 'on')

def power_off():
    hubip, apiuser, apikey, group_ids = parse_conf()
    for groupid in group_ids: 
        tradfriActions.power_group(hubip, apiuser, apikey, groupid, 'off')

if __name__ == "__main__":
    power_on()
    time.sleep(5)
    power_off()
    sys.exit(0)
