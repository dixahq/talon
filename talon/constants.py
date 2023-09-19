from __future__ import absolute_import
import regex as re
import os

# You can customize these by setting an environment variable.
TOO_LONG_SIGNATURE_LINE = int(os.environ.get('TALON_TOO_LONG_SIGNATURE_LINE', 60))
SIGNATURE_MAX_LINES = int(os.environ.get('TALON_SIGNATURE_MAX_LINES', 15))
SIGNATURE_LINE_MAX_CHARS = int(os.environ.get('TALON_SIGNATURE_LINE_MAX_CHARS', 40))

# regex to fetch signature based on common signature words
# To modify use `add_filter('talon_email_signature_patterns', YOUR_FUNCTION_NAME)`
RE_SIGNATURE = r'''
    ^[\s]*--*[\s]*[a-z\s\.]*$
    |
    ^thanks[\s,!\.]*$
    |
    ^thanks?[\s]+you[\s,!\.]*$
    |
    ^regards[\s,!\.]*$
    |
    ^cheers[\s,!\.]*$
    |
    ^all\s+(?:the)?(?:my)?\s+best[\s,!\.]*$
    |
    ^best[a-z\s,!\.]*$
    |
    ^sincerely[a-z,!\.]*$
'''

# To modify use `add_filter('talon_email_footer_patterns', YOUR_FUNCTION_NAME)`
RE_FOOTER =r'''
    ^sent\s+from\s+my[\s,!\w]*$
    |
    ^sent\s+from\s+Mailbox\s+for\s+[\s,!\w]*.*$
    |
    ^sent\s+from\s+a\s+phone.*$
    |
    ^sent\s+(?:\S*\s+)?from\s+my[\s,!\w]*.*$
    |
    ^Enviado\s+desde\s+mi\s+(?:\S+\s+){0,2}[\s,!\w]*.*$
'''

# To modify use `add_filter('talon_email_signature_words', YOUR_FUNCTION_NAME)`
RE_SIGNATURE_WORDS = r'''
    [Tt]hank.*[,\.!]?
    |
    [Bb]est[,\.]?
    |
    [Rr]egards[,\.!]?
    |
    [Cc]heers[,\.!]?
    |
    [Ss]incerely[,\.]?
'''

# To modify use `add_filter('talon_email_footer_words', YOUR_FUNCTION_NAME)`
RE_FOOTER_WORDS = r'''
    [Ss]ent\s+from\s+my[\s,!\w]*
    |
    [Ss]ent\s+from\s+[M|m]ailbox\s+for\s+[\s,!\w]*.*
    |
    [Ss]ent\s+from\s+a\s+phone.*
    |
    [Ss]ent\s+(?:\S*\s+)?from\s+my[\s,!\w]*.*
    |
    [Ee]nviado\s+desde\s+mi\s+(\S+\s+){0,2}[\s,!\w]*.*
'''

# To modify use `add_filter('talon_email_footer_lines', YOUR_FUNCTION_NAME)`
# Complete lines without patterns will be matched in reverse email body using a Levenshtein distance measurment with a threshold of .7
# Modify the ratio with `add_filter('talon_email_footer_lines_ratio', YOUR_FUNCTION_NAME)
KNOWN_FOOTER_LINES = []

#To modify use `add_filter('talon_email_sender_blacklist', YOUR_FUNCTION_NAME)`
BAD_SENDER_NAMES = [
    # known mail domains
    'hotmail', 'gmail', 'yandex', 'mail', 'yahoo', 'mailgun', 'mailgunhq',
    'example',
    # first level domains
    'com', 'org', 'net', 'ru',
    # bad words
    'mailto'
]

RE_DELIMITER = re.compile(r'\r?\n')

# see _mark_candidate_indexes() for details
# c - could be signature line
# d - line starts with dashes (could be signature or list item)
# l - long line
RE_SIGNATURE_CANDIDATE = re.compile(r'''
    (?P<candidate>c+d)[^d]
    |
    (?P<candidate>c+d)$
    |
    (?P<candidate>c+)
    |
    (?P<candidate>d)[^d]
    |
    (?P<candidate>d)$
''', re.I | re.X | re.M | re.S)

RE_EMAIL = re.compile('\S@\S')
RE_RELAX_PHONE = re.compile('(\(? ?[\d]{2,3} ?\)?.{,3}?){2,}')
RE_URL = re.compile(r"""https?://|www\.[\S]+\.[\S]""")

# Taken from:
# http://www.cs.cmu.edu/~vitor/papers/sigFilePaper_finalversion.pdf
# Line matches the regular expression "^[\s]*---*[\s]*$".
RE_SEPARATOR = re.compile('^[\s]*---*[\s]*$')

# Taken from:
# http://www.cs.cmu.edu/~vitor/papers/sigFilePaper_finalversion.pdf
# Line has a sequence of 10 or more special characters.
RE_SPECIAL_CHARS = re.compile(('^[\s]*([\*]|#|[\+]|[\^]|-|[\~]|[\&]|[\$]|_|[\!]|'
                    '[\/]|[\%]|[\:]|[\=]){10,}[\s]*$'))

# Taken from:
# http://www.cs.cmu.edu/~vitor/papers/sigFilePaper_finalversion.pdf
# Line contains a pattern like Vitor R. Carvalho or William W. Cohen.
RE_NAME = re.compile('[A-Z][a-z]+\s\s?[A-Z][\.]?\s\s?[A-Z][a-z]+')

INVALID_WORD_START = re.compile('\(|\+|[\d]')
