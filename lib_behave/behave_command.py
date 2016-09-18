import re
import subprocess
import sublime
import shutil

class BehaveCommand(object):
    ERROR_PATTERN = re.compile('ParseError|ConfigError|FileNotFoundError|InvalidFileLocationError|InvalidFilenameError|Exception')

    def run(self, cwd, *args, **kwargs):
        command = tuple(self.behave_command) + \
            tuple(arg for arg in args if arg)
        return self._launch_process(cwd, command, **kwargs)

    def _launch_process(self, cwd, command, append_fun=None):
        startupinfo = None
        if sublime.platform() == 'windows':
            # Prevent Windows from opening a console when starting a process
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(command,
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True,
                                   cwd=cwd,
                                   startupinfo=startupinfo)

        if append_fun:
            for line in process.stdout:
                append_fun(line)

        stdout, _ = process.communicate()

        if self.ERROR_PATTERN.match(stdout):
            raise Exception("An error occurred while launching behave.\n",
                            stdout)
        return stdout

    @property
    def behave_command(self):
        settings = sublime.load_settings('SublimeBehave.sublime-settings')
        behave_cmd = settings.get('behave_command', None)

        if behave_cmd and isinstance(behave_cmd, list):
            return behave_cmd

        behave_cmd = shutil.which('behave')
        if not behave_cmd:
            sublime.status_message('behave could not be found. '
                                   'Is it installed?')
            raise Exception('behave could not be found. Is it installed?')
        return [behave_cmd]
