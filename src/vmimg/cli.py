#!/usr/bin/env python3

import argparse
import logging
import sys
import vmimg


def main(argv):
    arg_parser_common = argparse.ArgumentParser(add_help=False)
    arg_parser_common.add_argument("-v", "--verbose", action="count",
                                   help="Verbose output.")
    arg_parser = argparse.ArgumentParser(prog="vmimg", description="VM disk image utils.",
                                         parents=[arg_parser_common])
    arg_parser.add_argument("-V", "--version", action="version",
                                   version=vmimg.__version__, help="Show version.")
    arg_parser_subs = arg_parser.add_subparsers(help="Subcommands", dest="cmd")
    arg_parser_info = arg_parser_subs.add_parser("info", help="Query disk image information.",
                                                 parents=[arg_parser_common])
    arg_parser_conv = arg_parser_subs.add_parser("convert", help="Convert disk image.",
                                                 parents=[arg_parser_common])
    args = arg_parser.parse_args(argv)

    level = logging.WARN
    if args.verbose:
        if 1 == args.verbose:
            level = logging.INFO
        if 2 <= args.verbose:
            level = logging.DEBUG
    logging.basicConfig(level=level)

    if "info" == args.cmd:
        from vmimg import info
        return info.handle(args)
    elif "convert" == args.cmd:
        from vmimg import convert
        return convert.handle(args)
    else:
        arg_parser.print_help()
        return 0

if "__main__" == __name__:
    ret = main(sys.argv[1:])
    sys.exit(ret)

