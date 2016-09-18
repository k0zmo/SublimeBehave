import re
import sublime
import json
from collections import defaultdict

from .behave_command import BehaveCommand

class StepDefinition:
    STEP_TYPE = {
        'given': 1,
        'when': 2,
        'then': 3,
        'generic': 4
    }

    def __init__(self, step_type, phrase, file_name, line):
        self.step_type = StepDefinition.STEP_TYPE[step_type]
        self.phrase = phrase
        self.file_name = file_name
        self.line = int(line)

    def __repr__(self):
        return json.dumps(self,
                  default=lambda o: o.__dict__,
                  sort_keys=True, indent=4)

class StepRegistry:
    def __init__(self):
        self.step_defs = defaultdict(list)
        self.directory = ''
        # dont include 'GENERIC' steps since behave does appends them to every other
        self.step_type_header = re.compile(r'(GIVEN|WHEN|THEN) STEP DEFINITIONS\[(\d)\]:')
        self.step_pattern = re.compile(r'\s{2}(.*\s)\s*# (.*):(\d+)')
        self.order = ['given', 'then', 'when']

    def get_count(self):
        return len(self.step_defs)

    def update_definitions(self, directory):
        sublime.status_message('Behave: Updating index of step definitions')
        self._update_definitions(directory)
        self.directory = directory
        sublime.status_message('Behave: Done updating index of step definitions')

    def _update_definitions(self, directory):
        args = ['--dry-run',
                '-f', 'steps',
                '--no-summary',
                '--no-snippets',
                '--exclude=.*']

        out = BehaveCommand().run(directory, *args)

        current_type = ''
        num_steps = 0
        self.step_defs.clear()

        for line in iter(out.splitlines()):
            if len(current_type) == 0:
                match = self.step_type_header.search(line)
                if match:
                    current_type = match.group(1).lower()
                    num_steps = int(match.group(2))
            elif num_steps > 0:
                num_steps -= 1
                match = self.step_pattern.search(line)
                if not match:
                    continue
                # remove first phrase (given, when, then) - we dont need it
                phrase = match.group(1).strip() #.split(' ', 1)[1]
                self.step_defs[current_type].append(StepDefinition(current_type,
                                                                   phrase, 
                                                                   match.group(2),
                                                                   match.group(3)))
            else:
                current_type = ''

        #print(self.step_defs)

    def get_definition_by_location(self, step_type, file_name, line):
        step_def = self.step_defs.get(step_type)
        if step_def is None:
            return None
        return next((x for x in step_def
                     if x.line == line and x.file_name == file_name))

    def get_definition_by_phrase(self, step_type, phrase):
        step_def = self.step_defs.get(step_type)
        if step_def is None:
            return None
        return next((x for x in step_def
                     if x.phrase.find(phrase[1:-1]) != -1))

    def get_definition_by_index(self, index):
        tmp = 0
        for step_type in self.order:
            list_by_type = self.step_defs.get(step_type)
            if list_by_type is None:
                continue
            if index - tmp < len(list_by_type):
                return list_by_type[index - tmp]
            else:
                tmp = tmp + len(list_by_type)
        return None

    def __iter__(self):
        for step_type in self.order:
            list_by_type = step_registry.step_defs.get(step_type)
            if list_by_type is None:
                continue
            for step_def in list_by_type:
                yield step_def

step_registry = StepRegistry()
