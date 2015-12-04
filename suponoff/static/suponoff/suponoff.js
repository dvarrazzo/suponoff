/* jshint asi: true */

'use strict';

var RESOURCE_WARNING_FRACTION = 0.80
var RESOURCE_ERROR_FRACTION   = 0.95

// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = window.jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
        }
    }
});


function get_ajax_url(action)
{
	var url = window.location.href;
	if (url[url.length - 1] == '#')
		url = url.slice(0, url.length - 1)
	if (url[url.length - 1] != '/')
		url += '/'
	url += action
	return url
}

// http://stackoverflow.com/q/10420352/2211825
function getReadableFileSizeString(fileSizeInBytes)
{
    var i = -1;
    var byteUnits = [' kB', ' MB', ' GB', ' TB', 'PB', 'EB', 'ZB', 'YB'];
    do {
        fileSizeInBytes = fileSizeInBytes / 1024;
        i++;
    } while (fileSizeInBytes > 1024);

    return Math.max(fileSizeInBytes, 0.1).toFixed(1) + byteUnits[i];
}

function get_resource_alert_level(resource_value, resource_limit)
{
    var alert_level = 0;
    var fraction = resource_value / resource_limit;
    if (fraction > RESOURCE_WARNING_FRACTION)
        alert_level = 1;
    if (fraction > RESOURCE_ERROR_FRACTION)
        alert_level = 2;
    return alert_level;
}

function update_procinfo(procinfo)
{
    var box = $('#' + process_id(procinfo));
    if (!box) { return; }

    var level = 0;

    // stash a copy of the last known resource levels into the dom element, for later retrieval
    // they will be used to adjust the alert level for the process; even if we do not have
    // up-to-date resource levels, we want to make the program and group divs the correct color
    // based on the last reported levels, otherwise they revert back to green.
    box.data('procinfo', procinfo);

    // modify the alert level based on resource levels
    if ('fileno' in procinfo && 'max_fileno' in procinfo)
        level = Math.max(level, get_resource_alert_level(
            procinfo.fileno, procinfo.max_fileno));
    if ('vmsize' in procinfo && 'max_vmsize' in procinfo)
        level = Math.max(level, get_resource_alert_level(
            procinfo.vmsize, procinfo.max_vmsize));

    box.find('.resources-heading').show();

    var fileno_div = box.find('div.resource.fileno');
    if ('fileno' in procinfo) {
        if ('max_fileno' in procinfo) {
            fileno_div.find('.textual-value')
                .text(procinfo.fileno + " / " + procinfo.max_fileno);
            fileno_div.find('.progress-bar').
                attr('aria-valuenow', procinfo.fileno).
                attr('aria-valuemax', procinfo.max_fileno).
                css('width', (procinfo.fileno*100/procinfo.max_fileno) + '%');
            fileno_div.find('.progress').show();
        } else {
            fileno_div.find('.textual-value').text(procinfo.fileno);
        }
        fileno_div.find('.textual-value').attr('title',
            procinfo.numfiles + " open files, " +
            procinfo.numconnections + " sockets")
        fileno_div.show();
    } else {
        fileno_div.hide();
    }

    var vmsize_div = box.find('div.resource.vmsize');
    if ('vmsize' in procinfo) {
        if ('max_vmsize' in procinfo) {
            vmsize_div.find('.textual-value').text(
                getReadableFileSizeString(procinfo.vmsize) + " / " +
                getReadableFileSizeString(procinfo.max_vmsize));
            vmsize_div.find('.progress-bar').
                attr('aria-valuenow', procinfo.vmsize).
                attr('aria-valuemax', procinfo.max_vmsize).
                css('width', (procinfo.vmsize*100/procinfo.max_vmsize) + '%');
            vmsize_div.find('.progress').show();
        } else {
            vmsize_div.find('.textual-value').text(
                getReadableFileSizeString(procinfo.vmsize));
        }
        vmsize_div.show();
    } else {
        vmsize_div.hide();
    }

    var numchildren_div = box.find('div.resource.numchildren');
    if ('numchildren' in procinfo && procinfo.numchildren) {
        numchildren_div.show().find('.numchildren').text(procinfo.numchildren);
    } else {
        numchildren_div.hide();
    }

    var numthreads_div = box.find('div.resource.numthreads');
    if ('numthreads' in procinfo && procinfo.numthreads > 1) {
        numthreads_div.show().find('.numthreads').text(procinfo.numthreads);
    } else {
        numthreads_div.hide();
    }

    var sparkline;
    var timestamp;
    var new_value;

    var cpu_div = box.find('div.resource.cpu');
    if ('cpu' in procinfo) {
        sparkline = cpu_div.find('.sparkline');
        timestamp = procinfo.cpu[0];
        var cpu = procinfo.cpu[1] + procinfo.cpu[2];
        if (sparkline.data('last_timestamp') !== undefined) {
            new_value = (cpu - sparkline.data('last_cpu'))
                / (timestamp - sparkline.data('last_timestamp'));
            if (new_value >= 0) {
                var values = sparkline.data('values');
                values.push(Math.round(new_value*100));
                while (values.length > 60) {
                    values.shift();
                }
            }
            sparkline.sparkline(sparkline.data('values'), {
                type: 'line', height: '32', lineWidth: 2,
                chartRangeMin: 0, chartRangeMax: 100,
            })
        } else {
            sparkline.data('values', []);
        }
        sparkline.data('last_cpu', cpu);
        sparkline.data('last_timestamp', timestamp);
        cpu_div.show();
    } else {
        cpu_div.hide();
    }

    var diskio_div = box.find('div.resource.diskio')
    if ('diskio' in procinfo) {
        sparkline = diskio_div.find('.sparkline');
        timestamp = procinfo.diskio[0];
        var diskio = (procinfo.diskio[3] + procinfo.diskio[4]) / 1024;
        if (sparkline.data('last_timestamp') !== undefined) {
            new_value = (diskio - sparkline.data('last_diskio'))
                / (timestamp - sparkline.data('last_timestamp'))
            if (new_value >= 0) {
                var values = sparkline.data('values');
                values.push(Math.round(new_value*100))
                while (values.length > 60) {
                    values.shift()
                }
            }
            sparkline.sparkline(sparkline.data('values'), {
                type: 'line', height: '32', lineWidth: 2 });
        } else {
            sparkline.data('values', []);
        }
        sparkline.data('last_diskio', diskio);
        sparkline.data('last_timestamp', timestamp);
        diskio_div.show();
    } else {
        diskio_div.hide();
    }

    box.attr('data-level', level).data('level', level);
}

function open_stream(button, stream)
{
	var program_div = $(button).parent('div.program')
	var program = program_div.attr('data-program-name')
	var group = program_div.parents('div.group').attr('data-group-name')
	var server = program_div.parents('div.server').attr('data-server-name')

	$.ajax({
        url: get_ajax_url('data/program-logs'),
		data: {
			stream: stream,
			program: program,
			pid: program_div.attr('data-pid'),
			group: group,
			server: server,
		}
	}).done(function(data) {
		var pre = $('#show-logs-dialog div.modal-body pre')
		pre.text(data)
		var h = Math.round($(window).height()*0.7)
		pre.css('height', h + 'px')
		pre.css('max-height', h + 'px')
		$('#show-logs-dialog .modal-title').text(
            server + ": " + group + ':' + program + " " + stream);

		$('#show-logs-dialog').modal()
	})
}

window.open_stdout = function(button)
{
	return open_stream(button, 'stdout');
}

window. open_stderr = function(button)
{
	return open_stream(button, 'stderr');
}

window.open_applog = function (button)
{
	return open_stream(button, 'applog');
}


function group_action() {
	var button = $(this);
	var action = button.data('action');
	var box = button.closest('.box');

	var groups;
	if (box.hasClass('procgroup')) {
		groups = box;
	} else {
		groups = box.find('.procgroup');
	}

	var data = {
		action: action,
		procs: JSON.stringify($.makeArray(groups.map(function () {
			return [[$(this).data('supervisor'), $(this).data('group')]]})))
	};

	$(button).button('loading')
	$.ajax({
		url: '/group_action',
		type: 'POST',
		data: data
	}).complete(function() {
		$(button).button('reset')
	})
}

function process_action() {
	var button = $(this);
	var action = button.data('action');
	var proc = $(button).closest('.process').data('process');
	var data = {
		action: action,
		supervisor: proc.supervisor,
		group: proc.group,
		process: proc.process,
	};
	$(button).button('loading')
	$.ajax({
		url: '/action',
		type: 'POST',
		data: data
	}).complete(function() {
		$(button).button('reset')
	})
}

function set_group_monitor(box, monitored, state) {
	if (!box.hasClass('procgroup')) {
		// Only when you open a group
		return;
	}

	var new_mon = Object();
	var procs = box.find('.process');
	if (state) {
		procs.each(function () {
			monitored[$(this).attr('id')] = true;
			new_mon[$(this).attr('id')] = true;
		});
	} else {
		procs.each(function () {
			delete monitored[$(this).attr('id')];
		});
	}
	refresh_monitored(new_mon);
}

function refresh_monitored(monitored) {
	var procs = $.map(monitored, function (v, k) {
		var proc = $('#' + k).data('process');
		if (proc) {
			return {
				supervisor: proc.supervisor,
				group: proc.group,
				process: proc.process };
		}
	});

	if (procs.length == 0) { return; }

	$.ajax({
		url: '/monitor',
		type: 'POST',
		data: { procs: JSON.stringify($.makeArray(procs)) }
	});
}

function data2procs(data) {
    var procs = [];
    for (var sname in data.supervisors) {
        var sdata = data.supervisors[sname];
        for (var gname in sdata.groups) {
            var gdata = sdata.groups[gname];
            gdata.tags = gdata.tags || [];
            gdata.tags.push('supervisor:' + sname);
            gdata.tags.sort();
            for (var pname in gdata.processes) {
                var proc = gdata.processes[pname];
                proc.supervisor = sname;
                proc.group = gname;
                proc.sup_group = sname + '-' + gname;
                proc.process = pname;
                proc.id = process_id(proc);
                proc.tags = gdata.tags;

                // Convert tags into attributes too
                for (var i in proc.tags) {
                    var tag = proc.tags[i];
                    var c = tag.search(':');
                    if (c > -1) {
                        proc[tag.substring(0,c)] = tag.substring(c+1);
                    } else {
                        proc[tag] = true;
                    }
                }
                procs.push(proc);
            }
        }
    }
    return procs;
}

function process_id(process) {
	return 'proc-' + process.supervisor
		+ '-' + process.group + '-' + process.process;
}

function Axis (label) {
	this.label = label
	this.values = [];
}

Axis.prototype.add_value = function (value) {
	if (0 > $.inArray(value, this.values)) {
		this.values.push(value);
	}
}

function collect_axes(procs) {
	var rv = Object();
	// Collect the possible attributes we may care. Some we know, some we
	// get from the tags.
	$.each(procs, function(i, proc) {
		$.each(proc.tags, function(j, tag) {
			var c = tag.search(':');
			var attr = $.trim(tag.substring(0,c));
			var val = $.trim(tag.substring(c+1));
			if (rv[attr] === undefined)
				rv[attr] = new Axis(attr);
			rv[attr].add_value(val);
		});
	});

	// Collect the values from the attributes found
	$.each(procs, function(i, proc) {
		for (var attr in rv) {
			if (rv[attr].label != '') {
				rv[attr].add_value(proc[attr] || 'undefined');
			}
		}
	});

	// Sort values and arrays
	rv = $.map(rv, function (v) { v.values.sort(); return v; });
	rv.sort(function (a1, a2) { return a1.label > a2.label; });
	return rv;
}
