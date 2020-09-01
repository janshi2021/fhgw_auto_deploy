import time
import sys


class Logger(object):

    def _get_timestamp(self):
        milliseconds = str(time.time()).split(".")
        millisecond = "0"
        if len(milliseconds) > 1:
            millisecond = milliseconds[-1]
        timestamp = time.strftime("%Z-%Y/%m/%d-%H:%M:%S") + "." + millisecond
        return timestamp

    def _log_directly(self, msg):
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()

    def info(self, msg):
        self._log_directly("<<INFO - {timestamp}>>: ".format(timestamp=self._get_timestamp()) + msg)

    def debug(self, msg):
        self._log_directly("<<DEBUG - {timestamp}>>: ".format(timestamp=self._get_timestamp()) + msg)

    def warn(self, msg):
        self._log_directly("<<WARN - {timestamp}>>: ".format(timestamp=self._get_timestamp()) + msg)

    def error(self, msg):
        self._log_directly("<<ERROR - {timestamp}>>: ".format(timestamp=self._get_timestamp()) + msg)

    def log_header(self, msg):
        self._log_directly("<<STEP - {timestamp}>>: ####".format(timestamp=self._get_timestamp()) + msg)
