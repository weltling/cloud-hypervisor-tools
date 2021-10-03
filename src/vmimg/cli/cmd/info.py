
import logging
import subprocess

log = logging.getLogger(__name__)

def handle(args):
    if args.part:
        part_table(args.image)
    return 0


def part_table(dev):
    cmd = ["sudo", "parted", "-s", dev, "unit", "B", "print"]
    log.info(" ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if proc.returncode:
        log.error(str(err, "utf-8").rstrip())
        return

    log.debug(str(out, "utf-8").rstrip())

    ret = []
    outl = str(out, "utf-8")).split("\n")
    for l in outl:
        
