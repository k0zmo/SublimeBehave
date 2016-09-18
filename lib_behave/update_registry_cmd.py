import sublime
import sublime_plugin
import os
import re

from .step_registry import step_registry
from .step_usages_registry import step_usages_registry
from .utils import get_project_root, \
    is_feature_file_in_project, \
    is_step_file_in_project, \
    get_phrase_from_line

class SbUpdateAllStepDefinitionsCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        super(SbUpdateAllStepDefinitionsCommand, self).__init__(window)

    def run(self):
        sublime.set_timeout_async(self.run_impl, 0)

    def run_impl(self):
        root = get_project_root(self.window)
        step_registry.update_definitions(root)
        step_usages_registry.update_step_usages(root)

    def is_enabled(self):
        return get_project_root(self.window) is not None

class SbUpdateStepUsagesCommand(sublime_plugin.TextCommand):
    REGION_NAME = 'sb.invalid_synax'
    ERROR_REGEX = re.compile(r'Failed to parse "(.*)":.*, at line (\d+)')

    def __init__(self, view):
        super(SbUpdateStepUsagesCommand, self).__init__(view)

    def run(self, edit):
        sublime.set_timeout_async(self.run_impl, 0)

    def run_impl(self):
        root = get_project_root(self.view.window())
        file_name = os.path.relpath(self.view.file_name(), root)
        try:
            step_usages_registry.update_step_usages(root, [file_name])
            self.view.erase_regions(self.REGION_NAME)
        except Exception as e:
            match = self.ERROR_REGEX.search(str(e))
            if match:
                file_name = os.path.normpath(match.group(1))
                line_no = int(match.group(2))
                sublime.status_message('Parse error: {}:{}'.format(file_name, line_no))

                if file_name == os.path.normpath(self.view.file_name()):

                    region = get_phrase_from_line(self.view, line_no)
                    self.view.add_regions(self.REGION_NAME,
                                          [region], 'invalid')
            else:
                sublime.status_message(
                    'General parse error, check console log for more details')
                raise

    def is_enabled(self):
        return is_feature_file_in_project(self.view)

class SbHighlightUndefinedStepsCommand(sublime_plugin.TextCommand):
    REGION_NAME = 'sb.undefined_steps'

    def __init__(self, view):
        super(SbHighlightUndefinedStepsCommand, self).__init__(view)

    def run(self, edit):
        sublime.set_timeout_async(self.run_impl, 0)

    def run_impl(self):
        # This requires fresh step_usages_registry
        file_name = os.path.relpath(self.view.file_name(),
                                    get_project_root(self.view.window()))
        undefs = step_usages_registry.get_undefined_step_usages(file_name)
        regions = [get_phrase_from_line(self.view, undef[1]) for undef in undefs]
        self.view.add_regions(self.REGION_NAME, regions, 'comment')            

    def is_enabled(self):
        return is_feature_file_in_project(self.view)

class SbStepRegistryEventListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        if is_feature_file_in_project(view):
            view.run_command('sb_highlight_undefined_steps')

    def on_post_save(self, view):
        if is_feature_file_in_project(view):
            view.run_command('sb_update_step_usages')
            view.run_command('sb_highlight_undefined_steps')
        elif is_step_file_in_project(view):
            view.window().run_command('sb_update_all_step_definitions')
