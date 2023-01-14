import os
import sys

from helpers.definitions import TRANSLATION_INDEX


def count_chars(a, b):
    if type(a) is int:
        return a + len(b[TRANSLATION_INDEX].encode('utf-8'))
    else:
        return len(a[TRANSLATION_INDEX].encode('utf-8')) + len(b[TRANSLATION_INDEX].encode('utf-8'))


def relative_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
