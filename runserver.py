import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
import redis
import threading
from functools import partial
LISTENERS = []

def redis_listener():
    r = redis.Redis()
    ps = r.pubsub()
    ps.subscribe('realtime')
    io_loop = tornado.ioloop.IOLoop.instance()
    for message in ps.listen():
        for client in LISTENERS:
            io_loop.add_callback(partial(client.on_message, message))

class NewMsgHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.render('index.html')

    def post(self, *args, **kwargs):
        data = self.get_argument('data')
        r = redis.Redis()
        r.publish('realtime', data)

class RealtimeHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        LISTENERS.append(self)

    def on_message(self, message):
        self.write_message(message['data'])
    def on_close(self):
        LISTENERS.remove(self)

class EvernoteHandler(tornado.websocket.WebSocketHandler):

settings = {}

application = tornado.web.Application([
    (r'/', NewMsgHandler),
    (r'/realtime', RealtimeHandler),
    (r'/evernote', EvernoteHandler)
], **settings)

if __name__ == '__main__':
    threading.Thread(target=redis_listener).start()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.bind(5000)
    http_server.start(0)
    tornado.ioloop.IOLoop.instance().start()

__author__ = 'kyle'
