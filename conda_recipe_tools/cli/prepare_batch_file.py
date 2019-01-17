#! /usr/bin/env python
# prepare a batch file for submission via c3i batch

import argparse
import subprocess
import sys
from pathlib import Path
from subprocess import PIPE


def main():
    # parse args
    parser = argparse.ArgumentParser(
        description='Prepare a batch file for submission via c3i batch')
    parser.add_argument(
        '--batch_file', default='batch_file.txt',
        help='filename of batch file to create, default is batch_file.txt')
    parser.add_argument(
        '--base_dir', default='.', type=str,
        help='feedstock base directory, default is the current directory')
    parser.add_argument(
        '--stdout', action='store_true',
        help='print contents of the batch file to stdout')
    args = parser.parse_args()

    # find the list of changed feedstocks
    cmd = ['git', '-C', args.base_dir, 'ls-files', '-m']
    complete = subprocess.run(cmd, stdout=PIPE, check=True)
    changed = complete.stdout.decode('utf-8').split()
    feedstocks_changed = set([Path(c).parts[0] for c in changed])

    # write the batch file
    if args.stdout:
        for i in feedstocks_changed:
            print(i)
    else:
        with open(args.batch_file, 'w') as f:
            for i in feedstocks_changed:
                f.write(i + '\n')
    sys.exit(0)


if __name__ == "__main__":
    main()
