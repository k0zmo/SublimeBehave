import re
import sublime
import json
from collections import defaultdict

from .behave_command import BehaveCommand

class StepUsage:
    def __init__(self, file_name, line, def_file_name, def_line):
        self.file_name = file_name
        self.line = line
        self.def_file_name = def_file_name
        self.def_line = def_line

    def __repr__(self):
        return json.dumps(self,
                  default=lambda o: o.__dict__,
                  sort_keys=True, indent=4)

class StepUsagesRegistry:
    def __init__(self):
        self.step_usages = defaultdict(list)
        self.directory = ''
        self.step_def_pattern = re.compile(
            r'^@(?:given|when|then)\((?:.*)\)\s*# (.*):(\d+)$')
        self.undefined_pattern = re.compile(r'^UNDEFINED STEPS\[\d+\]:$')
        self.unused_pattern = re.compile(r'^UNUSED STEP DEFINITIONS\[\d+\]:$')
        self.step_usage_pattern = re.compile(r'^\s{2}(?:.*)\s*# (.*):(\d+)$')

    @staticmethod
    def get_status_message(feature_files):
        if len(feature_files) == 0:
            return 'for all files'
        return 'for files: ' + ', '.join(feature_files)

    def update_step_usages(self, directory, feature_files=[]):
        s = StepUsagesRegistry.get_status_message(feature_files)
        sublime.status_message('Behave: Updating index of step usages ' + s)
        self._update_step_usages(directory, feature_files)
        self.directory = directory
        sublime.status_message(
            'Behave: Done updating index of step usages ' + s)

    def _update_step_usages(self, directory, feature_files=[]):
        args = ['--dry-run',
                '--no-summary',
                '--no-snippets', 
                '-f', 'steps.usage'] + feature_files
        out = BehaveCommand().run(directory, *args)

        if len(feature_files) > 0:
            # remove entries corresponding to feature_files
            for feature_file in (x for x in feature_files
                                 if self.step_usages.get(x) is not None):
                del self.step_usages[feature_file]
        else:  # remove all entries
            self.step_usages.clear()

        class ParserState:
            section_lookup = 1  # looking for @step or UNDEFINED section
            step_usage_lookup = 2  # inside @step, parsing step usage
            undefined_lookup = 3  # inside UNDEFINED STEPS, parsing step usage
            skip_section = 4
        parser_state = ParserState.section_lookup

        for line in iter(out.splitlines()):
            if parser_state is ParserState.section_lookup:
                match = self.step_def_pattern.search(line) # check if it's @step('')
                if match:
                    def_file_name = match.group(1)
                    def_line_no = int(match.group(2))
                    parser_state = ParserState.step_usage_lookup
                else:
                    match = self.undefined_pattern.search(line) # fallback to undefined section
                    if match:
                        parser_state = ParserState.undefined_lookup
                    else:
                        match = self.unused_pattern.search(line) # fallback to unused section
                        parser_state = ParserState.section_lookup if not match \
                            else ParserState.skip_section
            elif parser_state is ParserState.step_usage_lookup:
                if len(line.strip()) == 0:
                    parser_state = ParserState.section_lookup
                else:
                    match = self.step_usage_pattern.search(line)
                    if match:
                        key = match.group(1)
                        self.step_usages[key].append(StepUsage(key, 
                                                               int(match.group(2)),
                                                               def_file_name, 
                                                               def_line_no))
            elif parser_state is ParserState.undefined_lookup:
                if len(line.strip()) == 0:
                    parser_state = ParserState.section_lookup
                else:
                    match = self.step_usage_pattern.search(line)
                    if match:
                        # add undefined step usage
                        key = match.group(1)
                        self.step_usages[key].append(StepUsage(key,
                                                               int(match.group(2)),
                                                               '', -1))
            elif parser_state is ParserState.skip_section:
                if len(line.strip()) == 0:
                    parser_state = ParserState.section_lookup

        # print(self.step_usages)

    def get_undefined_step_usages(self, file_name):
        return ((x.file_name, x.line) for x in self.step_usages[file_name]
                if x.def_line == -1)

    def get_step_definition(self, file_name, line_no):
        l = self.step_usages.get(file_name)
        if l is None:
            return None
        step_usage = next((x for x in l if x.line == line_no), None)
        if step_usage is None:
            return None
        return (step_usage.def_file_name, step_usage.def_line)

step_usages_registry = StepUsagesRegistry()
