#! /usr/bin/env python
""" Extract the index.json file from a conda package. """

import argparse
import tarfile


def extract_index_json(conda_pkg, outfile):
    """ Extract the index.json file from a conda package. """
    with tarfile.open(conda_pkg, 'r') as tfile:
        with tfile.extractfile('info/index.json') as efile:
            with open(outfile, 'wb') as f:
                f.write(efile.read())


def main():
    parser = argparse.ArgumentParser(
        description='Extract the index.json file from a conda package.')
    parser.add_argument('conda_pkg', help='conda package to extract from.')
    parser.add_argument(
        '-o', '--outfile', default='index.json',
        help='filename to extract index.json')
    args = parser.parse_args()
    extract_index_json(args.conda_pkg, args.outfile)


if __name__ == "__main__":
    main()
