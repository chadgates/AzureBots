import django.core.handlers.wsgi
from bots import apachewebserver

class wsgi_app():

    application = django.core.handlers.wsgi.WSGIHandler()

if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    httpd = make_server('localhost', 8080, wsgi_app)
    httpd.serve_forever()

