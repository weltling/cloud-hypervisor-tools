
import os
import logging
import subprocess
import tempfile
from parse import *
from vmimg.disk.part import Part

log = logging.getLogger(__name__)

class DiskError(Exception):
    pass

class Disk():
    
    # XXX destruct cleanly especially wrt mounts, attached loop devs, etc.
    def __init__(self, dev, args=None):
        if isinstance(dev, str):
            self.__create_from_path(dev)
        if isinstance(dev, tuple):
            # (path, image_fmt)
            self.__create_from_path(dev[0], dev[1])

    def __create_from_path(self, dev, dev_fmt=None):
        if not dev_fmt:
            dev_fmt = Disk.get_dev_fmt(dev)
            if "raw" != dev_fmt:
                dev = Disk.dev_fmt_cvt(dev, dev_fmt, out_fmt="raw")

        cmd = ["sudo", "parted", "-s", dev, "unit", "s", "print"]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").rstrip())

        # Attributes will be assigned in the same order as matched placeholders.
        pats = [
                {"pat": "Model: {:>}", "done": False, "attr": ["model"]},
                {"pat": "Disk {}: {:d}s", "done": False, "attr": ["dev", "sectors"]},
                {"pat": "Partition Table: {:>}", "done": False, "attr": ["table"]},
                {"pat": "Sector size (logical/physical): {:d}B/{:d}B", "done": False, "attr": ["sector_size_logical", "sector_size_physical"]},
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


    @staticmethod
    def get_dev_fmt(dev):
        cmd = ["sudo", "qemu-img", "info", dev]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(err, "utf-8").rstrip())
        log.debug(str(out, "utf-8").rstrip())

        outl = str(out, "utf-8").split("\n")
        for l in outl:
            res = parse("file format: {}", l)
            if res:
                return res[0]
        return None


    @staticmethod
    def dev_fmt_cvt(dev, dev_fmt, out_dev=None, out_fmt="raw"):
        if not out_dev:
            out_dev = os.path.splitext(dev)[0] + ".raw"

        # XXX Implement force condition
        if os.path.exists(out_dev):
            log.info("Reusing existing '{}'".format(out_dev))
            return out_dev

        cmd = ["qemu-img", "convert", "-f", dev_fmt, "-O", out_fmt, dev, out_dev]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(err, "utf-8").rstrip())
        return out_dev

    @staticmethod
    def dev_resize(dev, sz):
        cmd = ["qemu-img", "resize", dev, str(sz)]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(err, "utf-8").rstrip())

    def attach_lp(self):
        cmd = ["sudo", "losetup", "-f", "-P", "--show", self.dev]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(err, "utf-8").rstrip())
            return
        self.lp = str(out, "utf-8").rstrip()
        log.debug("Attached image to '{}'".format(self.lp))
        return self.lp 

    def detach_lp(self):
        cmd = ["sudo", "losetup", "-d", self.lp]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(err, "utf-8").rstrip())
        log.debug("Detached image from '{}'".format(self.lp))
        self.lp = None


    def make_gpt(self):
        if "gpt" == self.table:
            log.warning("Already have GPT")
            return

        cmd = ["sudo", "sgdisk", "--mbrtogpt", self.lp]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(out, "utf-8").rstrip())
        log.debug("Converted from '{}' to '{}'".format(self.table, "gpt"))
        self.table = "gpt"


    def part_del(self, num):
        if not self.lp:
            raise DiskError("Disk not attached to any loop device")
        Part.delete(self.lp, num)
        del self.part[num]


    def part_new(self, start, end, fs, flags = {}, num=-1):
        if not self.lp:
            raise DiskError("Disk not attached to any loop device")

        if num < 1:
            num = 1
            while num in self.part.keys():
                num += 1
        self.part[num] = Part.new(self.lp, num, start, end, fs, flags)

        return self.part[num]


    # Takes only the boot part
    def convert_efi_in_place(self, boot_part):
        # XXX Check if the conversion is really needed. Fe disk is not gpt, no efi part exists, etc. 

        # XXX check if part exists and bail out cleanly
        # XXX check if there's enough space after the deletion, so it can be reused for two parts
        p = self.part[boot_part]

        import dumper
        dumper.dump(self)
        dumper.dump(p)

        self.attach_lp()

        try:
            td = tempfile.TemporaryDirectory()
            p.mount(self.lp, td.name)
            bak_dir = p.backup()
            p.umount()
            td.cleanup()

            self.make_gpt()

            self.detach_lp()
            self.attach_lp()

            # XXX After the deletion, the data in the object might be inconsistent.
            # EFI part new
            p0_num = p.num
            p0_start = p.start
            p0_end = int((p.end - p.start)/2)
            p0_fs = "fat32"
            # Boot part, shrinked old one
            # num determined automatically
            p1_start = p0_end + 1
            p1_end = p.end
            p1_fs = p.fs
            p1_flags = p.flags

            # XXX Do part remove/add business, the object is still inconsistent at/after this point
            self.part_del(p.num)
            p0 = self.part_new(p0_start, p0_end, "fat", ["type={}".format(0xef00)], p0_num)
            p1 = self.part_new(p1_start, p1_end, p1_fs, p1_flags)

            p1_td = tempfile.TemporaryDirectory()
            p1.mount(self.lp, p1_td.name, True)
            p1.restore(bak_dir)
            p1.umount()
            p1_td.cleanup()

            dumper.dump(self)
        except:
            self.detach_lp()
            raise

        self.detach_lp()
