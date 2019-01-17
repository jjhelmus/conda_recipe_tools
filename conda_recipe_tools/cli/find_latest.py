#! /usr/bin/env python
import argparse
import csv
import re

from bs4 import BeautifulSoup
import feedparser
import requests

try:
    from packaging.version import parse as parse_version
except ImportError:
    from pip._vendor.packaging.version import parse as parse_version


def find_latest_version_github(name, extra):
    org = extra.get('gh_org', name)
    repo = extra.get('gh_repo', name)
    url = "https://github.com/{}/{}/releases.atom".format(org, repo)
    return max_version_from_feed(url)


def max_version_from_feed(url):
    data = feedparser.parse(url)
    raw_versions = [e['link'].split('/')[-1] for e in data['entries']]
    clean_versions = [clean_version_str(v) for v in raw_versions]
    versions = [parse_version(v) for v in clean_versions]
    filtered = [v for v in versions if not
                (v.is_prerelease or v.is_postrelease)]
    if len(filtered) == 0:
        return None
    return max(filtered)


def clean_version_str(ver):
    ver_prefix_remove = [
        'release-',
        'releases%2F',
        'rel%2Frelease-',
        'v',
        'r',
        'version-',
        'cyrus-sasl-',
        'gd-',
        'apache-parquet-cpp-',
        'apache-arrow-',
        'LMDB_',
        'xar-',
    ]
    for prefix in ver_prefix_remove:
        if ver.startswith(prefix):
            ver = ver[len(prefix):]
    return ver


def find_latest_version_pypi(name, extra):
    pypi_name = extra.get('pypi_name', name)
    url = 'https://pypi.org/pypi/{}/json'.format(pypi_name)
    r = requests.get(url)
    payload = r.json()
    return payload['info']['version']


def find_latest_version_url(name, extra):
    url = extra.get('url')
    regex = extra.get('regex', name+'-(.*).tar.gz')
    filter_prerelease = bool(extra.get('filter_pre', False))
    raw = False
    if 'ver_format' in extra:
        ver_format = extra.get('ver_format')
        raw = True
    if url is None:
        return None
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    versions = []
    for link in soup.find_all('a', href=True):
        match = re.match(regex, link['href'])
        if match:
            if raw:
                versions.append(ver_format.format(*match.groups()))
            else:
                ver_str = match.group(1)
                versions.append(parse_version(ver_str))
    if len(versions) == 0:
        return None
    if filter_prerelease:
        versions = [v for v in versions if not v.is_prerelease]
    latest_version = max(versions)
    return str(latest_version)


def _find_latest_tbb():
    url = 'https://github.com/01org/tbb/releases'
    regex = '(?:.*)/([\d_U]+).tar.gz'
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    versions = []
    for link in soup.find_all('a', href=True):
        match = re.match(regex, link.get('href'))
        if match:
            raw_ver_str = match.group(1)
            if '_U' in raw_ver_str:
                # YYYY_UX
                match2 = re.match('(\d+)_U(\d+)', raw_ver_str)
                ver_str = '{}.{}'.format(*match2.groups())
            else:
                # YYYY
                ver_str = raw_ver_str + '.0'
            versions.append(parse_version(ver_str))
    if len(versions) == 0:
        return None
    return str(max(versions))


def _find_latest_graphviz():
    url = "https://graphviz.gitlab.io/_pages/Download/Download_source.html"
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    regex = 'graphviz-(.*).tar.gz'
    versions = []
    for link in soup.find_all('a', href=True):
        match = re.match(regex, link.contents[0])
        if match:
            ver_str = match.group(1)
            # skip long developement snapshots
            if len(ver_str) > 10:
                continue
            versions.append(parse_version(ver_str))
    if len(versions) == 0:
        return None
    return str(max(versions))


def _find_latest_hdfeos2():
    from ftplib import FTP
    ftp = FTP('edhs1.gsfc.nasa.gov')
    ftp.login()
    files = ftp.nlst('edhs/hdfeos/latest_release/')
    ftp.close()
    for filename in files:
        match = re.match('(?:.*)HDF-EOS(.*)v1.00.tar.Z', filename)
        if match:
            return match.group(1)
    return None


CUSTOM = {
    'graphviz': _find_latest_graphviz,
    'hdfeos2': _find_latest_hdfeos2,
    'tbb': _find_latest_tbb,
}


def find_latest_version(name, info):
    update_type = info['update_type']
    extra = info['update_extra']
    if update_type == 'pypi':
        return find_latest_version_pypi(name, extra)
    elif update_type == 'url':
        return find_latest_version_url(name, extra)
    elif update_type == 'github':
        return find_latest_version_github(name, extra)
    elif update_type == 'custom':
        if name in CUSTOM:
            return CUSTOM[name]()
        else:
            return None
    else:
        return None


def read_pkg_info(pkg_info_filename):
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


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Find the latest version of packages")
    parser.add_argument(
        "--pkg_info", action='store', default='pkg_info.csv',
        help='file containing specification on how to find package versions')
    parser.add_argument(
        'packages', nargs='*',
        help='packages to check, leave blank to check all packages')
    return parser.parse_args()


def main():
    args = parse_arguments()
    pkg_info = read_pkg_info(args.pkg_info)
    if len(args.packages):
        names_to_check = args.packages
    else:
        names_to_check = sorted(pkg_info.keys())
    print('package_name,latest_version')
    for name in names_to_check:
        latest_version = find_latest_version(name, pkg_info[name])
        print(f'{name},{latest_version}')


if __name__ == "__main__":
    main()
