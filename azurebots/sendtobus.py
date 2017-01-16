# -*- coding: utf-8 -*-
# This is just a file to test and send some messages to the queue

from azure.servicebus import ServiceBusService, Message


import os

bus_service = ServiceBusService(
    service_namespace=os.getenv('AZURE_SERVICE_NAMESPACE'),
    shared_access_key_name=os.getenv('AZURE_SHARED_ACCESS_KEY_NAME'),
    shared_access_key_value=os.getenv('AZURE_SHARED_ACCESS_KEY_VALUE'))

msg = Message(b'azurequeue')
bus_service.send_queue_message('botsqueue', msg)
