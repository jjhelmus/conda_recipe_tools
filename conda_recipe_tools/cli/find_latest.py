#! /usr/bin/env python
import argparse

from conda_recipe_tools.find_version import find_latest_version
from conda_recipe_tools.pkg_info import read_pkg_info


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Find the latest version of packages")
    parser.add_argument(
        "--pkg_info", action='store', default='pkg_info.csv',
        help='file containing specification on how to find package versions')
    parser.add_argument(
        'packages', nargs='*',
        help='packages to check, leave blank to check all packages')
    return parser.parse_args()


def main():
    args = parse_arguments()
    pkg_info = read_pkg_info(args.pkg_info)
    if len(args.packages):
        names_to_check = args.packages
    else:
        names_to_check = sorted(pkg_info.keys())
    print('package_name,latest_version')
    for name in names_to_check:
        latest_version = find_latest_version(name, pkg_info[name])
        print(f'{name},{latest_version}')


if __name__ == "__main__":
    main()
