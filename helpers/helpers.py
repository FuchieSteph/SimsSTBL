from helpers.definitions import TRANSLATION_INDEX


def count_chars(a, b):
    if type(a) is int:
        return a + len(b[TRANSLATION_INDEX].encode('utf-8'))
    else:
        return len(a[TRANSLATION_INDEX].encode('utf-8')) + len(b[TRANSLATION_INDEX].encode('utf-8'))
