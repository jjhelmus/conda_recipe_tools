#! /usr/bin/env python
import argparse
from collections import defaultdict

from conda.models.match_spec import MatchSpec

from conda_recipe_tools.repodata import fetch_repodata
from conda_recipe_tools.repodata import newest_version_for_subdir


try:
    from packaging.version import parse as parse_version
except ImportError:
    from pip._vendor.packaging.version import parse as parse_version


def _find_pkgs_with_dep(packages, search_dep):
    """ Return a list of packages which have a given dependency """
    pkgs_with_dep = []
    for info in packages.values():
        for dep in info.get('depends', []):
            if dep.startswith(search_dep):
                pkgs_with_dep.append(info)
    return pkgs_with_dep


def _find_pkgs_to_rebuild(pkgs_with_dep, newest_version, search_rec):
    """ Return a dictionay of package names which need to be rebuilt

    Packages need to be rebuilt if the newest version of the packages do not
    have a package with dependencies that match the search_rec
    """
    search_dep = search_rec['name']
    status = defaultdict()
    for pkg_info in pkgs_with_dep:
        name = pkg_info['name']
        if parse_version(pkg_info['version']) != newest_version[name]:
            continue
        for dep in pkg_info.get('depends', []):
            if not dep.startswith(search_dep):
                continue
            spec = MatchSpec(dep)
            if spec.match(search_rec):
                status[name] = (False, None)
            else:
                if name not in status:
                    status[name] = (True, dep)
    return {name: dep for name, (rebuild, dep) in status.items() if rebuild}


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Find packages that needs to be re-built for a migration")
    parser.add_argument(
        'package_name', nargs=1, help='package which caused the migration')
    parser.add_argument(
        'package_version', nargs=1, help='version of above package')
    parser.add_argument(
        '--channel', action='store', default='main',
        help='channel to search, default is main')
    parser.add_argument(
        '--subdir', action='store', default='linux-64',
        help='subdir to search, default is linux-64')
    parser.add_argument(
        '--verb', '-v', action='store_true',
        help='verbose output')
    return parser.parse_args()


def main():
    args = parse_arguments()

    search_dep = args.package_name[0]
    search_version = args.package_version[0]
    search_rec = {
        'name': search_dep,
        'version': search_version,
        'build': '0',
        'build_number': 0
    }

    packages = fetch_repodata(args.channel, args.subdir)['packages']
    newest_version = newest_version_for_subdir(args.channel, args.subdir)

    pkgs_with_dep = _find_pkgs_with_dep(packages, search_dep)
    if args.verb:
        print(f"The following packages depend on {search_dep}")
        print("-----------------------------------------------")
        names = set(info['name'] for info in pkgs_with_dep)
        for name in sorted(names):
            print(name)

    rebuild = _find_pkgs_to_rebuild(pkgs_with_dep, newest_version, search_rec)
    if args.verb:
        print("\nThe following packages should be rebuilt")
        print("----------------------------------------")
    for name in sorted(rebuild):
        if args.verb:
            dep = rebuild[name]
            print(f"{name}: {dep}")
        else:
            print(name)


if __name__ == "__main__":
    main()
