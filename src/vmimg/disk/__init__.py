
import logging
import subprocess
from parse import *

log = logging.getLogger(__name__)

class Disk():
    
    def __init__(self, dev):
        cmd = ["sudo", "parted", "-s", dev, "unit", "s", "print"]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            log.error(str(err, "utf-8").rstrip())
            return

        log.debug(str(out, "utf-8").rstrip())

        # Attributes will be assigned in the same order as matched placeholders.
        pats = [
                {"pat": "Model: {:>}", "done": False, "attr": ["model"]},
                {"pat": "Disk {}: {:d}s", "done": False, "attr": ["dev", "sectors"]},
                {"pat": "Partition Table: {:>}", "done": False, "attr": ["table"]},
                {"pat": "Sector size (logical/physical): {:d}B/{:d}B", "done": False, "attr": ["sector_size_local", "sector_size_physical"]},
                {"pat": "Disk Flags:", done: False, "attr": []},
        ]
        ret = []
        outl = str(out, "utf-8").split("\n")
        k = 0
        p = 0
        outl_len = len(outl)
        while k < outl_len:
            l = outl[k]
            for i, reg in enumerate(pats):
                if reg["done"]:
                    i += 1
                    continue
                res = parse(reg["pat"], l)
                if res:
                    pats[i]["done"] = True
                    for n, attr in enumerate(reg["attr"]):
                        setattr(self, attr, res[n])
                    continue
                i += 1
            k += 1

        import dumper
        dumper.dump(k)
        # Continue on partition info.
        pat = "{:d>} {:d>}"
        self.part = {} 
        while k < outl_len:
            l = outl[k]
            res = parse(pat, l)
            if res:
                self.part[res[0]] = {"start_sector": res[1]}
            k += 1

        import dumper
        dumper.dump(self)
            
