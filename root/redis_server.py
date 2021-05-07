import redis


class RedisServer:
    r = None

    def __init__(self, host, port, password):
        self.r = redis.StrictRedis(host=host, port=port, db=0, password=password, decode_responses=True)
        return

    def set(self, key, value):
        try:
            self.r.set(key, value)
            return True
        except:
            return False

    def get(self, key):
        try:
            return self.r.get(key)
        except:
            return False

    def insr(self, key):
        try:
            return self.r.incr(key)
        except:
            return False

    def insrget(self, key):
        try:
            self.r.incr(key)
            return self.r.get(key)
        except:
            return False


if __name__ == "__main__":
    r = RedisServer("pan.yixiangzhilv.com", 6379, "@Danny20070601")
    r.set(0, 1)
    r.set(0, 2)
    print(r.get(0))
