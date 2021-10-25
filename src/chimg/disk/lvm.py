
import logging
import subprocess
import tempfile
import time
from parse import *
from chimg.disk.part import Part

log = logging.getLogger(__name__)


class LvmError(Exception):
    pass


# XXX Split into VG and LV classes to handle things correctly.
#     LVM class would still stay as a management instance.

class LVM():

    def __init__(self, part_lo):
        self.part_lo = part_lo
        self.lo = None
        self.lv = None
        self.vg = None
        self.mnt_pt = None
        self.vg_active = False


    def __del__(self):
        if self.mnt_pt:
            self.umount()
        self.deactivate()


    # XXX Support multiple VG
    def scan_vg(self, tmo=1):
        k = 0
        while k < tmo:
            cmd = ["sudo", "vgscan", "--devices", self.part_lo]
            log.info(" ".join(cmd))
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            if proc.returncode:
                raise LvmError(str(err, "utf-8").rstrip())
            log.debug(str(out, "utf-8").strip())

            res = parse("Found volume group \"{}\"{:>}", str(out, "utf-8").strip())

            if res:
                self.vg = res[0]
                return self.vg

            log.debug("Couldn't read VG info, will retry in {} seconds".format(k))
            time.sleep(k)
            k += 1

        return None

    # XXX Support multiple VG
    def scan_lv(self, tmo=1):
        k = 0
        while k < tmo:
            cmd = ["sudo", "lvdisplay", "--devices", self.part_lo, "--colon"]
            log.info(" ".join(cmd))
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            if proc.returncode:
                raise LvmError(str(err, "utf-8").rstrip())
            log.debug(str(out, "utf-8").strip())


            if out:
                self.lv = []
                outl = str(out, "utf-8").split("\n")
                for l in outl:
                    res = parse("{}:{:>}", l)
                    if res:
                        lv = "{}".format(res[0].strip())
                        self.lv.append(lv)
                return self.lv

            log.debug("Couldn't read LV info, will retry {} seconds".format(k))
            time.sleep(k)
            k += 1

        return None


    def activate(self):
        if self.vg_active:
            return
        if not self.vg:
            return
        cmd = ["sudo", "vgchange", "-ay", self.vg]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise LvmError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").strip())
        self.vg_active = True

        
    def deactivate(self):
        if not self.vg_active:
            return
        cmd = ["sudo", "vgchange", "-an", self.vg]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise LvmError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").strip())
        self.vg = None
        self.vg_active = False


    def mount(self,  mnt_pt, rw=False):
        # XXX check if the mount point exists, create if it doesn't
        if not self.lo:
            self.lo = Part.make_part_dev_path(disk_dev, self.num)

        # XXX uid= won't work on FAT and alike, append automatically.
        #cmd = ["sudo", "mount", "-o", "ro,uid={}".format(os.getuid()), self.lo, mnt_pt]
        r_opt = "rw" if True == rw else "ro"
        cmd = ["sudo", "mount", "-o", r_opt, self.lo, mnt_pt]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise LvmError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").rstrip())

        self.mnt_pt = mnt_pt


    def umount(self):
        cmd = ["sudo", "umount", self.lo]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise LvmError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").rstrip())

        self.mnt_pt = None

