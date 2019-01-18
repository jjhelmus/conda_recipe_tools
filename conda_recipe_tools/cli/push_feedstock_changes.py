#! /usr/bin/env python
# push feedstock changes to AnacondaRecipes git organization
# requires Python 3.5+

import argparse
import logging
import os
import sys

from conda_recipe_tools.git import FeedStock, NotFeedstockRepo
from conda_recipe_tools.recipe import CondaRecipe


LOG_FORMAT = '%(asctime)s - %(levelname)s : %(message)s'


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

        # find the recipe version
        meta_filename = os.path.join(feedstock_path, 'recipe', 'meta.yaml')
        recipe = CondaRecipe(meta_filename)
        version = recipe.version

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
