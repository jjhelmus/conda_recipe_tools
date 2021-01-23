#! /usr/bin/env python
import argparse
import os

from conda_recipe_tools.find_version import find_latest_version
from conda_recipe_tools.pkg_info import read_pkg_info

from bs4 import FeatureNotFound
from requests.exceptions import ConnectionError


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Find the latest version of packages")
    parser.add_argument(
        "--pkg_info", action='store', default=None,
        help=(
            'File containing specification on how to find package versions. '
            'The default is to use the file specified by the PKG_INFO_FILE '
            'environment variable. If this variable is not set, pkg_info.csv '
            'in the current directy is used.'))
    parser.add_argument(
        "--no_header", action='store_true',
        help='Do not print header line, helpful when appending to a file')
    parser.add_argument(
            "--fail-hard", action="store_true",
            help="If the lookup fails, this will cause the tool to exit early."
            )
    parser.add_argument(
        'packages', nargs='*',
        help='packages to check, leave blank to check all packages')
    return parser.parse_args()


def main():
    args = parse_arguments()
    pkg_info = args.pkg_info
    if pkg_info is None:
        pkg_info = os.environ.get('PKG_INFO_FILE', 'pkg_info.csv')
    pkg_info = read_pkg_info(pkg_info)
    if len(args.packages):
        names_to_check = args.packages
    else:
        names_to_check = sorted(pkg_info.keys())
    if not args.no_header:
        print('package_name,latest_version')
    for name in names_to_check:
        info = pkg_info.get(name, {})
        update_type = info.get('update_type', 'pypi')
        extra = info.get('update_extra', {})
        try:
            latest_version = find_latest_version(name, update_type, extra)
        except FeatureNotFound as e:
            raise e
        except ConnectionError as e:
            latest_version = 'could_not_reach_url'
        except:
            latest_version = 'version_lookup_failed'
            if args.fail_hard:
                exit(1)
        print(f'{name},{latest_version}')


if __name__ == "__main__":
    main()
