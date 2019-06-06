#! /usr/bin/env python
# create report with recipe diffs for a series of feedstocks

import argparse
import os.path
import sys

from jinja2 import Template

from conda_recipe_tools.recipe import CondaRecipe
from conda_recipe_tools.git import GitRepo
from conda_recipe_tools.util import get_feedstock_dirs

from pygments import highlight
from pygments.lexers import DiffLexer
from pygments.formatters import HtmlFormatter


def make_report(report_entries, template_filename, outfile):
    if template_filename is None:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        template_filename = os.path.join(this_dir, 'report_template.html')
    with open(template_filename) as f:
        template_text = f.read()
    report_template = Template(template_text)
    report_text = report_template.render(report_entries=report_entries)
    if outfile is None:
        print(report_text)
    else:
        with open(outfile, 'w') as f:
            f.write(report_text)


def get_diff_html(feedstock_path, remote_org):
    repo = GitRepo(feedstock_path)
    diff_cf_text = repo.diff(f'{remote_org}/master', 'recipe')
    diff_origin_text = repo.diff('origin/master', 'recipe')

    formatter = HtmlFormatter(cssclass='diff')
    diff_cf_html = highlight(diff_cf_text, DiffLexer(), formatter)
    diff_origin_html = highlight(diff_origin_text, DiffLexer(), formatter)
    return diff_cf_html, diff_origin_html


def create_report_entry(
            feedstock_name, label_prefix, concourse_url, base_dir, remote_org):
    feedstock_path = os.path.join(base_dir, feedstock_name)
    recipe_path = os.path.join(feedstock_path, 'recipe', 'meta.yaml')
    diff_cf_html, diff_origin_html = get_diff_html(feedstock_path, remote_org)
    pipeline_label = label_prefix + feedstock_name.rsplit('-', 1)[0]
    recipe = CondaRecipe(recipe_path)
    entry = {
        'pkg_name': recipe.name,
        'feedstock_name': feedstock_name,
        'version': recipe.version,
        'concourse_url': concourse_url + '/pipeline/' + pipeline_label,
        'cf_url': f'https://github.com/{remote_org}/{feedstock_name}',
        'diff_cf_html': diff_cf_html,
        'diff_origin_html': diff_origin_html,
        'id_diff_cf': f'id_{feedstock_name}_diff_cf',
        'id_diff_origin': f'id_{feedstock_name}_diff_origin',
        'id_checkbox': f'id_{feedstock_name}_checkbox',
    }
    return entry


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create a report with recipe diffs for feedstocks')
    parser.add_argument(
        'feedstock_dir', nargs='*',
        help='one or more feedstock directories for the report')
    parser.add_argument(
        '--file', '-f', type=str,
        help='file with feedstock directories to include in report')
    parser.add_argument(
        '--outfile', help='html file to write report to, default is stdout')
    parser.add_argument(
        '--remote-org', default='conda-forge', type=str,
        help='GitHub organization to base diff upon.')
    parser.add_argument(
        '--base_dir', default='.', type=str,
        help='feedstock base directory, default is current directory')
    parser.add_argument(
        '--template',
        help="Report template, default is template included in package.")
    parser.add_argument(
        '--label-prefix', default='autobot_',
        help="prefix used for pipeline labels.")
    parser.add_argument(
        '--concourse_url',
        default='https://concourse.example.com/teams/main',
        help="Concourse URL")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    feedstock_dirs = get_feedstock_dirs(args.feedstock_dir, args.file)

    # create report entires
    report_entries = []
    for feedstock_name in feedstock_dirs:
        report_entries.append(create_report_entry(
            feedstock_name, args.label_prefix, args.concourse_url,
            args.base_dir, args.remote_org))

    # write report
    make_report(report_entries, args.template, args.outfile)
    return 0


if __name__ == "__main__":
    sys.exit(main())
