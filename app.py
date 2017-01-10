import django.core.handlers.wsgi
from bots import apachewebserver

class wsgi_app():
    apachewebserver.start('config')
    application = django.core.handlers.wsgi.WSGIHandler()