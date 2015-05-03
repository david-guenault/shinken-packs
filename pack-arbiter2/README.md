# Arbiter2

## Purpose

shinken pack for monitoring shinken 2.x.x daemons.

## Prerequisites

You will need to install the requests module

```
pip install requests
```

## Using

You just have to tag your shinken host with arbiter2 (single arbiter) or arbiter2-multi (two arbiters with high availability). Then you must add the following host macros. 

- _shinken_daemon : a coma separated list of shinken daemons to monitor (arbiter,broker,scheduler,poller,reactionner,receiver)
- _shinken_arbiters a coma separated list of host adresses where arbiters are running. Only for multi arbiters setups (arbiter1.domain.tld, arbiter2.domain.tld)

Single arbiter exemple:

```
define host {
    host_name arbiter1
    address arbiter1.lab.lan
    use arbiter2
    contact_groups admins
    _SHINKEN_DAEMON arbiter, broker, receiver, scheduler, poller, reactionner
}

Multi arbiters exemple:

```
define host {
    host_name arbiter1
    address arbiter1.lab.lan
    use arbiter2-multi
    contact_groups admins
    _SHINKEN_DAEMON arbiter, broker, receiver, scheduler, poller, reactionner
  _shinken_arbiters arbiter1.lab.lan, arbiter2.lab.lan
}

define host {
    host_name arbiter2
    address arbiter2.lab.lan
    use arbiter2-multi
    contact_groups admins
    _SHINKEN_DAEMON arbiter, broker, receiver, scheduler, poller, reactionner
  _shinken_arbiters arbiter1.lab.lan, arbiter2.lab.lan
}
```

## Console visualisation

You can get a complete view of the shinken daemons state using the verbose mode (-v). 

```
./check_shinken2.py -a rah1.lab.lan, rah2.lab.lan -v
From : rah1.box4prod.lan

+----------------------------------------------------------------------------------------------------------+
|         TYPE         |         NAME         |     STATUS      |        REALM        | ATTEMPTS |  SPARE  |
+----------------------------------------------------------------------------------------------------------+
| reactionner          | reactionner-rah1     |      alive      | All                 |   0/3    |         |
| reactionner          | reactionner-rah2     |      alive      | All                 |   0/3    |    X    |
| broker               | broker-rah1          |      alive      | All                 |   0/3    |         |
| broker               | broker-rah2          |      alive      | All                 |   0/3    |    X    |
| arbiter              | arbiter-rah1         |      alive      |                     |   0/3    |         |
| arbiter              | arbiter-rah2         |      alive      |                     |   0/3    |    X    |
| scheduler            | scheduler-rah1       |      alive      | All                 |   0/3    |         |
| scheduler            | scheduler-rah2       |      alive      | All                 |   0/3    |         |
| scheduler            | scheduler-rah3       |      alive      | All                 |   0/3    |    X    |
| receiver             | receiver-rah1        |      alive      | All                 |   0/3    |         |
| receiver             | receiver-rah2        |      alive      | All                 |   0/3    |    X    |
| poller               | poller-rah1          |      alive      | All                 |   0/3    |         |
| poller               | poller-rah2          |      alive      | All                 |   0/3    |         |
| poller               | poller-rah3          |      alive      | All                 |   0/3    |    X    |
+----------------------------------------------------------------------------------------------------------+

```

