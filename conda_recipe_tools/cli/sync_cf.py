#! /usr/bin/env python
# sync feedstocks with conda-forge by a git rebase
# requires Python 3.5+

import argparse
import logging
import os
import pathlib
import sys

from conda_recipe_tools.git import FeedStock, NotFeedstockRepo

LOG_FORMAT = '%(asctime)s - %(levelname)s : %(message)s'


def sync_feedstock(feedstock_path):
    """ Sync a feedstock against conda-forge by a rebase

    returns True on success, False when the rebase failed
    """
    try:
        feedstock = FeedStock(feedstock_path)
    except NotFeedstockRepo:
        logging.warning('not a feedstock: ' + feedstock_path)
        return False
    feedstock.rebase_abort(check=False)  # abort any failed rebases
    feedstock.checkout()    # git checkout master
    feedstock.fetch()       # git fetch origin
    feedstock.reset_hard()  # git reset --hard origin/master
    feedstock.add_remote('conda-forge', check=False)
    feedstock.fetch('conda-forge')
    complete = feedstock.rebase('conda-forge', check=False)
    if complete.returncode:
        # the rebase failed, abort it
        feedstock.rebase_abort(check=False)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Sync feedstocks with conda-forge by rebasing')
    parser.add_argument(
        'feedstock_dir', nargs='*',
        help='one or more feedstock directories to sync')
    parser.add_argument(
        '--file', '-f', type=str,
        help='file with feedstock directories to sync')
    parser.add_argument(
        '--outfile',
        help='file to write synced feedstocks, default is not to write')
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

    # sync recipes
    successfully_rebased = []
    for feedstock_dir in feedstock_dirs:
        if feedstock_dir.endswith('/'):
            feedstock_dir = feedstock_dir[:-1]
        logging.info('rebasing: ' + feedstock_dir)
        feedstock_path = os.path.join(args.base_dir, feedstock_dir)
        if sync_feedstock(feedstock_path):
            successfully_rebased.append(feedstock_path)
        else:
            logging.warning('rebase failed: ' + feedstock_dir)

    # write file of successfully rebased feedstocks if requested
    if args.outfile:
        with open(args.outfile, 'w') as f:
            for fs in successfully_rebased:
                f.write(str(pathlib.Path(fs)) + '\n')
    return 0


if __name__ == "__main__":
    sys.exit(main())
