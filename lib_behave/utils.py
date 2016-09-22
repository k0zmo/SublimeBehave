import sublime
import os

def check_selector(view, selector):
    try:
        return view.score_selector(view.sel()[0].begin(), selector) > 0
    except IndexError:
        return False

def is_gherkin(view):
    if not view:
        return False
    return check_selector(view, 'text.gherkin.feature')

def is_python(view):
    if not view:
        return False
    return check_selector(view, 'source.python')

def get_project_root(window):
    '''
    Pick first folder if any
    '''
    folders = window.folders()
    if len(folders) < 1:
        return None
    return folders[0]

def is_view_in_folder(view, folder):
    if not view.file_name() or not folder:
        return False
    return os.path.commonprefix([view.file_name(), folder]) == folder  

def is_feature_file_in_project(view):
    if not is_gherkin(view):
        return False
    folder = get_project_root(view.window())
    if folder is None:
        return False
    return is_view_in_folder(view, os.path.join(folder, 'features'))

def is_step_file_in_project(view):
    if not is_python(view):
        return False
    folder = get_project_root(view.window())
    if folder is None:
        return False
    return is_view_in_folder(view, os.path.join(folder, 'features', 'steps'))

def get_phrase_from_line(view, line):
    region = view.line(view.text_point(line - 1, 0))
    # modify region, trimming spaces
    phrase = view.substr(region)
    region.a += _get_first_nonspace(phrase)
    region.b -= _get_first_nonspace(reversed(phrase))
    if region.a > region.b:
        region.a = region.b
    return region

def _get_first_nonspace(phrase):
    margin = 0
    for char in phrase:
        if char.isspace():
            margin += 1
        else:
            break
    return margin

def get_line_from_cursor(view, event):
    pt = view.window_to_text((event["x"], event["y"]))
    return view.rowcol(pt)[0] + 1
