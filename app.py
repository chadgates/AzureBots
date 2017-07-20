import sys
import django.core.handlers.wsgi
from bots import apachewebserver
import azure_jobqueue
import threading


class AzureJobQueue(threading.Thread):
    def run(self):
        azure_jobqueue.start()

config = 'config'
apachewebserver.start(config)
wsgi_app = django.core.handlers.wsgi.WSGIHandler()


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    AzureJobQueue().start()
    httpd = make_server('localhost', 5555, wsgi_app)
    httpd.serve_forever()
