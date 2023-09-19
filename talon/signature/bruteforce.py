from __future__ import absolute_import

import logging
import Levenshtein
from talon.constants import (SIGNATURE_MAX_LINES,TOO_LONG_SIGNATURE_LINE,RE_SIGNATURE,RE_FOOTER, KNOWN_FOOTER_LINES,RE_SIGNATURE_CANDIDATE)
from talon.utils import get_delimiter, apply_filters, compile_pattern

log = logging.getLogger(__name__)

def extract_signature(msg_body):
    '''
    Analyzes message for a presence of signature block (by common patterns)
    and returns tuple with two elements: message text without signature block
    and the signature itself.

    >>> extract_signature('Hey man! How r u?\n\n--\nRegards,\nRoman')
    ('Hey man! How r u?', '--\nRegards,\nRoman')

    >>> extract_signature('Hey man!')
    ('Hey man!', None)
    '''
    try:
        # identify line delimiter first
        delimiter = get_delimiter(msg_body)

        # make an assumption
        stripped_body = msg_body.strip()
        footer = None

        # decide on signature candidate
        lines = stripped_body.splitlines()

        (candidate, lines, footer) = get_signature_candidate(lines)
        candidate = delimiter.join(candidate)

        # try to extract signature
        sig_pattern = compile_pattern('talon_email_signature_patterns', RE_SIGNATURE)
        signature = sig_pattern.search(candidate)

        if not signature:
            return (stripped_body.strip(), footer)
        else:
            signature = signature.group()
            # when we splitlines() and then join them
            # we can lose a new line at the end
            # we did it when identifying a candidate
            # so we had to do it for stripped_body now
            stripped_body = delimiter.join(lines)
            stripped_body = stripped_body[:-len(signature)]

            if footer:
                footer = delimiter.join(footer)
                signature = delimiter.join([signature, footer])

            return (stripped_body.strip(), signature.strip())
    except Exception:
        log.exception('ERROR extracting signature')
        return (msg_body, None)


def get_signature_candidate(lines):
    """Return lines that could hold signature

    The lines should:

    * be among last SIGNATURE_MAX_LINES non-empty lines.
    * not include first line
    * be shorter than TOO_LONG_SIGNATURE_LINE
    * not include more than one line that starts with dashes
    """
    # non empty lines indexes
    non_empty = [i for i, line in enumerate(lines) if line.strip()]

    # if message is empty or just one line then there is no signature
    if len(non_empty) <= 1:
        return ([],lines,None)

    # we don't expect signature to start at the 1st line
    candidate = non_empty[1:]

    # Strip know footer lines

    footer_start_idx = len(candidate)-1
    footer = None

    footer_pattern = compile_pattern('talon_email_footer_patterns', RE_FOOTER)
    footer_lines = apply_filters('talon_email_footer_lines', KNOWN_FOOTER_LINES)
    similarity_ratio = apply_filters('talon_email_footer_lines_ratio', 0.75)
    found_footer = False
    for i, line_idx in reversed(list(enumerate(candidate))):
        is_footer_line = False

        if footer_pattern.search(lines[line_idx]):
            is_footer_line = True
            found_footer = True

        if (is_footer_line):
            footer_start_idx = i
            continue
        else:
            for footer_line in footer_lines:
                if Levenshtein.ratio(footer_line, lines[line_idx]) > similarity_ratio:
                    is_footer_line = True
                    found_footer = True
                    footer_start_idx = i
                    break

            if is_footer_line:
                continue
            else:
                break

    # There is a likely scenario that one line replies with a footer such as 'sent from my iphone' won't be caught.
    # In this case if there are only 2 lines in an email and one of them is a footer, we send back 0 candidates
    if (footer_start_idx != len(candidate)-1):
        sig_stop = footer_start_idx
        footer = lines[candidate[sig_stop]:]
        lines = lines[:candidate[sig_stop]]
        candidate = candidate[:sig_stop]
    elif ((len(candidate) == 1) and found_footer):
        footer = lines[candidate[footer_start_idx]:]
        lines = lines[:candidate[footer_start_idx]]
        candidate = []

    # signature shouldn't be longer then SIGNATURE_MAX_LINES
    candidate = candidate[-SIGNATURE_MAX_LINES:]
    markers = _mark_candidate_indexes(lines, candidate)
    candidate = _process_marked_candidate_indexes(candidate, markers)

    # get actual lines for the candidate instead of indexes
    if candidate:
        candidate = lines[candidate[0]:]
        return (candidate,lines,footer)

    return ([],lines,footer)


def _mark_candidate_indexes(lines, candidate):
    """Mark candidate indexes with markers

    Markers:

    * c - line that could be a signature line
    * l - long line
    * d - line that starts with dashes but has other chars as well

    >>> _mark_candidate_lines(['Some text', '', '-', 'Bob'], [0, 2, 3])
    'cdc'
    """

    # at first consider everything to be potential signature lines
    markers = list('c' * len(candidate))
    # mark lines starting from bottom up
    for i, line_idx in reversed(list(enumerate(candidate))):
        if len(lines[line_idx].strip()) > TOO_LONG_SIGNATURE_LINE:
            markers[i] = 'l'
        else:
            line = lines[line_idx].strip()
            if (line.startswith('-') and line.strip("-")):
                markers[i] = 'd'

    return "".join(markers)


def _process_marked_candidate_indexes(candidate, markers):
    """
    Run regexes against candidate's marked indexes to strip
    signature candidate.

    >>> _process_marked_candidate_indexes([9, 12, 14, 15, 17], 'clddc')
    [15, 17]
    """
    match = RE_SIGNATURE_CANDIDATE.match(markers[::-1])
    return candidate[-match.end('candidate'):] if match else []
