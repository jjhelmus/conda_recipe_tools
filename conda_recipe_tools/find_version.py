""" Looks version for projects. """

import re

from bs4 import BeautifulSoup

import feedparser

import requests

try:
    from packaging.version import parse as parse_version
except ImportError:
    from pip._vendor.packaging.version import parse as parse_version


class NoURLError(Exception):
    # Raised when no url is passed.
    pass

class NoVersionError(Exception):
    # Raised when we cannot find a version.
    pass

class NoCustomLookupError(Exception):
    # Raised when there is no custom function implemented.
    pass


def find_latest_version(name, update_type='pypi', extra=None, extra_str=None):
    """ Find the latest version for a given project.

    Parameters
    ----------
    name : str
        Name of project to lookup version for
    update_type : str
        How the latest version should be determined.  Option are:
            * pypi : Determine version from PyPI.
            * url : Look up version by parsing a URL.
            * github : Find version from GitHub release.
            * custom : Use one of the custom lookup function.
    extra : None or dict
        Additional parameters passed to the update method that are used when
        determining the latest version.
    extra_str : None or str
        A string encoding the extra dictionary parameters with format:
        key1=value1;key2=value2
        If extra_str is not None, the extra parameter is ignored.

    Returns
    -------
    version : Version or None
        The latest version, None when this cannot be determined.

    """
    if extra_str is not None:
        if extra_str == '':
            extra = {}
        else:
            extra = dict(s.split('=') for s in extra_str.split(';'))
    if extra is None:
        extra = {}
    if update_type == 'pypi':
        return _find_latest_version_pypi(name, extra)
    elif update_type == 'url':
        return _find_latest_version_url(name, extra)
    elif update_type == 'github':
        return _find_latest_version_github(name, extra)
    elif update_type == 'gitlab':
        return _find_latest_version_gitlab(name, extra)
    elif update_type == 'custom':
        if name in CUSTOM:
            return CUSTOM[name]()
        else:
            raise NoCustomLookupError(f'No lookup implemented for {name}')
    else:
        return f'skipped-{update_type}-{extra}'


def _find_latest_version_pypi(name, extra):
    pypi_name = extra.get('pypi_name', name)
    url = 'https://pypi.org/pypi/{}/json'.format(pypi_name)
    r = requests.get(url)
    payload = r.json()
    return parse_version(payload['info']['version'])


def _find_latest_version_url(name, extra):
    url = extra.get('url')
    regex = extra.get('regex', name+'-(.*).tar.gz')
    filter_prerelease = bool(extra.get('filter_pre', False))
    raw = False
    if 'ver_format' in extra:
        ver_format = extra.get('ver_format')
        raw = True
    if url is None:
        raise NoURLError('url is none')
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
        raise NoVersionError("No version was found.")
    if filter_prerelease:
        versions = [v for v in versions if not v.is_prerelease]
    latest_version = max(versions)
    if raw:
        latest_version = parse_version(latest_version)
    return latest_version


def _find_latest_version_github(name, extra):
    org = extra.get('gh_org', name)
    repo = extra.get('gh_repo', name)
    url = "https://github.com/{}/{}/releases.atom".format(org, repo)
    return _max_version_from_feed(url)


def _max_version_from_feed(url):
    data = feedparser.parse(url)
    raw_versions = [e['link'].split('/')[-1] for e in data['entries']]
    clean_versions = [_clean_version_str(v) for v in raw_versions]
    versions = [parse_version(v) for v in clean_versions]
    if _allow_post_or_pre(url):
        filtered = versions
    else:
        filtered = [v for v in versions if not
                    (v.is_prerelease or v.is_postrelease)]
    if len(filtered) == 0:
        raise NoVersionError('No version was found.')
    return max(filtered)


def _clean_version_str(ver):
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
        'zopfli-',
        'mpir-',
    ]
    for prefix in ver_prefix_remove:
        if ver.startswith(prefix):
            ver = ver[len(prefix):]
    return ver


def _allow_post_or_pre(url):
    allowed_post_or_pre = [
        'NVIDIA/nccl',
    ]
    return any(elem in url for elem in allowed_post_or_pre)


def _find_latest_version_gitlab(name, extra):
    org = extra.get('gl_org', name)
    repo = extra.get('gl_repo', name)
    url = "https://gitlab.com/api/v4/projects/{}%2F{}/releases".format(org, repo)
    data = requests.get(url).json()
    raw_versions = [e['tag_name'] for e in data]
    clean_versions = [_clean_version_str(v) for v in raw_versions]
    versions = [parse_version(v) for v in clean_versions]
    if _allow_post_or_pre(url):
        filtered = versions
    else:
        filtered = [v for v in versions if not
                    (v.is_prerelease or v.is_postrelease)]
    if len(filtered) == 0:
        raise NoVersionError('No version was found.')
    return max(filtered)


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
        raise NoVersionError('No version was found.')
    return max(versions)


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
        raise NoVersionError('No version was found.')
    return max(versions)


def _find_latest_hdfeos2():
    from ftplib import FTP
    try:
        ftp = FTP('edhs1.gsfc.nasa.gov')
        ftp.login()
        files = ftp.nlst('edhs/hdfeos/latest_release/')
        ftp.close()
    except:
        return None
    for filename in files:
        match = re.match('(?:.*)HDF-EOS(.*)v1.00.tar.Z', filename)
        if match:
            return parse_version(match.group(1))
    return None


CUSTOM = {
    'graphviz': _find_latest_graphviz,
    'hdfeos2': _find_latest_hdfeos2,
    'tbb': _find_latest_tbb,
}
