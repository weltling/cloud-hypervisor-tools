
import os
import logging
import subprocess
import shutil
import tempfile
from parse import *

log = logging.getLogger(__name__)


class PartError(Exception):
    pass


class Part():

    # XXX Currently only instantiated in Disk ctr only, make possible to instantiate standalone.
    def __init__(self, props):
        for p in props:
            setattr(self, p, props[p])

        self.lp = None
        self.mnt_pt = None


    @staticmethod
    def make_part_dev_path(disk_dev, num):
        # XXX check if the path is already a part dev path
        return "{}p{}".format(disk_dev, num)

    def mount(self, disk_dev, mnt_pt, rw=False):
        # XXX check if the mount point exists, create if it doesn't
        self.lp = Part.make_part_dev_path(disk_dev, self.num)

        # XXX uid= won't work on FAT and alike, append automatically.
        #cmd = ["sudo", "mount", "-o", "ro,uid={}".format(os.getuid()), self.lp, mnt_pt]
        r_opt = "rw" if True == rw else "ro"
        cmd = ["sudo", "mount", "-o", r_opt, self.lp, mnt_pt]
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
        log.debug(str(out, "utf-8").rstrip())

        return bak_dir

    def restore(self, bak_dir):
        if not self.mnt_pt:
            raise PartError("Partitinion is not mounted")

        cmd = "sudo cp -a {}/* {}".format(bak_dir, self.mnt_pt)
        log.info(cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        if proc.returncode:
            raise PartError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").rstrip())


    @staticmethod
    def delete(disk_dev, num):
        cmd = ["sudo", "sgdisk", "-d", str(num), disk_dev]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise PartError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").rstrip())


    @staticmethod
    def new(disk_dev, num, start, end, fs, flags):
        cmd = ["sudo", "sgdisk", "-n", "{}:{}:{}".format(num, start, end)]
        # XXX handle more flags
        for f in flags:
            if f.startswith("type="):
                t = int(parse("type={:d}", f)[0])
                cmd.append("-t")
                cmd.append("{}:0x{:x}".format(num, t))
                continue

        cmd.append(disk_dev)
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise PartError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").rstrip())

        Part.mkfs(disk_dev, num, fs)

        return Part({"num": num, "start": start, "end": end, "fs": fs, "flags": flags})


    @staticmethod
    def mkfs(disk_dev, num, fs):
        cmd = ["sudo", "mkfs", "-t", fs, Part.make_part_dev_path(disk_dev, num)]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise PartError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").rstrip())

