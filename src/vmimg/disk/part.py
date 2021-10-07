
import os
import logging
import subprocess
import shutil
import tempfile

log = logging.getLogger(__name__)


class PartError(Exception):
    pass


class Part():

    # XXX Currently only instantiated in Disk ctr only, make possible to instantiate standalone.
    def __init__(self, props):
        for p in props:
            setattr(self, p, props[p])

    @staticmethod
    def make_dev_path(loop, num):
        # XXX check if the path is already a part dev path
        return "{}p{}".format(loop, num)

    def mount(self, loop, mnt_pt):
        # XXX check if the mount point exists, create if it doesn't
        self.lp = Part.make_dev_path(loop, self.num)

        # XXX uid= won't work on FAT and alike, append automatically.
        # XXX Introduce arguments to mount RW and more for various situations.
        #cmd = ["sudo", "mount", "-o", "ro,uid={}".format(os.getuid()), self.lp, mnt_pt]
        # Mount RO for the time being!
        cmd = ["sudo", "mount", "-o", "ro", self.lp, mnt_pt]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise PartError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").rstrip())

        self.mnt_pt = mnt_pt


    def umount(self):
        cmd = ["sudo", "umount", self.lp]
        log.info(" ".join(cmd))

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise PartError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").rstrip())

        self.lp = None
        self.mnt_pt = None


    def backup(self):
        td = tempfile.TemporaryDirectory()

        bak_dir = td.name
        td.cleanup()
            
        cmd = ["sudo", "cp", "-a", self.mnt_pt, bak_dir]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise PartError(str(err, "utf-8").rstrip())

        return bak_dir
