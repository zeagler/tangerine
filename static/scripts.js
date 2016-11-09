var show_job
var button_map = {}
button_map["running"]  = "btn btn-info task Running"
button_map["starting"] = "btn btn-info task Running"
button_map["ready"]    = "btn btn-primary task Ready"
button_map["queued"]   = "btn btn-warning task Queued"
button_map["waiting"]  = "btn btn-warning task Queued"
button_map["failed"]   = "btn btn-danger task Failed"
button_map["success"]  = "btn btn-success task Success"
button_map["stopped"]  = "btn task Stopped"
button_map["stopping"] = "btn task Stopped"

var findTasks = function() {
  return function findMatches(q, cb) {
    var matches, substringRegex;

    matches = [];

    // regex used to determine if a string contains the substring `q`
    substrRegex = new RegExp(q, 'i');

    // iterate through the pool of strings and for any string that
    // contains the substring `q`, add it to the `matches` array
    job = $("#parent_job").val();
    if (job == "NULL") job = null

    $.each($tasks, function(i, str) {
      if (str.state !== "disabled" && str.parent_job == job) {
          $.each(str.tags, function(i, tag) {
              if (substrRegex.test(tag) && matches.indexOf("tag:"+tag) < 0) {
                matches.push("tag:"+tag);
              }
          })
          if (substrRegex.test(str.name)) {
            matches.push(str.name);
          }
      }
    });

    cb(matches);
  };
};

var findTags = function() {
  return function findMatches(q, cb) {
    var matches, substringRegex;

    matches = [];

    // regex used to determine if a string contains the substring `q`
    substrRegex = new RegExp(q, 'i');

    // iterate through the pool of strings and for any string that
    // contains the substring `q`, add it to the `matches` array
    job = $("#parent_job").val();
    if (job == "NULL") job = null

    $.each($tasks, function(i, str) {
        $.each(str.tags, function(i, tag) {
            if (substrRegex.test(tag) && matches.indexOf(tag) < 0) {
              matches.push(tag);
            }
        })
    });

    cb(matches);
  };
};

var findJobs = function() {
    return $jobs
};

var getTasks = function() {
    return $tasks
};

var findJob = function(job_id) {
    for (var i = 0; i < $jobs.length; i++) {
        if ($jobs[i].id == job_id)
            return $jobs[i]
    }
    return null
};

var add_more_handler = function(button) {
    if (button == "add-env") {
        split = " = "
        section = "environment";
        type = "env";
    } else if (button == "add-dvl") {
        split = " : "
        section = "datavolumes";
        type = "dvl";
    } else if (button == "add-prt") {
        split = " : "
        type = "prt";
    }
    
    $("#" + section).append('<span class="form-inline col-sm-10 pull-right added '+type+'"><span class="pull-left" style="width: 100%">' +
                  '<input class="input form-control" style="width: 46%" type="text">' +
                  split +
                  '<input class="input form-control" style="width: 46%" type="text">' +
                  ' ' +
                  '<button class="btn btn-danger remove-this" >-</button>' +
                  '</span></span>');
    
    $('.remove-this').click(function(e) {
        e.preventDefault();
        $(this).parent().parent().remove();
    });
}

$(document).ready(function(e) {
    // Add type ahead for the search box
/*
    $('#find-task .typeahead').typeahead({
        hint: false,
        highlight: true,
        minLength: 1
    },
    {
        name: 'tasks',
        source: findTasks()
    });
*/
});

$(document).on('click', '#switch li', function (e) {
    show_state($(this).text());
});

// Clear the DOM whenever a modal is dismissed
$('#displayTaskModal, #addTaskModal, #updateTaskModal, #cloneTaskModal, #jobModal').on('hidden.bs.modal',function(e){
    $($(this).find('.modal-content')).html("")
});

// Auto expand description box
$(document)
    .one('focus.textarea', '.autoExpand', function() {
        this.baseScrollHeight = this.scrollHeight;
        this.maxRows = this.getAttribute('data-max-rows');
    })
    .on('input.textarea', '.autoExpand', function(){
        this.rows = 1
        rows = Math.ceil((this.scrollHeight - this.baseScrollHeight) / 36)+1;
        this.rows = (rows<this.maxRows) ? rows : this.maxRows;
    });
    
function set_job(job) {
    show_job = job
    loadTasks()
}

function loadHosts() {
    $.get('get_hosts', function(data) {
        json = JSON.parse(data);
        
        if (json.redirect) {
            window.location.href = json.redirect;
        } else {
            $hosts = json.hosts;
            task_count = json.queued_task_count;
            host_count = 0;
            hosts_updated = "";
            
            for (var i = 0; i < $hosts.length; i++) {
                var tasks = ""
                for (var j = 0; j < $hosts[i].tasks.length; j++) {
                    if ($hosts[i].tasks[j].result_state == "success") {
                        task_state = "success"
                    } else if ($hosts[i].tasks[j].result_state == "failed" || $hosts[i].tasks[j].result_state == "host failure") {
                        task_state = "danger"
                    } else if ($hosts[i].tasks[j].result_state == "stopped") {
                        task_state = "default"
                    } else {
                        task_state = "info"
                    }
                    
                    tasks += '<div class="host_task"' +
                                  ' onclick="displayRunModal(' + $hosts[i].tasks[j].run_id + ')"' +
                                  ' data-toggle="tooltip" title="'+$hosts[i].tasks[j].name + "_" + $hosts[i].tasks[j].run_id+'">' +
                                  '<span class="fa fa-circle color-' + task_state + '"/>' +
                                  '<span>' +
                                          " " + $hosts[i].tasks[j].name + "_" + $hosts[i].tasks[j].run_id +
                                  '</span>' +
                              '</div>'
                }
                
                if (tasks == "") tasks='<p class="host_task">No Tasks</p>'
              
                if ($hosts[i].state == "inactive") {
                    var date = new Date($hosts[i].agent_termination_time*1000);
                    hosts_updated +=
                    '<div class="host_card panel panel-default">' +
                        '<div class="panel-body">' +
                            '<p class="host_ip">' + $hosts[i].host_ip + '</p>' +
                            '<p class="host_specs">' + $hosts[i].instance_type + ' | ' + ($hosts[i].available_memory/1024/1024).toFixed(2) + 'GB</p>' +
                            '<div class="active-host background-danger">Terminated: ' + date.getHours() + ':' + ("0" + date.getMinutes()).substr(-2) + '</div>' +
                            '<div class="well">' + tasks + '</div>' +
                        '</div>' +
                    '</div>'
                } else {
                    host_count++;
                    hosts_updated +=
                    '<div class="host_card panel panel-default">' +
                        '<div class="panel-body">' +
                            '<p class="host_ip">' + $hosts[i].host_ip + '</p>' +
                            '<p class="host_specs">' + $hosts[i].instance_type + ' | ' + ($hosts[i].available_memory/1024/1024).toFixed(2) + 'GB</p>' +
                            '<div class="active-host background-primary">Active</div>' +
                            '<div class="well">' + tasks + '</div>' +
                        '</div>' +
                    '</div>'
                }
            }

            if (hosts_updated == "") {
                $('#host_container').html('<div class="empty_hosts">No Hosts Available</div>')
            } else {
                $('#host_container').html(hosts_updated)
            }
            $('#host_count').html(host_count)
            $('#task_count').html(task_count)
            $('[data-toggle="tooltip"]').tooltip()
        }
    });
}

// refresh the tasks
function loadTasks() {
    $.get('get_project', function(data) {
        json = JSON.parse(data);
        
        if (json.redirect) {
            window.location.href = json.redirect;
        } else {
            $tasks = json.tasks;
            $jobs = json.jobs;
            
            job_updated = "";
            updated = "";
            
            for (var i = 0; i < $jobs.length; i++) {
                if ($jobs[i].state == "disabled" || $jobs[i].state == "disabling") {
                   continue
                }
                if (show_job !== null && $jobs[i].id == show_job) {
                    // This is the root job, display it seperately from the badges
                    job_updated += '<div id="job_panel" class="panel panel-default">' +
                                        '<div class="row" style="width: 98%; margin-left: 1%; overflow: hidden">' +
                                            '<div class="col-md-1 hidden-sm hidden-xs">' + 
                                                '<button id="job_back" class="btn fa fa-angle-left job_back" onmouseover="this.style.backgroundColor=\'#b1b1b1\'" onmouseout="this.style.backgroundColor=\'#dddddd\'" onclick="set_job(' + $jobs[i].parent_job + ')"></button>' +
                                            '</div>' + 
                                            '<div id="job_body" class="col-md-9 col-xs-12">' + 
                                                '<div id="job_title" class="hidden-sm hidden-xs" style="margin-top: 1%; width: 100%; text-overflow: ellipsis; overflow: hidden; text-align: center;">' + 
                                                    '<font size="3"><strong>' + $jobs[i].name + '</strong></font>' + 
                                                '</div>' + 
                                                '<div id="job_title" class="hidden-md hidden-lg hidden-xl center_all" style="margin-top: 1%; display: flex; width: 100%; height: 60px;">' + 
                                                    '<div style="width: 60px; margin-right: 2%;"><button id="job_back" class="btn fa fa-angle-left" style="margin-top: 0" onmouseover="this.style.backgroundColor=\'#b1b1b1\'" onmouseout="this.style.backgroundColor=\'#dddddd\'" onclick="set_job(' + $jobs[i].parent_job + ')"></button></div>' +
                                                    '<div class="hide-overflow" style="margin-top: 20px;"><font size="3"><strong>' + $jobs[i].name + '</strong></font></div>' + 
                                                '</div>' + 
                                                '<div style="margin: 2%;">' +
                                                    '<div class="row hidden-xs hidden-sm">' + 
                                                        '<div class="col-md-4 hidden-xs hide-overflow" style="display: flex;">' +
                                                            '<div style="font-weight: bold; margin-right: 4px; text-align: right;">State:</br>Image:</br></br>Next Run:</br>Last Run:</div>' + 
                                                            '<div class="hide-overflow">' + $jobs[i].state + '</br>' + $jobs[i].imageuuid + '</br></br>' + $jobs[i].next_run_str + '</br>' + $jobs[i].last_run_str + '</div>' + 
                                                        '</div>' + 
                                                        '<div class="col-md-8 hidden-xs hide-overflow" style="display: flex;">' +
                                                            '<div style="font-weight: bold; margin-right: 4px; text-align: right;">Id:</br>Command:</br>Entrypoint:</div>' + 
                                                            '<div class="hide-overflow">' + $jobs[i].id + '</br>' + $jobs[i].command_raw + '</br>' + $jobs[i].entrypoint_raw + '</div>' + 
                                                        '</div>' + 
                                                    '</div>' + 
                                                    '<div class="row hidden-xs hidden-md hidden-lg hidden-xl">' + 
                                                        '<div class="hide-overflow" style="display: flex;">' +
                                                            '<div style="font-weight: bold; margin-right: 4px; text-align: right;">Id:</br>State:</br>Image:</br>Next Run:</br>Last Run:</br>Command:</br>Entrypoint:</div>' + 
                                                            '<div class="hide-overflow">' + $jobs[i].id + '</br>' + $jobs[i].state + '</br>' + $jobs[i].imageuuid + '</br></br>' + $jobs[i].next_run_str + '</br>' + $jobs[i].last_run_str + '</br>' + $jobs[i].command_raw + '</br>' + $jobs[i].entrypoint_raw + '</div>' + 
                                                        '</div>' + 
                                                    '</div>' + 
                                                '</div>' + 
                                            '</div>' + 
                                            '<div class="col-md-2 hidden-xs hidden-sm">' + 
                                                '<div class="btn-toolbar" style="width: 100%; margin-top: 25%">' + 
                                                    '<div class="btn-group-vertical" style="width: 48%; margin-right: 4%;">' + 
                                                        '<button type="button" class="btn btn-default" style="margin-bottom: 10px;" onclick="displayJobMisfire(\''+$jobs[i].id+'\', \''+$jobs[i].name+'\')">Misfire</button>' +
                                                        '<button type="button" class="btn btn-default" onclick="displayJobStop(\''+$jobs[i].id+'\', \''+$jobs[i].name+'\')">Stop</button>' +
                                                    '</div>' + 
                                                    '<div class="btn-group-vertical" style="width: 48%;">' + 
                                                        '<button type="button" class="btn btn-default" style="margin-bottom: 10px;" onclick="displayJobUpdate(\''+$jobs[i].id+'\', \''+$jobs[i].name+'\')">Update</button>' +
                                                        '<button type="button" class="btn btn-danger" onclick="displayJobDanger(\''+$jobs[i].id+'\', \''+$jobs[i].name+'\')">Danger</button>' +
                                                    '</div>' + 
                                                '</div>' + 
                                            '</div>' + 
                                            '<div class="col-xs-12 hidden-md hidden-lg hidden-xl">' + 
                                                '<div class="btn-toolbar" style="width: 100%;">' + 
                                                    '<div class="btn-group-vertical" style="width: 48%; margin-right: 4%;">' + 
                                                        '<button type="button" class="btn btn-default" style="margin-bottom: 10px;" onclick="displayJobMisfire(\''+$jobs[i].id+'\', \''+$jobs[i].name+'\')">Misfire</button>' +
                                                        '<button type="button" class="btn btn-default" onclick="displayJobStop(\''+$jobs[i].id+'\', \''+$jobs[i].name+'\')">Stop</button>' +
                                                    '</div>' + 
                                                    '<div class="btn-group-vertical" style="width: 48%">' + 
                                                        '<button type="button" class="btn btn-default" style="margin-bottom: 10px;" onclick="displayJobUpdate(\''+$jobs[i].id+'\', \''+$jobs[i].name+'\')">Update</button>' +
                                                        '<button type="button" class="btn btn-danger" onclick="displayJobDanger(\''+$jobs[i].id+'\', \''+$jobs[i].name+'\')">Danger</button>' +
                                                    '</div>' + 
                                                '</div>' + 
                                            '</div>' + 
                                        '</div>' + 
                                    '</div>'
                    continue
                } else if (show_job !== null && $jobs[i].parent_job !== show_job) {
                    // This job is not a child of the root job, it should not be displayed
                    continue
                } else if (show_job == null && $jobs[i].parent_job !== null) {
                    // This job is a child of a job and should not be displayed in the root view
                    continue
                }

                if ($jobs[i].warning == true) {
                    badge_text = '<p><font size="6" color="yellow"> ! </font>  '+$jobs[i].name+'  <font size="6" color="yellow"> ! </font></p>';
                    warning = 'data-toggle="tooltip" title="'+$jobs[i].warning_message+'"'
                } else {
                    badge_text = '<p>'+$jobs[i].name+'</p>';
                    warning = ''
                }
                
                updated +=
                '<button ' + warning + ' id="job" type="button" ' +
                        'class="'+button_map[$jobs[i].state]+' d-inline-block" ' +
                        'onclick="set_job('+$jobs[i].id+')" ' +
                        'style="box-shadow:0px 0px 3px 6px gold inset; border: 0px"' +
                '">' + 
                    badge_text +
                '</button>';
            }
            
            for (var i = 0; i < $tasks.length; i++) {
                if ($tasks[i].state == "disabled" || $tasks[i].state == "disabling") {
                   continue
                }
                
                if (show_job !== null && $tasks[i].parent_job !== show_job) {
                    continue
                } else if (show_job == null && $tasks[i].parent_job !== null) {
                    continue
                }
                
                if ($tasks[i].warning == true) {
                    badge_text = '<p><font size="6" color="yellow"> ! </font>  '+$tasks[i].name+'  <font size="6" color="yellow"> ! </font></p>';
                    warning = 'data-toggle="tooltip" title="'+$tasks[i].warning_message+'"'
                } else {
                    badge_text = '<p>'+$tasks[i].name+'</p>';
                    warning = ''
                }

                updated +=
                '<button ' + warning + ' id="task" type="button" ' +
                        'class="'+button_map[$tasks[i].state]+' d-inline-block"' +
                        'onclick="displayTaskModal(\''+$tasks[i].id+'\')' +
                '">' + 
                    badge_text +
                '</button>';
            }
            
            $('#job_panel').html(job_updated)
            $('#tasks').html(updated)
            show_state($(".active")[1].textContent)
            $('[data-toggle="tooltip"]').tooltip()
        }
    });
}

function show_state(state) {
    var tasks = document.getElementsByClassName("task");
    var i = 0;
    
    if (state == "All")
        
        for (i=0; i<tasks.length; i++)
            tasks[i].style.display = '';
    else {
        for (i=0; i<tasks.length; i++)
            tasks[i].style.display = 'none';

        tasks = document.getElementsByClassName("task " + state);
        for (i=0; i<tasks.length; i++)
            tasks[i].style.display = '';
    }
}

function stop_job(id) {
    username = $($("#nav_user")[0]).find('img')[0].alt
    xhttp = new XMLHttpRequest();
    
    state = ""
    
    $.each($(".stateSelector"), function(i, str) {
        if (str.checked) {
            state += "&state=" + str.value
        }
    });

    
    xhttp.open("GET", "stop_job?id="+id+"&username="+username+state, true);
    xhttp.send();
}

function queue_job(id) {
    username = $($("#nav_user")[0]).find('img')[0].alt
    xhttp = new XMLHttpRequest();
    
    state = ""
    
    $.each($(".stateSelector"), function(i, str) {
        if (str.checked) {
            state += "&state=" + str.value
        }
    });

    xhttp.open("GET", "queue_job?id="+id+"&username="+username+state, true);
    xhttp.send();
}

function delete_job(id) {
    set_job(null)
    username = $($("#nav_user")[0]).find('img')[0].alt
    xhttp = new XMLHttpRequest();
    xhttp.open("GET", "delete_job?id="+id+"&username="+username+"&mode=1", true);
    xhttp.send();
}

function delete_task(id) {
    username = $($("#nav_user")[0]).find('img')[0].alt
    xhttp = new XMLHttpRequest();
    xhttp.open("GET", "delete_task?id="+id+"&username="+username);
    xhttp.send();
}

function displayJobMisfire(id, name) {
  $('#display-job-modal-content').html(
        '<div class="modal-header">' +
            '<button type="button" class="close" data-dismiss="modal">&times;</button>' +
            '<h4 class="modal-title" style="text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">Misfire ' + name + '?</h4>' +
        '</div>' +

        '<div class="modal-body">' +
            '<div class="text-center">' +
                '<p>Which tasks should be misfired? Selected tasks will stop and be restarted.</p>' + 
                '<input type="checkbox" id="queueFailed" class="stateSelector" value="failed" style="margin-left: 20px" checked> failed</input>' +
                '<input type="checkbox" id="queueStopped" class="stateSelector" value="stopped&state=stopping" style="margin-left: 20px" checked> stopped</input>' +
                '<input type="checkbox" id="queueQueued" class="stateSelector" value="queued&state=waiting" style="margin-left: 20px"> queued</input>' +
                '<input type="checkbox" id="queueRunning" class="stateSelector" value="running&state=starting&state=ready" style="margin-left: 20px"> running</input>' +
                '<input type="checkbox" id="queueSucceeded" class="stateSelector" value="success" style="margin-left: 20px"> succeeded</input>' +
                '<input type="checkbox" id="selectAll" style="margin-left: 20px"> all</input>' +
                '<br><br>' +
                '<button class="btn btn-default" class="close" data-dismiss="modal" style="margin-right: 40px;">Cancel</button>' +
                '<button class="btn btn-success" class="close" data-dismiss="modal" onclick="queue_job(' + id + ')">Comfirm</button>' +
            '</div>' +
        '</div>' +
        
        '<script>' + 
            'var checkedStates = [];' +
            '$("#selectAll").change(function() {' +
                'if($(this).is(":checked")) {' +
                    'checkedStates = [];' +
                    '$.each($(".stateSelector:checked"), function () { checkedStates.push(this.id); });' +
                    '$(".stateSelector").prop("checked", true);' +
                '} else {' +
                    '$(".stateSelector").prop("checked", false);' +
                    '$.each(checkedStates, function () { $("#" + this).prop("checked", true) });' +
                '}' +
            '});' +
            '$(".stateSelector").change(function() {' +
                'if($(this).is(":checked")) {' +
                    'if ($(".stateSelector:checked").length == 5) {' +
                        '$("#selectAll").prop("checked", true);' + 
                    '}' +
                '} else {' +
                    '$("#selectAll").prop("checked", false);' + 
                '}' +
            '});' +
        '</script>'
  );
  $('[data-toggle="tooltip"]').tooltip()
  $('#jobModal').modal('show');
}

function displayJobStop(id, name) {
  $('#display-job-modal-content').html(
        '<div class="modal-header">' +
            '<button type="button" class="close" data-dismiss="modal">&times;</button>' +
            '<h4 class="modal-title" style="text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">Stop ' + name + '?</h4>' +
        '</div>' +

        '<div class="modal-body">' +
            '<div class="text-center">' +
                '<p>Which tasks should be stopped?</p>' + 
                '<input type="checkbox" id="stopFailed" class="stateSelector" value="failed" style="margin-left: 20px"> failed</input>' +
                '<input type="checkbox" id="stopQueued" class="stateSelector" value="queued&state=waiting&state=ready" style="margin-left: 20px" checked> queued</input>' +
                '<input type="checkbox" id="stopRunning" class="stateSelector" value="running&state=starting&state=ready" style="margin-left: 20px" checked> running</input>' +
                '<input type="checkbox" id="stopSucceeded" class="stateSelector" value="success" style="margin-left: 20px"> succeeded</input>' +
                '<input type="checkbox" id="selectAll" style="margin-left: 20px"> all</input>' +
                '<br><br>' +
                '<button class="btn btn-default" class="close" data-dismiss="modal" style="margin-right: 20px;">Cancel</button>' +
                '<button class="btn btn-danger" class="close" data-dismiss="modal" onclick="stop_job(' + id + ')">Stop Job</button>' +
            '</div>' +
        '</div>' +
        
        '<script>' + 
            'var checkedStates = [];' +
            '$("#selectAll").change(function() {' +
                'if($(this).is(":checked")) {' +
                    'checkedStates = [];' +
                    '$.each($(".stateSelector:checked"), function () { checkedStates.push(this.id); });' +
                    '$(".stateSelector").prop("checked", true);' +
                '} else {' +
                    '$(".stateSelector").prop("checked", false);' +
                    '$.each(checkedStates, function () { $("#" + this).prop("checked", true) });' +
                '}' +
            '});' +
            '$(".stateSelector").change(function() {' +
                'if($(this).is(":checked")) {' +
                    'if ($(".stateSelector:checked").length == 4) {' +
                        '$("#selectAll").prop("checked", true);' + 
                    '}' +
                '} else {' +
                    '$("#selectAll").prop("checked", false);' + 
                '}' +
            '});' +
        '</script>'
  );
  $('#jobModal').modal('show');
}

function displayJobUpdate(id, name) {
    $('#update-task-modal-content').load("update_job_form?id=" + id, function() {
        $('#updateTaskModal').modal('show');
    });
}

function displayJobDanger(id, name) {
  $('#display-job-modal-content').html(
        '<div class="modal-header">' +
            '<button type="button" class="close" data-dismiss="modal">&times;</button>' +
            '<h4 class="modal-title" style="text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">Delete ' + name + '?</h4>' +
        '</div>' +

        '<div class="modal-body">' +
            '<div class="text-center">' +
                // '<input type="checkbox" id="deleteTasks" value="delete"> Delete Children? <span class="glyphicon glyphicon-question-sign" style="color: darkgrey" data-toggle="tooltip" data-placement="top" title="If this is checked all child tasks will be deleted. If this is not checked, child tasks will be moved to the root."></span>' +
                '<p>This will delete the job and all tasks contained in the job.</p>' + 
                '<br>' +
                '<button class="btn btn-default" class="close" data-dismiss="modal" style="margin-right: 20px;">Cancel</button>' +
                '<button class="btn btn-danger" class="close" data-dismiss="modal" onclick="delete_job(' + id + ')">Delete Job</button>' +
            '</div>' +
        '</div>'
  );
  $('[data-toggle="tooltip"]').tooltip()
  $('#jobModal').modal('show');
}

function addBulkModal() {
    $('#add-task-modal-content').load("bulk_add_form", function() {
        $('#addTaskModal').modal('show');
    });
}

function addJobModal() {
    $('#add-task-modal-content').load("new_job_form", function() {
        $('#addTaskModal').modal('show');
    });
}

function addTaskModal() {
    $('#add-task-modal-content').load("new_task_form", function() {
        $('#addTaskModal').modal('show');
    });
}

function updateTaskModal(id) {
    $('#update-task-modal-content').load("update_task_form?id=" + id, function() {
        $('#updateTaskModal').modal('show');
    });
}

function displayTaskModal(id) {
    $('#display-task-modal-content').load("display_task?id=" + id, function() {
        $('#displayTaskModal').modal('show');
    });
}

function displayRunModal(id) {
    $('#display-run-modal-content').load("display_run?id=" + id, function() {
        $('#displayRunModal').modal('show');
    });
}

function cloneTask(id) {
    $('#clone-task-modal-content').load("update_task_form?id=" + id + "&clone=true", function() {
        $('#cloneTaskModal').modal('show');
    });
}