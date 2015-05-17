#!/usr/bin/env python2
#
# Copyright (C) 2009-2015:
# David GUENAULT, david.guenault@gmail.com
#
# You should have received a copy of the GNU Affero General Public License
# along with this plugin.  If not, see <http://www.gnu.org/licenses/>.
#
#check_shinken2.py:
#    This check is getting daemons state from a arbiter connection


from optparse import OptionParser
import requests
from requests import exceptions
import sys

# Exit statuses recognized by Nagios and thus by Shinken
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

daemon_types = ['arbiter', 'broker', 'scheduler', 'poller', 'reactionner', 'receiver']


def ping(host=None, port=None, protocol="http", timeout=1, ssl=False, ca=False, cert=None, key=None):

    uri = "%s://%s:%s/ping" % (protocol, host, port)

    try:
        if ssl:
            pingresult = requests.get(uri, timeout=timeout, verify=ca, cert=(cert, key))
        else:
            pingresult = requests.get(uri, timeout=timeout, verify=False)

        if pingresult.text == "\"pong\"":
            return {"message": "pong", "status": True}
        else:
            return {"message": "Invalid response to ping (%s)" % pingresult.text, "status": False}
    except requests.exceptions.ConnectionError as err:
        return {"message": "Connection error (%s)" % err, "status": False}
    except requests.exceptions.Timeout:
        return {"message": "Timeout", "status": False}
    except requests.exceptions.InvalidURL:
        return {"message": "Invalid URL", "status": False}


def get_status(host=None,
               port=None,
               protocol="http",
               target=None,
               daemon=None,
               timeout=1,
               ssl=False,
               ca=None,
               cert=None,
               key=None):
    uri = "%s://%s:%s/get-all-states" % (protocol, host, port)
    statusresult = {}
    d = {}
    try:
        if ssl:
            statusresult = requests.get(uri, timeout=timeout, verify=ca, cert=(cert, key)).json()
        else:
            statusresult = requests.get(uri, timeout=timeout, verify=False).json()
    except requests.exceptions.ConnectionError:
        return {"message": "Connection error", "status": False}
    except requests.exceptions.Timeout:
        return {"message": "Timeout", "status": False}
    finally:
        if target in statusresult.keys():
            data = statusresult[target]
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
            return {"message": "Target or Daemon not found", "status": False, "data": data}
        else:
            return {"message": "OK", "status": True, "data": data}


def get_all_status(host=None,
                   port=None,
                   protocol="http",
                   timeout=1,
                   ssl=False,
                   ca=False,
                   cert=None,
                   key=None):
    uri = "%s://%s:%s/get-all-states" % (protocol, host, port)
    result = {}
    try:
        result = requests.get(uri, timeout=timeout, verify=ca, cert=(cert, key)).json()
    except requests.exceptions.ConnectionError:
        return {"message": "Connection error", "status": False}
    except requests.exceptions.Timeout:
        return {"message": "Timeout", "status": False}
    finally:

        print "From : ", host
        print

        print "+%s+" % (106 * "-")
        print "| {:^20} | {:^20} | {:^15} | {:^19} | {:^8} | {:^7} |".format("TYPE",
                                                                             "NAME",
                                                                             "STATUS",
                                                                             "REALM",
                                                                             "ATTEMPTS",
                                                                             "SPARE")
        print "+%s+" % (106 * "-")
        for key, data in result.iteritems():
            for daemon in data:

                attempts = "%s/%s" % (daemon["attempt"], daemon["max_check_attempts"])

                if not daemon["alive"]:
                    alive = "dead"
                else:
                    if daemon["attempt"] > 0:
                        alive = "retry"
                    else:
                        alive = "alive"

                if daemon["spare"]:
                    spare = "X"
                else:
                    spare = " "

                if "realm" in daemon.keys():
                    realm = daemon["realm"]
                else:
                    realm = ""

                print "| {:20} | {:20} | {:^15} | {:19} | {:^8} | {:^7} |".format(key, daemon["%s_name" % key],
                                                                                  alive,
                                                                                  realm,
                                                                                  attempts,
                                                                                  spare)
        print "+%s+" % (106 * "-")


if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option('-a', '--hostnames', dest='hostnames', default='127.0.0.1')
    parser.add_option('-p', '--portnumber', dest='portnum', default=7770, type=int)
    parser.add_option('-t', '--target', dest='target', default=False, type=str)
    parser.add_option('-d', '--daemonname', dest='daemon', default='')
    parser.add_option('-T', '--timeout', dest='timeout', default=1, type=float)
    parser.add_option('-v', '--verbose', action="store_true", dest='verbose', default=False)
    parser.add_option('--ssl', action="store_true", dest='ssl', default=False)
    parser.add_option('--ca', dest='ca', default=None)
    parser.add_option('--cert', dest='cert', default=None)
    parser.add_option('--key', dest='key', default=None)

    # Retrieving options
    options, args = parser.parse_args()
    options.helpme = False

    if options.ssl:
        proto = "https"
    else:
        proto = "http"

    # if options.ssl:
    #    print "[UNKNOWN] SSL/TLS support is not curently implemented"
    #    sys.exit(UNKNOWN)

    # first we ping the arbiters unless we find one alive
    if "," in options.hostnames:
        hostnames = options.hostnames.split(",")
    else:
        hostnames = [options.hostnames]

    hostname = False

    for h in hostnames:
        h = h.strip()
        result = ping(host=h,
                      port=options.portnum,
                      protocol=proto,
                      timeout=options.timeout,
                      ssl=options.ssl,
                      ca=options.ca,
                      cert=options.cert,
                      key=options.key)

        if result["status"]:
            hostname = h
            break

    if not hostname:
        # no arbiter are alive !
        print "CRITICAL : No arbiter reachable !"
        sys.exit(CRITICAL)

    # detailled output and no more
    if options.verbose:
        get_all_status(host=hostname,
                       port=options.portnum,
                       protocol=proto,
                       timeout=options.timeout,
                       ssl=options.ssl,
                       ca=options.ca,
                       cert=options.cert,
                       key=options.key)
        sys.exit(OK)

    # Check for required option target
    if not getattr(options, 'target'):
        print ('CRITICAL - target is not specified; '
               'You must specify which daemon type you want to check!')
        parser.print_help()
        sys.exit(CRITICAL)
    elif options.target not in daemon_types:
        print 'CRITICAL - target', options.target, 'is not a Shinken daemon!'
        parser.print_help()
        sys.exit(CRITICAL)

    # get daemons status (target = daemon type, daemon = daemon name)
    result = get_status(host=hostname,
                        port=options.portnum,
                        protocol=proto,
                        target=options.target,
                        daemon=options.daemon,
                        timeout=options.timeout,
                        ssl=options.ssl,
                        ca=options.ca,
                        cert=options.cert,
                        key=options.key)

    if not "status" in result.keys() or not result["status"]:
        print "Error : ", result["message"]
        sys.exit(UNKNOWN)
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
                print "[CRITICAL] The following %s(s) daemon(s) are dead : %s (from %s arbiter)" % (options.target,
                                                                                                    ",".join(set(dead)),
                                                                                                    hostname)
                sys.exit(CRITICAL)
            else:
                print "[OK] all %s daemons are alive (%s) (from %s arbiter)" % (options.target,
                                                                                ",".join(set(alive)),
                                                                                hostname)
        else:
            # specific daemon name
            if result["data"]["alive"]:
                print "[OK] %s %s is alive (from %s arbiter)" % (options.target, options.daemon, hostname)
                sys.exit(OK)
            else:
                print "[CRITICAL] %s %s is dead (from %s arbiter)" % (options.target, options.daemon, hostname)
                sys.exit(CRITICAL)


