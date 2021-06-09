import sublime
from sublime_plugin import WindowCommand

from ...common import util
from ...core.git_command import GitCommand
from .. import github, git_mixins


START_CREATE_MESSAGE = "Forking {repo} ..."
END_CREATE_MESSAGE = "Fork created successfully."


__all__ = ['GsGithubCreateForkCommand']


class GsGithubCreateForkCommand(
    WindowCommand,
    git_mixins.GithubRemotesMixin,
    GitCommand,
):
    """
    Get list of repos on GitHub associated with the active repo.  Display, and when
    selected, add selection as git remote.
    """
    def run(self):
        sublime.set_timeout_async(self.run_async, 0)

    def run_async(self):
        remotes = self.get_remotes()
        base_remote_name = self.get_integrated_remote_name(remotes)
        base_remote_url = remotes[base_remote_name]
        base_remote = github.parse_remote(base_remote_url)

        self.window.status_message(START_CREATE_MESSAGE.format(repo=base_remote.url))
        result = github.create_fork(base_remote)
        self.window.status_message(END_CREATE_MESSAGE)
        util.debug.add_to_log(("github: fork result:\n{}".format(result)))

        url = (
            result["ssh_url"]
            if base_remote_url.startswith("git@")
            else result["clone_url"]
        )
        self.window.run_command("gs_remote_add", {"url": url})
