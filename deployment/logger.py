import time

class Logger(object):

    def _get_timestamp(self):
        milliseconds = str(time.time()).split(".")
        millisecond = "0"
        if len(milliseconds) > 1:
            millisecond = milliseconds[-1]
        timestamp = time.strftime("%Z-%Y/%m/%d-%H:%M:%S") + "." + millisecond
        return timestamp

    def info(self, msg):

        print("<<INFO - {timestamp}>>: ".format(timestamp=self._get_timestamp()) + msg.title())

    def warn(self, msg):
        print("<<WARN - {timestamp}>>: ".format(timestamp=self._get_timestamp()) + msg.title())

    def error(self, msg):
        print("<<ERROR - {timestamp}>>: ".format(timestamp=self._get_timestamp()) + msg.title())