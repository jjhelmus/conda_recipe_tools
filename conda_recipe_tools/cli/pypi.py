#! /usr/bin/env python
# open PyPI to a

import argparse
import pathlib
import sys
import webbrowser

PYPI_WITH_VERSION = 'https://pypi.python.org/pypi/{package}/{version}'
PYPI_NO_VERSION = 'https://pypi.python.org/pypi/{package}'

WAREHOUSE_WITH_VERSION = 'https://pypi.org/project/{package}/{version}'
WAREHOUSE_NO_VERSION = 'https://pypi.org/project/{package}'


def get_pkg_name_from_cwd():
    """ Return the package name if the cwd is a feedstock. """
    path = pathlib.Path.cwd()
    for part in reversed(path.parts):
        if part.endswith('-feedstock'):
            return part[:-10]
    print("Error: cannot determine package name from cwd")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Open a PyPI package page')
    parser.add_argument(
        'packages', type=str, nargs='*',
        help=(
            'packages to open pages for, use package::version for versions. '
            'If no packages are specified, determine package name from cwd.'))
    parser.add_argument(
        '--warehouse', '-w', action='store_true',
        help='open in warehouse, pypi.org, default is PyPI, pypi.python.org')
    args = parser.parse_args()

    if len(args.packages) == 0:
        packages = [get_pkg_name_from_cwd()]
    else:
        packages = args.packages
    for package in packages:
        if '::' in package:
            package, version = package.split('::')
            if args.warehouse:
                url = WAREHOUSE_WITH_VERSION.format(
                    package=package, version=version)
            else:
                url = PYPI_NO_VERSION.format(package=package, version=version)
        else:
            if args.warehouse:
                url = WAREHOUSE_NO_VERSION.format(package=package)
            else:
                url = PYPI_NO_VERSION.format(package=package)
        webbrowser.open(url)


if __name__ == "__main__":
    main()
