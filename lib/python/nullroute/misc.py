import math
import os

def get_file_attr(path, attr):
    try:
        return os.getxattr(path, "user.%s" % attr).decode("utf-8")
    except FileNotFoundError:
        raise
    except OSError:
        return None

def set_file_attr(path, attr, value):
    try:
        os.setxattr(path, "user.%s" % attr, value.encode("utf-8"))
    except FileNotFoundError:
        raise
    except OSError:
        pass

def escape_html(text):
    xlat = [
        ('&', '&amp;'),
        ('<', '&lt;'),
        ('>', '&gt;'),
        ('"', '&quot;'),
    ]
    for k, v in xlat:
        text = text.replace(k, v)
    return text

def escape_shell(text):
    escaped = "\\$`\""
    quoted = " \n'?*[]()<>{};&|~" + escaped
    if any(c in text for c in quoted):
        for k in escaped:
            text = text.replace(k, "\\" + k)
        text = '"%s"' % text
    return text

def filter_filename(name):
    xlat = [
        (' ', '_'),
        ('　', '_'),
        ('"', '_'),
        ('*', '_'),
        ('/', '⁄'),
        (':', '∶'),
        ('<', '_'),
        ('>', '_'),
        ('?', '？'),
    ]
    name = name.strip()
    for k, v in xlat:
        name = name.replace(k, v)
    if name.startswith("."):
        name = "_" + name
    if name.endswith("~"):
        name = name.replace("~", "∼")
    return name

def uniq(items):
    seen = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            yield item

def fmt_size_short(nbytes, decimals=1, si=False):
    prefixes = "BkMGTPEZYH"
    div = 1000 if si else 1024
    exp = 0
    while nbytes >= div:
        nbytes /= div
        exp += 1
    return "%.*f%s" % (decimals, nbytes, prefixes[exp])

def fmt_size(nbytes, decimals=1, si=False):
    if nbytes == 0:
        return "0 bytes"
    prefixes = ".kMGTPEZYH"
    div = 1000 if si else 1024
    exp = int(math.log(nbytes, div))
    if exp == 0:
        return "%.*f bytes" % (nbytes, decimals)
    elif exp < len(prefixes):
        quot = nbytes / div**exp
        return "%.*f %sB" % (quot, decimals, prefixes[exp])
    else:
        exp = len(prefixes) - 1
        quot = nbytes / div**exp
        return "%f %sB" % (quot, prefixes[exp])
    return str(nbytes)

def unescape(line):
    state = 0
    acc = ""
    outv = [""]
    esc = {"n": "\n", "t": "\t"}
    for ch in line:
        if state == 1:
            if ch in "01234567" and len(acc) < 4:
                acc += ch
            elif len(acc) > 0:
                outv.append(int(acc, 8))
                outv.append("")
                state = 0
                # fall
            # TODO: hex
            else:
                outv[-1] += esc.get(ch, ch)
                state = 0
                continue
        if state == 0:
            if ch == "\\":
                state = 1
                acc = ""
            elif ch == "\"":
                pass
            else:
                outv[-1] += ch
    outb = bytearray()
    for cur in outv:
        if hasattr(cur, "encode"):
            outb += cur.encode("utf-8")
        else:
            outb.append(cur)
    return outb.decode("utf-8")

def unquote(line):
    if line[0] == line[-1] == "\"":
        line = line[1:-1]
    return unescape(line)
