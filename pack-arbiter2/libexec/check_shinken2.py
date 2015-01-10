#!/usr/bin/env python
#
# Copyright (C) 2009-2011:
#    Denis GERMAIN, dt.germain@gmail.com
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    David GUENAULT, david.guenault@gmail.com   
#
# You should have received a copy of the GNU Affero General Public License
# along with this plugin.  If not, see <http://www.gnu.org/licenses/>.
"""
check_shinken2.py:
    This check is getting daemons state from a arbiter connection.
"""

import os
import socket
from optparse import OptionParser
import requests
from requests import exceptions
import json

# Exit statuses recognized by Nagios and thus by Shinken
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

daemon_types = ['arbiter', 'broker', 'scheduler', 'poller', 'reactionner']

def ping(host=None, port=None, proto="http"):
    uri = "%s://%s:%s/ping" % (proto, host, port)
    try:
        result = requests.get(uri)
        if result.text == "\"pong\"":
            message = { "message":"pong", "status":True }
        else:
            message = { "message":"Invalid response to ping (%s)" % result.text, "status":False }
    except requests.exceptions.ConnectionError:
        message = { "message":"Connection error", "status":False }
    except requests.exceptions.Timeout:
        message = { "message":"Timeout", "status":False }

    return message    

def get_status(host=None, port=None, proto="http", target=None, daemon=None):
    uri = "%s://%s:%s/get-all-states" % (proto, host, port)
    try:
        result = requests.get(uri).json()
    except requests.exceptions.ConnectionError:
        message = { "message":"Connection error", "status":False }
    except requests.exceptions.Timeout:
        message = { "message":"Timeout", "status":False }
    finally:
        if target in result.keys():
            data = result[target]
        else:
            data = False

        if daemon:
            found = False
            for d in data:
                if d["%s_name" % target] == daemon:
                    found = True
                    break

            if found:
                data = d
            else:
                data = False


        if not data:
            message = { "message":"Target or Daemon not found", "status":False, "data":data }
        else:
            message = { "message":"OK", "status":True, "data":data }

    return message
 

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option('-a', '--hostname', dest='hostname', default='127.0.0.1')
    parser.add_option('-p', '--portnumber', dest='portnum', default=7770, type=int)
    parser.add_option('-s', '--ssl', dest='ssl', default=False)
    parser.add_option('-t', '--target', dest='target')
    parser.add_option('-d', '--daemonname', dest='daemon', default='')
    parser.add_option('-w', '--warning', dest='warning', default=1, type=int)
    parser.add_option('-c', '--critical', dest='critical', default=0, type=int)
    parser.add_option('-T', '--timeout', dest='timeout', default=10, type=float)

    # Retrieving options
    options, args = parser.parse_args()
    # TODO: for now, helpme doesn't work as desired
    options.helpme = False

    # Check for required option target
    if not getattr(options, 'target'):
        print ('CRITICAL - target is not specified; '
               'You must specify which daemon type you want to check!')
        parser.print_help()
        raise SystemExit(CRITICAL)
    elif options.target not in daemon_types:
        print 'CRITICAL - target', options.target, 'is not a Shinken daemon!'
        parser.print_help()
        raise SystemExit(CRITICAL)

    if options.ssl:
        proto = "https"
    else:
        proto = "http"

    # first we ping the arbiter
    result = ping(host=options.hostname, port=options.portnum, proto=proto)
    if not result["status"]:
        print "CRITICAL : the Arbiter is not reachable : (%s)." % result["message"] 
        raise SystemExit(CRITICAL)

    # get daemons status (target = daemon type, daemon = daemon name)
    result = get_status(host=options.hostname, port=options.portnum, proto=proto, target=options.target, daemon = options.daemon)
    if not "status" in result.keys() or not result["status"]:
        print "Error : ", result["message"]
        SystemExit(UNKNOWN)
    else:
        if type(result["data"]) is list:
            # multiple daemons
            dead = []
            alive = []
            for d in result["data"]:
                if d["alive"]:
                    alive.append(d["%s_name" % options.target])
                else:
                    dead.append(d["%s_name" % options.target])

            if len(dead) > 0:
                print "[CRITICAL] The following %s(s) daemon(s) are dead : %s " % (options.target, ",".join(set(dead)))
                SystemExit(CRITICAL)
            else:
                print "[OK] all %s daemons are alive" % options.target
        else:
            # specific daemon name
            if result["data"]["alive"]:
                print "[OK] %s %s is alive" % (options.target, options.daemon)
                SystemExit(OK)
            else:
                print "[CRITICAL] %s %s is dead" % (options.target, options.daemon)
                SystemExit(CRITICAL)


