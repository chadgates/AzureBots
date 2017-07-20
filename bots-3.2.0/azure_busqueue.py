#!/usr/bin/env python
import sys
import os
import time
import datetime
import subprocess
import threading
from bots import botsinit
from bots import botslib
from bots import botsglobal
import json
import zlib
import base64
# from SimpleXMLRPCServer import SimpleXMLRPCServer

from azure.servicebus import ServiceBusService, Queue, Message


# Takes these from ENVIRONMENT !!!!
bus_service = ServiceBusService(
    service_namespace=os.getenv('AZURE_SERVICE_NAMESPACE'),
    shared_access_key_name=os.getenv('AZURE_SHARED_ACCESS_KEY_NAME'),
    shared_access_key_value=os.getenv('AZURE_SHARED_ACCESS_KEY_VALUE'))

# -------------------------------------------------------------------------------


# class JobqueueServer(threading.Thread):
#     """
#     An RPC server for backward compatibility. This is required by the bots web gui to enable to start jobs via
#     front end.
#
#     The jobs are passed into the Azure Job-Queue.
#     This is a drop-in replacement for the bots-jobqueuserver, therefore the bots-jobqueueserver should not be
#     running at the same time.
#     """
#     class Jobqueue(object):
#         """
#         Provides the addjob function required by the bots web gui
#         """
#         def __init__(self, logger):
#             self.logger = logger
#
#         def addjob(self, task, priority):
#             envelope = {u'route': task[3]}
#             msg = Message(json.dumps(envelope))
#             bus_service.send_queue_message('botsqueue', msg)
#             self.logger.info(u'Added job: %(task)s',
#                              {'task': task[3]})
#             return 0
#
#     def __init__(self, ip, port, logger):
#         super(JobqueueServer, self).__init__()
#         self.running = True
#         self.logger = logger
#         self.server = SimpleXMLRPCServer((ip, port), logRequests=False)
#         self.server.register_introspection_functions()
#         self.server.register_instance(self.Jobqueue(self.logger))
#
#     def run(self):
#         self.server.serve_forever()
#
#     def stop_server(self):
#         self.server.shutdown()
#         self.server.server_close()


# -------------------------------------------------------------------------------
def maxruntimeerror(logger, maxruntime, jobnumber, task_to_run):
    logger.error(u'Job %(job)s exceeded maxruntime of %(maxruntime)s minutes',
                 {'job': jobnumber, 'maxruntime': maxruntime})
    botslib.sendbotserrorreport(u'[Bots Azure Bus Queue] - Job exceeded maximum runtime',
                                u'Job %(job)s exceeded maxruntime of %(maxruntime)s minutes:\n %(task)s' % {
                                    'job': jobnumber, 'maxruntime': maxruntime, 'task': task_to_run})


def start():
    """
    The main thread is listening to the Azure Message Bus Queue.
    The messages are expected in following format:

    JSON Format:
    {'route': 'azurequeue',
    'filename': '6820162_20140611201926_1009634015.txt',
    'content': base64gz
    }

    The content must be base64 encoded and gzipped.
    example:
    file = open("some_edi_file.txt")
    base64gz = base64.b64encode(zlib.compress(file.read()))

    The files are written into the directory BOTSSYS/botsqueue.
    The routes should have this directory as income channel only.
    The route MUST delete the file.
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

    process_name = 'azure_busqueue'
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
        logger.log(25, u'Bots %(process_name)s azurequeue created: "%(azurequeue)s', {'process_name': process_name,
                                                                                      'azurequeue': 'botsqueue'})
    else:
        logger.log(25, u'Bots %(process_name)s azurequeue connected: "%(azurequeue)s', {'process_name': process_name,
                                                                                        'azurequeue': 'botsqueue'})

    # Initialized XML RPC Server for backward compatibility
    # port = botsglobal.ini.getint('jobqueue','port',28082)
    # xmlrpcserver = JobqueueServer('localhost', port, logger)
    # xmlrpcserver.start()

    # Get path to bots-engine
    botsenginepath = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                                  'bots-engine.py')

    maxruntime = botsglobal.ini.getint('settings', 'maxruntime', 60)
    maxseconds = maxruntime * 60
    time.sleep(3)  # to allow jobqserver to start
    jobnumber = 0

    try:
        while True:

            # Retrieve the message from the Azure queue
            busmsg = bus_service.receive_queue_message('botsqueue', peek_lock=True)

            # Check that there is actually a body
            if busmsg.body:
                jobnumber += 1

                # Make sure the body has a JSON formatted element in it
                try:
                    message = json.loads(busmsg.body)
                except Exception as msg:

                    logger.error(u'Error reading job %(job)s: %(msg)s', {'job': jobnumber, 'msg': msg})
                    botslib.sendbotserrorreport(u'[Bots Azure Bus Queue] - Error reading job',
                                                u'Error reading job %(job)s:\n '
                                                u'%(rec_msg)s\n\n'
                                                u' %(msg)s' % {
                                                    'job': jobnumber,
                                                    'rec_msg': busmsg.body,
                                                    'msg': msg})
                    busmsg.delete()
                    continue

                # Check that there is a valid route element in the JSON
                if 'route' in message:
                    task_to_run = [sys.executable, botsenginepath, '-c' + configdir, message['route']]
                else:
                    msg = 'File does not contain the route element.'
                    logger.error(u'Error starting job %(job)s: %(msg)s', {'job': jobnumber, 'msg': msg})
                    botslib.sendbotserrorreport(u'[Bots Azure Bus Queue] - Error starting job',
                                                u'Error starting job %(job)s:\n '
                                                u'%(rec_msg)s\n\n'
                                                u' %(msg)s' % {
                                                    'job': jobnumber,
                                                    'rec_msg': busmsg.body,
                                                    'msg': msg})
                    busmsg.delete()
                    continue

                # Check if a file is part of the message, and a filename is passed as well
                # if no file is in the message, then route will be called but no file is written
                # TODO: this will need to be reviewed. Right now, if content was there but no filename, it would proceed
                #       without being the files, thus just calling the route !
                #       most probably this should cause an exit - or if no filename, then add a random name
                if 'filename' in message and 'content' in message and (
                    bool(message['content'] and message['content'].strip()) and
                    bool(message['filename'] and message['filename'].strip())):

                    # uncode and unzip the file. on failure, exit without processing the file
                    try:
                        edifile = zlib.decompress(base64.b64decode(message['content']))
                        filepath = botsglobal.ini.get('directories', 'botssys') + "/" + 'botsqueue/' + message[
                            'filename']
                        f = botslib.opendata(filename=filepath, mode='w')
                        f.write(edifile)
                        f.close()
                    except Exception as msg:
                        logger.error(u'Error starting job %(job)s: %(msg)s', {'job': jobnumber, 'msg': msg})
                        botslib.sendbotserrorreport(u'[Bots Azure Bus Queue] - Error writing file',
                                                    u'Error writing file %(job)s:\n '
                                                    u'%(task)s\n\n'
                                                    u'%(filename)s\n\n'
                                                    u' %(msg)s' % {
                                                        'job': jobnumber,
                                                        'task': task_to_run,
                                                        'filename': message['filename'],
                                                        'msg': msg})
                        busmsg.delete()
                        continue

            # Starting the timer thread and engage the bots engine
                timer_thread = threading.Timer(maxseconds, maxruntimeerror,
                                               args=(logger, maxruntime, jobnumber, task_to_run))
                timer_thread.start()
                try:
                    starttime = datetime.datetime.now()
                    logger.info(u'Starting job %(job)s: %(task)s', {'job': jobnumber, 'task' : task_to_run })
                    result = subprocess.call(task_to_run, stdin=open(os.devnull, 'r'), stdout=open(os.devnull, 'w'),
                                             stderr=open(os.devnull, 'w'))
                    time_taken = datetime.timedelta(seconds=(datetime.datetime.now() - starttime).seconds)
                    logger.info(u'Finished job %(job)s, elapsed time %(time_taken)s, result %(result)s',
                                {'job': jobnumber, 'time_taken': time_taken, 'result': result})


                except Exception as msg:
                    logger.error(u'Error starting job %(job)s: %(msg)s', {'job': jobnumber, 'msg': msg})
                    botslib.sendbotserrorreport(u'[Bots Azure Bus Queue] - Error starting job',
                                                u'Error starting job %(job)s:\n %(task)s\n\n %(msg)s' % {
                                                    'job': jobnumber,
                                                    'task': task_to_run,
                                                    'msg': msg})
                    timer_thread.cancel()
                    busmsg.delete()
                    continue

                # Success !!! Message was received and processed.
                # It is time to cancel the timer and remove the message from the queue.
                # TODO: probably need to clean up the directory where the file was written after processing, if
                #       the file was not deleted by the route! Better save than sorry!

                timer_thread.cancel()
                busmsg.delete()


    except KeyboardInterrupt:
        pass

    # stopping the XMLRPC Server
    # xmlrpcserver.stop_server()
    sys.exit(0)

if __name__ == '__main__':
    start()
