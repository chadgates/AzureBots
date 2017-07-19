# -*- coding: utf-8 -*-
# This is just a file to test and send some messages to the queue

from azure.servicebus import ServiceBusService, Message
import zlib
import base64
import json

import os

bus_service = ServiceBusService(
    service_namespace=os.getenv('AZURE_SERVICE_NAMESPACE'),
    shared_access_key_name=os.getenv('AZURE_SHARED_ACCESS_KEY_NAME'),
    shared_access_key_value=os.getenv('AZURE_SHARED_ACCESS_KEY_VALUE'))


file = open("/Users/wl/bots_local/botssys/infile/INTTRA/6820162_20140611201926_1009634015.txt")
base64gz = base64.b64encode(zlib.compress(file.read()))


# A good message
envelope = {'route': 'azurequeue',
            'filename': '6820162_20140611201926_1009634015.txt',
            'content': base64gz,
            }
msg = Message(json.dumps(envelope))
bus_service.send_queue_message('botsqueue', msg)


# Not a JSON message
msg = Message('giberish')
bus_service.send_queue_message('botsqueue', msg)


# A JSON message missing elements
envelope = {'nothere': 'azurequeue',
            'filename': '6820162_20140611201926_1009634015.txt',
            'content': base64gz,
            }
msg = Message(json.dumps(envelope))
bus_service.send_queue_message('botsqueue', msg)


# A JSON message without content
envelope = {'route': 'azurequeue',
            'filename': '6820162_20140611201926_1009634015.txt',
            'content': None,
            }

msg = Message(json.dumps(envelope))
bus_service.send_queue_message('botsqueue', msg)


# A JSON message with empty content
envelope = {'route': 'azurequeue',
            'filename': '',
            'content': '',
            }
msg = Message(json.dumps(envelope))
bus_service.send_queue_message('botsqueue', msg)


# A JSON message without a file name
envelope = {'route': 'azurequeue',
            'filename': '',
            'content': base64gz,
            }
msg = Message(json.dumps(envelope))
bus_service.send_queue_message('botsqueue', msg)