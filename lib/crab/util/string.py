import re

def remove_quotes(value):
  """If the given string starts and ends with matching quote marks,
  remove them from the returned value."""

  if (value.startswith("'") and value.endswith("'")) \
  or (value.startswith('"') and value.endswith('"')):
      return value[1:-1]
  else:
      return value

def quote_multiword(value):
    """If the given string contains space characters, return it
    surrounded by double quotes, otherwise return the original string."""

    if value.find(' ') != -1:
        return '"' + value + '"'
    else:
        return value

def split_quoted_word(value):
    """Splits the given string on the first word boundary, unless it starts
    with a quote.

    If quotes are present it splits at the first matching quote. Eg.:

    >>> split_quoted_word('alpha bravo charlie delta echo')
    ['alpha', 'bravo charlie delta echo']
    >>> split_quoted_word('"alpha bravo" charlie delta echo')
    ('alpha bravo', 'charlie delta echo')

    Does not handle escaped quotes within the string."""

    if value.startswith("'"):
        (a, b) = value[1:].split("'", 1)
    elif value.startswith('"'):
        (a, b) = value[1:].split('"', 1)
    else:
        return value.split(None, 1)

    return (a, b.lstrip())

def alphanum(value):
    """Removes all non-alphanumeric characters from the string,
    replacing them with underscores."""

    return re.sub('[^a-zA-Z0-9]', '_', value)
