
import os
import logging
from chimg.disk import Disk
from chimg.cli import comm, bcolors

log = logging.getLogger(__name__)

def handle(args):
    return do_conv(args)

def do_conv(args):
    src_path = args.source[0]
    if args.in_place:

        if not args.boot_part:
            log.error("For the in-place conversion the boot partition number is required")
            return 3

        dev_fmt = Disk.get_dev_fmt(src_path)
        if "raw" == dev_fmt:
            tgt_path = os.path.splitext(src_path)[0] + "_copy.raw"
            dev = Disk.dev_fmt_cvt(src_path, dev_fmt, tgt_path, out_fmt="raw")
        else:
            tgt_path = args.target
            dev = Disk.dev_fmt_cvt(src_path, dev_fmt, tgt_path, out_fmt="raw")

        src = Disk((dev, dev_fmt))

        # XXX For the time being it is still easier to resize image
        #     rather than going into business of resising partitions.
        #     Still, some scenariom might need an aligned image size.
        if "gpt" != src.table:
            # Assume sector size at least 512B.
            sz = (src.sectors + 2048) * src.sector_size_logical
            del src
            Disk.dev_resize(dev, sz)
            src = Disk((dev, dev_fmt))

        src.convert_efi_in_place(int(args.boot_part))

    else:
        #src = Disk(src_path)
        #tgt = vm_disk.Disk(src, args)
        raise Exception("ATM only in-place conversion is implemented, please attach -i")

    return 0
