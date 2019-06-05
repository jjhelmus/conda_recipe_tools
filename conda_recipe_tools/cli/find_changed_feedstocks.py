#! /usr/bin/env python
# find feedstocks which have changed since they were last checked
# requires Python 3.5+

import argparse
import glob
import json
import logging
import os
import sys

from conda_recipe_tools.git import GitRepo

LOG_FORMAT = '%(asctime)s - %(levelname)s : %(message)s'


def read_last_commits(checkfile):
    """ Read in the latest commits from a json checkfile if it exists. """
    if not os.path.exists(checkfile):
        return {}
    with open(checkfile) as f:
        last_commits = json.load(f)
    return last_commits


def update_feedstock(feedstock_path):
    """ Update a feedstock and return the commit hash of the master branch. """
    feedstock = GitRepo(feedstock_path)
    feedstock.fetch()       # git fetch origin
    feedstock.reset_hard()  # git reset --hard origin/master
    return feedstock.commit_hash


def main():
    parser = argparse.ArgumentParser(description=(
        'Find feedstocks which have changed since they were last checked'))
    parser.add_argument(
        '--base_dir', default='.', type=str,
        help='feedstock base directory, default is current directory')
    parser.add_argument(
        '--log', default='info',
        help='log level; debug, info, warning, error, critical')
    parser.add_argument(
        '--outfile', default='changed_feedstocks.txt', type=str,
        help='name of file to write changed feedstocks.')
    parser.add_argument(
        '--checkfile', default='last_feedstock_commits.json', type=str,
        help='name of file to check and store the commits hashes')
    args = parser.parse_args()

    # set up logging
    log_numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(log_numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log)
    logging.basicConfig(level=log_numeric_level, format=LOG_FORMAT)

    # update and find outdated feedstocks
    last_commits = read_last_commits(args.checkfile)
    feedstock_paths = sorted(glob.glob('*-feedstock'))
    changed_feedstocks = []
    for feedstock_path in feedstock_paths:
        logging.info('updating: ' + feedstock_path)
        commit_hash = update_feedstock(feedstock_path)
        if last_commits.get(feedstock_path) != commit_hash:
            logging.info('feedstock has changed: ' + feedstock_path)
            changed_feedstocks.append(feedstock_path)
            last_commits[feedstock_path] = commit_hash

    # write checkfile and outfile
    with open(args.checkfile, 'w') as f:
        json.dump(last_commits, f)
    with open(args.outfile, 'wt') as f:
        for changed_feedstock in changed_feedstocks:
            f.write(changed_feedstock+'\n')
    return 0


if __name__ == "__main__":
    sys.exit(main())
