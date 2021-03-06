#!/usr/bin/env python
import json
import logging
from collections import defaultdict
from six.moves import urllib

from six.moves import xmlrpc_client

from django.core.context_processors import csrf
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings

import supcast


LOG = logging.getLogger(__name__)


def _get_supervisor(name):
    url = supcast.get_url(name)
    supervisor = xmlrpc_client.ServerProxy(url, verbose=False)
    return supervisor


def _get_monhelper_url(name):
    sup_url = supcast.get_url(name)
    url = urllib.parse.urlparse(sup_url)
    port = url.port
    if port is None:
        raise ValueError("no port in url: %s" % sup_url)
    bits = list(url.netloc.partition(str(port)))
    bits[1] = str(port + 1)
    new_url = url._replace(netloc=''.join(bits))
    return urllib.parse.urlunparse(new_url)

def _get_monhelper(name):
    # Assume monhelper is running at port + 1 of supervisor
    url = _get_monhelper_url(name)
    monhelper = xmlrpc_client.ServerProxy(url, verbose=False)
    return monhelper


def _get_server_data(name, resource_pids, metadata):
    supervisor = _get_supervisor(name)
    monhelper = _get_monhelper(name)
    try:
        processes = supervisor.supervisor.getAllProcessInfo()
        server = {}
        pids = []
        for process in processes:
            if process["pid"]:
                pids.append(process["pid"])
            group_name = process['group']
            group = server.setdefault(group_name,
                                      {"processes": [],
                                      "total_processes": 0,
                                      "running_processes": 0})
            process["can_be_stopped"] = process["statename"] in {"RUNNING"}
            process["can_be_restarted"] = process["statename"] in {"RUNNING"}
            process["can_be_started"] = process["statename"] in {"STOPPED", "EXITED"}
            if process["statename"] in {"RUNNING"}:
                group['running_processes'] += 1
            else:
                group['has_not_running_processes'] = True
            group['total_processes'] += 1
            group['processes'].append(process)

            if group['total_processes'] == 1:
                group_tags = set()
                for server_regex, group_regex, tags in metadata:
                    group_match = group_regex.match(group_name)
                    server_match = server_regex.match(name)
                    if group_match and server_match:
                        group_tags.update(tags)
                group['tags'] = list(sorted(group_tags))

        if resource_pids:
            try:
                resources_dict = monhelper.getProcessResourceUsage(
                    list(int(x) for x in resource_pids))
            except ConnectionRefusedError:
                LOG.warning("Remote server %s doesn't have the monhelper"
                            " extension", name)
            else:
                for pid, resources in resources_dict.items():
                    for process in processes:
                        if str(process['pid']) == pid:
                            process['resources'] = resources
                            break
    finally:
        supervisor("close")()
        monhelper("close")()
    return server

def get_data(request):
    data = json.dumps(supcast.get_all_state())
    return HttpResponse(data, content_type='application/json')

@ensure_csrf_cookie
def home(request, template_name="suponoff/index.html"):
    data = supcast.get_all_state()

    context = {
        "data": json.dumps(data),
        "SITE_ROOT": settings.SITE_ROOT,
    }

    context.update(csrf(request))

    #LOG.debug("Context: %s", context)
    resp = render_to_response(template_name, context)
    return resp


def action(request):
    sup = request.POST['supervisor']
    sup = _get_supervisor(sup)
    program = "{}:{}".format(request.POST['group'], request.POST['process'])
    action = request.POST['action']
    try:
        if action == 'start':
            LOG.info("starting %s %s", sup, program)
            sup.supervisor.startProcess(program)
        elif action == 'stop':
            LOG.info("stopping %s %s", sup, program)
            sup.supervisor.stopProcess(program)
        elif action == 'restart':
            try:
                LOG.info("stopping %s %s", sup, program)
                sup.supervisor.stopProcess(program)
            except:
                pass
            LOG.info("starting %s %s", sup, program)
            sup.supervisor.startProcess(program)
        else:
            return HttpResponse("bad action: %s" % action, status=400)
    except Exception as e:
        LOG.error("failed to %s %s: %s", action, program, e)
        resp = HttpResponse(str(e), status=400)
    else:
        resp = HttpResponse('')
        resp['Access-Control-Allow-Origin'] = "*"
    finally:
        sup("close")()

    return resp


def group_action(request):
    procs = request.POST.get('procs')
    try:
        procs = json.loads(procs)
    except:
        return HttpResponse("bad procs: %s" % procs, status=400)

    action = request.POST['action']
    sups = { s for s, _ in procs }
    sups = { s: _get_supervisor(s) for s in sups }
    wait = len(procs) == 1
    try:
        for sup, group in procs:
            sup = sups[sup]
            try:
                if action == 'start_all':
                    LOG.info("starting %s %s wait=%s", sup, group, wait)
                    sup.supervisor.startProcessGroup(group, wait)
                elif action == 'stop_all':
                    LOG.info("stopping %s %s wait=%s", sup, group, wait)
                    sup.supervisor.stopProcessGroup(group, wait)
                else:
                    return HttpResponse("bad action: %s" % action, status=400)
            except Exception as e:
                LOG.error("failed to %s %s: %s", action, group, e)
    finally:
        for sup in sups.values():
            sup("close")()

    resp = HttpResponse('')
    resp['Access-Control-Allow-Origin'] = "*"
    return resp


def monitor(request):
    procs = request.POST.get('procs')
    try:
        procs = json.loads(procs)
        procs = [ dict(
            supervisor=p['supervisor'], group=p['group'], process=p['process'])
            for p in procs ]
    except:
        return HttpResponse("bad procs: %s" % procs, status=400)

    psups = defaultdict(list)
    for p in procs:
        psups[p['supervisor']].append(p)

    for sup, procs in psups.items():
        sup = _get_supervisor(sup)
        sup.supervisor.sendRemoteCommEvent('monitor',
            json.dumps(procs))

    resp = HttpResponse('')
    resp['Access-Control-Allow-Origin'] = "*"
    return resp

def get_program_logs(request):
    logs = "Logs for program {}:{} in server {}".format(
        request.GET['group'], request.GET['program'], request.GET['server'])
    stream = request.GET['stream']
    assert stream in {'stdout', 'stderr', 'applog'}

    if stream == 'stdout':
        supervisor = _get_supervisor(request.GET['server'])
        try:
            logs, _offeset, _overflow = supervisor.supervisor.tailProcessStdoutLog(
                "{}:{}".format(request.GET['group'], request.GET['program']),
                -100000, 100000)
        finally:
            supervisor("close")()
    elif stream == 'stderr':
        supervisor = _get_supervisor(request.GET['server'])
        try:
            logs, _offeset, _overflow = supervisor.supervisor.tailProcessStderrLog(
                "{}:{}".format(request.GET['group'], request.GET['program']),
                -100000, 100000)
        finally:
            supervisor("close")()
    elif stream == 'applog':
        supervisor = _get_monhelper(request.GET['server'])
        try:
            logs, _offeset, _overflow = supervisor.tailApplicationLog(
                int(request.GET['pid']), -100000, 100000)
        finally:
            supervisor("close")()
    else:
        raise AssertionError
    return HttpResponse(logs, content_type='text/plain')
