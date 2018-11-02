#!/usr/bin/env python
import argparse
import csv
import datetime
import os.path
import subprocess

from collections import defaultdict

import jinja2

import yaml

PACKAGES_TO_SKIP = [
    'boto3',
    'botocore',
]
MAX_BUILDS = '8'


# borrowed from update_recipe
class NullUndefined(jinja2.Undefined):
    def __unicode__(self):
        return self._undefined_name

    def __getattr__(self, name):
        return "{}.{}".format(self, name)

    def __getitem__(self, name):
        return '{}["{}"]'.format(self, name)


# borrowed from update_recipe
def render_meta_yaml(text):
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


# borrowed from update_recipe, minimal version
class CondaRecipe(object):

    def __init__(self, meta_filename):
        """ initalize """
        # read the meta.yaml file for the recipe
        with open(meta_filename) as f:
            self.text = f.read()
        self._render_and_parse()

    def _render_and_parse(self):
        self._rendered = render_meta_yaml(self.text)
        self._parsed = yaml.load(self._rendered)

    @property
    def name(self):
        return self._parsed['package']['name']

    @property
    def version(self):
        return self._parsed['package']['version']


def srun(cmd, check=False):
    """ run a commmand in a shell """
    return subprocess.run(cmd, shell=True, check=check)


def get_packages_to_process(csv_filename):
    """ Return a dictionary of package: version to process. """
    to_process = {}
    with open(csv_filename) as csvfile:
        reader = csv.DictReader(filter(lambda x: x[0] != "#", csvfile))
        for row in reader:
            name = row['package_name']
            version = row['new_version']
            if name in PACKAGES_TO_SKIP:
                continue
            if version == 'None':
                continue
            to_process[name] = version
    return to_process


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Start Grimlock")
    parser.add_argument(
        '--csv', action='store', default='new_packages.csv',
        help='CSV file containing packages to process')
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Prepare for batch builds but do not submit')
    return parser.parse_args()


def main():
    args = parse_arguments()
    to_process = get_packages_to_process(args.csv)

    # update recipes, record those which were successful
    good_feedstocks = []
    for name, version in to_process.items():

        feedstock_name = "{}-feedstock".format(name)
        meta_yaml = os.path.join(feedstock_name, 'recipe', 'meta.yaml')

        # update the recipes
        srun("sync_cf {}".format(feedstock_name))
        srun("update_recipe --version {} --meta {}".format(version, meta_yaml))

        # check if the update was successful
        try:
            recipe = CondaRecipe(meta_yaml)
            if recipe.version == version:
                good_feedstocks.append(feedstock_name)
        except:
            continue

    # create recipe_clobber.yaml files
    for feedstock_name in good_feedstocks:
        srun("create_clobber {}".format(feedstock_name))

    # create grimlock_batch_file_20YYMMDD.txt
    dt = datetime.datetime.now()
    batch_file_name = dt.strftime('grimlock_batch_file_%Y%m%d.txt')
    label_prefix = dt.strftime('grimlock_%Y%m%d_')
    with open(batch_file_name, 'w') as f:
        for feedstock_name in good_feedstocks:
            f.write(feedstock_name + '\n')

    # run c3i batch
    cmd = 'c3i batch {} --max-builds {} --label-prefix {}'.format(
        batch_file_name, MAX_BUILDS, label_prefix)
    if args.dry_run:
        print("Dry run, no submission. Command to start builds is:")
        print(cmd)
    else:
        srun(cmd)


if __name__ == "__main__":
    main()
