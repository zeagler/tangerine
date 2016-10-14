<script>
    /***
     * Functions for managing tasks
     ***/
    function disableTask(id) {
        xhttp = new XMLHttpRequest();
        xhttp.open("GET", "disable_task?id="+id, true);
        xhttp.send();
    }

    function stopTask(id) {
        xhttp = new XMLHttpRequest();
        xhttp.open("GET", "stop_task?id="+id, true);
        xhttp.send();
    }

    function misfireTask(id) {
        username = $($("#nav_user")[0]).find('img')[0].alt
        xhttp = new XMLHttpRequest();
        xhttp.open("GET", "queue_task?id="+id+"&username="+username, true);
        xhttp.send();
    }
</script>










<div class="modal-header">
    <button type="button" class="close" data-dismiss="modal">&times;</button>
    % if not task.parent_job == None:
        <h4 class="modal-title">${task.name} - ${job.name}</h4>
    % else:
        <h4 class="modal-title">${task.name}</h4>
    % endif
    <script src="static/scripts.js"></script> 
</div>

<div class="modal-body" style="height: 60%; overflow: auto;">
    <form class="form-horizontal" id="add_task_form" role="form" autocomplete="off">

        <ul id="task_switch" class="nav nav-tabs nav-justified" style="padding-bottom: 10px">
            <li class="active"><a href="#overview" data-toggle="tab">Overview</a></li>
            <li><a href="#container" data-toggle="tab">Container</a></li>
            <li><a href="#env-pane" data-toggle="tab">Environment</a></li>
            <li><a href="#sch" data-toggle="tab">Scheduling</a></li>
            <li><a href="#rsrt" data-toggle="tab">Restart</a></li>
        </ul>
        <div class="tab-content">
            <div class="tab-pane active" id="overview">
                <div class="row">
                    % if not task.parent_job == None:
                        <div class="col-md-6" ><dl class="dl-horizontal"><dt>Next Run: </dt><dd>${job.next_run_str}</dd></dl></div>
                    % else:
                        <div class="col-md-6" ><dl class="dl-horizontal"><dt>Next Run: </dt><dd>${task.next_run_str}</dd></dl></div>
                    % endif
                    <div class="col-md-6"><dl class="dl-horizontal"><dt>Last Success: </dt><dd>${task.last_success_str}</dd></dl></div>
                </div>
                <div class="row">
                    <div class="col-md-6"><dl class="dl-horizontal"><dt>Last Run: </dt><dd>${task.last_run_str}</dd></dl></div>
                    <div class="col-md-6"><dl class="dl-horizontal"><dt>Last Failure: </dt><dd>${task.last_fail_str}</dd></dl></div>
                </div>
                </br>
                </br>
                <dl class="dl-horizontal pull-left" style="padding-left: 0px;">
                    % if not task.parent_job == None:
                        <dt>Parent: </dt><dd>${task.parent_job}</dd></br>
                    % endif
                    <dt>State </dt><dd>${task.state}</dd></br>
                    <dt>Task ID </dt><dd>${task.id}</dd></br>
                    <dt>Description</dt><dd>${task.description}</dd></br>
                </dl>
            </div>

            <div class="tab-pane" id="container">
                <div class="tab-pane active" id="container">
                    <dl class="dl-horizontal">
                        % if task.parent_job == None:
                            <dt>Image </dt><dd>${task.imageuuid}</dd></br>
                            <dt>Command </dt><dd>${task.command_raw}</dd></br>
                            <dt>Entrypoint </dt><dd>${task.entrypoint_raw}</dd></br>
                            <dt>Working Dir </dt><dd></dd></br>
                            <dt>User </dt><dd></dd></br>
                            <dt>Console </dt><dd></dd>
                        % else:
                            % if task.imageuuid == "":
                                <dt>Image </dt><dd style="color: red">${job.imageuuid}</dd></br>
                            % else:
                                <dt>Image </dt><dd>${task.imageuuid}</dd></br>
                            % endif
                            
                            % if task.command_raw == "":
                                <dt>Command </dt><dd style="color: red">${job.command_raw}</dd></br>
                            % else:
                                <dt>Command </dt><dd>${task.command_raw}</dd></br>
                            % endif
                            
                            % if task.entrypoint_raw == "":
                                <dt>Entrypoint </dt><dd style="color: red">${job.entrypoint_raw}</dd></br>
                            % else:
                                <dt>Entrypoint </dt><dd>${task.entrypoint_raw}</dd></br>
                            % endif
                        
                            <dt>Working Dir </dt><dd></dd></br>
                            <dt>User </dt><dd></dd></br>
                            <dt>Console </dt><dd></dd>
                            </br></br>
                        % endif
                    </dl>
                    <p style="color: red">*red fields are inherited from the parent</p>
                </div>
            </div>
            <div class="tab-pane" id="env-pane">
                <dl class="dl-horizontal">
                    % if task.parent_job == None:
                        <dt>Environment </dt>
                        <dd>
                            % for env in task.environment_raw:
                                ${env[0]} = ${env[1]}</br>
                            % endfor
                        </dd></br>
                        <dt>Data Volumes </dt>
                        <dd>
                            % for dvl in task.datavolumes:
                                ${dvl}</br>
                            % endfor
                        </dd></br>
                        <dt>Exposed Ports </dt><dd></dd>
                    % else:
                        <dt>Environment </dt>
                            % for env in task.environment_raw:
                                <dd>${env[0]} = ${env[1]}</dd>
                            % endfor
                            % for env in job.environment_raw:
                                % if "env:" + env[0] in task.removed_parent_defaults:
                                    
                                % elif env[0] in dict(task.environment).keys():
                                
                                % else:
                                    <dd style="color: red">${env[0]} = ${env[1]}<dd>
                                % endif
                            % endfor
                        </br>
                        <dt>Data Volumes </dt>
                            % for dvl in task.datavolumes:
                                <dd>${dvl}<dd>
                            % endfor
                            % for dvl in job.datavolumes:
                                % if "dvl:" + dvl.split(":")[1] in task.removed_parent_defaults:
                                    
                                % elif dvl.split(":")[1] in dict(dvl.split(":") for dvl in task.datavolumes).values():
                                
                                % else:
                                    <dd style="color: red">${dvl}<dd>
                                % endif
                            % endfor
                        </br>
                        <dt>Exposed Ports </dt><dd></dd>
                        </br></br>
                    % endif
                </dl>
                <p style="color: red">*red fields are inherited from the parent</p>
            </div>
            <div class="tab-pane" id="sch">
                <dl class="dl-horizontal">
                    % if task.parent_job == None:
                        <dt>Cron </dt><dd>${task.cron}</dd></br>
                    % else:
                        <dt>Cron </dt><dd style="color: red">${job.cron}</dd></br>
                    % endif
                    <dt>Dependencies</dt>
                    <dd>
                        % for dep in task.dependencies:
                            ${dep}</br>
                        % endfor
                    </dd></br>
                    <dt>Tags</dt>
                    <dd>
                        % for tag in task.tags:
                            ${tag}</br>
                        % endfor
                    </dd></br>
                </dl>
                <p style="color: red">*red fields are inherited from the parent</p>
            </div>
            <div class="tab-pane" id="rsrt">
                <dl class="dl-horizontal">
                    <dt>Restartable</dt><dd>${task.restartable}</dd></br>
                    <dt>Recoverable Exit Codes</dt>
                    <dd>${', '.join(str(rec) for rec in task.recoverable_exitcodes)}</dd></br>
                    <dt>Max Failures</dt><dd>${task.max_failures}</dd></br>
                    <dt>Inital Delay (min)</dt><dd>${task.delay}</dd></br>
                    <dt>Delay After Failure</dt><dd>${task.reschedule_delay}</dd>
                </dl>
            </div>
        </div>
    </form>
</div>

<div class="modal-footer">
    <div class="pull-left">
        <div id="disableTask" class="btn-group">
            <button class="btn btn-danger dropdown-toggle" data-toggle="dropdown">Danger<span class="caret"></span></button>
            <li class="dropdown-menu"><button onclick="delete_task('${task.id}')" class="btn btn-danger" data-dismiss="modal">Delete</button></li>
        </div>
        <button type="button" class="btn btn-default" + data-dismiss="modal" onclick="updateTaskModal('${task.id}')">Update</button>
        <button type="button" class="btn btn-default" + data-dismiss="modal" onclick="cloneTask('${task.id}')">Clone</button>
    </div>
    <button type="button" class="btn btn-default" + data-dismiss="modal" onclick="stopTask('${task.id}')">Stop</button>
    <button type="button" class="btn btn-default" + data-dismiss="modal" onclick="misfireTask('${task.id}')">Misfire</button>
    <button type="button" class="btn btn-default" + data-dismiss="modal">Close</button>
</div>