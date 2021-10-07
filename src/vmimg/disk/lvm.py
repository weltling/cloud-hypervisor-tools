
import logging
import subprocess
import tempfile
import time
from parse import *
from vmimg.disk.part import Part

log = logging.getLogger(__name__)


class LvmError(Exception):
    pass

class LVM():

    def __init__(self, lo):
        self.lo = lo

    def scan_vg(self, tmo=1):
        k = 0
        while k < tmo:
            cmd = ["sudo", "vgscan", "--devices", self.lo]
            log.info(" ".join(cmd))
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            if proc.returncode:
                raise PartError(str(err, "utf-8").rstrip())
            log.debug(str(out, "utf-8").strip())

            res = parse("Found volume group \"{}\"{:>}", str(out, "utf-8").strip())

            if res:
                self.vg = res[0]
                return self.vg

            time.sleep(k)
            k += 1

        return None

    def scan_lv(self, tmo=1):
        k = 0
        while k < tmo:
            cmd = ["sudo", "lvs", "--devices", self.lo, "--separator", ":", "--noheadings"]
            log.info(" ".join(cmd))
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            if proc.returncode:
                raise PartError(str(err, "utf-8").rstrip())
            log.debug(str(out, "utf-8").strip())


            if out:
                self.lv = []
                outl = str(out, "utf-8").split("\n")
                for l in outl:
                    res = parse("{}:{}:{:>}", l)
                    if res:
                        lv = "{}-{}".format(res[1].strip(), res[0].strip())
                        self.lv.append(lv)
                return self.lv

            time.sleep(k)
            k += 1

        return None


    def activate(self):
        #td = tempfile.TemporaryDirectory()
        pass

        
