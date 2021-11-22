
import os
import logging
import subprocess
import tempfile
from parse import *
from chimg.disk.part import Part
from chimg.disk.lvm import LVM

log = logging.getLogger(__name__)

class DiskError(Exception):
    pass

class Disk():
    
    def __init__(self, dev, attach=False):
        self.lo = None
        self.part = {} 
        if isinstance(dev, str):
            self.__create_from_path(dev, attach=attach)
        if isinstance(dev, tuple):
            # (path, image_fmt)
            self.__create_from_path(dev[0], dev[1], attach)

    def __del__(self):
        for p in self.part:
            del p
        if self.lo:
            self.detach_lo()

    def __create_from_path(self, dev, dev_fmt=None, attach=False):
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

        if attach:
            self.attach_lo()

        # Continue on partition info.
        def pt(l, d):
            u = d + 1
            if len(idx) <= u:
                return l[idx[d]["pos"]:].strip()
            return l[idx[d]["pos"]:idx[u]["pos"]].strip()


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
            self.part[p["num"]] = Part(p, self)
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

    def attach_lo(self):
        if self.lo:
            return self.lo
        cmd = ["sudo", "losetup", "-f", "-P", "--show", self.dev]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(err, "utf-8").rstrip())
            return
        self.lo = str(out, "utf-8").rstrip()
        log.debug("Attached image to '{}'".format(self.lo))
        return self.lo 

    def detach_lo(self):
        if not self.lo:
            return
        cmd = ["sudo", "losetup", "-d", self.lo]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(err, "utf-8").rstrip())
        log.debug("Detached image from '{}'".format(self.lo))
        self.lo = None


    def make_gpt(self):
        if "gpt" == self.table:
            log.warning("Already have GPT")
            return

        cmd = ["sudo", "sgdisk", "--mbrtogpt", self.lo]
        log.info(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(out, "utf-8").rstrip())
        log.debug("Converted from '{}' to '{}'".format(self.table, "gpt"))
        self.table = "gpt"


    def part_del(self, num):
        if not self.lo:
            raise DiskError("Disk not attached to any loop device")
        Part.delete(self.lo, num)
        del self.part[num]


    def part_new(self, start, end, fs, flags = {}, num=-1):
        if not self.lo:
            raise DiskError("Disk not attached to any loop device")

        if num < 1:
            num = 1
            while num in self.part.keys():
                num += 1
        self.part[num] = Part.new(self, num, start, end, fs, flags)

        return self.part[num]


    @staticmethod
    def sync():
        # All but root part is unmounted
        cc = ["sudo", "sync"]
        proc = subprocess.Popen(cc, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()


    # Takes only the boot part
    def convert_efi_in_place(self, boot_part, root_part, subscription_user=None, subscription_pass=None, dns_server=None):
        # XXX Check if the conversion is really needed. Fe disk is not gpt, no efi part exists, etc. 

        # XXX check if part exists and bail out cleanly
        # XXX check if there's enough space after the deletion, so it can be reused for two parts
        bp = self.part[boot_part]

        self.attach_lo()

        try:
            td = tempfile.TemporaryDirectory()
            bp.mount(self.lo, td.name)
            bak_dir = bp.backup()
            bp.umount()
            td.cleanup()

            self.make_gpt()

            self.detach_lo()
            self.attach_lo()

            old_uuid = bp.uuid
            old_partuuid = bp.partuuid


            # XXX After the deletion, the data in the object might be inconsistent.
            # EFI part new
            p0_num = bp.num
            p0_start = bp.start
            p0_end = int((bp.end - bp.start)/2)
            p0_fs = "fat32"
            # Boot part, shrinked old one
            # num determined automatically
            p1_start = p0_end + 1
            p1_end = bp.end
            p1_fs = bp.fs
            # Enforce ext4 unconditionally, disregard what the original one was
            # p1_fs = "ext4"
            p1_flags = bp.flags

            # XXX Do part remove/add business, the object is still inconsistent at/after this point
            self.part_del(bp.num)
            #p0 = self.part_new(p0_start, p0_end, "fat", ["type={}".format(0xef00)], p0_num)
            p0 = self.part_new(p0_start, p0_end, p0_fs, ["type=ef"], p0_num)
            p1 = self.part_new(p1_start, p1_end, p1_fs, p1_flags)

            # Prepare boot and efi parts
            p1_td = tempfile.TemporaryDirectory()
            p1.mount(self.lo, p1_td.name, True)

            p0_td = tempfile.TemporaryDirectory()
            p0.mount(self.lo, p0_td.name, True)

            # Move things around
            p1.restore(bak_dir)
            # XXX This part is very vague, will probably only fork for RHEL family
            # XXX pack into a method
            if os.path.isdir(os.path.join(p1.mnt_pt, "efi")):
                cmd = "sudo mv {}/* {}".format(os.path.join(p1.mnt_pt, "efi"), p0.mnt_pt)
                log.info(cmd)
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                out, err = proc.communicate()
                if proc.returncode:
                    raise DiskError(str(err, "utf-8").rstrip())
                log.debug(str(out, "utf-8").rstrip())

            # Tear down boot and efi parts
            p0.umount()
            p0_td.cleanup()

            p1.umount()
            p1_td.cleanup()
            # Remove backup, ignore errors
            cmd = ["sudo", "rm", "-rf", bak_dir]
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            log.info(" ".join(cmd))

            # Figure out root part
            lvm = None
            rp = None
            rp_td = tempfile.TemporaryDirectory()
            if isinstance(root_part, int):
                rp = self.part[root_part]
                rp.mount(self.lo, rp_td.name, True) 
            elif isinstance(root_part, str):
                # Must be on LVM
                # XXX Pack LVM part search into a method
                for p in self.part:
                    got_it = False
                    for k, v in self.part[p].__dict__.items():
                        if "flags" == k and "lvm" in v:
                    #for k, v in disk.part[p].__dict__.items():
                    #    if "flags" == k and "lvm" in v:
                    #        lvm = LVM(Part.make_part_dev_path(self.lo, disk.part[p].num))
                            lvm = LVM(Part.make_part_dev_path(self.lo, self.part[p].num))
                            vg = lvm.scan_vg(3)
                            lv = lvm.scan_lv(3)
                            if root_part in lv:
                                lvm.lo = root_part
                                lvm.activate()
                                lvm.mount(rp_td.name, True) 
                                got_it = True
                            break
                    if got_it:
                        break
            else:
                rp_td.cleanup()
                raise DiskError("Can't interpret '{}' as root partition".format(root_part))
            if not got_it:
                rp_td.cleanup()
                raise DiskError("Couldn't find LV '{}' in VG '{}'".format(root_part, lvm.vg))
 
            # Fix fstab
            fn = os.path.join(rp_td.name, "etc", "fstab")
            with open(fn, "r") as f:
                out = f.read()
                f.close()
            log.debug(out)

            out = out.replace(old_uuid, p1.uuid)
            out = out.replace(old_partuuid, p1.partuuid)
            tfn = tempfile.NamedTemporaryFile()
            with open(tfn.name, "w") as f:
                f.write(out)

            cmd = "sudo cp {} {}".format(tfn.name, fn)
            log.info(cmd)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            out, err = proc.communicate()
            if proc.returncode:
                raise DiskError(str(err, "utf-8").rstrip())
            log.debug(str(out, "utf-8").rstrip())

            with open(fn, "r") as f:
                out = f.read()
                f.close()
            log.debug(out)


            # Install GRUB from the distro
            # XXX This is distro specific. RHEL in this case.
            # XXX This is arch specific.
            boot_mnt_pt = os.path.join(rp_td.name, "boot")
            p1.mount(self.lo, boot_mnt_pt, True)
            efi_mnt_pt = os.path.join(boot_mnt_pt, "efi")
            p0.mount(self.lo, efi_mnt_pt, True)

            #"grub2-install;" \
            #"tree /boot;" \
            #"efibootmgr -v;" \
            cmds = []
            cmds.append("if test -f /etc/resolv.conf; then mv /etc/resolv.conf /etc/resolv.conf~; fi")
            if dns_server:
                cmds.append("echo 'nameserver {}' > /etc/resolv.conf".format(dns_server))
            cmds.append("if test -f /etc/yum.repos.d/cna.repo; then mv /etc/yum.repos.d/cna.repo /etc/yum.repos.d/cna.repo.off; fi")
            if subscription_user and subscription_pass:
                cmds.append("subscription-manager register --username {} --password {} --auto-attach || true".format(subscription_user, subscription_pass))
            # XXX Put the package manager into a separate class depending on distro.
            cmds.append("yum install --disablerepo=* --enablerepo=rhel-8-for-x86_64-baseos-rpms -y grub2-pc grub2-efi-x64 efibootmgr dbxtool mokutil shim-x64 grubby")
            cmds.append("grub2-mkconfig -o /boot/efi/EFI/redhat/grub.cfg")
            cmds.append("rm -rf /boot/efi/NvVars;")
            cmds.append("subscription-manager unregister || true")
            cmds.append("if test -f /etc/yum.repos.d/cna.repo.off; then mv /etc/yum.repos.d/cna.repo.off /etc/yum.repos.d/cna.repo; fi")
            cmds.append("rm /etc/resolv.conf")
            cmds.append("if test -f /etc/resolv.conf~; then cp /etc/resolv.conf~ /etc/resolv.conf; fi")

            self.chroot_init(rp_td.name)
            for cmd in cmds:
                try:
                    info=0
                    if cmd.startswith("subscription-manager"):
                        info=2
                    self.chroot(rp_td.name, cmd, info=info)
                except DiskError as e:
                    log.debug(str(e))
            self.chroot_teardown(rp_td.name)

            # Tear down boot and efi part
            p0.umount()
            p0_td.cleanup()

            p1.umount()
            p1_td.cleanup()

            # All but root part is unmounted
            Disk.sync()

            # Tear down LVM.
            if rp:
                rp.umount() 
                Disk.sync()
            elif lvm:
                lvm.umount() 
                Disk.sync()
                lvm.deactivate()
            rp_td.cleanup()

        except:
            self.detach_lo()
            raise

        self.detach_lo()

    def chroot_init(self, root):
        #mnts = [
        #        ["sudo", "mount", "--types", "proc", "/proc", os.path.join(root, "proc")],
        #        ["sudo", "mount", "--rbind", "/sys", os.path.join(root, "sys")],
        #        ["sudo", "mount", "--make-rslave", os.path.join(root, "sys")],
        #        ["sudo", "mount", "--rbind", "/dev", os.path.join(root, "dev")],
        #        ["sudo", "mount", "--make-rslave", os.path.join(root, "dev")],
        #        ]
        mnts = [
                ["sudo", "mount", "--bind", "/dev", os.path.join(root, "dev")],
                ["sudo", "mount", "--bind", "/sys", os.path.join(root, "sys")],
                ["sudo", "mount", "--bind", "/proc", os.path.join(root, "proc")],
                ]

        for mc in mnts:
            log.info(" ".join(mc))
            proc = subprocess.Popen(mc, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            if proc.returncode:
                log.debug(str(err, "utf-8").rstrip())
            log.debug(str(out, "utf-8").rstrip())

    def chroot_teardown(self, root):
        # Some additional mounts within the actually requested ones could be made
        # automatically from within the rootfs. Try to unmount them all before.
        cc = ["sudo", "mount"]
        proc = subprocess.Popen(cc, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(err, "utf-8").rstrip())
        mns = []
        for ln in str(out, "utf-8").strip().split("\n"):
            t = ln.split(" ")
            if t[2].startswith(root) and t[2] != root:
                not_part = True
                for p in self.part:
                    if t[2] == self.part[p].mnt_pt:
                        not_part = False
                        break
                if not_part:
                    mns.append(t[2])
        mns.sort(key=len, reverse=True)
        for mc in mns:
            c = ["sudo", "umount", mc]
            log.info(" ".join(c))
            proc = subprocess.Popen(c, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            if proc.returncode:
                log.debug(str(err, "utf-8").rstrip())
            log.debug(str(out, "utf-8").rstrip())
            Disk.sync()

        cc = ["sudo", "sync"]
        proc = subprocess.Popen(cc, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


    def chroot(self, root, cmd, args=[], info=0):

        cc = ["sudo", "chroot", root,  "/bin/bash", "-c", cmd]
        # Zero imply print the whole cmd
        if not info:
            log.info(" ".join(cc))
        else:
            # Only show that many segments
            log.info("{} {} ...".format(" ".join(cc[:5]), " ".join(cmd.split(" ")[:info])))
        proc = subprocess.Popen(cc, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            raise DiskError(str(err, "utf-8").rstrip())
        if not info:
            log.debug(str(out, "utf-8").rstrip())

