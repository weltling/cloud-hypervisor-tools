#!/usr/bin/env python3

import argparse
import logging
import sys
import vmimg


def main(argv = []):
    if len(argv) == 0:
        argv = sys.argv[1:]

    # Common args for every cmd.
    arg_parser_common = argparse.ArgumentParser(add_help=False)
    arg_parser_common.add_argument("-v", "--verbose", action="count",
                                   help="Verbose output. Pass more than once to increase the level.")
    # Main arg parser.
    arg_parser = argparse.ArgumentParser(prog="vmimg", description="VM disk image utils.")
    arg_parser.add_argument("-V", "--version", action="version",
                                   version=vmimg.__version__, help="Show version.")
    # Subcommands.
    arg_parser_subs = arg_parser.add_subparsers(help="Subcommands", dest="cmd")
    # Image analysis.
    arg_parser_info = arg_parser_subs.add_parser("info", help="Query disk image information.",
                                                 parents=[arg_parser_common])
    arg_parser_info.add_argument("image", action="store", help="Path to the image to be analyzed.")
    arg_parser_info.add_argument("-p", "--part", action="store_true",
                                 help="Partition information.")
    # Image conversion.
    arg_parser_conv = arg_parser_subs.add_parser("convert", help="Convert disk image.",
                                                 parents=[arg_parser_common])
    arg_parser_conv.add_argument("-r", "--root-part", action="store",
                                 help="Source root partition number.")
    arg_parser_conv.add_argument("-b", "--boot-part", action="store",
                                 help="Source boot partition number.")
    arg_parser_conv.add_argument("-l", "--lvm-vg", action="store",
                                 help="Source LVM VG name.")
    arg_parser_conv.add_argument("source", nargs=1)
    arg_parser_conv.add_argument("target", nargs=1)
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

