import sublime
import sublime_plugin
import re

from .step_registry import step_registry
from .utils import is_feature_file_in_project, get_phrase_from_line

class SbInsertNewStepCommand(sublime_plugin.TextCommand):
    STEP_PHRASE_PATTERN = re.compile('\{([^\}]*)\}')

    def __init__(self, view):
        super(SbInsertNewStepCommand, self).__init__(view)

    def run(self, edit):
        if step_registry.get_count() == 0:
            steps_list = ['No step definitions available']
            callback = None
        else:
            steps_list = [[x.phrase, '{}:{}'.format(x.file_name, x.line)]
                          for x in step_registry]
            callback = self._steps_found
        self.view.window().show_quick_panel(steps_list, callback)

    def _steps_found(self, index):
        if index < 0:
            return
        sel_step = step_registry.get_definition_by_index(index)
        if sel_step is None:
            return

        contents = self._snippetize_step(sel_step.phrase)
        self.view.run_command('insert_snippet', {'contents': contents})

    def _snippetize_step(self, input):
        '''
        Turns 'Then {item:s} will be {value:d}'
        into 'Then "${1:item:s}" will be "${2:value:d}"'
        ### TODO: proper handling of double brackets, i.e: {{abc}}
        '''
        class incr_index:
            def __init__(self, f):
                self.index = 0
                self.f = f

            def __call__(self, matchobj):
                self.index += 1
                return self.f(matchobj, self.index)

        @incr_index
        def sub_cb(matchobj, index):
            return '"${{{}:{}}}"'.format(index, matchobj.group(1))

        return self.STEP_PHRASE_PATTERN.sub(sub_cb, input)

    def is_enabled(self):
        return is_feature_file_in_project(self.view)