#! /usr/bin/env python

import argparse
import logging
import os.path
import sys
from collections import defaultdict

from conda_build.api import render

import yaml

LOG_FORMAT = '%(asctime)s - %(levelname)s : %(message)s'


def prep_clobber(feedstock_dir):
    """ create a recipe_clobber.yaml file for a feedstock """

    recipe_dir = os.path.join(feedstock_dir, 'recipe')
    recipes = render(recipe_dir, finalize=False)
    metadata, download, needs_reparse = recipes[0]

    pkg_build_number = metadata.build_number()
    pkg_noarch_python = metadata.noarch_python or metadata.noarch == 'python'

    clobber = defaultdict(dict)
    # clobber noarch: python if present
    if pkg_noarch_python:
        clobber['build']['noarch'] = False
    # keep build numbers less than 1000
    if pkg_build_number >= 1000:
        clobber['build']['number'] = int(pkg_build_number - 1000)

    # write clobber
    if clobber:
        clobber_file = os.path.join(recipe_dir, 'recipe_clobber.yaml')
        with open(clobber_file, 'w') as f:
            yaml.dump(dict(clobber), f, default_flow_style=False)


def main():
    parser = argparse.ArgumentParser(
        description='Prepare recipe clobber file for a feedstock')
    parser.add_argument(
        'feedstock_dir', nargs='*',
        help='one or more feedstock directories to prepare clobber file for')
    parser.add_argument(
        '--file', '-f', type=str,
        help='file with feedstock directories to prepare file for')
    parser.add_argument(
        '--base_dir', default='.', type=str,
        help='feedstock base directory, default is current directory')
    parser.add_argument(
        '--log', default='info',
        help='log level; debug, info, warning, error, critical')
    args = parser.parse_args()

    # set up logging
    log_numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(log_numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log)
    logging.basicConfig(level=log_numeric_level, format=LOG_FORMAT)

    # detemine feedstock directories to sync
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
        logging.info('preparing files for: ' + feedstock_dir)
        prep_clobber(feedstock_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
