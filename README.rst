suponoff is a web interface to supervisor
=========================================

suponoff (short for Supervisor On/Off) is a Django app to control supervisor and
monitor the programs running under supervisor.

Every supervisor you want to monitor shoud register their state into a redis
instance. This is done by the script ``sup_broadcast.py``, which is an event
listener that can be configured in the supervisor itself with a config such::

    [eventlistener:sup_broadcast]
    command=python bin/sup_broadcast.py -c /path/to/supervisor.cfg
    events = PROCESS_STATE, SUPERVISOR_STATE_CHANGE, TICK_60, PROCESS_GROUP,
        REMOTE_COMMUNICATION

Optionally, you may run the provided program ``suponoff-monhelper.py``, which
should listen on the port following supervisor's (usually 9002) and provides
the following additional functionalities:

1. Reports back the resource limits and usage of the processes, such as
   number of file descriptors, memory, cpu, number of threads and subprocesses;

2. Provides the ability to monitor application log files in some cases: it
   looks at the process command line and parses it, looking for ``--logfile``
   or ``--log-file`` arguments.If it can find and open the indicated log file,
   then you will be able to open this log file from the web interface.


To use this app, create a Django project that includes ``suponoff`` in its
applications and includes the URLs from ``suponoff.urls``.  Then you add the
``SUP_REDIS_URL`` setting (where to get registered supervisors).  The web
interface can also add "tags" to each program, allowing you to filter by tags.
For an example, see the ``demo`` project in the source distribution.

Screenshot:
-----------
.. image:: https://raw.githubusercontent.com/GambitResearch/suponoff/master/demo/screenshot.png
