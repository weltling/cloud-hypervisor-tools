
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
                n = l.find("Number")
                if n >= 0:
                    idx.append({"pos": n, "prop": "num"})
                n = l.find("Start")
                if n >= 0:
                    idx.append({"pos": n, "prop": "start"})
                n = l.find("End")
                if n >= 0:
                    idx.append({"pos": n, "prop": "end"})
                n = l.find("Size")
                if n >= 0:
                    idx.append({"pos": n, "prop": "size"})
                n = l.find("Type")
                if n >= 0:
                    idx.append({"pos": n, "prop": "type"})
                n = l.find("File system")
                if n >= 0:
                    idx.append({"pos": n, "prop": "fs"})
                n = l.find("Name")
                if n >= 0:
                    idx.append({"pos": n, "prop": "name"})
                n = l.find("Flags")
                if n >= 0:
                    idx.append({"pos": n, "prop": "flags"})
                break

        # Continue on partition info.
        def pt(l, d):
            u = d + 1
            if len(idx) <= u:
                return l[idx[d]["pos"]:].strip()
            return l[idx[d]["pos"]:idx[u]["pos"]].strip()


        self.part = {} 
        while k < outl_len:
            l = outl[k]
            if len(l) <= 0:
                k += 1
                continue

            p = {}
            n = 0
            while n < len(idx):
                prop = idx[n]["prop"]
                val = pt(l, n)
                if "num" == prop:
                    p[prop] = int(val)
                elif "end" == prop or "start" == prop or "size" == prop:
                    p[prop] = int(val[:-1])
                elif "flags" == prop:
                    p[prop] = []
                    if val:
                        p[prop] = [f.strip() for f in val.split(",")]
                else:
                    p[prop] = val
                n += 1
            self.part[p["num"]] = Part(p)
            k += 1
