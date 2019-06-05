""" Interactions with git repositories. """

import logging
import subprocess
from subprocess import PIPE


class GitRepo(object):

    def __init__(self, path):
        self._path = path

    def _git(self, git_args, check=True):
        args = ['git', '-C', self._path] + git_args
        logging.debug('command: ' + ' '.join(args))
        complete = subprocess.run(args, stdout=PIPE, stderr=PIPE)
        logging.debug('returncode: ' + str(complete.returncode))
        logging.debug('stdout: ' + complete.stdout.decode('utf-8'))
        logging.debug('stderr: ' + complete.stderr.decode('utf-8'))
        if check:
            complete.check_returncode()
        return complete

    def checkout(self, branch='master'):
        return self._git(['checkout', branch])

    def fetch(self, remote='origin'):
        return self._git(['fetch', remote])

    def reset_hard(self, remote='origin', branch='master'):
        return self._git(['reset', '--hard', '%s/%s' % (remote, branch)])

    def rebase(self, remote, branch='master', check=True):
        return self._git(['rebase', '%s/%s' % (remote, branch)], check)

    def rebase_abort(self, check=True):
        self._git(['rebase', '--abort'], check)

    def push(self, remote='origin', local_branch='master',
             remote_branch='master', force=False, check=True):
        refspec = '{src}:{dst}'.format(src=local_branch, dst=remote_branch)
        if force:
            return self._git(['push', '--force', remote, refspec], check)
        return self._git(['push', remote, refspec], check)

    def branch(self, branch_name):
        return self._git(['checkout', '-b', branch_name])

    def branch_from(self, branch_name, start_branch='master'):
        return self._git(['checkout', '-B', branch_name, start_branch])

    def branch_delete(self, branch_name):
        return self._git(['branch', '-D', branch_name])

    def diff(self, commit=None, path=None):
        cmd = ['diff']
        if commit is not None:
            cmd.append(commit)
            if path is not None:
                cmd.append(path)
        out = self._git(cmd)
        return out.stdout.decode('utf-8')

    def ls_files_modified(self):
        out = self._git(['ls-files', '-m'])
        return out.stdout.decode('utf-8').split()

    @property
    def commit_hash(self):
        """ commit hash for the current HEAD """
        out = self._git(['rev-parse', 'HEAD'])
        return out.stdout.decode('utf-8').strip()


class NotFeedstockRepo(Exception):
    pass


class FeedStock(GitRepo):

    def __init__(self, path, feedstock_name=None):
        super(FeedStock, self).__init__(path)
        if feedstock_name is None:
            out = self._git(['config', '--get', 'remote.origin.url'])
            origin_url = out.stdout.decode('utf-8').strip()
            feedstock_name = origin_url.split('/')[-1]
            if feedstock_name.endswith('.git'):
                feedstock_name = feedstock_name[:-4]
        if not feedstock_name.endswith('feedstock'):
            raise NotFeedstockRepo('not a feedstock: %s' % (feedstock_name))
        self._feedstock_name = feedstock_name

    def add_remote(self, org, remote_name=None, check=True):
        url = 'https://github.com/%s/%s' % (org, self._feedstock_name)
        if remote_name is None:
            remote_name = org
        self._git(['remote', 'add', remote_name, url], check=check)
