import sublime
import sublime_plugin
import os
from .behave_command import BehaveCommand
from .utils import get_project_root, is_feature_file_in_project

class SbRunBehaveCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        super(SbRunBehaveCommand, self).__init__(window)

    def run(self):
        sublime.set_timeout_async(self.run_impl, 0)

    def run_impl(self):
        root = get_project_root(self.window)
        view = self.window.active_view()
        feature_files = []
        if is_feature_file_in_project(view):
            for sel in view.sel(): 
                line_no = view.rowcol(sel.begin())[0] + 1
                file_name = os.path.relpath(view.file_name(), root)
                feature_files.append('{}:{}'.format(file_name, line_no))

        panel = self.window.create_output_panel('behave')
        self.window.run_command("show_panel", {"panel": "output.behave"})

        def append_fun(line):
            panel.run_command('append', {'characters': line,
                                         'scroll_to_end': True})

        args = ['--no-skipped'] + feature_files
        out = BehaveCommand().run(root, *args, append_fun=append_fun)

    def is_enabled(self):
        return get_project_root(self.window) is not None
