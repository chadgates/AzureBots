**Content of this file**

sendtobus.py has some examples of sending messages to the azure service bus to test the queues. 

the App_data_optional folder contains a version that uses the BOTS native Job-Queue. The messages from 
 Azure provide "route"-only entries, without containing files. This scenario may be useful, when 
 BOTS should pick-up messages in the traditional way but the pick-up is triggered by a message. 
 Example could be, that an FTP service is hosted in the cloud and when a file is written, a message
 is placed in the service bus to trigger bots to run a route. 
 
 azuretojobqueue