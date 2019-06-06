""" Utility functions. """


def get_feedstock_dirs(feedstock_dirs, feedstock_file):
    """ Return a list of feedstock directories to examine. """
    if feedstock_file is None:
        return feedstock_dirs
    # skip comments (#) and blank lines
    is_valid = lambda x: not x.startswith('#') and len(x.strip())
    with open(feedstock_file) as f:
        feedstock_dirs = [l.strip() for l in f if is_valid(l)]
    return feedstock_dirs
