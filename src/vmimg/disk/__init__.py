
import logging
import subprocess
from parse import *
from vmimg.disk.part import Part

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
        ]
        ret = []
        outl = str(out, "utf-8").split("\n")
        k = 0
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

        # Scroll to the part data table start.
        k = 0
        idx = []
        while k < outl_len:
            l = outl[k]
            k += 1
            if l.startswith("Number"):
                idx.append(l.find("Number"))
                idx.append(l.find("Start"))
                idx.append(l.find("End"))
                idx.append(l.find("Size"))
                idx.append(l.find("File system"))
                idx.append(l.find("Name"))
                idx.append(l.find("Flags"))
                break
        # Continue on partition info.
        def pt(l, d):
            u = d + 1
            if len(idx) <= u:
                return l[idx[d]:].strip()
            return l[idx[d]:idx[u]].strip()


        self.part = {} 
        while k < outl_len:
            l = outl[k]
            if len(l) <= 0:
                k += 1
                continue

            p = {"start": int(pt(l, 1)[:-1]), "end": int(pt(l, 2)[:-1]), "size": int(pt(l, 3)[:-1]), "fs": pt(l, 4), "name": pt(l, 5)}
            s = pt(l, 6)
            p["flags"] = []
            if s:
                p["flags"] = [f.strip() for f in s.split(",")]
            self.part[int(pt(l, 0))] = Part(int(pt(l, 0)), int(pt(l, 1)[:-1]), int(pt(l, 2)[:-1]), int(pt(l, 3)[:-1]), pt(l, 4), pt(l, 5), [f.strip() for f in pt(l, 6).split(",")])
            k += 1

        import dumper
        dumper.dump(self)
            
