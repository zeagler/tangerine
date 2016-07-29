<form class="form-horizontal" id="add_task_form" role="form" autocomplete="off">
    <div class="form-group">
        <div class="col-sm-6">
            <input class="form-control" name="name" placeholder="Name" type="text">
        </div>
      
        <div class="col-sm-6">
          <textarea class="form-control autoExpand" name="desc" rows='1' data-max-rows='3' placeholder="Description" style="overflow-x:hidden; resize: none;"></textarea>
        </div>
    </div>
    <ul id="task_switch" class="nav nav-tabs nav-justified" style="padding-bottom: 10px">
        <li class="active"><a href="#container" data-toggle="tab">Container</a></li>
        <li><a href="#env-pane" data-toggle="tab">Environment</a></li>
        <li><a href="#sch" data-toggle="tab">Scheduling</a></li>
        <li><a href="#rsrt" data-toggle="tab">Restart</a></li>
    </ul>
    <div class="tab-content">
        <div class="tab-pane active" id="container">
            <div class="form-group">
                <label class="control-label col-sm-2">
                    Image <span class="glyphicon glyphicon-question-sign" style="color: lightgrey" data-toggle="tooltip" data-placement="top" title="The images this task will be ran on. You can use `image` or `image:tag`"></span>
                </label>
                <div class="col-sm-10"><input class="form-control" name="image"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Command</label>
                <div class="col-sm-10"><input class="form-control" name="cmd"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Entrypoint</label>
                <div class="col-sm-10"><input class="form-control" name="etp"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2 disabled">Working Dir</label>
                <div class="col-sm-10"><input class="form-control" disabled name="wdr"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2 disabled">User</label>
                <div class="col-sm-10"><input class="form-control" disabled name="usr"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Console</label>
                <div class="col-sm-10"><input class="form-control" disabled name="csl"></div>
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
                    <span class="form-inline col-sm-10 pull-right added env"><span class="pull-left" style="width: 100%">
                        <input class="input form-control" style="width: 46%" type="text">
                        <span> = </span>
                        <input class="input form-control" style="width: 46%" type="text">
                        <span> </span>
                        <button class="btn btn-danger remove-this" >-</button>
                    </span></span>
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
                    <span class="form-inline col-sm-10 pull-right added dvl"><span class="pull-left" style="width: 100%">
                        <input class="input form-control" style="width: 46%" type="text">
                        <span> : </span>
                        <input class="input form-control" style="width: 46%" type="text">
                        <span> </span>
                        <button class="btn btn-danger remove-this" >-</button>
                    </span></span>
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
                    <select class="form-control radio-inline" name="state" style="display: inline-block;" placeholder="queued">
                        <option value="queued">queue to run now</option>
                        <option value="waiting">wait until next cron time</option>
                        <option value="stopped">disable until user intervention</option>
                    </select>
                </div>
            </div>
            <div class="form-group fuelux">
                <label class="control-label col-sm-2">Dependencies</label>
                <div class="col-sm-10 pillbox pull-right" data-initialize="pillbox" id="add-dep">
                    <ul class="clearfix pill-group">
                        <li class="pillbox-input-wrap btn-group" id="find-dep">
                            <input type="text" class="form-control typeahead pillbox-add-item" style="min-width: 240px;" placeholder="start typing to find dependencies">
                        </li>
                    </ul>
                </div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Cron</label>
                <div class="col-sm-10"><input class="form-control" name="cron"></div>
            </div>
        </div>
        <div class="tab-pane" id="rsrt">
            <div class="form-group">
                <input type="checkbox" class="checkbox-inline" id="rsrt" name="rsrt" checked="true"">
                <label class="control-label">Restartable</label>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Recoverable Exit Codes</label>
                <div class="col-sm-10"><input class="form-control" name="rec" value="0""></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Max Failures</label>
                <div class="col-sm-10"><input class="form-control" name="mxf" value="3"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Inital Delay(min)</label>
                <div class="col-sm-10"><input class="form-control" name="idl" value="0"></div>
            </div>
            <div class="form-group">
                <label class="control-label col-sm-2">Delay After Failure (min)</label>
                <div class="col-sm-10"><input class="form-control" name="daf" value="5"></div>
            </div>
        </div>
    </div>
</form>