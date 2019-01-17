#! /usr/bin/env python
# push feedstock changes to AnacondaRecipes git organization
# requires Python 3.5+

import argparse
import logging
import os
import subprocess
import sys
from subprocess import PIPE

from conda_build.api import render

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

    def push(self, remote='origin', local_branch='master',
             remote_branch='master', force=False, check=True):
        refspec = '{src}:{dst}'.format(src=local_branch, dst=remote_branch)
        if force:
            return self._git(['push', '--force', remote, refspec], check)
        return self._git(['push', remote, refspec], check)

    def branch(self, branch_name):
        return self._git(['checkout', '-b', branch_name])

    def branch_delete(self, branch_name):
        return self._git(['branch', '-D', branch_name])

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


def push_feedstock(feedstock_path):
    """ Push git changes to a feedstock to AnacondaRecipes

    returns True on success, False when the push failed
    """
    try:
        feedstock = FeedStock(feedstock_path)
    except NotFeedstockRepo:
        logging.warn("push failed because repo is not a feedstock")
        return False

    complete = feedstock.push(check=False)
    if complete.returncode:     # push failed b/c it is not a fast-forward
        logging.info('standard push failed, creating archive branch')

        # create temp branch of origin/master
        temp_branch = 'temp_origin_master'
        feedstock.branch(temp_branch)   # git checkout -b temp_origin_master
        feedstock.fetch()               # git fetch origin
        feedstock.reset_hard()          # git reset --hard origin/master

        # render the recipe to find the version
        recipe_dir = os.path.join(feedstock_path, 'recipe')
        recipes = render(recipe_dir, finalize=False)
        metadata, download, needs_reparse = recipes[0]
        version = metadata.version()

        # push to archive branch
        archive_branch = 'archive_{version}'.format(version=version)
        logging.info('push origin/master to ' + archive_branch)
        # git push origin master:archive_version
        feedstock.push(remote_branch=archive_branch, local_branch='HEAD')

        # force push master branch
        feedstock.checkout()        # git checkout master
        feedstock.push(force=True)  # git push --force origin master:master
        # git branch -D temp_origin_master
        feedstock.branch_delete(temp_branch)
        logging.info('force push succeeded')
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Push feedstock git changes to AnacondaRecipes.')
    parser.add_argument(
        'feedstock_dir', nargs='*',
        help='one or more feedstock directories to push')
    parser.add_argument(
        '--file', '-f', type=str,
        help='file with feedstock directories to push')
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
        logging.info('pushing: ' + feedstock_dir)
        feedstock_path = os.path.join(args.base_dir, feedstock_dir)
        if not push_feedstock(feedstock_path):
            logging.warning('push failed: ' + feedstock_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
