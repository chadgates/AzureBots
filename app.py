import sys
import django.core.handlers.wsgi
from bots import apachewebserver

config = 'config'
apachewebserver.start(config)
wsgi_app = django.core.handlers.wsgi.WSGIHandler()

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 5555, wsgi_app)
    httpd.serve_forever()
