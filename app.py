#!/usr/bin/env python
from bots import webserver

class wsgi_app:
    webserver.start()

if __name__ == '__main__':
    application = wsgi_app()
