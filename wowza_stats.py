#!/usr/bin/python

import os
import sys
import argparse
import time
import cPickle as pickle
import xmltodict
import re
import base64
import requests
from requests.auth import HTTPDigestAuth

parser = argparse.ArgumentParser(description='Zabbix TTI Wowza client')

parser.add_argument('-a', '--address', dest='server_address', help='Host or IP', required=True)
parser.add_argument('-k', '--key', dest='zkey', help='Counter to get', required=True)
parser.add_argument('-u', '--user', dest='username', help='Wowza User')
parser.add_argument('-p', '--pass', dest='password', help='Wowza Pass')
parser.add_argument('-t', '--ttl', dest='ttl', help='Local cache TTL', default=295)
parser.add_argument('-v', '--verbose', action='count', dest='verbose', help='Be verbose')

args = parser.parse_args()

keys = {
  'MessagesOutBytesRate': 0,
  'MessagesInBytesRate': 0,
  'ConnectionsCurrent': 0,
  'ConnectionsTotal': 0,
  'ConnectionsTotalRejected': 0
}

def get_data(server_address):
  pickle_filepath = "/tmp/wowza_stats.pickle"

  if args.verbose:
    print "Cache file exists: %s" % os.path.exists(pickle_filepath)
    if os.path.exists(pickle_filepath):
      print "Cache is %s seconds old" % str(time.time()-os.stat(pickle_filepath)[8])

  if not os.path.exists(pickle_filepath) or int(time.time()-os.stat(pickle_filepath)[8]) > int(args.ttl):
      # Get data from the server

      if args.verbose:
        print "Cache miss"
        print "Connecting to",server_address
                    
      response = requests.get('http://'+server_address+':8086/connectioncounts/', auth=HTTPDigestAuth(args.username, args.password))

      xmldata = xmltodict.parse(response.text)

      counters = {}

      for key in keys:
        if key in xmldata['WowzaMediaServer']:
          val = xmldata['WowzaMediaServer'][key]
          m = re.match(r"^(\d+)\s*E\s*(\d+)$",val)
          if m:
            counters[key] = float(m.group(0))*(10**float(m.group(1)))
          else:
            counters[key] = float(val)

      # Write the data to cache
      with open(pickle_filepath, 'w') as pickle_handle:
          pickle.dump(counters, pickle_handle)
  else:
      if args.verbose:
        print "Cache hit"
      with open(pickle_filepath) as pickle_handle:
          counters = pickle.load(pickle_handle)

  return counters

result = get_data(args.server_address)
if args.zkey in result:
  print str(result[args.zkey])
else:
  print "Did not find the specified key"
    