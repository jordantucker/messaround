#!/usr/bin/env python

import os, sys, subprocess, time, gzip, tempfile

if len(sys.argv) < 2:
    print 'usage: logcms.py [logfile=out...] [nogz] [nomove] [noshow] cfgfile [... rest of cmsRun arguments ...]'
    sys.exit(1)

args = []
log_fn = 'out.out'
gz = True
move = True
show = True
for a in sys.argv[1:]:
    if a.startswith('logfile='):
        log_fn = a.replace('logfile=', '')
    elif a == 'nomove':
        move = False
    elif a == 'nogz':
        gz = False
    elif a == 'noshow':
        show = False
    else:
        args.append(a)

if '.py' in args[0]:
    if not os.path.isfile(args[0]):
        raise ValueError('no config %s found!' % args[0])
    log_fn = 'out.' + os.path.basename(args[0]).replace('.py', '')
    
for arg in args:
    if ' ' in arg or '*' in arg or '"' in arg or "'" in arg or '$' in arg:
        raise ValueError('proper escaping of a character in "%s" not handled; refusing to run' % arg)
args = ' '.join(args)

tmp_log_fn = tempfile.mktemp()
shell_line = 'cmsRun %s >& %s' % (args, tmp_log_fn)
print shell_line
start = time.time()
print 'starting at', time.asctime()
print 'tail -f %s' % tmp_log_fn
print 'tail -f %s | grep Begin' % tmp_log_fn
exit_code = subprocess.call(shell_line, shell=True, executable='/bin/tcsh')
print 'cmsRun exit code:', exit_code, 'elapsed time: %.2f' % (time.time() - start)

if not move:
    log_fn = tmp_log_fn
    
if gz:
    if not log_fn.endswith('.gz'):
        log_fn += '.gz'
    os.system('gzip -c %s > %s' % (tmp_log_fn, log_fn))
    os.system('rm %s' % tmp_log_fn)
elif move:
    os.system('mv %s %s' % (tmp_log_fn, log_fn))

if not move:
    print 'did not move logfile, is at', log_fn

if show:
    logf = (gzip.open if gz else open)(log_fn)
    l = 0
    for x in logf:
        l += 1
    if exit_code != 0 or l < 85:
        print 'log file:'
        if l > 85:
            cmd = 'less'
        else:
            cmd = 'zcat' if gz else 'cat'
        os.system('%s %s' % (cmd, log_fn))

sys.exit(exit_code)
