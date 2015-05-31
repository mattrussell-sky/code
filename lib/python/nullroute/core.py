from __future__ import print_function
import os
import sys
import traceback

try:
    _debug_env = int(os.environ.get("DEBUG"))
except:
    _debug_env = 0

try:
    _nested_env = int(os.environ.get("LVL"))
except:
    _nested_env = 0

os.environ["LVL"] = str(_nested_env + 1)

class Core(object):
    LOG_FATAL   = 0
    LOG_ERROR   = 1
    LOG_WARNING = 2
    LOG_NOTICE  = 3
    LOG_INFO    = 4
    LOG_DEBUG   = 5
    LOG_TRACE   = 6

    _levels = {
        LOG_FATAL:      ("fatal",   "\033[1;31m"),
        LOG_ERROR:      ("error",   "\033[1;31m"),
        LOG_WARNING:    ("warning", "\033[1;33m"),
        LOG_NOTICE:     ("notice",  "\033[1;35m"),
        LOG_INFO:       ("info",    "\033[1;34m"),
        LOG_DEBUG:      ("debug",   "\033[1;36m"),
        LOG_TRACE:      ("trace",   "\033[36m"),
    }

    # internal state

    _log_level = LOG_TRACE if _debug_env else LOG_INFO
    _num_warnings = 0
    _num_errors = 0

    # public constants

    arg0 = sys.argv[0].split("/")[-1]

    # logging functions

    @classmethod
    def set_log_level(self, level):
        self._log_level = level

    @classmethod
    def raise_log_level(self, level):
        self._log_level = max(self._log_level, level)

    @classmethod
    def _log(self, level, msg,
             log_prefix=None, log_color=None,
             fmt_prefix=None, fmt_color=None,
             skip=0):
        level = min(max(level, 0), self.LOG_TRACE)
        if level > self._log_level:
            return
        debug = (self._log_level >= self.LOG_DEBUG)
        fh = sys.stderr
        colors = getattr(fh, "isatty", lambda: False)()
        output = []

        if debug or _nested_env:
            output.append(self.arg0)
            if debug:
                output.append("[%d]" % os.getpid())
            output.append(": ")

        prefix = log_prefix or self._levels[level][0]
        color = log_color or self._levels[level][1]

        if fmt_prefix and not debug:
            if colors:
                output.append(fmt_color or color)
            output.append(fmt_prefix)
            if colors:
                output.append("\033[m")
            output.append(" ")
        else:
            if colors:
                output.append(color)
            output.append(prefix)
            output.append(": ")
            if colors:
                output.append("\033[m")

        if level >= self.LOG_DEBUG:
            func = traceback.extract_stack()[-(skip+3)][2]
            if colors:
                output.append("\033[38;5;60m")
            output.append("(%s) " % func)
            if colors:
                output.append("\033[m")

        output.append(msg)

        print("".join(output), file=fh)

    @classmethod
    def trace(self, msg, **kwargs):
        self._log(self.LOG_TRACE, msg, **kwargs)

    @classmethod
    def debug(self, msg, **kwargs):
        self._log(self.LOG_DEBUG, msg, **kwargs)

    @classmethod
    def info(self, msg, **kwargs):
        self._log(self.LOG_INFO, msg, **kwargs)

    @classmethod
    def notice(self, msg, **kwargs):
        self._log(self.LOG_NOTICE, msg, **kwargs)

    @classmethod
    def warn(self, msg, **kwargs):
        self._num_warnings += 1
        self._log(self.LOG_WARNING, msg, **kwargs)

    @classmethod
    def err(self, msg, **kwargs):
        self._num_errors += 1
        self._log(self.LOG_ERROR, msg, **kwargs)
        return False

    @classmethod
    def die(self, msg, status=1, **kwargs):
        self._num_errors += 1
        self._log(self.LOG_FATAL, msg, **kwargs)
        sys.exit(status)

    @classmethod
    def exit(self):
        sys.exit(self._num_errors > 0)
