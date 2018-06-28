# !/usr/bin/env python
from azure.servicebus import ServiceBusService, Queue

import sys
import os
from bots import botsinit, botsglobal, job2queue


bus_service = ServiceBusService(
    service_namespace=os.getenv('AZURE_SERVICE_NAMESPACE'),
    shared_access_key_name=os.getenv('AZURE_SHARED_ACCESS_KEY_NAME'),
    shared_access_key_value=os.getenv('AZURE_SHARED_ACCESS_KEY_VALUE'))

JOBQUEUEMESSAGE2TXT = {
    0: u'OK, job is added to queue',
    1: u'Error, job not to jobqueue. Can not contact jobqueue-server',
    4: u'Duplicate job, not added.',
}


def start():
    # NOTE: bots directory should always be on PYTHONPATH - otherwise it will not start.
    # ***command line arguments**************************
    usage = '''
    This is "%(name)s" version %(version)s, part of Bots open source edi translator (http://bots.sourceforge.net).
    A utility to generate the index file of a plugin; this can be seen as a database dump of the configuration.
    This is eg useful for version control.
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
    if not botsglobal.ini.getboolean('jobqueue', 'enabled', False):
        print 'Error: bots jobqueue cannot start; not enabled in %s/bots.ini' % configdir
        sys.exit(1)

    try:
        # Initialize a queue
        queue_options = Queue()
        queue_options.max_size_in_megabytes = '5120'
        queue_options.default_message_time_to_live = 'PT10M'
        queue_options.lock_duration = 'PT2M'
        queue_options.dead_lettering_on_message_expiration = True

        if bus_service.create_queue('botsqueue', queue_options, fail_on_exist=False):
            print('Info: Azure queue created')

    except:
        print ('Error: Azure queue does not exist, nor can it be created: ' + os.getenv('AZURE_SERVICE_NAMESPACE'))
        sys.exit(1)

    process_name = 'azurebus'
    logger = botsinit.initserverlogging(process_name)
    logger.log(25, u'Bots %(process_name)s started.', {'process_name': process_name})
    logger.log(25, u'Bots %(process_name)s configdir: "%(configdir)s".',
               {'process_name': process_name, 'configdir': botsglobal.ini.get('directories', 'config')})

    botsenginepath = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                                  'bots-engine.py')  # get path to bots-engine
    logger.info(u'Bots %(process_name)s started.', {'process_name': process_name})

    try:
        while True:
            busmsg = bus_service.receive_queue_message('botsqueue', peek_lock=True)

            if busmsg.body:

                try:
                    logger.info(u'Send to queue "%(path)s %(config)s %(task)s".',
                                {'path': botsenginepath, 'config': '-c' + configdir, 'task': busmsg.body})

                    status = job2queue.send_job_to_jobqueue([
                        sys.executable, botsenginepath, '-c' + configdir, busmsg.body
                    ])

                    if status != 1:
                        busmsg.delete()
                    logger.info(JOBQUEUEMESSAGE2TXT[status])

                except Exception as msg:
                    logger.info(u'Error in adding task to queue: "%(msg)s".', {'msg': msg})


    except KeyboardInterrupt:
        print('CTRL+C pressed, terminating')
        sys.exit(0)
    except SystemExit:
        print('Goodbye')
        sys.exit(0)


if __name__ == '__main__':
    start()
