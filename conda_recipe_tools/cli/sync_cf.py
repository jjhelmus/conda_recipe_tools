#! /usr/bin/env python
# sync feedstocks with conda-forge by a git rebase
# requires Python 3.5+

import argparse
import logging
import os
import subprocess
import sys
from subprocess import PIPE

LOG_FORMAT = '%(asctime)s - %(levelname)s : %(message)s'


class NotFeedstockRepo(Exception):
    pass


class GitRepo(object):

    def __init__(self, path):
        self._path = path

    def _git(self, git_args, check=True):
        args = ['git', '-C', self._path] + git_args
        logging.debug('command: ' + ' '.join(args))
        complete = subprocess.run(args, stdout=PIPE, stderr=PIPE)
        logging.debug('returncode: ' + str(complete.returncode))
        logging.debug('stdout: ' + complete.stdout.decode('utf-8'))
        logging.debug('stderr: ' + complete.stderr.decode('utf-8'))
        if check:
            complete.check_returncode()
        return complete

    def checkout(self, branch='master'):
        return self._git(['checkout', branch])

    def fetch(self, remote='origin'):
        return self._git(['fetch', remote])

    def reset_hard(self, remote='origin', branch='master'):
        return self._git(['reset', '--hard', '%s/%s' % (remote, branch)])

    def rebase(self, remote, branch='master', check=True):
        return self._git(['rebase', '%s/%s' % (remote, branch)], check)

    def rebase_abort(self, check=True):
        self._git(['rebase', '--abort'], check)

    def ls_files_modified(self):
        out = self._git(['ls-files', '-m'])
        return out.stdout.decode('utf-8').split()


class FeedStock(GitRepo):

    def __init__(self, path, feedstock_name=None):
        super(FeedStock, self).__init__(path)
        if feedstock_name is None:
            out = self._git(['config', '--get', 'remote.origin.url'])
            origin_url = out.stdout.decode('utf-8').strip()
            feedstock_name = origin_url.split('/')[-1]
            if feedstock_name.endswith('.git'):
                feedstock_name = feedstock_name[:-4]
        if not feedstock_name.endswith('feedstock'):
            raise NotFeedstockRepo('not a feedstock: %s' % (feedstock_name))
        self._feedstock_name = feedstock_name

    def add_remote(self, org, remote_name=None, check=True):
        url = 'https://github.com/%s/%s' % (org, self._feedstock_name)
        if remote_name is None:
            remote_name = org
        self._git(['remote', 'add', remote_name, url], check=check)


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
    for feedstock_dir in feedstock_dirs:
        if feedstock_dir.endswith('/'):
            feedstock_dir = feedstock_dir[:-1]
        logging.info('rebasing: ' + feedstock_dir)
        feedstock_path = os.path.join(args.base_dir, feedstock_dir)
        if not sync_feedstock(feedstock_path):
            logging.warning('rebase failed: ' + feedstock_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
