# gevent for async
from gevent import monkey
monkey.patch_all()

from gevent.pywsgi import WSGIServer

# gevent end
#from multiprocessing import Process, Event
from post_rec import AlphaConfig, AlphaPathLookUp
import os
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

    def create_flask_app(self):
        try:
            from flask import Flask, request
            from flask_compress import Compress
            from flask_cors import CORS
            from flask_json import FlaskJSON, as_json, JsonError
        except ImportError:
            raise ImportError('Flask or its dependencies are not fully installed, '
                              'they are required for serving HTTP requests.')

        app = Flask(__name__)
        app.config.update(DEBUG=False)
        #print("configged")

        @app.route('/methodCore', methods=['POST', 'GET'])
        @as_json
        def encode_query():
            data = request.form if request.form else request.json
            if type(data)==str:
                data=json.loads(data)
            logger.info("******in service:{}, new request from {}******\nquery data--->{}".format(
                self.args.ServiceName, request.remote_addr, json.dumps(data)[:50]+"... ...")
                )
            try:
                return self.processCore(data)
            except Exception as e:
                logger.error('error when handling HTTP request', exc_info=True)
                raise JsonError(description=str(e), type=str(type(e).__name__))

        #print("wrappering")
        CORS(app, origins=self.args.cors)
        FlaskJSON(app)
        Compress().init_app(app)
        return app

    def start(self):
        app = self.create_flask_app()
        #self.is_ready.set()
        #async
        #print("created server")
        listener=(self.args.listen_ip, self.args.port)
        http_server = WSGIServer(listener, app)
        logger.info("\n*************{} service is running({}:{})*************\n".format(self.args.ServiceName, self.args.listen_ip, self.args.port))

        http_server.serve_forever()
        #sync
        #app.run(port=self.args.port, threaded=True, host=self.args.listen_ip)

