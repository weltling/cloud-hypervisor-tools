
import logging

log = logging.getLogger(__name__)

def pt(l, d):
    u = d + 1
    if len(idx) <= u:
        return l[idx[d]:].strip()
    return l[idx[d]:idx[u]].strip()


class Part():
    def __init__(self, props):
        for p in props:
            setattr(self, p, props[p])
