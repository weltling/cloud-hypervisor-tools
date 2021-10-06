
import logging
from vmimg import disk as vm_disk
from vmimg.cli import comm, bcolors

log = logging.getLogger(__name__)

def handle(args):
    do_info(args.image)
    return 0

def do_info(dev):
    disk = vm_disk.Disk(dev)
    
    # XXX show bootloader info
    #     show virtio driver info
    comm.head("Disk info")
    comm.msg("Device: {}".format(disk.dev))
    comm.msg("Model: {}".format(disk.model))
    comm.msg("Sectors: {}".format(disk.sectors))
    comm.msg("Sector logical size: {}".format(disk.sector_size_logical))
    comm.msg("Sector physical size: {}".format(disk.sector_size_physical))
    if disk.table != "gpt":
        comm.fail("Partition table: {}".format(disk.table))
    else:
        comm.ok("Partition table: {}".format(disk.table))
    comm.msg("")

    comm.head("Partition info")
    for p in disk.part:
        for k, v in disk.part[p].__dict__.items():
            comm.msg("{}: {}".format(k, v))
        comm.msg("")

