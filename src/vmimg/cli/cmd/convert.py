
import logging
from vmimg.disk import Disk
from vmimg.cli import comm, bcolors

log = logging.getLogger(__name__)

def handle(args):
    return do_conv(args)

def do_conv(args):
    src_path = args.source[0]
    tgt_path = args.target
    if args.in_place:

        if not args.boot_part:
            log.error("For the in-place conversion the boot partition number is required")
            return 3

        dev_fmt = Disk.get_dev_fmt(src_path)
        if "raw" == dev_fmt:
            # XXX use copy
            pass
        else:
            dev = Disk.dev_fmt_cvt(src_path, dev_fmt, tgt_path, out_fmt="raw")

        src = Disk((dev, dev_fmt))
        src.convert_efi_in_place(int(args.boot_part))
    else:
        #src = Disk(src_path)
        #tgt = vm_disk.Disk(src, args)
        raise Exception("ATM only in-place conversion is implemented, please attach -i")

    return 0
