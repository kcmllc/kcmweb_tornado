import threading
import redis

class OpenChannel(threading.Thread):
    def __init__(self, channel, host = None, port = None):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.redis = redis.StrictRedis(host = host or 'localhost', port = port or 6379)
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channel)

        self.output = []

    # lets implement basic getter methods on self.output, so you can access it like a regular list
    def __getitem__(self, item):
        with self.lock:
            return self.output[item]

    def __getslice__(self, start, stop = None, step = None):
        with self.lock:
            return self.output[start:stop:step]

    def __str__(self):
        with self.lock:
            return self.output.__str__()

    # thread loop
    def run(self):
        for message in self.pubsub.listen():
            with self.lock:
                self.output.append(message['data'])

    def stop(self):
        self._Thread__stop()

__author__ = 'kyle'
