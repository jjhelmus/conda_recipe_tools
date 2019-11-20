#! /usr/bin/env python

import argparse

from conda_recipe_tools.repodata import newest_version_for_channel


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Find packages where an upstream channel has a newer version.")
    parser.add_argument(
        'packages', nargs='*',
        help='one or more packages to check.')
    parser.add_argument(
        "--all", action='store_true',
        help='examine all packages in the base channel')
    parser.add_argument(
        "--show-both", action='store_true',
        help='show information for all packages, not just those which are newer in upstream.')
    parser.add_argument(
        "--base-channel", type=str, default='main',
        help="Base channel to compare against upstream, default is 'main'")
    parser.add_argument(
        '--upstream', default='conda-forge', type=str,
        help="upstream channel, default is 'conda-forge'")
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
    base_newest, _ = newest_version_for_channel(args.base_channel, args.subdirs)
    upstream_newest, _ = newest_version_for_channel(args.upstream, args.subdirs)
    if not args.no_header:
        print("pkg_name,base_version,upstream_version")
    if args.all:
        pkgs = base_newest.keys()
    else:
        pkgs = args.packages
    for pkg in pkgs:
        base_ver = base_newest[pkg]
        if pkg not in upstream_newest:
            continue
        upstream_ver = upstream_newest[pkg]
        if upstream_ver > base_ver:
            print(f"{pkg},{base_ver},{upstream_ver}")
        elif args.show_both:
            print(f"{pkg},{base_ver},{upstream_ver}")


if __name__ == "__main__":
    main()
