#!/usr/bin/env python

import os
from collections import defaultdict
from pprint import pprint

# Could use DBSAPI or DASAPI or whatever, but I'm too lazy to learn it.

class das_query:
    def __init__(self, ana01=False, ana02=False, ana03=False, json=False):
        if sum((ana01, ana02, ana03)) > 1:
            raise ValueError('only one of ana0X options allowed')
        self.ana01 = ana01
        self.ana02 = ana02
        self.ana03 = ana03
        self.extra = 'instance=prod/phys01' if (ana01 or ana02 or ana03) else ''
        if ana02:
            self.extra = self.extra.replace('01', '02')
        if ana03:
            self.extra = self.extra.replace('01', '03')
        self.cmd = "das_client.py --limit=0 --query '%s %%s'" % self.extra
        self.json = json
        if json:
            self.cmd += ' --format=json'
        
    def __call__(self, query, line_filter=lambda s: True, line_xform=lambda s: s):
        full_cmd = self.cmd % query
        cmdout = os.popen(full_cmd).readlines()
        if self.json:
            return cmdout[0]
        ret = []
        for line in cmdout:
            line = line.strip()
            if line_filter(line):
                x = line_xform(line)
                if x is not None:
                    ret.append(x)
        if not ret:
            raise RuntimeError('query %r (ana01: %s ana02: %s ana03: %s) did not succeed. full das command:\n%s\ndas command output:\n%s' % (query, self.ana01, self.ana02, self.ana03, full_cmd, ''.join(cmdout) if cmdout else cmdout))
        return ret

def files_in_dataset(dataset, ana01=False, ana02=False, ana03=False):
    return das_query(ana01, ana02, ana03)('dataset=%s file' % dataset,
                                          lambda s: s.endswith('.root'))

def numevents_in_dataset(dataset, ana01=False, ana02=False, ana03=False):
    def xform(line):
        try:
            return int(line)
        except ValueError:
            return None
    return das_query(ana01, ana02, ana03)('dataset=%s | grep dataset.nevents' % dataset,
                                          line_xform=xform)[0]

def files_numevents_in_dataset(dataset, ana01=False, ana02=False, ana03=False):
    def xform(line):
        line = line.split()
        if not len(line) == 2 or not line[0].endswith('.root'):
            return None
        try:
            return line[0], int(line[1])
        except ValueError:
            return None
    return das_query(ana01, ana02, ana03)('dataset=%s file | grep file.name,file.nevents' % dataset,
                                          line_xform=xform)

def sites_for_dataset(dataset, ana01=False, ana02=False, ana03=False):
    return das_query(ana01, ana02, ana03)('dataset=%s site' % dataset,
                                          line_filter=lambda s: s.startswith('T'))

def files_for_events(run_events, dataset, ana01=False, ana02=False, ana03=False):
    run_lumis = defaultdict(list)
    for x in run_events: # list of runs, or list of (run, event), or list of (run, lumi, event)
        if type(x) == int:
            run_lumis[x] = None
        elif len(x) == 2:
            run_lumis[x[0]] = None
        else:
            run_lumis[x[0]].append(x[1])

    files = []

    json_str = das_query(ana01, ana02, ana03, json=True)('file,run,lumi dataset=%s' % dataset)
    #open('json_str','wt').write(json_str)
    #json_str = open('json_str2').read()
    obj = eval(json_str) # json.loads doesn't work...
    #pprint(obj)

    if type(obj) == dict and sorted(obj.keys()) == [u'apilist', u'ctime', u'das_server', u'data', u'incache', u'mongo_query', u'nresults', u'status', u'timestamp']:
        obj = obj['data']

    for x in obj:
        #assert len(x['run']) == len(x['lumi'])
        assert len(set(y['name'] for y in x['file'])) == 1

        keep = False
        class StopIt(Exception):
            pass

        try:
            for run_d in x['run']:
                run = run_d['run_number']
                allowed = run_lumis[run]
                if allowed is None:
                    keep = True
                    raise StopIt()

                for lumi_d in x['lumi']:
                    for lumi_lo, lumi_hi in lumi_d['number']:
                        for lumi in allowed:
                            if lumi >= lumi_lo and lumi <= lumi_hi:
                                keep = True
                                raise StopIt()
        except StopIt:
            pass

        if keep:
            files.append(str(x['file'][0]['name']))

    return files

if __name__ == '__main__':
    execfile('events_to_debug.txt')
    #pprint(files_for_events(duh, 'fuh'))
    #raise 1
    from JMTucker.Tools.Samples import *
    for s in data_samples[:5]:
        pprint(files_for_events(duh, s.dataset))
