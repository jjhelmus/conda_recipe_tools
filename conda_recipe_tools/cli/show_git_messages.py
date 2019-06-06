#! /usr/bin/env python

import argparse
import os.path
import sys

from conda_build.api import render


def show_git_message(feedstock_dir):
    """ print out the git message for a feedstock. """

    recipe_dir = os.path.join(feedstock_dir, 'recipe')
    recipes = render(recipe_dir, finalize=False)
    metadata, download, needs_reparse = recipes[0]

    pkg_version = metadata.version()
    pkg_name = metadata.name()

    git_message = "git commit -m '{name} {ver}' --allow-empty ".format(name=pkg_name, ver=pkg_version)
    print(git_message)


def main():
    parser = argparse.ArgumentParser(
        description='print git messages for a set of feedstocks.')
    parser.add_argument(
        'feedstock_dir', nargs='*',
        help='one or more feedstock directories to prepare files for')
    parser.add_argument(
        '--file', '-f', type=str,
        help='file with feedstock directories to prepare files for')
    parser.add_argument(
        '--base_dir', default='.', type=str,
        help='feedstock base directory, default is current directory')
    args = parser.parse_args()

    # detemine feedstock directories to list
    if args.file is not None:
        # skip comments (#) and blank lines
        is_valid = lambda x: not x.startswith('#') and len(x.strip())
        with open(args.file) as f:
            feedstock_dirs = [l.strip() for l in f if is_valid(l)]
    else:
        feedstock_dirs = args.feedstock_dir

    for feedstock_dir in feedstock_dirs:
        if feedstock_dir.endswith('/'):
            feedstock_dir = feedstock_dir[:-1]
        show_git_message(feedstock_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
