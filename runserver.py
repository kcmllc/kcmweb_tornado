import json
import threading
import sys
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
from sockjs.tornado import SockJSRouter, SockJSConnection
from evernote.api.client import EvernoteClient
import redis
import logging
import tornadoredis
import thread
from utils.utils import OpenChannel
from functools import partial
import toredis


class NewMsgHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.render('index.html')

    def post(self, *args, **kwargs):
        data = self.get_argument('data')
        r = redis.Redis()
        r.publish('realtime', data)


class RealtimeHandler(SockJSConnection):
    clients = set()

    def on_open(self, info):
        # logging.info('Incoming client from %s' % info.ip)
        self.broadcast(self.clients, "Someone joined.")

        self.clients.add(self)

    def on_message(self, message):
        logging.debug('Received something from client: %s', message)

    def on_close(self):
        self.clients.remove(self)

    @classmethod
    def pubsub(cls, msg):
        if msg.kind in ['message', 'pmessage']:
            logging.debug('Pushing: %s' % msg.body)
            for c in cls.clients:
                c.send(msg.body)


class EvernoteHandler(tornado.web.RequestHandler):
    # def prepare(self):

    # print self.application.settings
    # self.devtoken = self.application.settings['EVERNOTE_TOKEN']
    # self.client = EvernoteClient(token=self.devtoken)
    # self.user_store = self.client.get_user_store()
    # self.user = self.user_store.getUser()
    #
    def get(self, *args, **kwargs):
        print self.application.settings
        self.render('evernote.html')

    def post(self, *args, **kwargs):
        title = self.get_argument('title')
        text = self.get_argument('text')
        r = redis.Redis()
        r.publish('realtime', 'New Evernote message saved')


class TornadoApplication(tornado.web.Application):
    def __init__(self, handlers):
        self.handlers = [
            (r'/', NewMsgHandler),
            (r'/evernote', EvernoteHandler)
        ]
        self.handlers += handlers
        self.settings = {
            'EVERNOTE_TOKEN': 'S=s1:U=8ec46:E=150eea5c34e:C=14996f49620:P=1cd:A=en-devtoken:V=2:H=4e69f82d21ec4b94c2971c9a5893ad2b'
        }

        self.data = set()
        self.sockets = []
        # self.redis = redis.Redis().pubsub().subscribe('realtime')
        self.redis_channels = {}
        super(TornadoApplication, self).__init__(self.handlers, **self.settings)


if __name__ == '__main__':
    port = 5000
    key = 'realtime'
    import logging

    logging.getLogger().setLevel(logging.DEBUG)
    rclient = tornadoredis.Client(host='localhost', port=6379)
    rclient.connect()
    Router = SockJSRouter(RealtimeHandler, '/realtime')
    redis_thread = threading.Thread(rclient.psubscribe('realtime', lambda s: rclient.listen(RealtimeHandler.pubsub)))
    try:
        # redis_thread.setDaemon(True)
        redis_thread.start()
    except(KeyboardInterrupt, SystemExit):
        redis_thread.__Thread__exit()
        sys.exit()
    app = TornadoApplication(Router.urls)
    app.listen(5000)
    # http_server = tornado.httpserver.HTTPServer(Application())
    # http_server.bind(5000)
    # http_server.start(0)
    logging.info('Listening on port %d for redis pubsub channel %s', port, key)
    tornado.ioloop.IOLoop.instance().start()

__author__ = 'kyle'
