import gc
import time, sys
from twisted.logger import Logger

log = Logger()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

GC_PERIOD_SECONDS = 1#3 * 60 * 60 # 3 hours

def is_hist_obj(tpe, _str_or_o):
    for t in pgc.id_types:
        if type(t) is str:
            return t == tpe
        elif tpe == t[0] and (_str_or_o if type(_str_or_o) is str else str(_str_or_o)).startswith(t[1]): # [type, val_start]
            return True
    return False

class Stat:
    def __init__(self, count, size, objects):
        self.count = count
        self.size = size
        self.objects = objects

def get_gc_stats():
    go = {}
    for o in gc.garbage:
        tpe = type_str(o)
        if tpe not in go:
            go[tpe] = Stat(1, sys.getsizeof(o), [])
        else:
            go[tpe].count += 1
            go[tpe].size += sys.getsizeof(o)
            go[tpe].objects.append((id(o), str(o)))
    allo = {}
    for o in gc.get_objects():
        tpe = type_str(o)
        if tpe not in allo:
            allo[tpe] = Stat(1, sys.getsizeof(o), [])
        else:
            allo[tpe].count += 1
            allo[tpe].size += sys.getsizeof(o)
            if is_hist_obj(tpe, o):
                allo[tpe].objects.append((id(o), str(o)[:180]))
    return [go, allo]

def stats_str(stat):
    tpe, count, size = stat
    prev_diff = [0, 0]
    
    if tpe in pgc.prev_stats:
        prev_diff[0] = count - pgc.prev_stats[tpe].count
        prev_diff[1] = size - pgc.prev_stats[tpe].size
    
    first_diff = [0, 0]
    
    if tpe in pgc.first_stats:
        first_diff[0] = count - pgc.first_stats[tpe].count
        first_diff[1] = size - pgc.first_stats[tpe].size
    
    prev_count_sigh = ''
    if prev_diff[0] > 0:
        prev_count_sigh = '+'

    first_count_sigh = ''
    if first_diff[0] > 0:
        first_count_sigh = '+'
    
    prev_size_sigh = ''
    if prev_diff[1] > 0:
        prev_size_sigh = '+'

    first_size_sigh = ''
    if first_diff[1] > 0:
        first_size_sigh = '+'

    s = "%s: %s,%s%s,%s%s %s,%s%s,%s%s" % (tpe, count, prev_count_sigh, prev_diff[0], first_count_sigh, first_diff[0], size, prev_size_sigh, prev_diff[1], first_size_sigh, first_diff[1])

    if prev_diff[0] != 0 or prev_diff[1] != 0 or first_diff[0] != 0 or first_diff[1] != 0:
        if prev_diff[0] > 0 or prev_diff[1] > 0:
            return bcolors.WARNING + s + bcolors.ENDC
        elif prev_diff[0] < 0 or prev_diff[1] < 0:
            return bcolors.OKGREEN + s + bcolors.ENDC
        else:
            return bcolors.OKBLUE + s + bcolors.ENDC
    else:
        return None #s # not changed

def pgc(none): # periodical_garbage_collect
    #global pool
    #pool.closeCachedConnections()

    tm = int(time.time())
    if tm - pgc.time >= GC_PERIOD_SECONDS:
        log.info('GC: COLLECTED: %s' % gc.collect())
        go, allo = get_gc_stats()
        log.info("GC: GARBAGE OBJECTS STATS (%s)" % len(go))
        for tpe, stats in sorted(go.iteritems(), key=lambda t: t[0]):
            log.info("GC: %s: %s, %s" % (tpe, stats.count. stats.size))

        log.info("GC: ALL OBJECTS STATS (%s)" % len(allo))

        if not pgc.first_stats:
            pgc.first_stats = allo

        size = 0
        cur_ids = []
        cur_values = []
        for tpe, stats in sorted(allo.iteritems(), key=lambda t: t[0]):
            scount = stats.count
            ssize = stats.size
            objects = stats.objects
            sstr = stats_str([tpe, scount, ssize])
            if sstr:
                log.info("GC: %s" % sstr)
            size += ssize
            for _id, _str in objects:
                if is_hist_obj(tpe, _str):
                    cur_ids.append(_id)
                    cur_values.append(_str)
        if not pgc.first_size:
            pgc.first_size = size
            pgc.prev_size = size
        log.info('GC: ALL OBJECT SIZE: %s,%s,%s' % (size, size - pgc.prev_size, size - pgc.first_size))

        if pgc.ids:
            new_ids = []
            for tpe_filter in pgc.id_types:
                #import pdb;pdb.set_trace()
                if type(tpe_filter) is str:
                    tpe = tpe_filter
                else:
                    tpe = tpe_filter[0]
                objects = allo[tpe].objects
                count = 0
                for _id, _str in objects:
                    if is_hist_obj(tpe, _str) and _id not in pgc.ids and (not pgc.filter_by_value or _str not in pgc.values):
                        log.info('GC new obj %s(%s): {str!r}' % (tpe, _id), str=_str)
                        count += 1
                        new_ids.append(_id)
                log.info('GC new obj %s: %s items' % (tpe, count))

            step = -1
            for ids in pgc.hist_ids:
                step_ids = []
                for tpe_filter in pgc.id_types:
                    if type(tpe_filter) is str:
                        tpe = tpe_filter
                    else:
                        tpe = tpe_filter[0]
                    objects = allo[tpe].objects
                    count = 0
                    for _id, _str in objects:
                        if _id in ids and is_hist_obj(tpe, _str) and (not pgc.filter_by_value or _str not in pgc.values):
                            log.info('GC %s new obj %s(%s): {str!r}' % (step, tpe, _id), str = _str)
                            count += 1
                            step_ids.append(_id)
                            break
                    log.info('GC %s new obj %s: %s items' % (step, tpe, count))
                step -= 1
                ids[:] = [] #clear list
                ids.extend(step_ids) # add evailable
                if step_ids:
                    pgc.oldest_id = step_ids[-1]
            pgc.hist_ids.insert(0, new_ids)
            pgc.hist_ids[:] = pgc.hist_ids[0:3]
            log.info('GC oldest id %s' % pgc.oldest_id)
            #if pgc.oldest_id:
            #    print_obj_id_refs(pgc.oldest_id)


        pgc.ids = cur_ids
        pgc.values = cur_values
        pgc.prev_stats = allo
        pgc.prev_size = size

        pgc.time = tm

OLDEST_OBJ_DEPTH = 1

def print_obj_ref(depth, os):
    for o in os:
        refs = gc.get_referrers(o)
        log.info('GC oldest %s ref cnt:%s %s(%s): %s' % ('*' * depth, len(refs), str(type(o)), id(o), str(o)[:500]))
        if depth < OLDEST_OBJ_DEPTH:
            print_obj_ref(depth+1, refs)

def get_obj_by_id(o_id):
    return [o for o in gc.get_objects() if id(o)==o_id][0]

def print_obj_id_refs(o_id):
    #print_obj_ref(0, (get_obj_by_id(o_id),))
    o = get_obj_by_id(o_id)
    refs = gc.get_referrers(o)
    log.info('gc oldest obj cnt:%s %s(%s): {str!r}' % (len(refs), str(type(o)), id(o)), {'str': str(o)[:500]})
    #import types
    first = True
    for r in refs:
        #    import pdb;pdb.set_trace()
        log.info('gc oldest %s ref cnt:%s %s(%s): {str!r}' % ('*', -1, str(type(r)), id(r)), {'str': str(r)[:500].replace(hex(o_id), bcolors.WARNING + str(hex(o_id)) + bcolors.ENDC)})
        if first and type(r) is dict:
            refs2 = gc.get_referrers(r)
            for r2 in refs2:
                log.info('gc oldest %s ref cnt:%s %s(%s): {str!r}' % ('**', -2, str(type(r2)), id(r2)), {'str': str(r2)[:500].replace(hex(id(r)), bcolors.WARNING + str(hex(id(r))) + bcolors.ENDC)})
                if str(type(r2)) == "<type 'collections.deque'>":
                    refs3= gc.get_referrers(r2)
                    for r3 in refs3:
                        log.info('gc oldest %s ref cnt:%s %s(%s): {str!r}' % ('**', -3, str(type(r3)), id(r3)), {'str': str(r3)[:500].replace(hex(id(r2)), bcolors.WARNING + str(hex(id(r2))) + bcolors.ENDC)})

            first = False


pgc.first_stats = None
pgc.prev_stats = {}
pgc.first_size = None
pgc.prev_size = None

pgc.oldest_id = None
pgc.hist_ids = []


def type_str(obj):
    switcher = {
            "<type 'instance'>": lambda o: str(type(o)) + '(' + o.__class__.__name__ + ')',
            "<type 'instancemethod'>": lambda o: str(type(o)) + '(' + str(o) + ')'
        }
    func = switcher.get(str(type(obj)), lambda o: str(type(o)))
    return func(obj)

pgc.ids = []
pgc.id_types = [
        #["<type 'instance'>", "<twisted.web.client._HTTP11ClientFactory instance"],
        #"<type 'instancemethod'>",
        #"<type 'instance'>(DelayedCall)",
        #"<class 'twisted.logger._logger.Logger'>",
        #"<type 'list'>"
        ]
pgc.values = []
pgc.filter_by_value = False

pgc.time = int(time.time())
