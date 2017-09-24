import time
from pympler import tracker
import gc


class Monitor(object):

	prev_time = None

	def __init__(self, period_second=10 * 60, log=None):
		self.period_second = period_second
		self.log = log
		self.tr = tracker.SummaryTracker()

	def show_diff(none):
	    tm = int(time.time())
	    if not self.prev_time or tm - prev_time >= self.period_second:
	        gc.collect()
	        for line in tr.format_diff():
	            self.log.info(line)
	        self.prev_time = tm
