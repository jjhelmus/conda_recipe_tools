#! /usr/bin/env python

import argparse

from conda_recipe_tools.repodata import newest_version_for_channel


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Find the newest version of package(s) in a channel.")
    parser.add_argument(
        'packages', nargs='*',
        help='one or more packages show versions for')
    parser.add_argument(
        "--all", action='store_true',
        help='show the newest version of all packages in the channel')
    parser.add_argument(
        "--channel", type=str, default='main',
        help="Channel to examine, default is 'main'")
    parser.add_argument(
        "--show-subdirs", action="store_true",
        help="Also show the newest version for each subdir")
    parser.add_argument(
        '--subdirs', nargs='*',
        default=['linux-64', 'osx-64', 'win-32', 'win-64', 'linux-ppc64le', 'noarch'],
        help=("subdirs to examine in both the base and upstream channel, "
              "default is linux-64, osx-64, win-32, win-64, linux-ppc64le and noarch."))
    parser.add_argument(
        "--no_header", action='store_true',
        help='Do not print header line, helpful when appending to a file')
    return parser.parse_args()


def main():
    args = parse_arguments()
    newest, by_subdir = newest_version_for_channel(args.channel, args.subdirs)
    if not args.no_header:
        if args.show_subdirs:
            subdir_str = ','.join([s+'_version' for s in args.subdirs])
            print("pkg_name,newest_version," + subdir_str)
        else:
            print("pkg_name,newest_version")
    if args.all:
        pkgs = newest.keys()
    else:
        pkgs = args.packages
    for pkg in sorted(pkgs):
        ver = newest[pkg]
        if args.show_subdirs:
            subdir_vers = [by_subdir[s].get(pkg) for s in args.subdirs]
            subdir_vers_str = ','.join([str(v) for v in subdir_vers])
            print(f"{pkg},{ver}," + subdir_vers_str)
        else:
            print(f"{pkg},{ver}")


if __name__ == "__main__":
    main()
