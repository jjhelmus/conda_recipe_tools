#! /usr/bin/env python
# output feedstock

import argparse
import os
import glob
import subprocess

from conda_recipe_tools.git import FeedStock, NotFeedstockRepo
from conda_recipe_tools.util import get_feedstock_dirs


def can_rebase(feedstock_path, upstream='conda-forge', upstream_branch='master'):
    """ Determine if a feedstock can be rebased against an upstream repository.

    Parameters
    ----------
    feedstock_path : str
        Relative or absolute path to a feedstock directory.
    upstream : str
        Name of upstream GitHub organization, default is conda-forge.
    upstream_branch : str
        Branch of the upstream organization to test against, default is master.

    Returns
    -------
    can_be_rebased : bool or None
        True if the feedstock can be rebased on the upstream, False if the
        rebase fails. None is returned if feedstock_path does not refer to a
        feedstock, for example when it is a folder in the aggregate repository.
    is_exact : bool
        True if a successful rebased is identical to the upstream repository.

    """
    try:
        feedstock = FeedStock(feedstock_path)
    except NotFeedstockRepo:
        return None, False
    original_hash = feedstock.commit_hash
    feedstock.add_remote(upstream, check=False)
    try:
        feedstock.fetch(upstream)
    except subprocess.CalledProcessError:
        return None, False
    complete = feedstock.rebase(upstream, branch=upstream_branch, check=False)
    if complete.returncode:
        # the rebase failed, abort it and check out original hash
        feedstock.rebase_abort(check=False)
        feedstock.checkout(original_hash)
        return False, False
    rebase_hash = feedstock.commit_hash
    upstream_hash = feedstock.rev_parse(f'{upstream}/{upstream_branch}')
    is_exact = (rebase_hash == upstream_hash)
    feedstock.checkout(original_hash)
    return True, is_exact


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Show upstream status for one or more feedstocks.")
    parser.add_argument(
        'feedstock_dir', nargs='*',
        help='one or more feedstock directories determine status for.')
    parser.add_argument(
        "--all", action='store_true',
        help='find the status of all feedstock directories')
    parser.add_argument(
        '--file', '-f', type=str,
        help='file with feedstock directories')
    parser.add_argument(
        '--upstream', default='conda-forge', type=str,
        help="upstream github organization, default is 'conda-forge'")
    parser.add_argument(
        '--base_dir', default='.', type=str,
        help='feedstock base directory, default is current directory')
    parser.add_argument(
        "--no_header", action='store_true',
        help='Do not print header line, helpful when appending to a file')
    return parser.parse_args()


def main():
    args = parse_arguments()
    if args.all:
        pathname = os.path.join(args.base_dir, '*-feedstock')
        feedstock_paths = sorted(glob.glob(pathname))
    else:
        dirs = get_feedstock_dirs(args.feedstock_dir, args.file)
        feedstock_paths = [os.path.join(args.base_dir, d) for d in dirs]
    if not args.no_header:
        print("pkg_name,can_rebase,exact_rebase")
    for feedstock_path in feedstock_paths:
        can_be_rebased, is_exact = can_rebase(feedstock_path, args.upstream)
        pkg_name = (
            feedstock_path
            .replace('./', '')
            .replace('/', '')
            .replace('-feedstock', ''))
        print(f'{pkg_name},{can_be_rebased},{is_exact}')


if __name__ == "__main__":
    main()
