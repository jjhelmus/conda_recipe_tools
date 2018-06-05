#! /usr/bin/env python
# Open GitHub repos

import argparse
import webbrowser

URL_NO_ORG = 'https://github.com/{org}/'
URL_WITH_ORG = 'https://github.com/{org}/{repo_name}'

def main():
    parser = argparse.ArgumentParser(description='Open a Github repository')
    parser.add_argument(
        'repos', type=str, nargs='+',
        help='Repositories to open, syntax is org or org::project')
    args = parser.parse_args()

    for repo in args.repos:
        if '::' in repo:
            org, repo_name = repo.split('::')
            url = URL_WITH_ORG.format(org=org, repo_name=repo_name)
        else:
            url = URL_NO_ORG.format(org=repo)
        webbrowser.open(url)


if __name__ == "__main__":
    main()
