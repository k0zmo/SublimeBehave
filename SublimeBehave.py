import sublime
from .lib_behave import *
from .lib_behave.utils import get_project_root, is_feature_file_in_project
import sys

def plugin_loaded():
    print('SublimeBehave: Loaded')

    def initial_update():
        window = sublime.active_window()
        if get_project_root(window):
            window.run_command('sb_update_all_step_definitions')

            view = window.active_view()
            if is_feature_file_in_project(view):
                view.run_command('sb_highlight_undefined_steps')

    sublime.set_timeout(initial_update, 200.0)
