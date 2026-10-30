"""Final text formatting for the opt-in technology talking-head caption style.

Semantic cue splitting remains the author's job using real word times.
"""
import re
import string
import unicodedata


def format_technology_caption(text):
    """Comma separators -> two U+0020; preserve numeric grouping and meaningful marks.

    Run after language/glossary/spacing edits and before BOTH SRT and ASS serialization.
    Line/cue edge whitespace is removed; punctuation-only lines produce no blank cue.
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    marker = '\ue000'
    while marker in text:
        marker += '\ue001'
    saved = []
    def protect(match):
        saved.append(match.group())
        return marker + str(len(saved)-1) + marker
    # Only conventional groups of three count as thousands separators; 1,2 is a list.
    text = re.sub(r'(?<![\d,，])\d{1,3}(?:[,，]\d{3})+(?:\.\d+)?(?!\d|[,，]\d)', protect, text)
    text = re.sub(r'(?:[ \t]*[,，])+[ \t]*', '  ', text)
    for i, number in enumerate(saved):
        text = text.replace(marker + str(i) + marker, number)
    lines = []
    for line in text.split('\n'):
        line = line.strip(' \t')
        # Drop ordinary terminal periods, not ellipses or meaningful inner decimals.
        line = re.sub(r'(?<![.。])[.。]$', '', line).rstrip(' \t')
        if line:
            lines.append(line)
    return '\n'.join(lines)


def format_no_punctuation_caption(text):
    """Replace punctuation runs with two ASCII spaces; trim each display line.

    Includes numeric punctuation and ASCII punctuation; never edits timecodes.
    Keep semantic line breaks and non-punctuation symbols such as emoji.
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = []
    for line in text.split('\n'):
        parts = []
        in_separator = False
        for original in line:
            is_punctuation = unicodedata.category(original).startswith('P') or original in string.punctuation
            if is_punctuation:
                if not in_separator:
                    while parts and parts[-1] in (' ', '\t'):
                        parts.pop()
                    parts.append('  ')
                in_separator = True
            elif in_separator and original in (' ', '\t'):
                continue
            else:
                parts.append(original)
                in_separator = False
        result = ''.join(parts).strip(' \t')
        if result:
            lines.append(result)
    return '\n'.join(lines)


def format_caption(text, punctuation_style):
    """Apply the user's explicit selection to shared SRT/ASS display text."""
    if punctuation_style == 'no-punctuation':
        return format_no_punctuation_caption(text)
    if punctuation_style == 'existing':
        return format_technology_caption(text)
    raise ValueError('Select no-punctuation or existing')


def ass_text(text):
    """Serialize already formatted plain text without whitespace normalization."""
    return text.replace('{', '（').replace('}', '）').replace('\n', r'\N')
