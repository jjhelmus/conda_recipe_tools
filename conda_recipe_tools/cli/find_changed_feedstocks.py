#! /usr/bin/env python
# find feedstocks which have changed since they were last checked
# requires Python 3.6+

import argparse
import json
import logging
import os
import sys

from conda_recipe_tools.git import FeedStock, NotFeedstockRepo
from conda_recipe_tools.util import get_feedstock_dirs

LOG_FORMAT = '%(asctime)s - %(levelname)s : %(message)s'


def read_last_commits(checkfile):
    """ Read in the latest commits from a json checkfile if it exists. """
    if not os.path.exists(checkfile):
        return {}
    with open(checkfile) as f:
        last_commits = json.load(f)
    return last_commits


def find_changed_feedstocks(feedstock_dirs, last_commits, remote_org):
    """ Return a list of feedstocks which have changed. """
    changed_feedstocks = []
    for feedstock_dir in feedstock_dirs:
        logging.info('checking: ' + feedstock_dir)
        if feedstock_dir.endswith('/'):
            feedstock_dir = feedstock_dir[:-1]
        try:
            feedstock = FeedStock(feedstock_dir)
        except NotFeedstockRepo:
            logging.warning('not a feedstock: ' + feedstock_dir)
            continue
        feedstock.add_remote(remote_org, check=False)
        feedstock.fetch(remote_org)
        commit_hash = feedstock.rev_parse(f'{remote_org}/master')
        if last_commits.get(feedstock_dir) != commit_hash:
            logging.info('feedstock has changed: ' + feedstock_dir)
            changed_feedstocks.append(feedstock_dir)
            last_commits[feedstock_dir] = commit_hash
    return changed_feedstocks


def main():
    parser = argparse.ArgumentParser(description=(
        'Find feedstocks which have changed since they were last checked'))
    parser.add_argument(
        'feedstock_dir', nargs='*',
        help='one or more feedstock directories to check')
    parser.add_argument(
        '--file', '-f', type=str,
        help='file with feedstock directories to check')
    parser.add_argument(
        '--outfile', default='changed_feedstocks.txt', type=str,
        help='name of file to write changed feedstocks.')
    parser.add_argument(
        '--checkfile', default='cf_feedstock_commits.json', type=str,
        help='name of file to check and store the commit hashes')
    parser.add_argument(
        '--remote-org', default='conda-forge', type=str,
        help='GitHub organization to check for updates.')
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

    # find outdated feedstocks
    feedstock_dirs = get_feedstock_dirs(args.feedstock_dir, args.file)
    last_commits = read_last_commits(args.checkfile)
    changed_feedstocks = find_changed_feedstocks(
        feedstock_dirs, last_commits, args.remote_org)

    # write checkfile and outfile
    with open(args.checkfile, 'w') as f:
        json.dump(last_commits, f)
    with open(args.outfile, 'wt') as f:
        for changed_feedstock in changed_feedstocks:
            f.write(changed_feedstock+'\n')
    return 0


if __name__ == "__main__":
    sys.exit(main())
