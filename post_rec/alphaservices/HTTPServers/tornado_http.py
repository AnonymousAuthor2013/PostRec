# -*- UTF-8 -*-
import os
import tornado
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from typing import Optional, Awaitable

from post_rec import AlphaConfig, AlphaPathLookUp

#from multiprocessing import Process, Event
import json
from  post_rec.Utility import getLogger

logger = getLogger(__name__)


class AlphaHTTPProxy(object):
    def __init__(self,config_file):
        super().__init__()
        self.args = AlphaConfig.loadConfig( os.path.join( AlphaPathLookUp.ConfigPath, config_file ) )
        #self.is_ready = Event()


    def processCore(self, data):
        raise NotImplementedError

    def create_tornado_app(self):
        processCore=self.processCore
        ServiceName=self.args.ServiceName
        class ALphaHandler(RequestHandler):
            
            @tornado.web.asynchronous
            @tornado.gen.coroutine
            def post(self):
                
                query_argument = json.loads(self.request.body)
                results=processCore(query_argument)

                results = json.dumps(results)
                self.set_header('Content-type', 'application/json')
                self.write(results)


            def get(self):
                self.post()

            def on_finish(self):
                pass

        app = Application([
            (r"/methodCore", ALphaHandler)
        ])
        return app

    def start(self):
        app=self.create_tornado_app()

        http_server = HTTPServer(app)
        http_server.listen(port=self.args.port, address=self.args.listen_ip)
        logger.info("\n*************{} service is running({}:{})*************\n".format(self.args.ServiceName, self.args.listen_ip, self.args.port))
        IOLoop.current().start()


