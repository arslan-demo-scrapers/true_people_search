import re
from html import unescape


def clean(text):
    if isinstance(text, (int, float)):
        return text

    text = unescape(text or '')
    for c in ['\r\n', '\n\r', u'\n', u'\r', u'\t', u'\xa0', '...']:
        text = text.replace(c, ' ')
    return re.sub(' +', ' ', text).strip()


def clean_all(seq):
    return [clean(e) for e in seq if clean(e)]
