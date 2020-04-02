import sublime, sublime_plugin

from urllib.parse import urlparse
import os
import re
import subprocess


class CopyGithubLinkCommand(sublime_plugin.TextCommand):
    def run_git(self, cmd, cwd):
        print(cmd, cwd)
        try:
            p = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=cwd)
            result = p.communicate()
            output = result[0].decode('utf-8').strip()
            print('output: %s' % output)
        except Exception as e:
            print('Error running %s: %s' % (cmd, e))
            return
        return output


    def get_repo_url(self):
        filename = self.view.file_name()
        if not filename or len(filename) == 0:
            sublime.status_message('Can\'t copy: No filename for view.')
            return
        remote = self.run_git(['git', 'config', '--get', 'remote.origin.url'], os.path.dirname(filename))
        if not remote:
            return
        if remote[:4] == 'git@':
            # ssh remote. transform to https
            p = re.compile('^git@(?P<host>[^:]+):(?P<path>.*)\.git$')
            m = p.match(remote)
            if not m:
                print('Unable to parse remote url %s' % remote)
                return
            host = m.group('host')
            path = m.group('path')
            remote = 'https://%s/%s' % (host, path)
        print('parsed remote %s' % remote)
        u = urlparse(remote)

        return remote
  

    def run(self, edit):
        filename = self.view.file_name()
        if len(filename) == 0:
            sublime.status_message('Can\'t copy: No filename for view.')
            return

        dirname = os.path.dirname(filename)
        branchname = self.run_git(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], dirname)
        project_dir = self.run_git(['git', 'rev-parse', '--show-toplevel'], dirname)
        relpath = self.run_git(['git', 'ls-files', '--error-unmatch', filename], project_dir)
        repo_url = self.get_repo_url()
        if not repo_url:
            sublime.status_message("Error: No remote url for project")
            return
        url = '%s/blob/%s/%s' % (repo_url, branchname, relpath) # todo: line number
        print('url: %s' % url)
        sublime.set_clipboard(url)
        sublime.status_message("Copied Github link")


    def is_enabled(self):
        return bool(self.get_repo_url())
