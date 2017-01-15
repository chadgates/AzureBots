import bots.communication as communication
from azure.servicebus import ServiceBusService, Queue


bus_service = ServiceBusService(
    service_namespace=os.getenv('AZURE_SERVICE_NAMESPACE'),
    shared_access_key_name=os.getenv('AZURE_SHARED_ACCESS_KEY_NAME'),
    shared_access_key_value=os.getenv('AZURE_SHARED_ACCESS_KEY_VALUE'))

class xmlrpc(communication.xmlrpc):
    def connect(self,*args,**kwargs):
        try:
            if bus_service.create_queue('botsqueue', queue_options, fail_on_exist=False):
                print('Info: Azure queue created')
            else:
                print('Info: Azure queue already exists')
        except:
            print 'Error: Azure queue does not exist, nor can it be created'
            sys.exit(1)



        busmsg = bus_service.receive_queue_message('botsqueue', peek_lock=True)

        if busmsg.body:
            print(busmsg.body)