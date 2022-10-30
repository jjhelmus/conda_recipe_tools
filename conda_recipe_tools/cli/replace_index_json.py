#! /usr/bin/env python
""" Replace the index.json file in a conda package. """

import argparse
import json
import os.path
import pathlib
import shutil
import tarfile
import tempfile


def get_pkg_name(index_json):
    """ Return a conda package name from a index.json file. """
    with open(index_json, 'rb') as f:
        info = json.load(f)
    pkg_name = '{name}-{version}-{build}.tar.bz2'.format(**info)
    return pkg_name


def replace_index_json(input_conda_pkg, index_json, output_conda_pkg):
    """ Create a conda package with a new index.json file """
    with tempfile.TemporaryDirectory() as raw_tmp_dir:
        tmp_dir = pathlib.Path(raw_tmp_dir)
        # extract the old tarball
        with tarfile.open(input_conda_pkg, 'r') as input_tfile:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(input_tfile, path=tmp_dir)

        # replace the tarball index.json with the file on the command line
        current_index_json = os.path.join(tmp_dir, 'info', 'index.json')
        shutil.copyfile(index_json, current_index_json)

        # create the new tarball
        # adapted from logic in conda_build/build.py
        def order(f):
            # we don't care about empty files so send them back via 100000
            fsize = os.stat(os.path.join(tmp_dir, f)).st_size or 100000
            # info/* records will be False == 0, others will be 1.
            info_order = int(os.path.dirname(f) != 'info')
            return info_order, fsize

        # add files in order of a) in info directory, b) increasing size so
        # we can access small manifest or json files without decompressing
        # possible large binary or data files
        link_or_file = lambda x: x.is_file() or x.is_symlink()
        files = [f.relative_to(tmp_dir) for f in tmp_dir.rglob('*') if link_or_file(f)]
        with tarfile.open(output_conda_pkg, 'w:bz2') as output_tfile:
            for f in sorted(files, key=order):
                output_tfile.add(os.path.join(tmp_dir, f), f, recursive=False)
    return


def main():
    parser = argparse.ArgumentParser(
        description='Replace the index.json file in a conda package.')
    parser.add_argument('input_conda_pkg', help='conda package to replace')
    parser.add_argument('index_json', help='index.json file')
    parser.add_argument(
        '-o', '--output_conda_pkg', default=None,
        help='output package filename, default is determined from index.json')
    parser.add_argument(
        '-c', '--clobber', action='store_const', const=True, default=False,
        help='clobber output package is present, default is to error out')
    args = parser.parse_args()
    if args.output_conda_pkg is None:
        output_conda_pkg = get_pkg_name(args.index_json)
    else:
        output_conda_pkg = args.output_conda_pkg
    if os.path.exists(output_conda_pkg) and not args.clobber:
        raise IOError('output conda package exists, use --clobber to replace')
    replace_index_json(args.input_conda_pkg, args.index_json, output_conda_pkg)


if __name__ == "__main__":
    main()
