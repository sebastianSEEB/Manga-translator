from collections import OrderedDict
from copy import deepcopy
from time import monotonic

class SessionCache:
    def __init__(self, size=24, ttl=1800):
        self.size, self.ttl, self.items = size, ttl, OrderedDict()
    def get(self, key):
        self.prune()
        if key not in self.items: return None
        born, value = self.items[key]
        self.items.move_to_end(key)
        return deepcopy(value)
    def put(self, key, value):
        self.prune()
        if not self.size: return
        self.items[key] = (monotonic(), deepcopy(value))
        self.items.move_to_end(key)
        while len(self.items) > self.size: self.items.popitem(last=False)
    def prune(self):
        now = monotonic()
        for key in list(self.items):
            if now - self.items[key][0] >= self.ttl: del self.items[key]
    def clear(self): self.items.clear()
