import os
import time
import subprocess as sp

here = os.path.abspath(os.path.dirname(__file__))
datadir = os.path.join(here, 'data')

def datafile(*path):
    return os.path.join(datadir, *path)

def run_supervisor(config):
    cmdline = [ os.path.join(here, '../env2/bin/supervisord'),
        '-n', '-c', datafile(config) ]
    cwd = os.path.join(here, '..')
    env = dict(os.environ)
    env['PATH'] = cwd + os.pathsep + os.environ['PATH']
    sup = sp.Popen(cmdline, close_fds=True, cwd=cwd, env=env)
    time.sleep(5)       # TODO: something more event-based?
    return sup

def stop_supervisor(sup):
    sup.terminate()
    rc = sup.wait()
    print ("sup stopped with %s" % rc)
