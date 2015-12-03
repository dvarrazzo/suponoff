"""
Get info about a running process
"""

import time

import psutil

import logging
logger = logging.getLogger()


def get_process_info(pid):
    result = {}
    try:
        proc = psutil.Process(pid)
    except:
        logger.exception("Process %s:", pid)
        return result

    result["fileno"] = proc.num_fds()
    try:
        proc.rlimit
    except AttributeError:
        max_fileno = -1
        max_vmsize = -1
    else:
        max_fileno = proc.rlimit(psutil.RLIMIT_NOFILE)[0]
        max_vmsize = proc.rlimit(psutil.RLIMIT_AS)[0]
    if max_fileno != -1:
        result["max_fileno"] = max_fileno

    result["numconnections"] = len(proc.connections('all'))
    result["numfiles"] = len(proc.open_files())

    if max_vmsize != -1:
        result["max_vmsize"] = str(max_vmsize)
    result["vmsize"] = str(proc.memory_info()[1])
    result["numchildren"] = len(proc.children())
    result["numthreads"] = proc.num_threads()
    result["cpu"] = ",".join(
        str(x) for x in [time.time()] + list(proc.cpu_times()))
    result["diskio"] = ",".join(

        str(x) for x in [time.time()] + list(proc.io_counters()))
    return result
