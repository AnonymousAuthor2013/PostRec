# -*- UTF-8 -*-
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

#from post_rec.DocSearchEngine.service import config
from post_rec.DocSearchEngine.service.http_handler import SearchHandler, KnowAlphaHandler

def search_server(config):
    app = Application([
        (r"/search", SearchHandler)
    ])
    http_server = HTTPServer(app)
    http_server.listen(config.http_port)
    print('Development server is running at http://10.1.1.32:%s/search' % config.http_port)
    print('Notice: You can use parameters: title, body, created_date, tags, size')
    IOLoop.current().start()


def know_alpha_server(config):
    app = Application([
        (r"/know_alpha", KnowAlphaHandler)
    ])
    http_server = HTTPServer(app)
    http_server.listen(config.http_port)
    print('Development server is running at http://10.1.1.32:%s/know_alpha' % config.http_port)
    print('Notice: You can use parameters: title and size')
    IOLoop.current().start()


if __name__ == '__main__':
    import post_rec
    import os

    config = post_rec.loadConfig(os.path.join(post_rec.ConfigPath, "docSearcherService.json"))

    know_alpha_server(config)
