#!/usr/bin/env python

# Please note the LICENSE file accompanying this script.
# See https://github.com/reincubate/celery-worker-check for more information.

import sys

ALERT_ON_UNEXPECTED_WORKERS = True  # Whether to raise alert if unexpected workers are seen
ALERT_ON_MISSING_WORKERS    = True  # Whether to raise alert if expected workers are missing
ALERT_ON_WORKERS_NOT_OK     = True  # Whether to raise alert if worker status is not OK

ALERT_ON_UNEXPECTED_SERVERS = True  # Whether to raise alert if unexpected servers are seen
ALERT_ON_MISSING_SERVERS    = True  # Whether to raise alert if expected servers are missing


if len(sys.argv) < 1:
    raise Exception( 'You must pipe in output from `manage.py celery status` and specify at least one expected worker and count, for instance `manage.py celery status > celery-worker-check.py specialworker-4@serverA otherworker-5@serverB workername-2@serverC`' )

def parse_worker_identifier( identifier ):
    ''' Extract meaning from a string like `workername-2@server`. '''
    worker, server = identifier.split('@')
    workerchunks = worker.split('-')
    worker = '-'.join( workerchunks[:-1] )
    index = int( workerchunks[-1:][0] )
    return server, worker, index

def populate_status_dict( sdict, server, worker, index ):
    if not server in sdict.keys():
        sdict[server] = {}

    if not worker in sdict[server].keys():
        sdict[server][worker] = []

    if not index in sdict[server][worker]:
        sdict[server][worker].append( index )

expected_servers, found_servers = {}, {}

# Prepare a hash of expected servers
for l in sys.argv[1:]:
    server, worker, index = parse_worker_identifier( l )
    for i in range(index):
        populate_status_dict( expected_servers, server, worker, i )

# Prepare a hash of the servers we've found
for l in sys.stdin:
    # Skip blank and last summary line
    if l == '' or '@' not in l:
        continue

    identifier, status = l.split(': ')
    status = status.strip()
    server, worker, index = parse_worker_identifier( identifier )
    populate_status_dict( found_servers, server, worker, index )

    if ALERT_ON_WORKERS_NOT_OK and status != 'OK':
        print 'Status not OK for %s: %s' % ( identifier, status )
        continue

# Of course, you could do this in a much simpler way by serialising both
# dicts and then just diffing them. We do it the detailed way so that we
# can pick out the specifics of the problem -- and potentially later add
# in functionality to try and recover.

missing_servers = set( expected_servers.keys() ).difference( set( found_servers.keys() ) )
unexpected_servers = set( found_servers.keys() ).difference( set( expected_servers.keys() ) )
present_servers = set( found_servers.keys() ) & set( expected_servers.keys() )

if ALERT_ON_UNEXPECTED_SERVERS:
    for s in unexpected_servers:
        i = 0
        for x in found_servers[s]:
            i += len( found_servers[s][x] ) # Calculate impact of missing server
        print 'Server %s is unexpectedly present, accounts for %s workers...' % ( s, i )

if ALERT_ON_MISSING_SERVERS:
    for s in missing_servers:
        i = 0
        for x in expected_servers[s]:
            i += len( expected_servers[s][x] ) # Calculate impact of missing server
        print 'Server %s was missing, accounts for %s missing workers...' % ( s, i )
        
for s in present_servers:
    missing_workers = set( expected_servers[s].keys() ).difference( set( found_servers[s].keys() ) )
    unexpected_workers = set( found_servers[s].keys() ).difference( set( expected_servers[s].keys() ) )
    present_workers = set( expected_servers[s].keys() ) & set( found_servers[s].keys() )

    if ALERT_ON_UNEXPECTED_WORKERS:
        for w in unexpected_workers:
            i = len( found_servers[s][w] )
            print 'Worker %s@%s was unexpectedly present, accounts for %s workers...' % ( w, s, i )

    if ALERT_ON_MISSING_WORKERS:
        for w in missing_workers:
            i = len( expected_workers[w] )
            print 'Worker %s@%s was missing, accounts for %s missing workers...' % ( w, s, i )

    for w in present_workers:
        missing_worker_instances = set( sorted( expected_servers[s][w] ) ).difference( set( sorted( found_servers[s][w] ) ) )
        unexpected_worker_instances = set( sorted( found_servers[s][w] ) ).difference( set( sorted( expected_servers[s][w] ) ) )

        if ALERT_ON_UNEXPECTED_WORKERS:
            for i in unexpected_worker_instances:
                print 'Worker %s-%s@%s was unexpectedly present...' % ( w, i, s )

        if ALERT_ON_MISSING_WORKERS:
            for i in missing_worker_instances:
                print 'Worker %s-%s@%s was missing...' % ( w, i, s )