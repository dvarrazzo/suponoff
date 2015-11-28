/* jshint asi: true */

'use strict';

var $ = window.$;
var _ = window._;

var ALERT_LEVEL_CLASSES = {
	0: 'bg-success',
	1: 'bg-info',
	2: 'bg-warning',
	3: 'bg-warning',
	4: 'bg-danger'
}

var TAG_FILTER_MODE_AND = false;
var RESOURCE_WARNING_FRACTION = 0.80
var RESOURCE_ERROR_FRACTION   = 0.95



var UPDATE_INTERVAL = 5000 // interval between updates, in milliseconds
// number of updates after which we query full resources, even for hidden programs
var UPDATE_FULL_RESOURCES = 12

var UPDATE_NUMBER = 0;




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


$(document).ready(function() {
	$('.group_details_toggle').click(function(){
		var programs = $(this).parent().parent().find('.program')
		programs.toggle('fast')
	})


	$('#node-finder').keypress(function(e){
		if(e.keyCode == 13) {
			node_finder(e.target.value)
		}
	})

	$('#show-logs-dialog').on('shown.bs.modal', function () {
		var pre = $('#show-logs-dialog div.modal-body pre')
		var height = pre[0].scrollHeight;
		pre.scrollTop(height);
	})


	$('.tag-toggles input').change(filter_by_tags)

	update().done(function(){
		//console.log('first update done');
		$('#page-loading').fadeOut(1000);
	})

	// setInterval(update, UPDATE_INTERVAL)

    $('#tag-filter-mode').change(function() {
      TAG_FILTER_MODE_AND = $(this).prop('checked')
      filter_by_tags()
    })

	filter_by_tags()
})

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

function update()
{
	var resource_programs
	if (UPDATE_NUMBER % UPDATE_FULL_RESOURCES === 0) {
		resource_programs = $('div.program')
	} else {
		resource_programs = $('div.program:visible')
	}
	UPDATE_NUMBER += 1
	var server_pids = {}
	resource_programs.each(function(idx, program) {
		var server = $(program).parents('div.server').attr('data-server-name')
		var pids = server_pids[server]
		if (pids === undefined) {
			pids = []
			server_pids[server] = pids
		}
		pids.push($(program).attr('data-pid'))
	});
	// console.log(pids)
	return $.ajax({
        url: get_ajax_url('data'),
		type: 'POST',
		data: JSON.stringify({server_pids: server_pids})
	}).done(update_data_received)
}

function update_data_received(data)
{
	//console.log( 'data:', data);

	for (var server_name in data.supervisors) {
		var server = data.supervisors[server_name]
		for (var group_name in server.groups) {
			var group = server.groups[group_name]
			var group_alert_level = 0
			var group_num_processes_running = 0
			for (var process_idx in group.processes) {
				var process = group.processes[process_idx]
				var process_alert_level = update_process_ex(server_name, group_name, process)
				if (process_alert_level > group_alert_level)
					group_alert_level = process_alert_level
				if (process.statename == 'RUNNING')
					group_num_processes_running += 1
			}
			var group_div = $(_.template('div.server#server-<%= server %> div.group#group-<%= group %>',
										 {server: server_name, group: group_name}))
			group_div.find('>h4>span.group-name').removeClass('bg-success bg-danger bg-info bg-warning').addClass(
				ALERT_LEVEL_CLASSES[group_alert_level])
			group_div.find('.num-processes-running').text(group_num_processes_running.toString())
		}
	}

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
	var alert_level = 0
	var fraction = resource_value / resource_limit
	if (fraction > RESOURCE_WARNING_FRACTION)
		alert_level = 2
	if (fraction > RESOURCE_ERROR_FRACTION)
		alert_level = 4
	return alert_level
}

function update_process_ex(server_name, group_name, process)
{
	//console.debug(server_name, group_name, process)
	var query = _.template('div.server#server-<%= server %> div.group#group-<%= group %> div.program#process-<%= program %>',
						   {server: server_name, group: group_name, program: process.name})
	var program_div = $(query)
	//console.debug(program_div)
	program_div.find('.program-description').text(process.description)
	program_div.find('.program-state').text(process.statename)
	program_div.attr('data-pid', process.pid)

	var alert_level =
		{
			'RUNNING':  0,
			'STOPPED':  2,
			'BACKOFF':  4,
			'STARTING': 1,
			'STOPPING': 1,
			'EXITED':   3,
			'FATAL':    4
		}[process.statename]

	if ('resources' in process) {
		// stash a copy of the last known resource levels into the dom element, for later retrieval
		// they will be used to adjust the alert level for the process; even if we do not have
		// up-to-date resource levels, we want to make the program and group divs the correct color
		// based on the last reported levels, otherwise they revert back to green.
		program_div[0].resources = process.resources
	}
	var resources = program_div[0] && program_div[0].resources
	if (resources !== undefined) {
		// modify the alert level based on resource levels
		if ('fileno' in resources && 'max_fileno' in resources)
			alert_level = Math.max(alert_level, get_resource_alert_level(resources.fileno, resources.max_fileno))
		if ('vmsize' in resources && 'max_vmsize' in resources)
			alert_level = Math.max(alert_level, get_resource_alert_level(resources.vmsize, resources.max_vmsize))
	}

	if ('resources' in process) {
		program_div.find('.resources-heading').show()
		var fileno_div = program_div.find('div.resource.fileno')
		if ('fileno' in process.resources) {
			if ('max_fileno' in process.resources) {
				fileno_div.find('.textual-value').text(_.template('<%= current %> / <%= max %>', {current: process.resources.fileno,
																								  max: process.resources.max_fileno}))
				fileno_div.find('.progress-bar').
					attr('aria-valuenow', process.resources.fileno).
					attr('aria-valuemax', process.resources.max_fileno).
					css('width', (process.resources.fileno*100/process.resources.max_fileno) + '%')
				fileno_div.find('.progress').show()
			} else {
				fileno_div.find('.textual-value').text(_.template('<%= current %>', {current: process.resources.fileno}))
			}
			fileno_div.find('.textual-value').attr('title', _.template('<%= files %> open files, <%= connections %> sockets', {files: process.resources.numfiles, connections: process.resources.numconnections}))
			fileno_div.show()
		} else {
			fileno_div.hide()
		}

		var vmsize_div = program_div.find('div.resource.vmsize')
		if ('vmsize' in process.resources) {
			if ('max_vmsize' in process.resources) {
				vmsize_div.find('.textual-value').text(_.template('<%= current %> / <%= max %>', {current: getReadableFileSizeString(process.resources.vmsize),
																								  max: getReadableFileSizeString(process.resources.max_vmsize)}))
				vmsize_div.find('.progress-bar').
					attr('aria-valuenow', process.resources.vmsize).
					attr('aria-valuemax', process.resources.max_vmsize).
					css('width', (process.resources.vmsize*100/process.resources.max_vmsize) + '%')
				vmsize_div.find('.progress').show()
			} else {
				vmsize_div.find('.textual-value').text(_.template('<%= current %>', {current: getReadableFileSizeString(process.resources.vmsize)}))
			}
			vmsize_div.show()
		} else {
			vmsize_div.hide()
		}

		var numchildren_div = program_div.find('div.resource.numchildren')
		if ('numchildren' in process.resources && process.resources.numchildren) {
			numchildren_div.find('.numchildren').text(process.resources.numchildren.toString())
			numchildren_div.show()
		} else {
			numchildren_div.hide()
		}

		var numthreads_div = program_div.find('div.resource.numthreads')
		if ('numthreads' in process.resources && process.resources.numthreads > 1) {
			numthreads_div.find('.numthreads').text(process.resources.numthreads.toString())
			numthreads_div.show()
		} else {
			numthreads_div.hide()
		}
		var sparkline
		var last_timestamp
		var timestamp
		var new_value

		var cpu_div = program_div.find('div.resource.cpu')
		if ('cpu' in process.resources) {
			sparkline = cpu_div.find('.sparkline')[0];
			last_timestamp = sparkline.data_last_timestamp
			var cpu_values = process.resources.cpu.split(',')
			timestamp = parseFloat(cpu_values[0])
			var cpu = parseFloat(cpu_values[1]) + parseFloat(cpu_values[2])
			if (sparkline.data_last_timestamp !== undefined) {
				new_value = (cpu - sparkline.data_last_cpu) / (timestamp - sparkline.data_last_timestamp)
				if (new_value >= 0) {
					sparkline.data_values.push(Math.round(new_value*100))
					while (sparkline.data_values.length > 60) {
						sparkline.data_values.shift()
					}
				}
				$(sparkline).sparkline(sparkline.data_values, {
					type: 'line',
					height: '32',
					lineWidth: 2,
					chartRangeMin: 0,
					chartRangeMax: 100,
					//normalRangeMin: 0,
					//normalRangeMax: 100,
					//normalRangeColor: '#ffffff',
				})
			} else {
				sparkline.data_values = [];
			}
			sparkline.data_last_cpu = cpu;
			sparkline.data_last_timestamp = timestamp;
			cpu_div.show()
		} else {
			cpu_div.hide()
		}

		var diskio_div = program_div.find('div.resource.diskio')
		if ('diskio' in process.resources) {
			sparkline = diskio_div.find('.sparkline')[0];
			last_timestamp = sparkline.data_last_timestamp
			var diskio_values = process.resources.diskio.split(',')
			timestamp = parseFloat(diskio_values[0])
			var diskio = (parseFloat(diskio_values[3]) + parseFloat(diskio_values[4]))/1024
			if (sparkline.data_last_timestamp !== undefined) {
				new_value = (diskio - sparkline.data_last_diskio) / (timestamp - sparkline.data_last_timestamp)
				if (new_value >= 0) {
					sparkline.data_values.push(Math.round(new_value*100))
					while (sparkline.data_values.length > 60) {
						sparkline.data_values.shift()
					}
				}
				$(sparkline).sparkline(sparkline.data_values, {
					type: 'line',
					height: '32',
					lineWidth: 2,
					//chartRangeMin: 0,
					//chartRangeMax: 100,
					//normalRangeMin: 0,
					//normalRangeMax: 100,
					//normalRangeColor: '#ffffff',
				})
			} else {
				sparkline.data_values = [];
			}
			sparkline.data_last_diskio = diskio;
			sparkline.data_last_timestamp = timestamp;
			diskio_div.show()
		} else {
			diskio_div.hide()
		}

	}
	var state_class = ALERT_LEVEL_CLASSES[alert_level]
	program_div.find('>h5').removeClass('bg-success bg-danger bg-info bg-warning').addClass(state_class)

	if (alert_level > 1) {
		program_div.parent(".group").show();
	}

	return alert_level;
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
			_.template('<%= server %>: <%= group %>:<%= program %> <%= stream %>',
					   {
						   stream: stream,
						   program: program,
						   group: group,
						   server: server,
					   }))

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


window.on_stopall_clicked = function (button)
{
	var server = $(button).parents('div.server').attr('data-server-name')
	$(button).button('loading')
	$.ajax({
        url: get_ajax_url('action'),
		type: 'POST',
		data: {
			server: server,
			action_stop_all: true,
		}
	}).done(function() {
		$(button).button('reset')
	})
}

window.on_startall_clicked = function (button)
{
	var server = $(button).parents('div.server').attr('data-server-name')
	$(button).button('loading')
	$.ajax({
        url: get_ajax_url('action'),
		type: 'POST',
		data: {
			csrftoken: csrftoken,
			server: server,
			action_start_all: true,
		}
	}).done(function() {
		$(button).button('reset')
	})


}


function _group_action(button, action)
{
	var server = $(button).parents('div.server').attr('data-server-name')
	var group = $(button).parents('div.group').attr('data-group-name')
	var data = 	{
		server: server,
		group: group,
		program: '*',
	}
	data[action] = true
	$(button).button('loading')
	$.ajax({
        url: get_ajax_url('action'),
		type: 'POST',
		data: data
	}).done(function() {
		$(button).button('reset')
	})
}

window.on_group_start_clicked = function (button)
{
	_group_action(button, 'action_start')
}

window.on_group_restart_clicked = function (button)
{
	_group_action(button, 'action_restart')
}

window.on_group_stop_clicked = function (button)
{
	_group_action(button, 'action_stop')
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

function filter_by_tags()
{
	var show
	var tag
	var i
	var enabled_tags = {}
	$('.tag-toggles > div.taggroup input:checked').each(function (idx, checkbox) {
		//console.log(checkbox)
		var tag = $(checkbox).attr('data-tag')
		enabled_tags[tag] = true
	})
	// console.log("Filter mode AND: ", TAG_FILTER_MODE_AND)
	// console.log(">>> enabled tags: ", enabled_tags)
	$('div.group').each(function (idx, group_div) {
		var tags = $(group_div).attr('data-tags').split(' ')
		if (tags.length === 1 && tags[0].length === 0)
			tags = []

		if (TAG_FILTER_MODE_AND) {
			// AND
			show = true;
			var have_tags = {}
			for (i in tags) {
				have_tags[tags[i]] = true;
			}
			// console.log(have_tags)
			for (tag in enabled_tags) {
				if (!(tag in have_tags)) {
					show = false;
					break
				}
			}
		} else {
			// OR
			show = tags.length? false : true;
			for (i in tags) {
				if (tags[i] in enabled_tags) {
					show = true
					break
				}
			}
		}
		if (show) {
			$(group_div).show()
		} else {
			$(group_div).hide()
		}
	})

}


function data2procs(data) {
    var procs = [];
    for (var sname in data.supervisors) {
        var sdata = data.supervisors[sname];
        for (var gname in sdata.groups) {
            var gdata = sdata.groups[gname];
            for (var pname in gdata.processes) {
                var proc = gdata.processes[pname];
                proc.supervisor = sname;
                proc.group = gname;
                proc.sup_group = sname + '-' + gname;
                proc.process = pname;
                proc.id = process_id(proc);
                proc.tags = gdata.tags || [];

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
	rv['supervisor'] = new Axis('supervisor');
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
