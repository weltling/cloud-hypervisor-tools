
import logging

log = logging.getLogger(__name__)

def pt(l, d):
    u = d + 1
    if len(idx) <= u:
        return l[idx[d]:].strip()
    return l[idx[d]:idx[u]].strip()


class Part():
    def __init__(self, num, start, end, size, fs, name, flags):
        self.num = num
        self.start = start
        self.end = end
        self.size = size
        self.fs = fs
        self.name = name
        self.flags = flags
