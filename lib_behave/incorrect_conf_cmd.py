import sublime_plugin
from .utils import get_project_root

class SbIncorrectConfigurationCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        super(SbIncorrectConfigurationCommand, self).__init__(window)

    def run(self):
        self.window.show_quick_panel(
            ["Please open your project's Behave root directory and set it as a first folder on the list"],
            None)

    def is_enabled(self):
        return get_project_root(self.window) is None