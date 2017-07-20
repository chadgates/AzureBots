#!/usr/bin/env python
import sys
import os
from bots import botsinit
from bots import botsglobal
import json
from SimpleXMLRPCServer import SimpleXMLRPCServer
from azure.servicebus import ServiceBusService, Message, Queue


bus_service = ServiceBusService(
    service_namespace=os.getenv('AZURE_SERVICE_NAMESPACE'),
    shared_access_key_name=os.getenv('AZURE_SHARED_ACCESS_KEY_NAME'),
    shared_access_key_value=os.getenv('AZURE_SHARED_ACCESS_KEY_VALUE'))

# -------------------------------------------------------------------------------


class Jobqueue(object):
    """
    Provides the addjob function required by the bots web gui
    """

    def __init__(self, logger):
        self.logger = logger

    def addjob(self, task, priority):
        envelope = {u'route': task[3]}
        msg = Message(json.dumps(envelope))
        bus_service.send_queue_message('botsqueue', msg)
        self.logger.info(u'Added job: %(task)s',
                         {'task': task[3]})
        return 0


def start():
    """
    this is a drop-in replacement in case the user want to use the standard (as per bots default install) jobqueue,
    and put the jobs into the Azure Service Bus.
    ATTENTION: THIS WILL NOT WORK ON AZURE APP SERVICE, and can only be used in an environment that enables access
    to the localhost:xmlrpc server port (like on a Azure Virtual Machine, or your local installation or ...).
    """
    # NOTE: bots directory should always be on PYTHONPATH - otherwise it will not start.
    # ***command line arguments**************************
    usage = '''
    This is "%(name)s" version %(version)s, part of Bots open source edi translator (http://bots.sourceforge.net).
    Server program that ensures only a single bots-engine runs at any time, and no engine run requests are 
    lost/discarded. Each request goes to a queue and is run in sequence when the previous run completes. 
    Use of the job queue is optional and must be configured in bots.ini (jobqueue section, enabled = True).
    Usage:
        %(name)s  -c<directory>
    Options:
        -c<directory>   directory for configuration files (default: config).

    ''' % {'name': os.path.basename(sys.argv[0]), 'version': botsglobal.version}
    configdir = 'config'
    for arg in sys.argv[1:]:
        if arg.startswith('-c'):
            configdir = arg[2:]
            if not configdir:
                print 'Error: configuration directory indicated, but no directory name.'
                sys.exit(1)
        else:
            print usage
            sys.exit(0)
    # ***end handling command line arguments**************************

    botsinit.generalinit(configdir)  # find locating of bots, configfiles, init paths etc.
    if not botsglobal.ini.getboolean('jobqueue','enabled',False):
        print 'Error: bots jobqueue cannot start; not enabled in %s/bots.ini' % configdir
        sys.exit(1)

    process_name = 'azure_jobqueue'
    logger = botsinit.initserverlogging(process_name)
    logger.log(25, u'Bots %(process_name)s started.', {'process_name': process_name})
    logger.log(25, u'Bots %(process_name)s configdir: "%(configdir)s".',
               {'process_name': process_name, 'configdir': botsglobal.ini.get('directories', 'config')})

    # Initialize the Azure Queue in case not existing:
    queue_options = Queue()
    queue_options.max_size_in_megabytes = '5120'
    queue_options.default_message_time_to_live = 'PT10M'
    queue_options.lock_duration = 'PT2M'
    queue_options.dead_lettering_on_message_expiration = True

    if bus_service.create_queue('botsqueue', queue_options, fail_on_exist=False):
        logger.log(25, u'Bots %(process_name)s azurequeue created: "%(azurequeue)s"', {'process_name': process_name,
                                                                                      'azurequeue': 'botsqueue'})
    else:
        logger.log(25, u'Bots %(process_name)s azurequeue connected: "%(azurequeue)s"', {'process_name': process_name,
                                                                                        'azurequeue': 'botsqueue'})


    port = botsglobal.ini.getint('jobqueue','port',28082)
    server = SimpleXMLRPCServer(('localhost', port), logRequests=False)
    server.register_introspection_functions()
    server.register_instance(Jobqueue(logger))

    # Start the server and serve forever....
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        server.server_close()

    sys.exit(0)


if __name__ == '__main__':
    start()
