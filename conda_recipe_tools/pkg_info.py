""" Read in package infomation. """

import csv


def read_pkg_info(pkg_info_filename):
    """ Read in package information from a CSV file. """
    pkg_info = {}
    with open(pkg_info_filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['package_name']
            update_type = row['update_type']
            extra_str = row['update_extra']
            if extra_str == '':
                extra = {}
            else:
                extra = dict(s.split('=') for s in extra_str.split(';'))
            pkg_info[name] = {'update_type': update_type}
            pkg_info[name]['update_extra'] = extra
    return pkg_info
