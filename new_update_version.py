#! /usr/bin/env python

import argparse
import os
import re

from collections import defaultdict

import jinja2

import yaml


class NullUndefined(jinja2.Undefined):
    def __unicode__(self):
        return self._undefined_name

    def __getattr__(self, name):
        return "{}.{}".format(self, name)

    def __getitem__(self, name):
        return '{}["{}"]'.format(self, name)


def render_meta_yaml(text):
    """
    Render the meta.yaml with Jinja2 variables.

    Parameters
    ----------
    text : str
        The raw text in conda-forge feedstock meta.yaml file

    Returns
    -------
    str
        The text of the meta.yaml with Jinja2 variables replaced.
    """
    env = jinja2.Environment(undefined=NullUndefined)
    content = env.from_string(text).render(
        os=os,
        environ=defaultdict(str),
        compiler=lambda x: x + "_compiler_stub",
        pin_subpackage=lambda *args, **kwargs: "subpackage_stub",
        pin_compatible=lambda *args, **kwargs: "compatible_pin_stub",
        cdt=lambda *args, **kwargs: "cdt_stub",
    )
    return content


class CondaRecipe(object):
    """
    Representation of a conda recipe meta.yaml file.

    Parameters
    ----------
    meta_filename : str
        Path to the recipe's meta.yaml file.

    """

    def __init__(self, meta_filename):
        """ initalize """
        # read the meta.yaml file for the recipe
        with open(meta_filename) as f:
            self.text = f.read()
        self._render_and_parse()

    def _render_and_parse(self):
        self._rendered = render_meta_yaml(self.text)
        self._parsed = yaml.load(self._rendered)

    def _apply_replacements(self, patterns):
        for pattern, replacement in patterns:
            self.text = re.sub(pattern, replacement, self.text)
        self._render_and_parse()

    def _check_replacement(self, attr, value):
        if str(getattr(self, attr)) != str(value):
            raise AttributeError("{} could not be set".format(attr))

    def _replace_and_check(self, patterns, attr, value):
        self._apply_replacements(patterns)
        self._check_replacement(attr, value)

    @property
    def name(self):
        return self._parsed['package']['name']

    @property
    def version(self):
        return self._parsed['package']['version']

    @version.setter
    def version(self, version):
        patterns = (
            ('version:\s*[A-Za-z0-9._-]+',
             'version: "{version}"'.format(version=version)),

            ('{%\s*set\s+version\s*=\s*[^\s]*\s*%}',
             '{{% set version = "{version}" %}}'.format(version=version)),
        )
        self._replace_and_check(patterns, 'version', version)

    @property
    def hash_type(self):
        source_section = self._parsed['source']
        if 'md5' in source_section:
            hash_type = 'md5'
        elif 'sha256' in source_section:
            hash_type = 'sha256'
        elif 'sha1' in source_section:
            hash_type = 'sha1'
        else:
            hash_type = None
        return hash_type

    @property
    def url(self):
        source_section = self._parsed['source']
        if 'url' in source_section:
            return source_section['url']
        else:
            return None

    @property
    def hash_value(self):
        if self.hash_type is None:
            return None
        else:
            return self._parsed['source'][self.hash_type]

    @hash_value.setter
    def hash_value(self, hash_value):
        hash_type = self.hash_type
        # non-jinja sha256: abcd... and similar replacements
        m = re.search('\s*{}:(.+)'.format(hash_type), self.text)
        if m is None:
            patterns = ((
                '{}:\s*[0-9A-Fa-f]+'.format(hash_type),
                '{}: {}'.format(hash_type, hash_value)),)
        else:
            patterns = ((
                '{}:{}(?=\r\n|\n)'.format(hash_type, m.group(1)),
                '{}: {}'.format(hash_type, hash_value)),)
        # jinja {% set blah = 'hash' %} replacements
        checksum_names = [
            'hash_value', 'hash', 'hash_val', 'sha256sum', 'checksum',
            hash_type]
        base1 = '''{{%\s*set {checkname} = ['"][0-9A-Fa-f]+['"] %}}'''
        base2 = '{{% set {checkname} = "{h}" %}}'
        for cn in checksum_names:
            patterns += ((base1.format(checkname=cn),
                          base2.format(checkname=cn, h=hash_value)),)
        self._replace_and_check(patterns, 'hash_value', hash_value)

    @property
    def build_number(self):
        return self._parsed['build']['number']

    @build_number.setter
    def build_number(self, build_number):
        patterns = (
            ('(?=\s*?)number:\s*([0-9]+)',
             'number: {}'.format(build_number)),
            ('(?=\s*?){%\s*set build_number\s*=\s*"?([0-9]+)"?\s*%}',
             '{{% set build_number = {} %}}'.format(build_number)),
            ('(?=\s*?){%\s*set build\s*=\s*"?([0-9]+)"?\s*%}',
             '{{% set build = {} %}}'.format(build_number)),
        )
        self._replace_and_check(patterns, 'build_number', build_number)

    def __str__(self):
        props = ['name', 'version', 'hash_type', 'hash_value', 'url',
                 'build_number']
        info = '\n'.join(['{}: {}'.format(p, getattr(self, p)) for p in props])
        return info

    def write(self, filename):
        with open(filename, 'w') as f:
            f.write(self.text)


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

    recipe = CondaRecipe('meta.yaml')
    recipe.set_version('1.0.0')
    recipe.write('meta.yaml')


    """
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
    """


if __name__ == "__main__":
    main()
