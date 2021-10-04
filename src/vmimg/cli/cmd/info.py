
import logging
from vmimg import disk as vm_disk

log = logging.getLogger(__name__)

def handle(args):
    if args.part:
        part_table(args.image)
    return 0

def part_table(dev):
    disk = vm_disk.Disk(dev)
