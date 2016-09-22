import sublime
import sublime_plugin
import os

from .step_registry import step_registry
from .step_usages_registry import step_usages_registry
from .utils import get_project_root, \
    is_feature_file_in_project, \
    is_step_file_in_project, \
    get_phrase_from_line

class SbListStepsCommand(sublime_plugin.WindowCommand):
    '''
    Lists all defined steps in Sublime's Quick Panel and goes to selected one
    '''
    def __init__(self, window):
        super(SbListStepsCommand, self).__init__(window)

    def run(self):
        if step_registry.get_count() == 0:
            steps_list = ['No step definitions available']
            callback = None
        else:
            steps_list = [[x.phrase, '{}:{}'.format(x.file_name, x.line)]
                          for x in step_registry]
            callback = self._steps_found
        self.window.show_quick_panel(steps_list, callback)

    def _steps_found(self, index):
        if index < 0:
            return
        sel_step = step_registry.get_definition_by_index(index)
        if sel_step is None:
            return

        file_path = os.path.join(step_registry.directory, sel_step.file_name)
        self.window.open_file('{}:{}'.format(file_path, sel_step.line),
                              sublime.ENCODED_POSITION)

    def is_enabled(self):
        return get_project_root(self.window) is not None

class SbGotoStepDefinitionCommand(sublime_plugin.TextCommand):
    '''
    Goes to the definition of the currently selected step (by the text cursor) 
    '''
    def __init__(self, view):
        super(SbGotoStepDefinitionCommand, self).__init__(view)

    def run(self, edit):
        root = get_project_root(self.view.window())
        file_name = os.path.relpath(self.view.file_name(), root)
        line_no = self.view.rowcol(self.view.sel()[0].begin())[0] + 1

        result = step_usages_registry.get_step_definition(file_name, line_no)
        if result is None or result[1] == -1:
            sublime.status_message('Can\' find definition for step: `{}`'.format(
                self.view.substr(get_phrase_from_line(self.view, line_no))))
        else:
            self.view.window().open_file('{}:{}'.format(
                os.path.join(root, result[0]), result[1]), 
                sublime.ENCODED_POSITION)

    def is_enabled(self):
        return is_feature_file_in_project(self.view)

class SbFindAllStepReferencesCommand(sublime_plugin.TextCommand):
    '''
    Finds all references (in .feature files) for selected step definition
    '''
    def __init__(self, view):
        super(SbFindAllStepReferencesCommand, self).__init__(view)

    def run(self, edit):
        root = get_project_root(self.view.window())
        file_name = os.path.relpath(self.view.file_name(), root)
        line_no = self.view.rowcol(self.view.sel()[0].begin())[0] + 1

        refs = step_usages_registry.get_step_references(file_name, line_no)
        if len(refs) > 0:
            contents = 'Step references:\n'
            contents += '\n'.join('  {}:{}'.format(ref[0], ref[1]) for ref in refs)
        else:
            contents = 'No step references found'

        panel = self.view.window().create_output_panel('behave.refs')
        panel.set_syntax_file('Packages/SublimeBehave/Find Step References Results.hidden-tmLanguage')
        panel.run_command('append', {'characters': contents,
                                     'scroll_to_end': False})
        self.view.window().run_command("show_panel",
                                       {"panel": "output.behave.refs"})

    def is_enabled(self):
        return is_step_file_in_project(self.view)

class SbGotoStepReferenceCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        super(SbGotoStepReferenceCommand, self).__init__(view)

    def run(self, edit):
        line_no = self.view.rowcol(self.view.sel()[0].begin())[0] + 1
        location = self.view.substr(get_phrase_from_line(self.view, line_no))
        root = get_project_root(self.view.window())
        if line_no > 1:
            self.view.window().open_file(os.path.join(root, location), 
                                         sublime.ENCODED_POSITION)

    def is_enabled(self):
        try:
            return self.view.score_selector(self.view.sel()[0].begin(), 
                                            'sublime.behave.find.results') > 0
        except IndexError:
            return False

    def is_visible(self):
        return self.is_enabled()

class SbShowDefinitionEventListener(sublime_plugin.EventListener):
    def on_hover(self, view, point, hover_zone):
        if not sublime.load_settings(
                'SublimeBehave.sublime-settings').get('show_definitions'):
            return
        if hover_zone != sublime.HOVER_TEXT:
            return
        if not is_feature_file_in_project(view):
            return

        root = get_project_root(view.window())
        file_name = os.path.relpath(view.file_name(), root)
        line_no = view.rowcol(point)[0] + 1
        result = step_usages_registry.get_step_definition(file_name, line_no)

        if result is None or result[1] == -1:
            return

        def on_navigate(href):
            view.window().open_file(href, sublime.ENCODED_POSITION)

        file_location = '{}:{}'.format(os.path.join(root, result[0]), result[1])
        disp_file_location = '{}:{}'.format(result[0], result[1])

        # Same as in Default.symbol.py
        content = '''
            <body>
              <style>
                body {{
                  font-family: sans-serif;
                }}
                h1 {{ 
                  font-size: 1.1rem;
                  font-weight: bold;
                  margin: 0 0 0.25em 0;
                }}
                p {{
                  font-size: 1.05rem;
                  margin: 0;
                }}
              </style>
              <h1>Definition:</h1>
              <p><a href="{}">{}</a></p>
            </body>
        '''.format(file_location, disp_file_location)

        view.show_popup(
            content, 
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            location=point,
            on_navigate=on_navigate,
            max_width=1024)
