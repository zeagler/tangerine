<form class="form-horizontal" id="add_task_form" role="form" autocomplete="off">
    <div class="form-group">
        <div class="col-sm-6">
            % if not clone:
                <input class="form-control" name="id" type="hidden" value="${task.id}">
                <input class="form-control" name="name" placeholder="Name" type="text" value="${task.name}">
            % else:
                <input class="form-control" name="name" placeholder="Name" type="text" value="${task.name}-clone">
            % endif
        </div>
      
        <div class="col-sm-6">
          <textarea class="form-control autoExpand" name="desc" rows='1' data-max-rows='3' placeholder="Description" style="overflow-x:hidden; resize: none;" value="${task.description}"></textarea>
        </div>
    </div>
    <ul id="task_switch" class="nav nav-tabs nav-justified" style="padding-bottom: 10px">
        <li class="active"><a href="#container" data-toggle="tab">Container</a></li>
        <li><a href="#env-pane" data-toggle="tab">Environment</a></li>
        <li><a href="#sch" data-toggle="tab">Scheduling</a></li>
        <li><a href="#restart" data-toggle="tab">Restart</a></li>
    </ul>
    <div class="tab-content">
        <div class="tab-pane active" id="container">
            <div class="form-group">
                <label class="control-label col-sm-2">
                    Image <span class="glyphicon glyphicon-question-sign" style="color: lightgrey" data-toggle="tooltip" data-placement="top" title="The images this task will be ran on. You can use `image` or `image:tag`"></span>
                </label>
                <div class="col-sm-10"><input class="form-control" name="image" value="${task.imageuuid}"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Command</label>
                <div class="col-sm-10"><input class="form-control" name="cmd" value="${task.command_raw}"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Entrypoint</label>
                <div class="col-sm-10"><input class="form-control" name="etp" value="${task.entrypoint_raw}"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2 disabled">Working Dir</label>
                <div class="col-sm-10"><input class="form-control" disabled name="wdr" value=""></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2 disabled">User</label>
                <div class="col-sm-10"><input class="form-control" disabled name="usr" value=""></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Console</label>
                <div class="col-sm-10"><input class="form-control" disabled name="csl" value=""></div>
            </div>
        </div>
        <div class="tab-pane" id="env-pane">
            <div class="form-group">
                <span class="col-sm-2">
                    <label class="control-label">Environment</label>
                    <button id="add-env" class="center-block img-circle btn btn-primary btn-add-glyphicon add-more">
                        <span class="glyphicon glyphicon-plus"></span>
                    </button>
                </span>
                <div id="env">
                    % for env in task.environment_raw:
                        <span class="form-inline col-sm-10 pull-right added env"><span class="pull-left" style="width: 100%">
                            <input class="input form-control" style="width: 46%" type="text" value="${env[0]}">
                            <span> = </span>
                            <input class="input form-control" style="width: 46%" type="text" value="${env[1]}">
                            <span> </span>
                            <button class="btn btn-danger remove-this" >-</button>
                        </span></span>
                    % endfor
                </div>
            </div>
            <div class="form-group">
                <span class="col-sm-2">
                    <label class="control-label">Data Volumes</label>
                    <button id="add-dvl" class="center-block img-circle btn btn-primary btn-add-glyphicon add-more">
                        <span class="glyphicon glyphicon-plus"></span>
                    </button>
                </span>
                <div id="dvl">
                    % for dvl in task.datavolumes:
                        <span class="form-inline col-sm-10 pull-right added dvl"><span class="pull-left" style="width: 100%">
                            <input class="input form-control" style="width: 46%" type="text" value="${dvl.split(":")[0]}">
                            <span> : </span>
                            <input class="input form-control" style="width: 46%" type="text" value="${dvl.split(":")[1]}">
                            <span> </span>
                            <button class="btn btn-danger remove-this" >-</button>
                        </span></span>
                    % endfor
                </div>
            </div>
            <div class="form-group disabled">
                <span class="col-sm-2">
                    <label class="control-label">Exposed Ports</label>
                    <button id="add-prt" class="disabled center-block img-circle btn btn-primary btn-add-glyphicon add-more">
                        <span class="glyphicon glyphicon-plus"></span>
                    </button>
                </span>
                <div id="prt">
                    <span class="form-inline col-sm-5 pull-left added prt"><span class="pull-left" style="width: 100%">
                        <input class="disabled input form-control" style="width: 40%" type="text">
                        <span> : </span>
                        <input class="disabled input form-control" style="width: 40%" type="text">
                        <span> </span>
                        <button class="disabled btn btn-danger remove-this" >-</button>
                    </span></span>
                </div>
            </div>
        </div>
        <div class="tab-pane" id="sch">
            <div class="form-group">
                <label class="control-label col-sm-2">State</label>
                <div class="col-sm-10">
                    % if not clone:
                        <input disabled class="form-control input" name="state" style="display: inline-block;" value="${task.state}">
                    % else:
                        <select class="form-control radio-inline" name="state" style="display: inline-block;" placeholder="queued">
                            <option value="queued">queue to run now</option>
                            <option value="waiting">wait until next cron time</option>
                            <option value="stopped">disable until user intervention</option>
                        </select>
                    % endif
                </div>
            </div>
            <div class="form-group fuelux">
                <label class="control-label col-sm-2">Dependencies</label>
                <div class="col-sm-10 pillbox pull-right" data-initialize="pillbox" id="add-dep">
                    <ul class="clearfix pill-group">
                        % for dep in task.dependencies:
                            <li data-value="${dep}" class="btn btn-default pill">
                                <span>${dep}</span>
                                <span class="glyphicon glyphicon-close">
                                    <span class="sr-only">Remove</span>
                                </span>
                            </li>
                        % endfor
                        <li class="pillbox-input-wrap btn-group" id="find-dep">
                            <input type="text" class="form-control typeahead pillbox-add-item" style="min-width: 240px;" placeholder="start typing to find dependencies">
                        </li>
                    </ul>
                </div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Cron</label>
                <div class="col-sm-10"><input class="form-control" name="cron" value="${task.cron}"></div>
            </div>
        </div>
        <div class="tab-pane" id="restart">
            <div class="form-group">
                % if task.restartable:
                    <input type="checkbox" class="checkbox-inline" id="rsrt" checked="true">
                % else:
                    <input type="checkbox" class="checkbox-inline" id="rsrt" value="false">
                % endif
                <label class="control-label">Restartable</label>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Recoverable Exit Codes</label>
                <div class="col-sm-10"><input class="form-control" name="rec" value="${', '.join(str(rec) for rec in task.recoverable_exitcodes)}"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Max Failures</label>
                <div class="col-sm-10"><input class="form-control" name="mxf" value="${task.max_failures}"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Inital Delay(min)</label>
                <div class="col-sm-10"><input class="form-control" name="idl" value="${task.delay}"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Delay After Failure (min)</label>
                <div class="col-sm-10"><input class="form-control" name="daf" value="${task.reschedule_delay}"></div>
            </div>
        </div>
    </div>
</form>