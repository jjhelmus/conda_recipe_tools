#! /usr/bin/env python
import argparse

from conda_recipe_tools.repodata import fetch_repodata


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="List all packages that depend on a given package")
    parser.add_argument(
        'package_name', nargs=1, help='package to search')
    parser.add_argument(
        '--channel', action='store', default='main',
        help='channel to search, default is main')
    parser.add_argument(
        '--subdir', action='store', default='linux-64',
        help='subdir to search, default is linux-64')
    parser.add_argument(
        '--include-anaconda', action='store_true',
        help=('include anaconda and _anaconda_depends, '
              'by default these packages are ignored'))
    return parser.parse_args()


def main():
    args = parse_arguments()
    search_dep = args.package_name[0]
    packages = fetch_repodata(args.channel, args.subdir)['packages']
    for name, info in packages.items():
        if not args.include_anaconda:
            pkg_name = info['name']
            if pkg_name in ['anaconda', '_anaconda_depends']:
                continue
        for dep in info.get('depends', ()):
            if dep.startswith(search_dep):
                print(f'{name} :: {dep}')


if __name__ == "__main__":
    main()
