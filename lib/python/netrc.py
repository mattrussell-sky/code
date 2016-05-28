"""An object-oriented interface to .netrc files."""

# Module and documentation by Eric S. Raymond, 21 Dec 1998
# Improved to support quoted password tokens by <grawity@gmail.com>

import os, shlex, stat

__all__ = ["netrc", "NetrcParseError"]


def unquote(string):
    escape = {
        "n": "\n",
        "t": "\t",
    }
    if len(string) >= 2 and string[0] == string[-1] == "\"":
        buf, state = "", 0
        for char in string[1:-1]:
            if state == 0:
                if char == "\\":
                    state = 1
                else:
                    buf += char
            elif state == 1:
                buf += escape.get(char, char)
                state = 0
        return buf
    else:
        return string


def check_owner(fp):
    if os.name != 'posix':
        return
    prop = os.fstat(fp.fileno())
    if prop.st_uid != os.getuid():
        import pwd
        try:
            fowner = pwd.getpwuid(prop.st_uid)[0]
        except KeyError:
            fowner = 'uid %s' % prop.st_uid
        try:
            user = pwd.getpwuid(os.getuid())[0]
        except KeyError:
            user = 'uid %s' % os.getuid()
        raise NetrcParseError(
            ("~/.netrc file owner (%s) does not match"
             " current user (%s)") % (fowner, user),
            file, lexer.lineno)
    if prop.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise NetrcParseError(
           "~/.netrc access too permissive: access"
           " permissions must restrict access to only"
           " the owner", file, lexer.lineno)


class NetrcParseError(Exception):
    """Exception raised on syntax errors in the .netrc file."""
    def __init__(self, msg, filename=None, lineno=None):
        self.filename = filename
        self.lineno = lineno
        self.msg = msg
        Exception.__init__(self, msg)

    def __str__(self):
        return "%s (%s, line %s)" % (self.msg, self.filename, self.lineno)


class netrc(object):
    def __init__(self, file=None):
        default_netrc = file is None
        if file is None:
            try:
                file = os.path.join(os.environ['HOME'], ".netrc")
            except KeyError:
                raise OSError("Could not find .netrc: $HOME is not set")
        self.hosts = {}
        self.macros = {}
        with open(file) as fp:
            if default_netrc:
                check_owner(fp)
            self._parse(file, fp)

    def _parse(self, file, fp):
        lexer = shlex.shlex(fp)
        lexer.wordchars += r"""!#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
        while True:
            # Look for a machine, default, or macdef top-level keyword
            toplevel = tt = lexer.get_token()
            if not tt:
                break
            elif tt == 'machine':
                entryname = lexer.get_token()
            elif tt == 'default':
                entryname = 'default'
            elif tt == 'macdef':                # Just skip to end of macdefs
                entryname = lexer.get_token()
                self.macros[entryname] = []
                lexer.whitespace = ' \t'
                while 1:
                    line = lexer.instream.readline()
                    if not line or line == '\012':
                        lexer.whitespace = ' \t\r\n'
                        break
                    self.macros[entryname].append(line)
                continue
            else:
                raise NetrcParseError(
                    "bad toplevel token %r" % tt, file, lexer.lineno)

            # We're looking at start of an entry for a named machine or default.
            login = ''
            account = password = None
            self.hosts[entryname] = {}
            while True:
                tt = lexer.get_token()
                if (tt.startswith('#') or
                    tt in {'', 'machine', 'default', 'macdef'}):
                    if password:
                        self.hosts[entryname] = (login, account, password)
                        lexer.push_token(tt)
                        break
                    else:
                        raise NetrcParseError(
                            "malformed %s entry %s terminated by %s"
                            % (toplevel, entryname, repr(tt)),
                            file, lexer.lineno)
                elif tt == 'login' or tt == 'user':
                    login = unquote(lexer.get_token())
                elif tt == 'account':
                    account = unquote(lexer.get_token())
                elif tt == 'password':
                    password = unquote(lexer.get_token())
                else:
                    raise NetrcParseError("bad follower token %r" % tt,
                                          file, lexer.lineno)

    def authenticators(self, host):
        """Return a (user, account, password) tuple for given host."""
        return self.hosts.get(host) or self.hosts.get("default")

    def __repr__(self):
        """Dump the class data in the format of a .netrc file."""
        rep = ""
        for host in sorted(self.hosts.keys()):
            attrs = self.hosts[host]
            rep += "machine %s\n" % host
            if attrs[0]:
                rep += "\tlogin %r\n" % attrs[0]
            if attrs[1]:
                rep += "\taccount %r\n" % attrs[1]
            if attrs[2]:
                rep += "\tpassword %r\n" % attrs[2]
            rep += "\n"
        for macro in self.macros.keys():
            rep += "macdef %s\n" % macro
            for line in self.macros[macro]:
                rep += line
            rep += "\n"
        return rep

if __name__ == '__main__':
    print(netrc())
