#! /usr/bin/env python
# print out requirements for a PyPI package

import argparse

import requests

REQ_NO_VERSION = 'https://pypi.org/pypi/{package}/json'
REQ_WITH_VERSION = 'https://pypi.org/pypi/{package}/{version}/json'


def main():
    parser = argparse.ArgumentParser(
        description='List the requirements of a PyPI package')
    parser.add_argument(
        'packages', type=str, nargs='+',
        help='packages to open pages for, use package::version for versions')
    args = parser.parse_args()

    for package in args.packages:
        print(package)
        if '::' in package:
            package, version = package.split('::')
            url = REQ_WITH_VERSION.format(package=package, version=version)
        else:
            url = REQ_NO_VERSION.format(package=package)

        resp = requests.get(url)
        out = resp.json()
        print("-----------------------")
        for req in out['info']['requires_dist']:
            print(req)
        print()

if __name__ == "__main__":
    main()
