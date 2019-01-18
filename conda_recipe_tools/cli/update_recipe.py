#! /usr/bin/env python

import argparse

from conda_recipe_tools.recipe import CondaRecipe, find_hash

import requests


# This function is of limited use, it only looks up version for PyPI packages,
# for a more complete solution see the find_version module.
def find_latest_version(recipe):
    if recipe.url.startswith('https://pypi'):
        project, filename = recipe.url.split('/')[-2:]
        return _find_latest_version_pypi(project)
    else:
        return None


def _find_latest_version_pypi(project):
    url = 'https://pypi.org/pypi/{}/json'.format(project)
    r = requests.get(url)
    payload = r.json()
    return payload['info']['version']


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Update a conda recipe to a given version")
    parser.add_argument(
        '--meta', '-m', action='store', default=None,
        help="meta.yaml file to update, default will try common locations")
    parser.add_argument(
        '--version', '-v', action='store', default=None,
        help="version to update the recipe to, defaults is to latest.")
    parser.add_argument(
        '--hash', action='store', default=None,
        help="hash value for recipe, default will determine from source url.")
    parser.add_argument(
        '--build_number', action='store', default='0',
        help="build_number for recipe.")
    return parser.parse_args()


def main():

    args = parse_arguments()
    if args.meta is None:
        try:
            recipe = CondaRecipe('meta.yaml')
            args.meta = 'meta.yaml'
        except FileNotFoundError:
            recipe = CondaRecipe('recipe/meta.yaml')
            args.meta = 'recipe/meta.yaml'
    else:
        recipe = CondaRecipe(args.meta)

    # update the version
    if args.version is None:
        new_version = find_latest_version(recipe)
    else:
        new_version = args.version
    if new_version is None:
        raise ValueError('cannot determine version')
    if recipe.version == new_version:
        print("Recipe already at version:", new_version)
        return
    recipe.version = new_version

    # update the hash
    if args.hash is None:
        recipe.hash_value = find_hash(recipe)
    else:
        recipe.hash_value = args.hash

    # update the build_number
    if args.build_number is not None:
        recipe.build_number = args.build_number

    recipe.write(args.meta)
    print("Updated", args.meta, "to version", recipe.version)


if __name__ == "__main__":
    main()
