""" Utilities for working with conda repodata """

import bz2
import json
import os.path

import requests
try:
    from packaging.version import parse as parse_version
except ImportError:
    from pip._vendor.packaging.version import parse as parse_version


CRT_CACHE_DIR = os.path.expanduser(
    os.path.join('~', '.cache', 'conda_recipe_tools'))


def fetch_repodata(channel, subdir):
    """
    Fetch repodata for a given channel and subdir

    Parameters
    -----------
    channel : str
        Channel to fetch repodata. 'main' and 'free' will fetch repodata from
        repo.anaconda.com, all others from conda.anaconda.org.
    subdir : str
        Subdir to fetch repodata

    Returns
    -------
    repodata : dict
        Dictionary contain repodata.json contents.

    """
    # read in the possibly cached repodata
    cache_filename = f"repodata_{channel}_{subdir}.json"
    cache_dir = os.path.join(CRT_CACHE_DIR, 'repodata')
    cache_path = os.path.join(cache_dir, cache_filename)
    try:
        with open(cache_path) as fh:
            repodata = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        repodata = {}
    if channel in ["main", "free"]:
        url = f"https://repo.anaconda.com/pkgs/{channel}/{subdir}/repodata.json.bz2"
    else:
        url = f"https://conda.anaconda.org/{channel}/{subdir}/repodata.json.bz2"
    etag = repodata.pop('_etag', None)
    if etag is not None:
        headers = {'If-None-Match': etag}
    else:
        headers = {}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    if resp.status_code == 304:  # no change since last d/l
        return repodata
    repodata = json.loads(
        bz2.BZ2Decompressor()
        .decompress(resp.content)
    )
    repodata["_etag"] = resp.headers.get("etag")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w') as fh:
        json.dump(repodata, fh)
    repodata.pop("_etag")
    return repodata


def newest_version_for_subdir(channel, subdir):
    """
    Return the newest versions of all packages in a channel subdir

    Parameters
    -----------
    channel : str
        Channel to examine. 'main' and 'free' will fetch repodata from
        repo.anaconda.com, all others from conda.anaconda.org.
    subdir : str
        Subdir to examine.

    Returns
    -------
    newest : dict
        Dictionary mapping package names to Version objects with the newest
        version of each package in the subdir for the specified channel.

    """
    repodata = fetch_repodata(channel, subdir)
    newest = {}
    for pkg_info in repodata['packages'].values():
        name = pkg_info['name']
        version = parse_version(pkg_info['version'])
        if name not in newest:
            newest[name] = version
        else:
            newest[name] = max(version, newest[name])
    return newest


def newest_version_for_channel(channel, subdirs=None):
    """
    Find the newest versions of all packages in a channel in any subdir

    Parameters
    -----------
    channel : str
        Channel to examine. 'main' and 'free' will fetch repodata from
        repo.anaconda.com, all others from conda.anaconda.org.
    subdirs : list of str or None
        Subdirs to examine. None will examine a standard set of subdirs:
        'linux-64', 'win-32', 'win-64', 'osx-64', 'linux-ppc64le', and 'noarch'

    Returns
    -------
    newest_for_channel : dict
        Dictionary mapping package names to Version objects with the newest
        version of each package in any subdir for the specified channel.
    newest_by_subdir : dict of dicts
        Dictionary mapping subdir names to dictionaries with the newest
        packages for that subdir.

    """
    if subdirs is None:
        subdirs = ['linux-64', 'win-32', 'win-64', 'osx-64', 'linux-ppc64le', 'noarch']
    newest_by_subdir = {s: newest_version_for_subdir(channel, s) for s in subdirs}
    newest_for_channel = {}
    for subdir in subdirs:
        newest = newest_version_for_subdir(channel, subdir)
        newest_by_subdir[subdir] = newest
        for pkg, version in newest.items():
            if pkg not in newest_for_channel:
                newest_for_channel[pkg] = version
            else:
                newest_for_channel[pkg] = max(version, newest_for_channel[pkg])
    return newest_for_channel, newest_by_subdir
