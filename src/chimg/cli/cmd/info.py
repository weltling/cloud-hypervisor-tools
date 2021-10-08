
import logging
from chimg.disk import Disk
from chimg.disk.lvm import LVM
from chimg.disk.part import Part
from chimg.cli import comm, bcolors

log = logging.getLogger(__name__)

def handle(args):
    do_info(args)
    return 0

def do_info(args):
    dev = args.image
    disk = Disk(dev)
    if args.extended:
        lo = disk.attach_lo()
    
    # XXX show bootloader info
    #     show virtio driver info
    #     warn if mbr and there's no space at the end of the image
    #     gather distro info
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
    # XXX Define CH supported formats and mark fail if the original format is not supported.
    comm.msg("Image file format: {}".format(Disk.get_dev_fmt(dev)))
    comm.msg("")


    comm.head("Partition info")
    for p in disk.part:
        for k, v in disk.part[p].__dict__.items():
            if "lo" == k or "mnt_pt" == k:
                continue
            comm.msg("{}: {}".format(k, v))
            if "flags" == k and "lvm" in v and args.extended:
                lvm = LVM(Part.make_part_dev_path(lo, disk.part[p].num))
                lv = lvm.scan_lv(3)
                if not lv:
                    comm.warn("Partition contains LVM flags but no logical volumes have been found")
                    continue
                comm.msg("lv: {}".format(lv))
        comm.msg("")

    if args.extended:
        disk.detach_lo()
