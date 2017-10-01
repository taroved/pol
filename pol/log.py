import sys
from twisted.logger import globalLogBeginner, formatEventAsClassicLogText


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class LogHandler(object):
    """Handler of twisted log meaasges"""

    def __init__(self):
        #import pdb;pdb.set_trace()
        # requred, discardBuffer gets rid of the LimitedHistoryLogObserver, redirectStandardIO will loop print action
        globalLogBeginner.beginLoggingTo([self.print_log], discardBuffer=True, redirectStandardIO=False)


    def print_log(self, event):
        if 'isError' in event and event['isError']:
            sys.stdout.write(bcolors.FAIL + formatEventAsClassicLogText(event) + bcolors.ENDC)
            sys.stderr.write(formatEventAsClassicLogText(event))
            sys.stderr.flush()
        else:
            sys.stdout.write(formatEventAsClassicLogText(event))
        sys.stdout.flush()

