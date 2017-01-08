from bots import webserver
wsgi_app = webserver.start()


if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    httpd = make_server('localhost', 8080, wsgi_app)
    httpd.serve_forever()

