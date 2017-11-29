#! /usr/bin/env python
import argparse
import json
import re
from urllib.request import urlopen

try:
    from packaging.version import parse as parse_version
except ImportError:
    from pip._vendor.packaging.version import parse as parse_version

import jinja2
import yaml


class GitHubSource(object):

    RELEASE_URL = 'https://api.github.com/repos/{user}/{repo}/releases'
    def __init__(self, user, repo):
        self.releases = json.load(open('./github_releases.json'))

    @property
    def latest_version(self):
        versions = [parse_version(r['name']) for r in self.releases]
        filtered = [v for v in versions if not v.is_prerelease]
        if len(filtered) == 0:
            return None
        return str(max(filtered))

    def get_hash(self, version, filename, hash_type):
        pass


class PyPISource(object):

    def __init__(self, name):
        self.name = name
        url = 'https://pypi.io/pypi/' + self.name + '/json'
        response = urlopen(url)
        self._info = json.loads(response.read().decode('utf8'))

    @property
    def latest_version(self):
        all_releases = self._info['releases'].keys()
        versions = [parse_version(s) for s in all_releases]
        filtered = [v for v in versions if not v.is_prerelease]
        if len(filtered) == 0:
            return None
        return str(max(filtered))

    def get_hash(self, version, filename, hash_type):
        release_info = self._info['releases'][version]
        entry = [e for e in release_info if e['filename'] == filename][0]
        hash_value = entry['digests'][hash_type]
        return hash_value


class CondaRecipe(object):
    """
    Representation of a conda recipe meta.yaml file.

    Parameters
    ----------
    meta_filename : str
        meta.yaml path.

    """

    def __init__(self, meta_filename):
        """ initalize """
        # read the meta.yaml file for the recipe
        with open(meta_filename) as f:
            self._lines = f.readlines()

    @property
    def _info(self):
        """ Dictionary of recipe after rendering using jinja2. """
        text = ''.join(self._lines)
        defaults = {'compiler': lambda x: ''}
        rendered_text = jinja2.Template(text).render(defaults)
        return yaml.load(rendered_text)

    @property
    def name(self):
        """ package name. """
        return self._info['package']['name']

    @property
    def version(self):
        return self._info['package']['version']

    @version.setter
    def version(self, version):
        quoted_version = '"' + version + '"'
        pattern = '(?<=set version = ).*(?= %})'
        self._lines = [re.sub(pattern, quoted_version, l) for l in self._lines]
        if self._info['package']['version'] != version:
            raise AttributeError("version could not be set")

    @property
    def hash_type(self):
        source_section = self._info['source']
        if 'md5' in source_section:
            hash_type = 'md5'
        elif 'sha256' in source_section:
            hash_type = 'sha256'
        else:
            hash_type = None
        return hash_type

    @property
    def hash_value(self):
        return self._info['source'][self.hash_type]

    @hash_value.setter
    def hash_value(self, hash_value):
        hash_type = self.hash_type
        lines = self._lines
        # replace jinja templated hash tempates
        quoted_hash = '"' + hash_value + '"'
        pattern = '(?<=set hash_val = ).*(?= %})'
        lines = [re.sub(pattern, quoted_hash, l) for l in lines]
        pattern = '(?<=set hash_value = ).*(?= %})'
        lines = [re.sub(pattern, quoted_hash, l) for l in lines]
        pattern = '(?<=set hash = ).*(?= %})'
        lines = [re.sub(pattern, quoted_hash, l) for l in lines]
        if hash_type == 'sha256':
            pattern = '(?<=set sha256 = ).*(?= %})'
            lines = [re.sub(pattern, quoted_hash, l) for l in lines]
        if hash_type == 'md5':
            pattern = '(?<=set md5 = ).*(?= %})'
            lines = [re.sub(pattern, quoted_hash, l) for l in lines]

        # replace yaml hash values
        if hash_type == 'sha256':
            pattern = '(?<=sha256: )[0-9A-Fa-f]+'
            lines = [re.sub(pattern, hash_value, l) for l in lines]
        if hash_type == 'md5':
            pattern = '(?<=md5: )[0-9A-Fa-f]+'
            lines = [re.sub(pattern, hash_value, l) for l in lines]
        self._lines = lines
        if self._info['source'][self.hash_type] != hash_value:
            raise AttributeError("hash_value could not be set")

    @property
    def url_filename(self):
        url = self._info['source']['url']
        filename = url.split('/')[-1]
        return filename

    @property
    def source(self):
        source_url = self._info['source']['url']
        if source_url.startswith('https://pypi.io'):
            return PyPISource(self.name)
        elif source_url.startswith('https://github.com'):
            pattern = '(?<=https://github.com/)(.*?)/(.*?)/'
            user, repo = re.search(pattern, source_url).groups()
            return GitHubSource(user, repo)
        else:
            return None

    def write(self, filename):
        with open(filename, 'wb') as f:
            f.write(''.join(self._lines).encode('utf8'))


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Update a conda recipe to a given version")
    parser.add_argument(
        '--meta', '-m', action='store', default='meta.yaml',
        help="path to the recipe's meta.yaml files.")
    parser.add_argument(
        '--version', '-v', action='store', default=None,
        help="version to update the recipe to, defaults is to latest.")
    return parser.parse_args()


def main():
    args = parse_arguments()
    recipe = CondaRecipe(args.meta)
    source = recipe.source

    # update the version
    if args.version is None:
        recipe.version = source.latest_version
    else:
        recipe.version = args.version

    # update the hash
    hash_value = source.get_hash(
        recipe.version, recipe.url_filename, recipe.hash_type)
    recipe.hash_value = hash_value
    recipe.write(args.meta)
    print("Updated", args.meta, "to version", recipe.version)


if __name__ == "__main__":
    main()
