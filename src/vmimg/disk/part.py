
import logging

log = logging.getLogger(__name__)


class Part():
    def __init__(self, props):
        for p in props:
            setattr(self, p, props[p])
