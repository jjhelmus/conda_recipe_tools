#! /usr/bin/env python
import argparse
import os

from conda_recipe_tools.find_version import find_latest_version, NoURLError, NoVersionError, NoCustomLookupError
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
        lookup_fail = True
        info = pkg_info.get(name, {})
        update_type = info.get('update_type', 'pypi')
        extra = info.get('update_extra', {})
        try:
            latest_version = find_latest_version(name, update_type, extra)
            lookup_fail = False
        except FeatureNotFound as e:
            # this will raise is bs4 cannot use lxml as a feature to parse html
            raise e
        except ConnectionError as e:
            # this will happen when there is a timeout
            latest_version = 'could_not_reach_url'
        except NoURLError as e:
            # this will happen when there is no url specified
            latest_version = 'url_is_none'
        except NoVersionError as e:
            # this will happen when we cannot find a suitable url
            latest_version = 'no_versions_found'
        except NoCustomLookupError as e:
            # this happens when lookup_type is custom but we don't have it
            # implemented
            latest_version = 'custom_lookup_not_implemented'
        except Exception as e:
            # everything else
            latest_version = 'version_lookup_failed'
            if args.fail_hard:
                exit(1)

        if lookup_fail:
            no_header = os.path.isfile('zzz_failed_lookups.csv')
            with open('zzz_failed_lookups.csv', 'a') as fout:
                if not no_header:
                    fout.write('name,latest_version\n')
                fout.write(f'{name},{latest_version}\n')

        print(f'{name},{latest_version}')


if __name__ == "__main__":
    main()
