#!/usr/bin/env python3

import argparse
import logging
import sys
import chimg

# XXX check for dependency tools/libs at runtime

def main(argv = []):
    if len(argv) == 0:
        argv = sys.argv[1:]

    # Common args for every cmd.
    arg_parser_common = argparse.ArgumentParser(add_help=False)
    arg_parser_common.add_argument("-v", "--verbose", action="count",
                                   help="Verbose output. Pass more than once to increase the level.")
    # Main arg parser.
    arg_parser = argparse.ArgumentParser(prog="chimg", description="VM disk image utils.")
    arg_parser.add_argument("-V", "--version", action="version",
                                   version=chimg.__version__, help="Show version.")
    # Subcommands.
    arg_parser_subs = arg_parser.add_subparsers(help="Subcommands", dest="cmd")
    # Image analysis.
    arg_parser_info = arg_parser_subs.add_parser("info", help="Query disk image information. By default, a concise information is delivered without the image to be mounted.",
                                                 parents=[arg_parser_common])
    arg_parser_info.add_argument("image", action="store", help="Path to the image to be analyzed.")
    # Image conversion.
    arg_parser_conv = arg_parser_subs.add_parser("convert", help="Convert disk image.",
                                                 parents=[arg_parser_common])
    arg_parser_conv.add_argument("-r", "--root-part", action="store",
                                 help="Source root partition as number or LV as shown by the info command.")
    arg_parser_conv.add_argument("-b", "--boot-part", action="store",
                                 help="Source boot partition number.")
    arg_parser_conv.add_argument("-l", "--lvm-vg", action="store",
                                 help="Source LVM VG name.")
    arg_parser_conv.add_argument("-i", "--in-place", action="store_true",
                                 help="Copy the source image and modify it in-place.")
    arg_parser_conv.add_argument("--subscription-user", action="store",
                                 help="Username to use with the subscription. RHEL only right now.")
    arg_parser_conv.add_argument("--subscription-pass", action=Password, nargs="?",
                                 help="Password to use with the subscription. RHEL only right now.")
    arg_parser_conv.add_argument("--dns-server", action="store",
                                 help="DNS server to be used within the chrooted image environment. Required if packages are to be installed from an official repository.")
    arg_parser_conv.add_argument("source", nargs=1)
    arg_parser_conv.add_argument("target", nargs="?")
    # Read passed arguments.
    args = arg_parser.parse_args(argv)

    # Version and help are caught by argparse. Other than that, it's always
    # like `command subcommand --arg0 --arg1 ....
    if len(argv) <= 1:
        arg_parser.print_help()
        return 0

    level = logging.WARN
    if args.verbose:
        if 1 == args.verbose:
            level = logging.INFO
        if 2 <= args.verbose:
            level = logging.DEBUG
    logging.basicConfig(level=level)

    if "info" == args.cmd:
        from .cmd import info
        return info.handle(args)
    elif "convert" == args.cmd:
        from .cmd import convert
        return convert.handle(args)


# Source https://svn.blender.org/svnroot/bf-blender/trunk/blender/build_files/scons/tools/bcolors.py
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

class comm:
    @staticmethod
    def warn(s):
        print(bcolors.WARNING + s + bcolors.ENDC)

    @staticmethod
    def fail(s):
        print(bcolors.FAIL + s + bcolors.ENDC)

    @staticmethod
    def ok(s):
        print(bcolors.OKGREEN + s + bcolors.ENDC)

    @staticmethod
    def okb(s):
        print(bcolors.OKBLUE + s + bcolors.ENDC)

    @staticmethod
    def head(s):
        print(bcolors.HEADER + s + bcolors.ENDC)

    @staticmethod
    def msg(s):
        print(s)

class CliError(Exception):
    pass

