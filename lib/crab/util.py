def remove_quotes(value):
  if (value.startswith("'") and value.endswith("'")) \
  or (value.startswith('"') and value.endswith('"')):
      return value[1:-1]
  else:
      return value

def quote_multiword(value):
    if value.find(" ") != -1:
        return '"' + value + '"'
    else:
        return value

def split_quoted_word(value):
    if value.startswith("'"):
        (a, b) = value[1:].split("'", 1)
    elif value.startswith('"'):
        (a, b) = value[1:].split('"', 1)
    else:
        return value.split(None, 1)

    return (a, b.lstrip())
